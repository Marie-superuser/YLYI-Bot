# YLYI-Bot Architecture

Everything runs **locally**. This is intended to run on a local server in the library. 

The chatbot uses a free, open-source model (IBM
Granite provided by Ollama), with no API keys and no data leaving the machine.

There are two ways to run the project. They share the same library data.

```
                          ┌─────────────────────────────┐
                          │   Library source data        │
                          │   appointment .xlsx, survey  │
                          │   .xlsx, circulation .pdf     │
                          └───────────────┬─────────────┘
                                          │
                 ┌────────────────────────┴────────────────────────┐
                 │                                                  │
        (A) Streamlit dashboard                        (B) Docker / Open Web UI
            — PRIMARY —                                     — alternative —
```

---

## (A) Streamlit Dashboard + Insight Bot  ·  PRIMARY

Run with `dashboard/run-dashboard.command` (double-click) or
`streamlit run app.py`. Opens at http://localhost:8501.

```
   YOU (web browser)  ──  http://localhost:8501
        │
        ▼
 ┌──────────────────────────────────────────────────────────────────────┐
 │  Streamlit app   ( dashboard/app.py )                                  │
 │                                                                        │
 │   ┌──────────────────┐              ┌──────────────────────────────┐  │
 │   │  "Home" tab      │              │  "Insight Bot" tab           │  │
 │   │  charts + metrics│              │  chat box (st.chat_input)    │  │
 │   └────────┬─────────┘              └───────────────┬──────────────┘  │
 │            │ dataframes                             │ your question    │
 │            │                          ┌─────────────▼──────────────┐   │
 │            │                          │  src/bot.py : answer()     │   │
 │            │                          │                            │   │
 │            │            1. ROUTE      │  ┌──────────────────────┐  │   │
 │            │           the question   │  │  Ollama granite4.1   │  │   │
 │            │        ◄─────────────────┼─►│  :11434  (local)     │  │   │
 │            │       "which tool +      │  │  picks tool + args   │  │   │
 │            │        which filters?"   │  └──────────────────────┘  │   │
 │            │                          │             │ tool + args   │   │
 │            │                          │   2. GROUNDING GUARD        │   │
 │            │                          │      drop filters not in    │   │
 │            │                          │      the question text      │   │
 │            │                          │             │               │   │
 │            │                          │   3. COMPUTE (pandas)       │   │
 │            │                          │   ┌──────────────────────┐  │   │
 │            │                          │   │ count_appointments   │  │   │
 │            │                          │   │ breakdown_appointments│ │   │
 │            │                          │   │ satisfaction_summary │  │   │
 │            │                          │   │ list_options         │  │   │
 │            │                          │   └──────────┬───────────┘  │   │
 │            │                          └──────────────┼──────────────┘   │
 │            │                                         │ EXACT numbers     │
 │            ▼                                         ▼                   │
 │   ┌────────────────────────────────────────────────────────────────┐   │
 │   │  src/data.py   load_bookings() · load_satisfaction() · …        │   │
 │   │  (pandas reads the .xlsx / .pdf files, cached)                  │   │
 │   └───────────────────────────────┬────────────────────────────────┘   │
 └───────────────────────────────────┼────────────────────────────────────┘
                                      ▼
                            dashboard/data/   (xlsx + pdf)

  KEY IDEA:  the model only interprets the question and picks a tool.
             every number is computed by pandas from the real data —
             the same dataframes the charts use — so the bot and the
             charts can never disagree, and counts can't be hallucinated.
             If Ollama is off, a keyword fallback still answers common
             questions.
```

---

## (B) Docker / Open Web UI stack  ·  alternative

Run with `docker compose up -d`. Open Web UI at http://localhost:3000.
Builds a SQLite database from the Excel files and answers via a text-to-SQL tool.

```
   YOU (web browser)  ──  http://localhost:3000
        │
        ▼
 ┌───────────────────────────── Docker Compose ──────────────────────────────┐
 │                                                                            │
 │   ┌────────────────┐         ┌──────────────────┐       ┌──────────────┐   │
 │   │   ingestor     │  build  │   Open Web UI    │  chat │    Ollama    │   │
 │   │ (one-shot job) │         │   (chat server)  │◄─────►│  granite4.1  │   │
 │   │ ingest.py      │         │                  │       │   :11434     │   │
 │   └───────┬────────┘         └────────┬─────────┘       └──────────────┘   │
 │           │ reads xlsx                │ calls the                          │
 │           │ writes SQLite             │ text-to-SQL tool                   │
 │           ▼                           ▼                                    │
 │   ┌────────────────┐         ┌──────────────────────────────┐             │
 │   │  data/*.xlsx   │         │ openwebui-tool/ylyi_sql_tool │             │
 │   │       │        │         │ generates a SELECT, runs it   │             │
 │   │       ▼        │         │ read-only against the DB      │             │
 │   │  data/ylyi.db  │◄────────┤ (paste into Admin → Tools)    │             │
 │   │  (SQLite)      │  query  └──────────────────────────────┘             │
 │   └────────────────┘                                                      │
 │                                                                            │
 │   ingestor normalizes column names across the AY21–AY25 naming eras,       │
 │   de-duplicates the per-category "breakout" sheets, and skips unchanged    │
 │   files on re-run (hash-based incremental updates).                        │
 └────────────────────────────────────────────────────────────────────────────┘
```

---

## Why two approaches?

The Docker/Open Web UI stack came first and uses text-to-SQL(the model writes
a SQL query). That worked but occasionally resulted in unreliable SQL queries, so the
Insight Bot replaced free SQL generation with fixed,
structured tools. 

The model only fills in parameters, and the numbers are always
computed correctly. The dashboard is the recommended path; the Docker stack is kept
for reference and for anyone who prefers a hosted multi-user chat UI.

See [`README.md`](README.md) for setup and deployment steps.
