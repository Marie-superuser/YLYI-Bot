"""
YLYI-Bot ingestor — builds a SQLite database from Excel source files.

Phase 1 — Extract: read every .xlsx in /data/source into DataFrames.
Phase 2 — Load:    write to /data/ylyi.db with normalized schema.
           - Hash-based incremental updates: unchanged files are skipped.
           - Schema normalization across 3 eras of column naming (AY21-AY25).
           - Unmapped columns stored as JSON for forward compatibility.
           - Academic year and quarter derived from filename.
"""

import hashlib
import json
import logging
import os
import re
import sqlite3
import sys
from pathlib import Path

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

SOURCE_DIR = Path(os.environ.get("SOURCE_DIR", "/data/source"))
DB_PATH    = Path(os.environ.get("DB_PATH",    "/data/ylyi.db"))

# ── Column normalisation ──────────────────────────────────────────────────────
# Keys are lowercased, stripped column names from the source files.
# Values are canonical SQLite column names.
COLUMN_MAP: dict[str, str] = {
    "date":                                    "date",
    "service":                                 "service",
    "location":                                "location",
    "duration (mins.)":                        "duration_mins",
    "duration (mins)":                         "duration_mins",
    "signed up attendees count":               "attendees",
    # AY24-25
    "pnwu status":                             "pnwu_status",
    "pnwu academic affiliation":               "pnwu_affiliation",
    "topic":                                   "topic",
    "additional notes":                        "notes",
    "virtual/library meeting":                 "meeting_format",
    "tell us about your research project":     "topic",
    "tells us about your research project":    "topic",   # Q3 AY24-25 typo
    # AY21-22 / AY22-23
    "status":                                  "pnwu_status",
    "program/dept":                            "pnwu_affiliation",
    "event type":                              "event_type",
    "booking id":                              "booking_id",
    "tracking data":                           "tracking_data",
}

# Columns that hold free-text custom fields — captured in extra_fields JSON.
SKIP_PREFIXES = ("custom fields", "column")


def normalise_col(name: str) -> str | None:
    """Return canonical name, None to skip, or '__extra__' to put in JSON."""
    key = name.strip().lower()
    if key in COLUMN_MAP:
        return COLUMN_MAP[key]
    if any(key.startswith(p) for p in SKIP_PREFIXES):
        return "__extra__"
    return "__extra__"


# ── Filename metadata ─────────────────────────────────────────────────────────

def parse_filename_meta(stem: str) -> dict[str, str]:
    """Extract academic_year and quarter from a filename stem."""
    ay_match = re.search(r"AY\s*(\d{2}-\d{2})", stem, re.IGNORECASE)
    q_match  = re.search(r"\bQ([1-4])\b", stem, re.IGNORECASE)
    return {
        "academic_year": f"AY{ay_match.group(1)}" if ay_match else "",
        "quarter":       f"Q{q_match.group(1)}"   if q_match  else "",
    }


# ── SQLite schema ─────────────────────────────────────────────────────────────

DDL = """
CREATE TABLE IF NOT EXISTS ingest_metadata (
    filename      TEXT NOT NULL,
    sheet_name    TEXT NOT NULL,
    file_hash     TEXT NOT NULL,
    table_name    TEXT NOT NULL,
    rows_ingested INTEGER DEFAULT 0,
    ingested_at   TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (filename, sheet_name)
);

CREATE TABLE IF NOT EXISTS appointments (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file      TEXT,
    source_sheet     TEXT,
    academic_year    TEXT,
    quarter          TEXT,
    date             TEXT,
    service          TEXT,
    location         TEXT,
    duration_mins    REAL,
    attendees        INTEGER,
    pnwu_status      TEXT,
    pnwu_affiliation TEXT,
    topic            TEXT,
    notes            TEXT,
    meeting_format   TEXT,
    event_type       TEXT,
    booking_id       TEXT,
    tracking_data    TEXT,
    extra_fields     TEXT,
    ingested_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS survey_responses (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file   TEXT,
    source_sheet  TEXT,
    survey_year   TEXT,
    row_data      TEXT,
    ingested_at   TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_appt_date         ON appointments(date);
CREATE INDEX IF NOT EXISTS idx_appt_service      ON appointments(service);
CREATE INDEX IF NOT EXISTS idx_appt_location     ON appointments(location);
CREATE INDEX IF NOT EXISTS idx_appt_ay           ON appointments(academic_year);
CREATE INDEX IF NOT EXISTS idx_appt_quarter      ON appointments(quarter);
"""

