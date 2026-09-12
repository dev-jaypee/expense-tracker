"""
Expense Tracker - web UI for your existing tracker.

This reuses your real logic: the Expense class, the same expenses.csv
format ("name, amount, category"), the same category list, and the same
budget / daily-budget math from expense_tracker_v2.py. Only the
input()/print() loop has been replaced with a Streamlit interface.

Run it with:
    streamlit run app.py

Requires:
    pip install streamlit pandas plotly

Folder layout expected (keep these together):
    streamlit_expense/
        app.py
        expense.py            <- your Expense class, unchanged
        .streamlit/
            config.toml       <- theme
"""

import calendar
import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from expense import Expense

EXPENSE_FILE_PATH = "expenses.csv"
DEFAULT_BUDGET = 2000  # same default as your original script

EXPENSE_CATEGORIES = [
    "🍔Food",
    "🏠Home",
    "💼Work",
    "🎉Fun",
    "✨Misc",
]

CARD_CSS = """
<style>
.stApp { font-family: 'Inter', sans-serif; }

.metric-card {
    background: linear-gradient(135deg, #1A1D29 0%, #24273A 100%);
    border: 1px solid #2E3145;
    border-radius: 16px;
    padding: 24px;
    text-align: center;
}
.metric-card h2 { margin: 0; font-size: 2rem; color: #E8E8F0; }
.metric-card p { margin: 4px 0 0 0; color: #9A9DB0; font-size: 0.85rem; }
.metric-card.positive h2 { color: #6EE7A8; }
.metric-card.negative h2 { color: #F87171; }

div[data-testid="stForm"] {
    background: #1A1D29;
    border: 1px solid #2E3145;
    border-radius: 16px;
    padding: 24px;
}
.stButton > button { border-radius: 10px; font-weight: 600; }
div[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
h1, h2, h3 { letter-spacing: -0.02em; }
</style>
"""


# ---------------------------------------------------------------------------
# Core logic — unchanged from your original script apart from the removal
# of input()/print() calls, which don't make sense in a web UI.
# ---------------------------------------------------------------------------


def save_expense_to_file(new_expense: Expense, file_path: str) -> None:
    """Append one expense to the CSV, guarding against merged rows."""
    try:
        with open(file_path, "rb") as handle:
            handle.seek(0, 2)
            file_size = handle.tell()
            if file_size > 0:
                handle.seek(-1, 2)
                needs_newline = handle.read(1) != b"\n"
            else:
                needs_newline = False
    except FileNotFoundError:
        needs_newline = False

    with open(file_path, "a", encoding="utf-8") as handle:
        if needs_newline:
            handle.write("\n")
        handle.write(
            f"{new_expense.name}, {new_expense.amount}, {new_expense.category}\n")


def parse_expense_line(raw_line: str, line_number: int) -> Expense | None:
    """Turn one CSV line into an Expense, or None if it should be skipped."""
    cleaned_line = raw_line.strip()
    if not cleaned_line:
        return None

    fields = [field.strip() for field in cleaned_line.split(",")]
    if len(fields) != 3:
        st.session_state.setdefault("parse_warnings", []).append(
            f"Skipping line {line_number}: expected 3 fields but found "
            f"{len(fields)} -> {cleaned_line!r}"
        )
        return None

    name, amount_text, category = fields
    if not name or not category:
        st.session_state.setdefault("parse_warnings", []).append(
            f"Skipping line {line_number}: missing name or category -> {cleaned_line!r}"
        )
        return None

    try:
        amount = float(amount_text)
    except ValueError:
        st.session_state.setdefault("parse_warnings", []).append(
            f"Skipping line {line_number}: '{amount_text}' is not a valid amount "
            f"-> {cleaned_line!r}"
        )
        return None

    return Expense(name=name, amount=amount, category=category)


def load_expenses(file_path: str) -> list[Expense]:
    """Read and parse every expense from the CSV file."""
    st.session_state["parse_warnings"] = []
    try:
        with open(file_path, "r", encoding="utf-8") as handle:
            raw_lines = handle.readlines()
    except FileNotFoundError:
        raw_lines = []

    parsed_expenses = []
    for line_number, raw_line in enumerate(raw_lines, start=1):
        parsed = parse_expense_line(raw_line, line_number)
        if parsed is not None:
            parsed_expenses.append(parsed)
    return parsed_expenses


def delete_expense(all_expenses: list[Expense], index_to_remove: int, file_path: str) -> None:
    """Remove one expense and rewrite the CSV with everything else."""
    remaining = [e for i, e in enumerate(all_expenses) if i != index_to_remove]
    with open(file_path, "w", encoding="utf-8") as handle:
        for item in remaining:
            handle.write(f"{item.name}, {item.amount}, {item.category}\n")


def compute_summary(all_expenses: list[Expense], monthly_budget: float):
    """Same math as your summarize_expenses(), returned instead of printed."""
    spend_by_category: dict[str, float] = {}
    for item in all_expenses:
        spend_by_category[item.category] = spend_by_category.get(
            item.category, 0) + item.amount

    total_spent = sum(item.amount for item in all_expenses)
    remaining_budget = monthly_budget - total_spent

    today = datetime.datetime.now()
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    remaining_days = days_in_month - today.day

    if remaining_days > 0:
        daily_budget_label = f"${remaining_budget / remaining_days:.2f} / day"
    else:
        daily_budget_label = f"${remaining_budget:.2f} (last day of month)"

    return spend_by_category, total_spent, remaining_budget, daily_budget_label


