# YLYI-Bot — Your Library, Your Impact

Self-hosted data tools for the PNWU Health Sciences Library. Everything runs
locally on a free, open-source model. Initial architecture based on the San Jose State University’s KingBot project (with significant modifications). 

(IBM Granite via [Ollama](https://ollama.com))


The repository contains two things that share the same library data:

| Folder | What it is | Status |
|---|---|---|
| **`dashboard/`** | A **Streamlit** analytics dashboard with an **Insight Bot** tab that answers plain-English questions about the data. | Primary / recommended |
| `ingestor/`, `openwebui-tool/`, `docker-compose.yml` | An alternative **Docker** stack: builds a SQLite database from the Excel files and serves a chat UI ([Open Web UI](https://github.com/open-webui/open-webui)) with a text-to-SQL tool. | Earlier approach, still works |

If you just want the chatbot working, use the **dashboard** — it's simpler and is
what the screenshots/demo use. The Docker stack is kept for reference.

---

## How the Insight Bot answers reliably (and why it doesn't make up numbers)

Generic "ask-your-documents" RAG chatbots retrieve a
few similar text snippets and let the model guess totals, which produces
confident wrong answers. The Insight Bot avoids that:

```
  Your question                                   ┌─────────────────────┐
       │                                          │   data/ *.xlsx,     │
       ▼                                          │   *.pdf (library    │
  ┌─────────────┐   "which tool + filters?"       │   appointment &     │
  │   Ollama    │ ───────────────────────────►    │   survey data)      │
  │ granite4.1  │   (understands the question)    └──────────┬──────────┘
  │   (local)   │                                            │ pandas
  └─────────────┘                                            ▼
       │ picks a tool                              ┌─────────────────────┐
       ▼                                           │  Structured tools   │
  count_appointments / breakdown_appointments ───► │  compute the EXACT  │
  satisfaction_summary / list_options              │  number from data   │
                                                    └──────────┬──────────┘
                                                               ▼
                                                       grounded answer
```

**The model only interprets the question and chooses a tool. Every number comes
from pandas operations on the actual data** — the same dataframes the dashboard
charts use, so the bot and the charts never disagree. A "grounding guard" also
strips any filter the model adds that isn't in your question (so "appointments
each year" can't accidentally become "appointments in one year"). If Ollama is
off, a keyword fallback still answers common questions.

---

## Prerequisites

- **[Ollama](https://ollama.com/download)** running locally, with a tool-capable model:
  ```bash
  ollama pull granite4.1:3b
  ```
  Ollama listens on `http://localhost:11434`. (The dashboard talks to it there.)
- **Python 3.9+** (for the dashboard). Docker is only needed for the alternative stack.

---

## Quick start — the Dashboard + Insight Bot

### Easiest: double-click launcher (macOS)

In Finder, open `dashboard/` and double-click **`run-dashboard.command`**.
The first run sets up a Python environment (a few minutes); after that it's fast.
Your browser opens at **http://localhost:8501** — click **Insight Bot** in the
sidebar.

> If macOS blocks it the first time: right-click the file → **Open** → **Open**.

### Manual (any OS)

```bash
cd dashboard
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501.

### Try these questions
- *How many Book a Librarian appointments were there in 2023-2024?* → **115**
- *What percent of AY24-25 appointments were virtual?*
- *How many appointments each year?*
- *Show the 2025 satisfaction scores*
- Off-topic questions are politely redirected to the library website.

See [`dashboard/README.md`](dashboard/README.md) for the dashboard's tabs and how
to add new data.

---

## Alternative — the Docker / Open Web UI stack

Builds `data/ylyi.db` (SQLite) from the Excel files and serves a chat UI with a
text-to-SQL tool. Useful if you prefer a hosted multi-user chat over a Streamlit app.

```bash
cp .env.example .env          # set WEBUI_ADMIN_PASSWORD and WEBUI_SECRET_KEY
docker compose up -d          # starts ollama, open-webui, and the ingestor
docker compose exec ollama ollama pull granite4.1:3b   # first run only
```

- Open Web UI: **http://localhost:3000**
- The ingestor ([`ingestor/ingest.py`](ingestor/ingest.py)) reads every `.xlsx` in
  `data/` into SQLite, normalizing column names across the AY21–AY25 naming eras,
  de-duplicating the per-category "breakout" sheets, and supporting incremental
  re-runs (unchanged files are skipped by hash).
- To make the bot query the database, paste
  [`openwebui-tool/ylyi_sql_tool.py`](openwebui-tool/ylyi_sql_tool.py) into
  **Admin → Tools** and follow [`openwebui-tool/SYSTEM_PROMPT.md`](openwebui-tool/SYSTEM_PROMPT.md).

Re-run the ingestor after adding files:
```bash
docker compose up -d --force-recreate ingestor
```

---

## Repository layout

```
YLYI-Bot/
├── dashboard/                 # Streamlit dashboard + Insight Bot  (primary)
│   ├── app.py                 #   UI: Home (charts) + Insight Bot tab
│   ├── run-dashboard.command  #   double-click launcher (macOS)
│   ├── src/
│   │   ├── bot.py             #   the Insight Bot: structured tools + Ollama routing
│   │   ├── data.py            #   loads the xlsx/pdf data into dataframes
│   │   ├── charts.py          #   plotly charts
│   │   └── filters.py         #   chart filter widgets
│   ├── data/                  #   the library's Excel/PDF source data
│   └── requirements.txt
│
├── ingestor/                  # Docker stack: builds data/ylyi.db from xlsx
│   └── ingest.py
├── openwebui-tool/            # Docker stack: text-to-SQL tool for Open Web UI
│   ├── ylyi_sql_tool.py
│   └── SYSTEM_PROMPT.md
├── docker-compose.yml         # Docker stack orchestration
├── scripts/pull-model.sh
├── .env.example
└── README.md                  # you are here
```

---

## Deploying it for others

This is **self-hosted** — there's no cloud cost and the data stays local. Two
common ways to deploy:

1. **Per-machine (simplest).** On each staff machine: install Ollama + run
   `ollama pull granite4.1:3b`, copy this repo, and double-click
   `dashboard/run-dashboard.command`. Good for a few users.

2. **One shared server.** Run Ollama and the dashboard on a single always-on
   machine, and have staff open it over the local network. Launch Streamlit with
   `streamlit run app.py --server.address 0.0.0.0`, then share that machine's
   `http://<its-ip>:8501`. Set `OLLAMA_HOST` if Ollama runs elsewhere.

> Note: the Insight Bot needs Ollama reachable at `OLLAMA_HOST` (default
> `http://localhost:11434`). A cloud host like Streamlit Community Cloud will
> **not** work as-is, because it can't reach a model running on your machine.

### Adding new data later
Drop a new appointment `.xlsx` into `dashboard/data/` and add its filename to
`BOOKING_FILES` in `dashboard/src/data.py`. The charts and the bot both pick it
up automatically. (For the Docker stack, just drop it in `data/` and re-run the
ingestor.)

---

## Credits

Dashboard and bot by **E.R.A.I. Informatics** (Em Stelter · Roosevelt Brown ·
AJ Amrous · Ivette Ivanov) · sponsor **Jan Kuebel-Hernandez**, PNWU Health
Sciences Library. Bot routing pattern inspired by
[SJSU Library's KingbotGPT](https://github.com/sjsu-library/kingbotgpt), re-worked
to run fully locally on Ollama with a structured-query engine instead of OpenAI +
vector RAG.
