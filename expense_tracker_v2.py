from expense import Expense
import calendar
import datetime


def main():
    print("🎯Running Expense Tracker!")
    expense_file_path = "expenses.csv"
    budget = 2000

    # get user input for expense
    expense = get_user_expense()

    # write their expense to a file
    save_expense_to_file(expense, expense_file_path)

    # read file and summarize expenses
    summarize_expenses(expense_file_path, budget)


def get_user_expense():
    print("🎯Getting User Expense")
    expense_name = input("Enter expense name: ")
    expense_amount = float(input("Enter expense amount: "))
    # print(f"You have entered {expense_name}, {expense_amount}")

    expense_categories = [
        "🍔Food",
        "🏠Home",
        "💼Work",
        "🎉Fun",
        "✨Misc",
    ]

    while True:
        print("Select a Category: ")
        for i, category_name in enumerate(expense_categories):
            print(f"  {i+1}. {category_name}")

        value_range = f"[1-{len(expense_categories)}]"
        selected_index = int(
            input(f"Enter category number {value_range}: ")) - 1

        if selected_index in range(len(expense_categories)):
            selected_category = expense_categories[selected_index]
            new_expense = Expense(
                name=expense_name, category=selected_category, amount=expense_amount)
            return new_expense
        else:
            print("Invalid category. Please try again!")


def save_expense_to_file(expense: Expense, expense_file_path):
    print(f"💾 Saving User Expense: {expense} to {expense_file_path}")

    # Make sure we never glue a new row onto an existing line that is
    # missing its trailing newline (this is what caused rows to merge
    # after manual edits to the CSV).
    try:
        with open(expense_file_path, "rb") as f:
            f.seek(0, 2)  # go to end of file
            file_size = f.tell()
            if file_size > 0:
                f.seek(-1, 2)
                last_byte = f.read(1)
                needs_newline = last_byte != b"\n"
            else:
                needs_newline = False
    except FileNotFoundError:
        needs_newline = False

    with open(expense_file_path, "a", encoding="utf-8") as f:
        if needs_newline:
            f.write("\n")
        f.write(f"{expense.name}, {expense.amount}, {expense.category}\n")


def parse_expense_line(line, line_number):
    """
    Try to turn one raw CSV line into an Expense.
    Returns an Expense on success, or None if the line should be skipped
    (blank line, wrong number of fields, or a bad amount).
    Prints a friendly warning instead of crashing the whole program.
    """
    line = line.strip()

    # Skip blank lines (e.g. trailing newline at end of file, or a
    # blank line left behind after manually deleting an entry).
    if not line:
        return None

    fields = [field.strip() for field in line.split(",")]

    if len(fields) != 3:
        print(
            f"Skipping line {line_number}: expected 3 fields "
            f"(name, amount, category) but found {len(fields)} -> {line!r}"
        )
        return None

    expense_name, expense_amount, expense_category = fields

    if not expense_name or not expense_category:
        print(
            f"Skipping line {line_number}: missing name or category -> {line!r}")
        return None

    try:
        amount = float(expense_amount)
    except ValueError:
        print(
            f"Skipping line {line_number}: '{expense_amount}' is not a valid amount -> {line!r}")
        return None

    return Expense(name=expense_name, amount=amount, category=expense_category)


def summarize_expenses(expense_file_path, budget):
    print("📊 Summarizing User Expense")
    expenses: list[Expense] = []
    try:
        with open(expense_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = []

    for line_number, line in enumerate(lines, start=1):
        line_expense = parse_expense_line(line, line_number)
        if line_expense is not None:
            expenses.append(line_expense)

    if not expenses:
        print("No valid expenses found yet.")
        return

    amount_by_category = {}
    for expense in expenses:
        key = expense.category
        if key in amount_by_category:
            amount_by_category[key] += expense.amount
        else:
            amount_by_category[key] = expense.amount

    print("Expenses By Category 📊")
    for key, amount in amount_by_category.items():
        print(f"  {key}: ${amount:.2f}")

    total_spent = sum([x.amount for x in expenses])
    print(f"💵Total Spent: ${total_spent:.2f}")

    remaining_budget = budget - total_spent
    print(f"✅Budget Remaining: ${remaining_budget:.2f}")

    now = datetime.datetime.now()
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    remaining_days = days_in_month - now.day

    if remaining_days > 0:
        daily_budget = remaining_budget / remaining_days
        print(green(f"👉Budget Per Day: ${daily_budget:.2f}"))
    else:
        print(
            green(f"👉Budget Per Day: ${remaining_budget:.2f} (last day of the month)"))


def green(text):
    return f"\033[92m{text}\033[0m"


if __name__ == "__main__":
    main()