# ---------------------------------------------------------------------------
# UI sections — each renders one piece of the page.
# ---------------------------------------------------------------------------


def render_sidebar() -> float:
    """Render the sidebar and return the budget the user has set."""
    with st.sidebar:
        st.markdown("## 🎯 Expense Tracker")
        st.caption(f"Reading from `{EXPENSE_FILE_PATH}`")
        st.divider()
        monthly_budget = st.number_input(
            "Monthly budget", min_value=0.0, value=float(DEFAULT_BUDGET), step=50.0
        )
        st.divider()
        warnings = st.session_state.get("parse_warnings", [])
        if warnings:
            with st.expander(f"⚠️ {len(warnings)} line(s) skipped"):
                for warning in warnings:
                    st.caption(warning)
    return monthly_budget


def render_add_expense_form() -> None:
    """Render the add-expense form and save on submit."""
    with st.form("add_expense_form", clear_on_submit=True):
        st.subheader("Add an expense")
        name_col, amount_col, category_col = st.columns([2, 1, 1])
        name = name_col.text_input(
            "Expense name", placeholder="e.g. Groceries")
        amount = amount_col.number_input(
            "Amount", min_value=0.0, step=1.0, format="%.2f")
        category = category_col.selectbox("Category", EXPENSE_CATEGORIES)
        submitted = st.form_submit_button("➕ Add Expense", width="stretch")

        if submitted:
            if not name or amount <= 0:
                st.warning("Enter a name and an amount greater than 0.")
            else:
                save_expense_to_file(
                    Expense(name=name, category=category,
                            amount=amount), EXPENSE_FILE_PATH
                )
                st.success(f"Saved: {name} — ${amount:.2f}")
                st.rerun()


def render_metric_cards(
    total_spent: float, remaining_budget: float, daily_budget_label: str
) -> None:
    """Render the three summary cards at the top of the page."""
    total_col, remaining_col, daily_col = st.columns(3)
    with total_col:
        st.markdown(
            f'<div class="metric-card"><h2>${total_spent:,.2f}</h2><p>TOTAL SPENT</p></div>',
            unsafe_allow_html=True,
        )
    with remaining_col:
        css_class = "positive" if remaining_budget >= 0 else "negative"
        st.markdown(
            f'<div class="metric-card {css_class}"><h2>${remaining_budget:,.2f}</h2>'
            "<p>BUDGET REMAINING</p></div>",
            unsafe_allow_html=True,
        )
    with daily_col:
        st.markdown(
            f'<div class="metric-card"><h2>{daily_budget_label}</h2><p>DAILY BUDGET</p></div>',
            unsafe_allow_html=True,
        )


def render_category_chart(spend_by_category: dict[str, float]) -> None:
    """Render the donut chart of spending by category."""
    st.subheader("By category")
    chart_data = pd.DataFrame(
        {"Category": list(spend_by_category.keys()),
         "Amount": list(spend_by_category.values())}
    )
    figure = px.pie(
        chart_data,
        names="Category",
        values="Amount",
        hole=0.55,
        color_discrete_sequence=px.colors.sequential.Purples_r,
    )
    figure.update_layout(
        showlegend=True,
        margin={"t": 10, "b": 10, "l": 10, "r": 10},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#E8E8F0",
        height=320,
    )
    st.plotly_chart(figure, width="stretch")


def render_expense_table(all_expenses: list[Expense]) -> None:
    """Render the sortable table of all expenses."""
    st.subheader("All expenses")
    table_data = pd.DataFrame(
        [{"Name": e.name, "Category": e.category, "Amount": e.amount}
            for e in all_expenses]
    )
    st.dataframe(
        table_data,
        width="stretch",
        hide_index=True,
        column_config={
            "Amount": st.column_config.NumberColumn(format="$%.2f")},
    )


def render_delete_section(all_expenses: list[Expense]) -> None:
    """Render the delete-an-expense expander."""
    with st.expander("🗑️ Delete an expense"):
        selected_index = st.selectbox(
            "Select the expense to remove",
            options=range(len(all_expenses)),
            format_func=lambda i: (
                f"{all_expenses[i].name} — {all_expenses[i].category} — "
                f"${all_expenses[i].amount:.2f}"
            ),
        )
        if st.button("Delete this expense", type="secondary"):
            removed_name = all_expenses[selected_index].name
            delete_expense(all_expenses, selected_index, EXPENSE_FILE_PATH)
            st.success(f"Deleted: {removed_name}")
            st.rerun()


def main() -> None:
    """Assemble the full page."""
    st.set_page_config(page_title="Expense Tracker",
                       page_icon="🎯", layout="wide")
    st.markdown(CARD_CSS, unsafe_allow_html=True)

    monthly_budget = render_sidebar()

    st.title("Expense Tracker")
    render_add_expense_form()
    st.write("")

    all_expenses = load_expenses(EXPENSE_FILE_PATH)

    if not all_expenses:
        st.info("No valid expenses found yet. Add one above to get started.")
        return

    spend_by_category, total_spent, remaining_budget, daily_budget_label = compute_summary(
        all_expenses, monthly_budget
    )
    render_metric_cards(total_spent, remaining_budget, daily_budget_label)
    st.write("")

    chart_col, table_col = st.columns([1, 1.4])
    with chart_col:
        render_category_chart(spend_by_category)
    with table_col:
        render_expense_table(all_expenses)

    st.write("")
    render_delete_section(all_expenses)


if __name__ == "__main__":
    main()
