# Your Library, Your Impact Dashboard

A data analytics dashboard and AI insights bot built for the PNWU Health Sciences Library. Built by E.R.A.I. Informatics as a UW MSIM capstone project, 2025-2026.

## What This Is

The library collects a lot of data — appointment logs, satisfaction surveys, circulation reports — but it lived in spreadsheets and PDFs that nobody looked at. This dashboard pulls it all together into one place so library staff and leadership can actually use it.

There is also an **Insight Bot** that lets you ask plain-English questions about
the data and get answers grounded in real numbers. It runs on a **local model
(IBM Granite via Ollama) — no OpenAI and no API keys.** The model only interprets
your question; every number is computed from the same data the charts use, so the
bot can't make up totals. (Routing pattern inspired by SJSU Library's KingbotGPT,
re-worked to run locally with a structured-query engine instead of vector RAG.)

## What Is In The Dashboard

**Holistic Student Engagement**
Book a Librarian appointment trends from AY21-22 through AY24-25. Filterable by academic year and service type. The strategic plan target is 5% annual growth.

**Collection Value**
Physical book circulation data from LibraryWorld. Checkout trends across four academic years.

**Institutional Cost Avoidance**
How much money does the library save PNWU through ILL vs buying classroom licenses? Calculator coming in the next version.

**General Student Satisfaction**
PNWU Student Satisfaction Survey results from 2023 and 2025, filterable by program (DO, PT, OT, MAMS).

**Qualitative Impact**
Real anonymized student quotes from open-text survey responses.

## How To Run It Locally

First make sure the Insight Bot's model is available (one time):

```bash
ollama pull granite4.1:3b      # requires Ollama: https://ollama.com/download
```

**Easiest (macOS):** double-click `run-dashboard.command` in this folder. The
first run sets up a Python environment (a few minutes), then your browser opens
at http://localhost:8501.

**Manual (any OS):**

1. `cd dashboard`
2. `python3 -m venv .venv && source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. `streamlit run app.py`

The dashboard works even if Ollama isn't running — the Insight Bot just falls
back to keyword matching for common questions.

### Running from a terminal (Windows, macOS, Linux)

Use this if the double-click launcher isn't an option, or you're not on a Mac.

**One-time prerequisites**

- **Python 3.9 or newer** — <https://www.python.org/downloads/>
  *(Windows: tick "Add Python to PATH" during install.)*
- **Ollama** — <https://ollama.com/download>
- After Ollama installs, pull the AI model:
  ```bash
  ollama pull granite4.1:3b
  ```

**Step 1 — Open a terminal in the `dashboard` folder**

- macOS / Linux: open Terminal, then `cd path/to/YLYI-Bot/dashboard`
- Windows: open PowerShell or Command Prompt, then `cd path\to\YLYI-Bot\dashboard`

**Step 2 — Create the Python environment** *(first time only)*

```bash
# macOS / Linux
python3 -m venv .venv
```
```powershell
# Windows
python -m venv .venv
```

**Step 3 — Activate the environment**

```bash
# macOS / Linux
source .venv/bin/activate
```
```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```
```bat
:: Windows Command Prompt
.venv\Scripts\activate.bat
```

Your prompt should now start with `(.venv)`.

> **Windows tip:** if PowerShell rejects the activate script with an execution-policy error, run this once and try again:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

**Step 4 — Install the dependencies** *(first time only)*

```bash
pip install -r requirements.txt
```

**Step 5 — Run the dashboard**

```bash
streamlit run app.py
```

Your browser opens at **http://localhost:8501**. Click **Insight Bot** in the sidebar to try the chatbot.

**Stopping it:** press `Ctrl+C` in the terminal, then close the window.
**Starting it again later:** repeat Steps 1, 3, and 5 — the `.venv` and installed packages persist, so the slow steps don't repeat.

## How To Add New Data

- **New appointment quarter** — drop the Excel file in `data/`, add filename to `BOOKING_FILES` in `src/data.py`. Charts and the bot both pick it up.
- **New survey year** — add a new label map in `src/data.py`, update `load_satisfaction()`
- **Bot configuration** — set `OLLAMA_HOST` (default `http://localhost:11434`) or `YLYI_BOT_MODEL` (default `granite4.1:3b`) as environment variables to change where the bot looks for the model.

## Team
ERAI Infomatics 
- Em Stelter 
- Roosevelt Brown 
- AJ Amrous
- Ivette Ivanov 
- Jan Kuebel-Hernandez: project sponsor, PNWU Health Sciences Library Director
- Maria So: PWNU intern

## Acknowledgments

Bot architecture modeled after [SJSU Library KingbotGPT](https://github.com/sjsu-library/kingbotgpt).
Dashboard structure inspired by IMT 561 lab scaffold by Dr. Shane McGarry at UW iSchool.


