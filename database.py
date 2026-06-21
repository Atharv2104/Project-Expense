"""
database.py - SQLite database layer for the Expense Tracker.
Handles connection, schema creation, and core data operations.
"""

import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager

# Database file path (override EXPENSE_DB_DIR on Android via mobile app)
_BASE = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.environ.get("EXPENSE_DB_DIR") or os.path.join(_BASE, "database")
DB_PATH = os.path.join(DB_DIR, "expense_tracker.db")


def ensure_db_dir():
    """Create database directory if it does not exist."""
    os.makedirs(DB_DIR, exist_ok=True)


@contextmanager
def get_connection():
    """Context manager for database connections with row factory."""
    ensure_db_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database():
    """Initialize all database tables."""
    ensure_db_dir()
    with get_connection() as conn:
        cursor = conn.cursor()

        # Users table for authentication
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Expenses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                expense_type TEXT NOT NULL CHECK(expense_type IN ('Small', 'Big')),
                amount REAL NOT NULL,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # Monthly budget per user
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                month INTEGER NOT NULL,
                year INTEGER NOT NULL,
                amount REAL NOT NULL,
                UNIQUE(user_id, month, year),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # Income entries
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS income (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                title TEXT NOT NULL,
                amount REAL NOT NULL,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # Savings tracker
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS savings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                title TEXT NOT NULL,
                amount REAL NOT NULL,
                transaction_type TEXT NOT NULL CHECK(transaction_type IN ('Deposit', 'Withdrawal')),
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # Financial goals
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS financial_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                target_amount REAL NOT NULL,
                current_amount REAL DEFAULT 0,
                deadline TEXT,
                description TEXT,
                status TEXT DEFAULT 'In Progress' CHECK(status IN ('In Progress', 'Completed', 'Cancelled')),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # User preferences (theme, etc.)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                theme TEXT DEFAULT 'dark',
                currency_symbol TEXT DEFAULT '₹',
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # Indexes for faster queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_user_date ON expenses(user_id, date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(user_id, category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_income_user_date ON income(user_id, date)")


def create_sample_data():
    """Create sample user and expenses for demonstration."""
    from auth_core import hash_password

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", ("demo",))
        if cursor.fetchone():
            return

        pwd_hash, salt = hash_password("demo123")
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, salt) VALUES (?, ?, ?, ?)",
            ("demo", "demo@expensetracker.com", pwd_hash, salt),
        )
        user_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO user_settings (user_id, theme, currency_symbol) VALUES (?, ?, ?)",
            (user_id, "dark", "₹"),
        )

        today = datetime.now()
        month, year = today.month, today.year
        cursor.execute(
            "INSERT INTO budgets (user_id, month, year, amount) VALUES (?, ?, ?, ?)",
            (user_id, month, year, 25000.0),
        )

        sample_expenses = [
            (f"{year}-{month:02d}-01", "Morning Tea", "Food", "Small", 30.0, "Daily chai"),
            (f"{year}-{month:02d}-02", "Bus Pass", "Travel", "Small", 500.0, "Monthly pass"),
            (f"{year}-{month:02d}-03", "Grocery", "Food", "Small", 1200.0, "Weekly groceries"),
            (f"{year}-{month:02d}-05", "Mobile Recharge", "Bills", "Small", 299.0, "Prepaid"),
            (f"{year}-{month:02d}-08", "Movie Night", "Entertainment", "Small", 450.0, ""),
            (f"{year}-{month:02d}-01", "Rent", "Bills", "Big", 12000.0, "Monthly rent"),
            (f"{year}-{month:02d}-10", "Shopping", "Shopping", "Big", 3500.0, "Clothes"),
            (f"{year}-{month:02d}-12", "Doctor Visit", "Medical", "Big", 800.0, "Checkup"),
        ]
        for date, title, cat, etype, amt, notes in sample_expenses:
            cursor.execute(
                """INSERT INTO expenses (user_id, date, title, category, expense_type, amount, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (user_id, date, title, cat, etype, amt, notes),
            )

        cursor.execute(
            "INSERT INTO income (user_id, date, title, amount, notes) VALUES (?, ?, ?, ?, ?)",
            (user_id, f"{year}-{month:02d}-01", "Salary", 45000.0, "Monthly salary"),
        )
        cursor.execute(
            "INSERT INTO savings (user_id, date, title, amount, transaction_type, notes) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, f"{year}-{month:02d}-05", "Emergency Fund", 5000.0, "Deposit", "Monthly savings"),
        )
        cursor.execute(
            """INSERT INTO financial_goals (user_id, title, target_amount, current_amount, deadline, description)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, "New Laptop", 60000.0, 15000.0, f"{year + 1}-06-30", "Save for work laptop"),
        )


if __name__ == "__main__":
    init_database()
    create_sample_data()
    print(f"Database initialized at: {DB_PATH}")
