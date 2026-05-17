# Your Library, Your Impact Dashboard

A data analytics dashboard and AI insights bot built for the PNWU Health Sciences Library. Built by E.R.A.I. Informatics as a UW MSIM capstone project, 2025-2026.

## What This Is

The library collects a lot of data — appointment logs, satisfaction surveys, circulation reports — but it lived in spreadsheets and PDFs that nobody looked at. This dashboard pulls it all together into one place so library staff and leadership can actually use it.

There is also an AI bot (coming soon) that lets you ask plain-English questions about the data and get answers grounded in real numbers. The bot is modeled after SJSU Library's KingbotGPT project.

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

1. Clone the repo
2. Go into the dashboard folder: `cd Your-Library-Your-Impact/dashboard`
3. Install dependencies: `pip3 install streamlit plotly pandas openpyxl pypdf`
4. Run: `python3 -m streamlit run app.py`

## How To Add New Data

- **New appointment quarter** — drop the Excel file in `data/`, add filename to `BOOKING_FILES` in `src/data.py`
- **New survey year** — add a new label map in `src/data.py`, update `load_satisfaction()`
- **New AI bot knowledge** — add a `.txt` file to `data/knowledge/`, bot picks it up automatically

## Team
ERAI Infomatics 
- Em Stelter 
- Roosevelt Brown 
- AJ Amrous
- Ivette Ivanov 
- Jan Kuebel-Hernandez — project sponsor, PNWU Health Sciences Library

## Acknowledgments

Bot architecture modeled after [SJSU Library KingbotGPT](https://github.com/sjsu-library/kingbotgpt).
Dashboard structure inspired by IMT 561 lab scaffold by Dr. Shane McGarry at UW iSchool.