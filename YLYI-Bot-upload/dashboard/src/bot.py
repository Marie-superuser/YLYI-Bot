"""
YLYI Insight Bot — local, no OpenAI.

Design: the language model (a local Ollama model, default granite4.1:3b) is used
ONLY to understand the question and route it to a structured tool. Every number
comes from pandas operations on the SAME dataframes the dashboard charts use, so
the bot can never report a figure that disagrees with the charts, and it cannot
hallucinate counts. If Ollama is unavailable, a keyword fallback router keeps the
bot working for common questions.

Config (env vars, optional):
  OLLAMA_HOST     default http://localhost:11434
  YLYI_BOT_MODEL  default granite4.1:3b   (must be a tool-capable model)
"""

from __future__ import annotations

import os
import re

import pandas as pd

from src.data import load_bookings, load_satisfaction

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("YLYI_BOT_MODEL", "granite4.1:3b")

REDIRECT = (
    "I can only answer questions about the PNWU Library's Book a Librarian "
    "appointments and student satisfaction surveys. For other information, "
    "please visit https://www.pnwu.edu/about/offices-departments/library/"
)

# Matches the dashboard's plot_virtual_vs_inperson mapping so counts agree with
# the pie chart.
LOCATION_MAP = {"Virtual": "Virtual", "PNWU Library or Virtual": "In-Person"}


# ── Helpers ──────────────────────────────────────────────────────────────────

def _norm_ay(value: str | None) -> str | None:
    """'2023-2024' / '2023-24' / 'AY23-24' -> 'AY23-24'."""
    if not value:
        return None
    v = str(value).strip()
    if re.fullmatch(r"(?i)AY\d{2}-\d{2}", v):
        return v.upper()
    m = re.fullmatch(r"(?:20)?(\d{2})\s*[-/]\s*(?:20)?(\d{2})", v)
    if m:
        return f"AY{m.group(1)}-{m.group(2)}"
    return v


def _bookings() -> pd.DataFrame:
    df = load_bookings().copy()
    if df.empty:
        return df
    df["Delivery"] = df["Location"].replace(LOCATION_MAP)
    return df


def _apply_filters(df, academic_year=None, service=None, delivery=None):
    desc = []
    if academic_year:
        ay = _norm_ay(academic_year)
        df = df[df["AcademicYear"].str.upper() == ay]
        desc.append(ay)
    if service:
        df = df[df["Service"].str.contains(service.strip(), case=False, na=False)]
        desc.append(f"service~'{service.strip()}'")
    if delivery:
        d = delivery.strip().lower()
        if d.startswith("virt"):
            df = df[df["Location"] == "Virtual"]
            desc.append("virtual")
        elif d.startswith("in"):
            df = df[df["Location"] == "PNWU Library or Virtual"]
            desc.append("in-person")
    return df, (", ".join(desc) if desc else "all appointments")


# ── Tools (deterministic) ──────────────────────────────────────────────────────

def count_appointments(academic_year=None, service=None, delivery=None, **_) -> str:
    """Exact count of Book a Librarian appointments, optionally filtered."""
    df = _bookings()
    if df.empty:
        return "No appointment data is loaded."
    df, desc = _apply_filters(df, academic_year, service, delivery)
    return f"**{len(df)}** appointments ({desc})."


def breakdown_appointments(group_by="AcademicYear", academic_year=None,
                           service=None, **_) -> str:
    """Counts (and %) grouped by AcademicYear, Service, Delivery, or YearQuarter."""
    valid = {"academicyear": "AcademicYear", "service": "Service",
             "delivery": "Delivery", "yearquarter": "YearQuarter",
             "year": "AcademicYear", "quarter": "YearQuarter",
             "location": "Delivery"}
    col = valid.get(str(group_by).strip().lower())
    if col is None:
        return (f"I can break down by: AcademicYear, Service, Delivery, or "
                f"YearQuarter (got '{group_by}').")
    df = _bookings()
    if df.empty:
        return "No appointment data is loaded."
    df, desc = _apply_filters(df, academic_year, service, None)
    if df.empty:
        return f"No appointments matched ({desc})."
    counts = df[col].fillna("(not recorded)").value_counts()
    total = int(counts.sum())
    lines = [f"Appointments by {col} ({desc}; total {total}):"]
    for key, n in counts.items():
        lines.append(f"- {key}: {int(n)} ({100 * n / total:.1f}%)")
    return "\n".join(lines)


