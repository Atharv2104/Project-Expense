"""
expense_manager.py - CRUD operations and queries for expenses, income, savings, budgets.
"""

from datetime import datetime, timedelta
from database import get_connection

CATEGORIES = [
    "Food", "Travel", "Bills", "Shopping", "Medical",
    "Education", "Entertainment", "Other",
]
EXPENSE_TYPES = ["Small", "Big"]


def validate_date(date_str: str) -> bool:
    """Return True if date_str is a valid YYYY-MM-DD date."""
    if not date_str:
        return False
    try:
        datetime.strptime(date_str.strip(), "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate_amount(amount, allow_zero: bool = False) -> bool:
    """Return True if amount is a positive number (or zero if allowed)."""
    try:
        value = float(amount)
    except (TypeError, ValueError):
        return False
    if allow_zero:
        return value >= 0
    return value > 0


# ─── Expenses ───────────────────────────────────────────────────────────────

def add_expense(user_id, date, title, category, expense_type, amount, notes=""):
    """Add a new expense record."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO expenses (user_id, date, title, category, expense_type, amount, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, date, title, category, expense_type, float(amount), notes or ""),
        )
        return cursor.lastrowid


def update_expense(expense_id, user_id, date, title, category, expense_type, amount, notes=""):
    """Update an existing expense."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE expenses SET date=?, title=?, category=?, expense_type=?, amount=?, notes=?
               WHERE id=? AND user_id=?""",
            (date, title, category, expense_type, float(amount), notes or "", expense_id, user_id),
        )
        return cursor.rowcount > 0


def delete_expense(expense_id, user_id):
    """Delete an expense by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id=? AND user_id=?", (expense_id, user_id))
        return cursor.rowcount > 0


def get_expense(expense_id, user_id):
    """Get single expense by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM expenses WHERE id=? AND user_id=?", (expense_id, user_id))
        row = cursor.fetchone()
        return dict(row) if row else None


def search_expenses(user_id, date_from=None, date_to=None, category=None,
                    expense_type=None, search_text=None):
    """Search expenses with optional filters."""
    query = "SELECT * FROM expenses WHERE user_id = ?"
    params = [user_id]

    if date_from:
        query += " AND date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND date <= ?"
        params.append(date_to)
    if category and category != "All":
        query += " AND category = ?"
        params.append(category)
    if expense_type and expense_type != "All":
        query += " AND expense_type = ?"
        params.append(expense_type)
    if search_text:
        query += " AND (title LIKE ? OR notes LIKE ?)"
        params.extend([f"%{search_text}%", f"%{search_text}%"])

    query += " ORDER BY date DESC, id DESC"

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return [dict(r) for r in cursor.fetchall()]


def get_expenses_by_period(user_id, start_date, end_date):
    """Get all expenses in a date range."""
    return search_expenses(user_id, date_from=start_date, date_to=end_date)


# ─── Summaries ────────────────────────────────────────────────────────────────

def get_total_spending(user_id, start_date=None, end_date=None):
    """Total spending in optional date range."""
    expenses = search_expenses(user_id, date_from=start_date, date_to=end_date)
    return sum(e["amount"] for e in expenses)


def get_spending_by_type(user_id, start_date=None, end_date=None):
    """Return dict with Small and Big totals."""
    expenses = search_expenses(user_id, date_from=start_date, date_to=end_date)
    result = {"Small": 0.0, "Big": 0.0}
    for e in expenses:
        result[e["expense_type"]] = result.get(e["expense_type"], 0) + e["amount"]
    return result


def get_spending_by_category(user_id, start_date=None, end_date=None):
    """Return dict of category -> total amount."""
    expenses = search_expenses(user_id, date_from=start_date, date_to=end_date)
    result = {}
    for e in expenses:
        cat = e["category"]
        result[cat] = result.get(cat, 0) + e["amount"]
    return result


def get_weekly_summary(user_id, reference_date=None):
    """Summary for the week containing reference_date."""
    ref = reference_date or datetime.now().strftime("%Y-%m-%d")
    dt = datetime.strptime(ref, "%Y-%m-%d")
    start = (dt - timedelta(days=dt.weekday())).strftime("%Y-%m-%d")
    end = (dt + timedelta(days=6 - dt.weekday())).strftime("%Y-%m-%d")
    expenses = get_expenses_by_period(user_id, start, end)
    return {
        "start_date": start,
        "end_date": end,
        "total": sum(e["amount"] for e in expenses),
        "count": len(expenses),
        "small": sum(e["amount"] for e in expenses if e["expense_type"] == "Small"),
        "big": sum(e["amount"] for e in expenses if e["expense_type"] == "Big"),
        "by_category": _group_by_category(expenses),
    }


def get_monthly_summary(user_id, month=None, year=None):
    """Summary for a calendar month."""
    now = datetime.now()
    month = month or now.month
    year = year or now.year
    start = f"{year}-{month:02d}-01"
    if month == 12:
        end = f"{year}-12-31"
    else:
        end_dt = datetime(year, month + 1, 1) - timedelta(days=1)
        end = end_dt.strftime("%Y-%m-%d")

    expenses = get_expenses_by_period(user_id, start, end)
    return {
        "month": month,
        "year": year,
        "start_date": start,
        "end_date": end,
        "total": sum(e["amount"] for e in expenses),
        "count": len(expenses),
        "small": sum(e["amount"] for e in expenses if e["expense_type"] == "Small"),
        "big": sum(e["amount"] for e in expenses if e["expense_type"] == "Big"),
        "by_category": _group_by_category(expenses),
    }


def _group_by_category(expenses):
    result = {}
    for e in expenses:
        cat = e["category"]
        result[cat] = result.get(cat, 0) + e["amount"]
    return result


# ─── Budget ───────────────────────────────────────────────────────────────────

def set_budget(user_id, month, year, amount):
    """Set or update monthly budget."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO budgets (user_id, month, year, amount) VALUES (?, ?, ?, ?)
               ON CONFLICT(user_id, month, year) DO UPDATE SET amount=excluded.amount""",
            (user_id, month, year, float(amount)),
        )


def get_budget(user_id, month=None, year=None):
    """Get budget for month/year (defaults to current)."""
    now = datetime.now()
    month = month or now.month
    year = year or now.year
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT amount FROM budgets WHERE user_id=? AND month=? AND year=?",
            (user_id, month, year),
        )
        row = cursor.fetchone()
        return row["amount"] if row else 0.0


def get_remaining_budget(user_id, month=None, year=None):
    """Budget minus spending for the month."""
    now = datetime.now()
    month = month or now.month
    year = year or now.year
    budget = get_budget(user_id, month, year)
    summary = get_monthly_summary(user_id, month, year)
    return budget - summary["total"]


def is_budget_exceeded(user_id, month=None, year=None):
    """Check if monthly spending exceeds budget."""
    remaining = get_remaining_budget(user_id, month, year)
    budget = get_budget(user_id, month, year)
    if budget <= 0:
        return False, 0
    if remaining < 0:
        return True, abs(remaining)
    return False, 0


# ─── Income ─────────────────────────────────────────────────────────────────

def add_income(user_id, date, title, amount, notes=""):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO income (user_id, date, title, amount, notes) VALUES (?, ?, ?, ?, ?)",
            (user_id, date, title, float(amount), notes or ""),
        )
        return cursor.lastrowid


def update_income(income_id, user_id, date, title, amount, notes=""):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE income SET date=?, title=?, amount=?, notes=? WHERE id=? AND user_id=?",
            (date, title, float(amount), notes or "", income_id, user_id),
        )
        return cursor.rowcount > 0


def delete_income(income_id, user_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM income WHERE id=? AND user_id=?", (income_id, user_id))
        return cursor.rowcount > 0


def get_income_list(user_id, date_from=None, date_to=None):
    query = "SELECT * FROM income WHERE user_id = ?"
    params = [user_id]
    if date_from:
        query += " AND date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND date <= ?"
        params.append(date_to)
    query += " ORDER BY date DESC"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return [dict(r) for r in cursor.fetchall()]


def get_total_income(user_id, start_date=None, end_date=None):
    items = get_income_list(user_id, start_date, end_date)
    return sum(i["amount"] for i in items)


# ─── Savings ──────────────────────────────────────────────────────────────────

def add_savings(user_id, date, title, amount, transaction_type, notes=""):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO savings (user_id, date, title, amount, transaction_type, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, date, title, float(amount), transaction_type, notes or ""),
        )
        return cursor.lastrowid


def delete_savings(savings_id, user_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM savings WHERE id=? AND user_id=?", (savings_id, user_id))
        return cursor.rowcount > 0


def get_savings_list(user_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM savings WHERE user_id=? ORDER BY date DESC", (user_id,))
        return [dict(r) for r in cursor.fetchall()]


def get_savings_balance(user_id):
    """Net savings: deposits minus withdrawals."""
    items = get_savings_list(user_id)
    balance = 0.0
    for s in items:
        if s["transaction_type"] == "Deposit":
            balance += s["amount"]
        else:
            balance -= s["amount"]
    return balance


# ─── Financial Goals ──────────────────────────────────────────────────────────

def add_goal(user_id, title, target_amount, deadline="", description=""):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO financial_goals (user_id, title, target_amount, deadline, description)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, title, float(target_amount), deadline or None, description or ""),
        )
        return cursor.lastrowid


def update_goal_progress(goal_id, user_id, current_amount):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT target_amount FROM financial_goals WHERE id=? AND user_id=?",
            (goal_id, user_id),
        )
        row = cursor.fetchone()
        if not row:
            return False
        status = "Completed" if current_amount >= row["target_amount"] else "In Progress"
        cursor.execute(
            "UPDATE financial_goals SET current_amount=?, status=? WHERE id=? AND user_id=?",
            (float(current_amount), status, goal_id, user_id),
        )
        return True


def delete_goal(goal_id, user_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM financial_goals WHERE id=? AND user_id=?", (goal_id, user_id))
        return cursor.rowcount > 0


def get_goals(user_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM financial_goals WHERE user_id=? ORDER BY created_at DESC",
            (user_id,),
        )
        return [dict(r) for r in cursor.fetchall()]


def get_analytics(user_id, month=None, year=None):
    """Combined analytics for dashboard."""
    now = datetime.now()
    month = month or now.month
    year = year or now.year
    summary = get_monthly_summary(user_id, month, year)
    budget = get_budget(user_id, month, year)
    income = get_total_income(
        user_id,
        summary["start_date"],
        summary["end_date"],
    )
    savings = get_savings_balance(user_id)
    exceeded, over_amount = is_budget_exceeded(user_id, month, year)
    return {
        "monthly_total": summary["total"],
        "small_total": summary["small"],
        "big_total": summary["big"],
        "by_category": summary["by_category"],
        "budget": budget,
        "remaining_budget": budget - summary["total"] if budget > 0 else 0,
        "budget_exceeded": exceeded,
        "over_amount": over_amount,
        "income": income,
        "savings_balance": savings,
        "net_balance": income - summary["total"],
        "expense_count": summary["count"],
    }