APPOINTMENT_COLS = [
    "date", "service", "location", "duration_mins", "attendees",
    "pnwu_status", "pnwu_affiliation", "topic", "notes",
    "meeting_format", "event_type", "booking_id", "tracking_data",
]


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(DDL)
    conn.commit()


# ── Hash ──────────────────────────────────────────────────────────────────────

def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ── Sheet classification ──────────────────────────────────────────────────────

def is_appointment_sheet(sheet_name: str, df: pd.DataFrame) -> bool:
    """True if this sheet looks like booking/appointment data."""
    cols = {c.strip().lower() for c in df.columns}
    return "date" in cols and "service" in cols


def is_survey_sheet(sheet_name: str, filename: str) -> bool:
    return "satisfaction survey" in filename.lower() or "survey" in filename.lower()


def is_master_sheet(sheet_name: str) -> bool:
    """True if this is the file's consolidated 'ALL-...' bookings sheet.

    AY23-24/AY24-25 exports contain an ALL-BookingsReportingData master sheet
    plus per-category breakout sheets (Bioethics, Library Access, etc.) that are
    subsets of the master. Ingesting both double-counts every appointment.
    """
    return sheet_name.strip().lower().startswith("all")


# ── Row normalisation ─────────────────────────────────────────────────────────

def normalise_value(val) -> str | None:
    """Convert NaN / blank to None; strip strings; clean dates to ISO."""
    if val is None:
        return None
    if isinstance(val, float) and pd.isna(val):
        return None
    if isinstance(val, pd.Timestamp):
        if pd.isna(val):
            return None
        # Appointment dates carry no meaningful time — drop a midnight component.
        if (val.hour, val.minute, val.second) == (0, 0, 0):
            return val.strftime("%Y-%m-%d")
        return val.strftime("%Y-%m-%d %H:%M:%S")
    s = str(val).strip()
    return None if s in ("", "nan", "NaT", "None") else s


def df_to_appointment_rows(
    df: pd.DataFrame,
    source_file: str,
    source_sheet: str,
    academic_year: str,
    quarter: str,
) -> list[dict]:
    rows = []
    for _, raw in df.iterrows():
        record: dict[str, object] = {
            "source_file":   source_file,
            "source_sheet":  source_sheet,
            "academic_year": academic_year,
            "quarter":       quarter,
        }
        extra: dict[str, str] = {}

        for raw_col, raw_val in raw.items():
            canonical = normalise_col(str(raw_col))
            value     = normalise_value(raw_val)
            if canonical is None or canonical == "__extra__":
                if value is not None:
                    extra[str(raw_col).strip()] = value
            else:
                # Don't overwrite a value already set (e.g. topic mapped twice)
                if canonical not in record or record[canonical] is None:
                    record[canonical] = value

        # Ensure all expected columns present
        for col in APPOINTMENT_COLS:
            record.setdefault(col, None)

        record["extra_fields"] = json.dumps(extra) if extra else None
        rows.append(record)
    return rows


# ── Database writes ───────────────────────────────────────────────────────────

def upsert_appointments(
    conn: sqlite3.Connection,
    rows: list[dict],
    source_file: str,
    source_sheet: str,
) -> int:
    conn.execute(
        "DELETE FROM appointments WHERE source_file=? AND source_sheet=?",
        (source_file, source_sheet),
    )
    if not rows:
        return 0
    cols = [
        "source_file", "source_sheet", "academic_year", "quarter",
        *APPOINTMENT_COLS, "extra_fields",
    ]
    placeholders = ", ".join("?" * len(cols))
    sql = f"INSERT INTO appointments ({', '.join(cols)}) VALUES ({placeholders})"
    conn.executemany(sql, [[r.get(c) for c in cols] for r in rows])
    return len(rows)


def upsert_survey(
    conn: sqlite3.Connection,
    df: pd.DataFrame,
    source_file: str,
    source_sheet: str,
    survey_year: str,
) -> int:
    conn.execute(
        "DELETE FROM survey_responses WHERE source_file=? AND source_sheet=?",
        (source_file, source_sheet),
    )
    rows = []
    for _, raw in df.iterrows():
        row_data = {
            k: normalise_value(v)
            for k, v in raw.items()
            if normalise_value(v) is not None
        }
        rows.append((source_file, source_sheet, survey_year, json.dumps(row_data)))
    if rows:
        conn.executemany(
            "INSERT INTO survey_responses (source_file, source_sheet, survey_year, row_data) VALUES (?,?,?,?)",
            rows,
        )
    return len(rows)