def satisfaction_summary(year=None, program=None, **_) -> str:
    """Mean satisfaction score (1-5) per question for a survey year (2023 or 2025)."""
    try:
        yr = int(re.search(r"20\d{2}", str(year)).group()) if year else None
    except Exception:
        yr = None
    if yr not in (2023, 2025):
        return "Which survey year — 2023 or 2025?"
    df = load_satisfaction(yr)
    if df.empty:
        return f"No {yr} satisfaction data is loaded."
    if program and "LevelName" in df.columns:
        df = df[df["LevelName"].astype(str).str.contains(program.strip(),
                                                          case=False, na=False)]
    qcols = [c for c in df.columns
             if c not in ("Survey Year", "LevelName") and df[c].dtype.kind in "fi"]
    if not qcols:
        return f"No scored questions found for {yr}."
    means = df[qcols].mean(numeric_only=True).sort_values(ascending=False)
    lines = [f"{yr} satisfaction means (1-5), {len(df)} respondents"
             + (f", program~'{program}'" if program else "") + ":"]
    for q, m in means.items():
        if pd.notna(m):
            lines.append(f"- {q}: {m:.2f}")
    return "\n".join(lines)


def list_options(field="service", **_) -> str:
    """List the valid values for a field (service, academic_year, delivery)."""
    df = _bookings()
    if df.empty:
        return "No appointment data is loaded."
    f = str(field).strip().lower()
    col = {"service": "Service", "academic_year": "AcademicYear",
           "academicyear": "AcademicYear", "year": "AcademicYear",
           "delivery": "Delivery", "location": "Delivery"}.get(f, "Service")
    vals = sorted(v for v in df[col].dropna().unique())
    return f"{col} values: {vals}"


DISPATCH = {
    "count_appointments": count_appointments,
    "breakdown_appointments": breakdown_appointments,
    "satisfaction_summary": satisfaction_summary,
    "list_options": list_options,
}

# ── Tool specs for Ollama function-calling ─────────────────────────────────────

TOOLS = [
    {"type": "function", "function": {
        "name": "count_appointments",
        "description": ("Count Book a Librarian appointments. EVERY appointment is "
                        "a Book a Librarian appointment, so for a program-wide total "
                        "pass no filters. Do not filter service to 'Book a Librarian'."),
        "parameters": {"type": "object", "properties": {
            "academic_year": {"type": "string",
                              "description": "e.g. 'AY23-24'. '2023-2024' means 'AY23-24'."},
            "service": {"type": "string",
                        "description": "service substring e.g. 'Research Consultation', 'Bioethics'"},
            "delivery": {"type": "string", "enum": ["virtual", "in-person"]},
        }}}},
    {"type": "function", "function": {
        "name": "breakdown_appointments",
        "description": "Counts and percentages grouped by a field. Use for 'how many were virtual', 'by service', 'by year'.",
        "parameters": {"type": "object", "properties": {
            "group_by": {"type": "string",
                         "enum": ["AcademicYear", "Service", "Delivery", "YearQuarter"]},
            "academic_year": {"type": "string"},
            "service": {"type": "string"},
        }, "required": ["group_by"]}}},
    {"type": "function", "function": {
        "name": "satisfaction_summary",
        "description": "Mean student satisfaction scores (1-5) per question for a survey year.",
        "parameters": {"type": "object", "properties": {
            "year": {"type": "string", "enum": ["2023", "2025"]},
            "program": {"type": "string", "description": "optional program e.g. DO, PT, OT"},
        }, "required": ["year"]}}},
    {"type": "function", "function": {
        "name": "list_options",
        "description": "List valid values for a field before filtering.",
        "parameters": {"type": "object", "properties": {
            "field": {"type": "string", "enum": ["service", "academic_year", "delivery"]},
        }}}},
]

SYSTEM_PROMPT = (
    "You are the YLYI Insight Bot for the PNWU Health Sciences Library. Answer "
    "ONLY questions about Book a Librarian appointments and student satisfaction "
    "surveys, and ALWAYS by calling one of the provided tools — never compute or "
    "guess numbers yourself. 'Book a Librarian' is the name of the whole program; "
    "every appointment is one, so a program-wide total needs no filter. The phrase "
    "'2023-2024' means academic year 'AY23-24'. If the question is unrelated to the "
    "library, do not call a tool."
)


