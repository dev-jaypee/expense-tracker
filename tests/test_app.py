"""
Tests for the expense tracker's core logic.

Run with:
    pytest

These tests exist so that future changes to app.py can be verified in
seconds instead of by manually clicking through the UI. If a change
breaks parsing, the budget math, saving, or deleting, one of these
will fail and tell you exactly what broke.
"""

from app import (
    parse_expense_line,
    compute_summary,
    save_expense_to_file,
    delete_expense,
    load_expenses,
)
from expense import Expense
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ---------------------------------------------------------------------------
# parse_expense_line
# ---------------------------------------------------------------------------


def test_parse_expense_line_valid():
    expense = parse_expense_line("Coffee, 4.50, 🍔Food", 1)
    assert expense.name == "Coffee"
    assert expense.amount == 4.50
    assert expense.category == "🍔Food"


def test_parse_expense_line_blank_returns_none():
    assert parse_expense_line("", 1) is None
    assert parse_expense_line("   ", 2) is None


def test_parse_expense_line_wrong_field_count_returns_none():
    assert parse_expense_line("Coffee, 4.50", 1) is None
    assert parse_expense_line("Coffee, 4.50, Food, extra", 2) is None


def test_parse_expense_line_bad_amount_returns_none():
    assert parse_expense_line("Coffee, not-a-number, 🍔Food", 1) is None


def test_parse_expense_line_missing_name_or_category_returns_none():
    assert parse_expense_line(", 4.50, 🍔Food", 1) is None
    assert parse_expense_line("Coffee, 4.50, ", 2) is None


# ---------------------------------------------------------------------------
# compute_summary
# ---------------------------------------------------------------------------


def test_compute_summary_totals_and_groups_by_category():
    expenses = [
        Expense(name="Coffee", category="🍔Food", amount=4.50),
        Expense(name="Rice", category="🍔Food", amount=10.00),
        Expense(name="Rent", category="🏠Home", amount=800.00),
    ]
    by_category, total, remaining, _ = compute_summary(
        expenses, monthly_budget=1000)

    assert by_category["🍔Food"] == 14.50
    assert by_category["🏠Home"] == 800.00
    assert total == 814.50
    assert remaining == 185.50


def test_compute_summary_empty_list():
    by_category, total, remaining, _ = compute_summary([], monthly_budget=500)
    assert by_category == {}
    assert total == 0
    assert remaining == 500


def test_compute_summary_over_budget_goes_negative():
    expenses = [Expense(name="Big purchase", category="✨Misc", amount=2000)]
    _, total, remaining, _ = compute_summary(expenses, monthly_budget=500)
    assert total == 2000
    assert remaining == -1500


# ---------------------------------------------------------------------------
# save_expense_to_file / load_expenses / delete_expense (round-trip)
# ---------------------------------------------------------------------------


def test_save_and_load_round_trip(tmp_path):
    csv_path = tmp_path / "expenses.csv"
    save_expense_to_file(
        Expense(name="Coffee", category="🍔Food", amount=4.50), str(csv_path))
    save_expense_to_file(
        Expense(name="Rent", category="🏠Home", amount=800), str(csv_path))

    loaded = load_expenses(str(csv_path))

    assert len(loaded) == 2
    assert loaded[0].name == "Coffee"
    assert loaded[1].name == "Rent"


def test_load_expenses_missing_file_returns_empty_list(tmp_path):
    csv_path = tmp_path / "does_not_exist.csv"
    assert load_expenses(str(csv_path)) == []


def test_delete_expense_removes_only_selected_row(tmp_path):
    csv_path = tmp_path / "expenses.csv"
    expenses = [
        Expense(name="Coffee", category="🍔Food", amount=4.50),
        Expense(name="Rent", category="🏠Home", amount=800),
        Expense(name="Movie", category="🎉Fun", amount=15),
    ]
    with open(csv_path, "w", encoding="utf-8") as handle:
        for item in expenses:
            handle.write(f"{item.name}, {item.amount}, {item.category}\n")

    delete_expense(expenses, 1, str(csv_path))  # remove "Rent"

    remaining = load_expenses(str(csv_path))
    names = [e.name for e in remaining]
    assert names == ["Coffee", "Movie"]