def update_metadata(
    conn: sqlite3.Connection,
    filename: str,
    sheet_name: str,
    fhash: str,
    table_name: str,
    rows: int,
) -> None:
    conn.execute(
        """INSERT INTO ingest_metadata (filename, sheet_name, file_hash, table_name, rows_ingested, ingested_at)
           VALUES (?,?,?,?,?,datetime('now'))
           ON CONFLICT(filename, sheet_name) DO UPDATE SET
               file_hash=excluded.file_hash,
               rows_ingested=excluded.rows_ingested,
               ingested_at=excluded.ingested_at""",
        (filename, sheet_name, fhash, table_name, rows),
    )


# ── Main pipeline ─────────────────────────────────────────────────────────────

def process_xlsx(
    xlsx_path: Path,
    conn: sqlite3.Connection,
    stored_hashes: dict[tuple[str, str], str],
) -> int:
    fhash    = file_hash(xlsx_path)
    filename = xlsx_path.name
    meta     = parse_filename_meta(xlsx_path.stem)
    total    = 0

    try:
        sheets: dict[str, pd.DataFrame] = pd.read_excel(
            xlsx_path, sheet_name=None, engine="openpyxl"
        )
    except Exception as exc:
        log.warning("Could not read %s: %s", filename, exc)
        return 0

    # If the file has a consolidated master sheet, its per-category breakout
    # sheets are subsets — skip them to avoid double-counting.
    appt_sheets = {
        name for name, df in sheets.items()
        if not df.dropna(how="all").empty
        and is_appointment_sheet(name, df.dropna(how="all"))
    }
    has_master = any(is_master_sheet(name) for name in appt_sheets)

    for sheet_name, df in sheets.items():
        df = df.dropna(how="all")
        if df.empty:
            continue

        key = (filename, sheet_name)
        if stored_hashes.get(key) == fhash:
            log.info("  Skipping unchanged %s / %s", filename, sheet_name)
            continue

        if (
            has_master
            and sheet_name in appt_sheets
            and not is_master_sheet(sheet_name)
        ):
            log.info("  Skipping breakout sheet %s / %s (covered by master)", filename, sheet_name)
            continue

        if is_appointment_sheet(sheet_name, df):
            rows = df_to_appointment_rows(
                df, filename, sheet_name,
                meta["academic_year"], meta["quarter"],
            )
            n = upsert_appointments(conn, rows, filename, sheet_name)
            update_metadata(conn, filename, sheet_name, fhash, "appointments", n)
            log.info("  [appointments] %s / %s — %d rows", filename, sheet_name, n)
        elif is_survey_sheet(sheet_name, filename):
            year_match = re.search(r"\b(20\d{2})\b", filename)
            survey_year = year_match.group(1) if year_match else ""
            n = upsert_survey(conn, df, filename, sheet_name, survey_year)
            update_metadata(conn, filename, sheet_name, fhash, "survey_responses", n)
            log.info("  [survey] %s / %s — %d rows", filename, sheet_name, n)
        else:
            log.info("  Skipping unclassified sheet %s / %s", filename, sheet_name)
            continue

        total += 1

    conn.commit()
    return total


if __name__ == "__main__":
    log.info("=== YLYI-Bot ingestor starting ===")
    log.info("Source: %s  |  DB: %s", SOURCE_DIR, DB_PATH)

    xlsx_files = sorted(
        list(SOURCE_DIR.glob("*.xlsx")) + list(SOURCE_DIR.glob("*.xls"))
    )
    if not xlsx_files:
        log.warning("No Excel files found in %s", SOURCE_DIR)
        sys.exit(0)

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    # Load existing hashes for skip logic
    stored_hashes: dict[tuple[str, str], str] = {
        (row[0], row[1]): row[2]
        for row in conn.execute("SELECT filename, sheet_name, file_hash FROM ingest_metadata")
    }

    total_sheets = 0
    for xlsx in xlsx_files:
        log.info("Processing %s", xlsx.name)
        total_sheets += process_xlsx(xlsx, conn, stored_hashes)

    # Summary stats
    appt_count   = conn.execute("SELECT COUNT(*) FROM appointments").fetchone()[0]
    survey_count = conn.execute("SELECT COUNT(*) FROM survey_responses").fetchone()[0]
    conn.close()

    log.info("=== Ingest complete: %d sheets processed ===", total_sheets)
    log.info("    appointments: %d rows", appt_count)
    log.info("    survey_responses: %d rows", survey_count)