# ── Routing ────────────────────────────────────────────────────────────────────

def _llm_route(question: str):
    """Ask Ollama to pick a tool + args. Returns (name, args) or None."""
    import ollama

    client = ollama.Client(host=OLLAMA_HOST)
    resp = client.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "system", "content": SYSTEM_PROMPT},
                  {"role": "user", "content": question}],
        tools=TOOLS,
        options={"temperature": 0},
    )
    calls = resp.get("message", {}).get("tool_calls") or []
    if not calls:
        return None
    fn = calls[0]["function"]
    args = fn.get("arguments") or {}
    if isinstance(args, str):
        import json
        try:
            args = json.loads(args)
        except Exception:
            args = {}
    name = fn.get("name")
    return (name, args) if name in DISPATCH else None


def _heuristic_route(question: str):
    """Keyword fallback when the LLM is unavailable or emits no tool call."""
    q = question.lower()
    if not any(w in q for w in (
        "appointment", "booking", "book a librarian", "virtual", "in person",
        "in-person", "service", "consultation", "bioethics", "satisf",
        "survey", "score", "rating", "how many", "count", "total", "number",
        "year", "quarter", "trend", "deliver", "location",
    )):
        return None  # off-topic

    ay = None
    m = re.search(r"(?:AY)?\s*(20)?\d{2}\s*[-/]\s*(20)?\d{2}", question, re.I)
    if m:
        ay = m.group(0)
    elif re.search(r"\b20(2[0-5])\b", question):
        # bare year -> nearest academic year guess left to count (no filter)
        pass

    if any(w in q for w in ("satisf", "survey", "score", "rating")):
        yr = "2023" if "2023" in q else ("2025" if "2025" in q else "2025")
        return ("satisfaction_summary", {"year": yr})
    if "virtual" in q or "in person" in q or "in-person" in q or "deliver" in q:
        if any(w in q for w in ("percent", "%", "breakdown", "split", "vs", "versus", "ratio")):
            return ("breakdown_appointments", {"group_by": "Delivery", "academic_year": ay})
        deliv = "virtual" if "virtual" in q else "in-person"
        return ("count_appointments", {"academic_year": ay, "delivery": deliv})
    if "by service" in q or ("service" in q and "type" in q):
        return ("breakdown_appointments", {"group_by": "Service", "academic_year": ay})
    if any(w in q for w in ("by year", "each year", "trend", "over time", "by quarter")):
        gb = "YearQuarter" if "quarter" in q else "AcademicYear"
        return ("breakdown_appointments", {"group_by": gb})
    return ("count_appointments", {"academic_year": ay})


def _ground_args(question: str, args: dict) -> dict:
    """Drop filters the model added that aren't actually present in the question.

    Small models often inject a spurious academic_year/service/delivery filter
    (e.g. answering 'appointments each year' as if filtered to one year). Numbers
    come from pandas, so a wrong filter = a correct count of the wrong subset.
    This guard keeps a filter only if its cue appears in the user's text.
    """
    q = question.lower()
    out = dict(args or {})
    if out.get("academic_year") and not re.search(
        r"20\d{2}|ay\s*\d{2}-\d{2}|\b\d{2}-\d{2}\b", q
    ):
        out.pop("academic_year", None)
    if out.get("delivery") and not re.search(r"virtual|in[- ]?person|online", q):
        out.pop("delivery", None)
    if out.get("service") and str(out["service"]).strip().lower() not in q:
        out.pop("service", None)
    return out


def answer(question: str) -> str:
    """Main entry point used by the Streamlit UI."""
    if not question or not question.strip():
        return "Ask me about Book a Librarian appointments or the satisfaction surveys."

    route = None
    try:
        route = _llm_route(question)
    except Exception:
        route = None  # Ollama not reachable / model lacks tools -> fall back

    if route is None:
        route = _heuristic_route(question)

    if route is None:
        return REDIRECT

    name, args = route
    args = _ground_args(question, args)
    try:
        return DISPATCH[name](**args)
    except Exception as exc:
        return f"Sorry — I couldn't compute that ({exc}). Try rephrasing."
