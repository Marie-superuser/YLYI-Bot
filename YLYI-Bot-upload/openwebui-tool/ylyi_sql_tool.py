"""
YLYI Library Data Tool — paste this into Open Web UI Admin → Tools.

Instead of asking the model to write SQL (unreliable on small models), this
exposes a few parameterized tools. The model only picks a function and fills
in parameters; the Python code builds correct, bound SQL and computes exact
counts and percentages. Answers are deterministic and auditable.

DB path inside the open-webui container: /app/ylyi-data/ylyi.db
(mounted via docker-compose: ./data → /app/ylyi-data:ro)
"""

import os
import re
import sqlite3

DB_PATH = os.environ.get("YLYI_DB_PATH", "/app/ylyi-data/ylyi.db")

# Columns the model is allowed to filter or group by. Identifiers can't be
# bound as SQL parameters, so they must be validated against this allowlist.
FILTER_COLS = {"academic_year", "quarter", "service", "location",
               "pnwu_status", "pnwu_affiliation"}
GROUP_COLS = FILTER_COLS | {"meeting_format"}


def _connect() -> sqlite3.Connection:
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(
            f"Database not found at {DB_PATH}. "
            "Make sure the ingestor has run and the volume is mounted."
        )
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _norm_ay(value: str | None) -> str | None:
    """Map a user phrase like '2023-2024' or '2023-24' to 'AY23-24'."""
    if not value:
        return None
    v = value.strip()
    if re.fullmatch(r"(?i)AY\d{2}-\d{2}", v):
        return v.upper()
    m = re.fullmatch(r"(?:20)?(\d{2})\s*[-/]\s*(?:20)?(\d{2})", v)
    if m:
        return f"AY{m.group(1)}-{m.group(2)}"
    return v


def _norm_quarter(value: str | None) -> str | None:
    if not value:
        return None
    m = re.search(r"[1-4]", value)
    return f"Q{m.group(0)}" if m else value


def _build_filters(
    academic_year=None, quarter=None, service=None,
    location=None, pnwu_status=None, pnwu_affiliation=None, virtual=None,
):
    """Return (where_sql, params, description) from optional filters."""
    clauses: list[str] = []
    params: list = []
    desc: list[str] = []

    exact = {
        "academic_year": _norm_ay(academic_year),
        "quarter": _norm_quarter(quarter),
    }
    for col, val in exact.items():
        if val:
            clauses.append(f"{col} = ?")
            params.append(val)
            desc.append(f"{col}={val}")

    like = {
        "service": service,
        "location": location,
        "pnwu_status": pnwu_status,
        "pnwu_affiliation": pnwu_affiliation,
    }
    for col, val in like.items():
        if val:
            clauses.append(f"LOWER({col}) LIKE LOWER(?)")
            params.append(f"%{val.strip()}%")
            desc.append(f"{col}~'{val.strip()}'")

    if virtual is not None:
        cond = "(LOWER(location) LIKE '%virtual%' OR LOWER(meeting_format) LIKE '%virtual%')"
        clauses.append(cond if virtual else f"NOT {cond}")
        desc.append("virtual" if virtual else "not virtual")

    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    return where, params, (", ".join(desc) if desc else "all appointments")


class Tools:
    def __init__(self):
        pass

    def count_appointments(
        self,
        academic_year: str = "",
        quarter: str = "",
        service: str = "",
        location: str = "",
        virtual: bool = None,
    ) -> str:
        """
        Count PNWU "Book a Librarian" appointments, optionally filtered. EVERY
        row is a Book a Librarian appointment, so leave all filters blank for the
        grand total. Do NOT pass service='Book a Librarian' (not a real value).

        :param academic_year: e.g. 'AY23-24'. The phrase '2023-2024' means 'AY23-24'.
        :param quarter: 'Q1'..'Q4'.
        :param service: appointment category substring, e.g. 'Research Consultation', 'Bioethics'.
        :param location: location substring, e.g. 'Virtual'.
        :param virtual: True for virtual only, False for non-virtual only.
        :return: The exact count with the applied filter.
        """
        try:
            where, params, desc = _build_filters(
                academic_year=academic_year or None, quarter=quarter or None,
                service=service or None, location=location or None, virtual=virtual,
            )
            with _connect() as conn:
                n = conn.execute(
                    f"SELECT COUNT(*) FROM appointments{where}", params
                ).fetchone()[0]
            return f"{n} appointments ({desc})."
        except Exception as exc:
            return f"[Tool error: {exc}]"

    def breakdown_appointments(
        self,
        group_by: str,
        academic_year: str = "",
        service: str = "",
    ) -> str:
        """
        Break down Book a Librarian appointments by a column, with exact counts
        and percentages. Use this for "how many were virtual", "by service",
        "by quarter", etc.

        :param group_by: one of academic_year, quarter, service, location, meeting_format, pnwu_status, pnwu_affiliation.
        :param academic_year: optional filter, e.g. 'AY23-24'.
        :param service: optional service substring filter.
        :return: Each group value with count and percentage of the filtered total.
        """
        try:
            if group_by not in GROUP_COLS:
                return (
                    f"[Tool error: group_by must be one of {sorted(GROUP_COLS)}]"
                )
            where, params, desc = _build_filters(
                academic_year=academic_year or None, service=service or None,
            )
            with _connect() as conn:
                rows = conn.execute(
                    f"SELECT COALESCE(NULLIF({group_by},''),'(not recorded)') AS k, "
                    f"COUNT(*) AS n FROM appointments{where} "
                    f"GROUP BY k ORDER BY n DESC",
                    params,
                ).fetchall()
            total = sum(r["n"] for r in rows)
            if total == 0:
                return f"No appointments matched ({desc})."
            lines = [f"Breakdown by {group_by} ({desc}; total {total}):"]
            for r in rows:
                pct = 100.0 * r["n"] / total
                lines.append(f"  {r['k']}: {r['n']} ({pct:.1f}%)")
            return "\n".join(lines)
        except Exception as exc:
            return f"[Tool error: {exc}]"

    def list_values(self, column: str) -> str:
        """
        List the distinct values present in a column of the appointments table,
        so you know what filters are valid before counting.

        :param column: one of academic_year, quarter, service, location, meeting_format, pnwu_status, pnwu_affiliation.
        :return: The distinct values currently in the data.
        """
        try:
            if column not in GROUP_COLS:
                return f"[Tool error: column must be one of {sorted(GROUP_COLS)}]"
            with _connect() as conn:
                rows = conn.execute(
                    f"SELECT DISTINCT {column} v FROM appointments "
                    f"WHERE {column} IS NOT NULL AND {column} != '' ORDER BY v"
                ).fetchall()
            vals = [r["v"] for r in rows]
            return f"{column} values: {vals}" if vals else f"No values for {column}."
        except Exception as exc:
            return f"[Tool error: {exc}]"
