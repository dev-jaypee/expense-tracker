# 🎯 Expense Tracker

A simple, interactive expense tracker with a web interface — built in Python,
originally a terminal app, converted into a Streamlit web app.

**[Live demo →](https://etrackerly.streamlit.app)**

## Features

- Add expenses with a name, amount, and category
- Live-updating summary: total spent, budget remaining, suggested daily
  spending for the rest of the month
- Spending breakdown by category (donut chart)
- Sortable table of all expenses
- Delete any expense
- Dark, custom-themed interface

## Tech stack

- [Streamlit](https://streamlit.io) — web UI framework
- [Pandas](https://pandas.pydata.org) — data handling for the table/chart
- [Plotly](https://plotly.com/python/) — the category breakdown chart
- CSV file storage (no database required for this demo version)

## Project structure

```
.
├── app.py              # UI: forms, charts, layout — imports logic, doesn't duplicate it
├── expense.py           # The Expense data class
├── expenses.csv          # Sample data (this demo uses shared, resettable data)
├── conftest.py           # Makes app.py importable by pytest, regardless of how it's run
├── requirements.txt
├── .gitignore
├── .streamlit/
│   └── config.toml       # Theme (colors, dark mode)
└── tests/
    └── test_app.py       # Automated tests for parsing, budget math, save/delete
```

`app.py` is deliberately split into small functions: pure logic functions
(`parse_expense_line`, `compute_summary`, `save_expense_to_file`,
`delete_expense`, `load_expenses`) are separate from UI-rendering functions
(`render_add_expense_form`, `render_metric_cards`, etc.). This means the
logic can be tested and changed without touching the interface, and the
interface can be redesigned without touching the logic.

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL it prints (usually `http://localhost:8501`).

## Running the tests

```bash
pytest
```

Every core function (parsing a CSV line, computing totals, saving,
deleting) has test coverage, so a future change that breaks something
will fail a test immediately instead of failing silently in the UI.

## Deployment

Hosted for free on [Streamlit Community Cloud](https://streamlit.io/cloud),
connected directly to this repository's `main` branch. Any push to `main`
is picked up automatically and redeployed within a minute or two — no
manual redeploy step required.

## Notes on this demo version

This deployed version uses one shared CSV file as storage — anyone who
visits the live link can add or delete expenses, and data may be reset
periodically. This is intentional for a public portfolio demo.
