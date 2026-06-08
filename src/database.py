import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

if os.environ.get("TESTING") == "true":
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "test_finance.db")
else:
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "finance.db")

def get_connection():
    """Returns a sqlite3 connection object to the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes database tables if they do not exist."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Transactions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        description TEXT NOT NULL,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        type TEXT NOT NULL CHECK(type IN ('Income', 'Expense'))
    )
    """)
    
    # 2. Budgets Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS budgets (
        category TEXT PRIMARY KEY,
        amount REAL NOT NULL
    )
    """)
    
    # 3. Portfolio Assets Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS portfolio (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker TEXT NOT NULL,
        shares REAL NOT NULL,
        purchase_price REAL NOT NULL,
        purchase_date TEXT NOT NULL
    )
    """)
    
    # 4. ML training override table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ml_training_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT UNIQUE NOT NULL,
        category TEXT NOT NULL
    )
    """)
    
    conn.commit()
    conn.close()

def add_transaction(date: str, description: str, amount: float, category: str, trans_type: str):
    """Adds a transaction to the database and feeds the ML training table."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO transactions (date, description, amount, category, type) VALUES (?, ?, ?, ?, ?)",
        (date, description, amount, category, trans_type)
    )
    
    # Also seed / update training data for the classifier
    cursor.execute(
        "INSERT OR REPLACE INTO ml_training_data (description, category) VALUES (?, ?)",
        (description.strip().lower(), category)
    )
    conn.commit()
    conn.close()

def get_all_transactions() -> pd.DataFrame:
    """Fetches all transactions and returns them as a pandas DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC, id DESC", conn)
    conn.close()
    return df

def delete_transaction(tx_id: int):
    """Deletes a transaction from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
    conn.commit()
    conn.close()

def update_transaction(tx_id: int, date: str, description: str, amount: float, category: str, trans_type: str) -> bool:
    """Updates an existing transaction and returns True when a row changed."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE transactions
        SET date = ?, description = ?, amount = ?, category = ?, type = ?
        WHERE id = ?
        """,
        (date, description, amount, category, trans_type, tx_id)
    )
    changed = cursor.rowcount > 0
    if changed:
        cursor.execute(
            "INSERT OR REPLACE INTO ml_training_data (description, category) VALUES (?, ?)",
            (description.strip().lower(), category)
        )
    conn.commit()
    conn.close()
    return changed

def get_budgets() -> dict:
    """Fetches all category budgets as a dictionary {category: amount}."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT category, amount FROM budgets")
    rows = cursor.fetchall()
    conn.close()
    return {row["category"]: row["amount"] for row in rows}

def set_budget(category: str, amount: float):
    """Sets/updates a budget for a category."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO budgets (category, amount) VALUES (?, ?)",
        (category, amount)
    )
    conn.commit()
    conn.close()

def get_portfolio() -> pd.DataFrame:
    """Fetches portfolio holdings as a pandas DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM portfolio ORDER BY ticker ASC", conn)
    conn.close()
    return df

def add_portfolio_asset(ticker: str, shares: float, purchase_price: float, purchase_date: str):
    """Adds a stock/crypto transaction to the portfolio database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO portfolio (ticker, shares, purchase_price, purchase_date) VALUES (?, ?, ?, ?)",
        (ticker.upper().strip(), shares, purchase_price, purchase_date)
    )
    conn.commit()
    conn.close()

def delete_portfolio_asset(asset_id: int):
    """Deletes a portfolio asset by its ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM portfolio WHERE id = ?", (asset_id,))
    conn.commit()
    conn.close()

def update_portfolio_asset(asset_id: int, ticker: str, shares: float, purchase_price: float, purchase_date: str) -> bool:
    """Updates a portfolio purchase record and returns True when a row changed."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE portfolio
        SET ticker = ?, shares = ?, purchase_price = ?, purchase_date = ?
        WHERE id = ?
        """,
        (ticker.upper().strip(), shares, purchase_price, purchase_date, asset_id)
    )
    changed = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return changed

def get_ml_training_data() -> pd.DataFrame:
    """Fetches the training data overrides for the ML classifier."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT description, category FROM ml_training_data", conn)
    conn.close()
    return df

def clear_db():
    """Wipes all database contents (useful for resets)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions")
    cursor.execute("DELETE FROM budgets")
    cursor.execute("DELETE FROM portfolio")
    cursor.execute("DELETE FROM ml_training_data")
    conn.commit()
    conn.close()

def _shift_months(base_date: datetime, months_delta: int, day: int) -> datetime:
    """Returns base_date shifted by whole months, clamped to a safe day."""
    month = base_date.month + months_delta
    year = base_date.year + (month - 1) // 12
    month = ((month - 1) % 12) + 1
    return base_date.replace(year=year, month=month, day=min(day, 28))

def seed_demo_data():
    """Loads a realistic demo workspace for portfolio demos and interviews."""
    clear_db()
    base_date = datetime.today().replace(day=1)

    recurring = [
        (5, "Salary credit - Product Analyst", 165000.0, "Income", "Income"),
        (6, "Rent payment apartment", 42000.0, "Housing", "Expense"),
        (8, "BigBasket grocery order", 12800.0, "Groceries", "Expense"),
        (10, "Uber commute pass", 5200.0, "Transportation", "Expense"),
        (12, "Electricity and broadband bill", 7600.0, "Bills & Utilities", "Expense"),
        (15, "Swiggy and cafe meals", 9400.0, "Food & Dining", "Expense"),
        (18, "Netflix Spotify subscriptions", 2100.0, "Entertainment", "Expense"),
        (22, "Amazon household shopping", 11800.0, "Shopping", "Expense"),
        (25, "Monthly SIP transfer to ETF", 30000.0, "Investments", "Expense"),
    ]

    for month_delta in range(-5, 1):
        month_factor = 1 + ((month_delta + 5) * 0.015)
        for day, description, amount, category, trans_type in recurring:
            date_str = _shift_months(base_date, month_delta, day).strftime("%Y-%m-%d")
            adjusted = amount if trans_type == "Income" else round(amount * month_factor, 2)
            add_transaction(date_str, description, adjusted, category, trans_type)

    one_offs = [
        (-4, 14, "Freelance dashboard consulting", 22000.0, "Income", "Income"),
        (-3, 19, "Movie night and dinner", 5600.0, "Entertainment", "Expense"),
        (-2, 11, "Bike service and fuel", 7200.0, "Transportation", "Expense"),
        (-1, 20, "Laptop upgrade for analytics work", 145000.0, "Shopping", "Expense"),
        (0, 3, "Dividend from index fund", 4200.0, "Income", "Income"),
        (0, 7, "Zomato team lunch", 3600.0, "Food & Dining", "Expense"),
    ]
    for month_delta, day, description, amount, category, trans_type in one_offs:
        add_transaction(
            _shift_months(base_date, month_delta, day).strftime("%Y-%m-%d"),
            description,
            amount,
            category,
            trans_type,
        )

    for category, amount in {
        "Food & Dining": 15000.0,
        "Groceries": 18000.0,
        "Transportation": 9000.0,
        "Bills & Utilities": 12000.0,
        "Housing": 45000.0,
        "Shopping": 30000.0,
        "Entertainment": 7000.0,
        "Investments": 40000.0,
    }.items():
        set_budget(category, amount)

    demo_assets = [
        ("RELIANCE.NS", 12.0, 2450.0, -10),
        ("TCS.NS", 6.0, 3580.0, -9),
        ("HDFCBANK.NS", 22.0, 1540.0, -8),
        ("INFY.NS", 15.0, 1410.0, -7),
        ("ICICIBANK.NS", 18.0, 980.0, -6),
    ]
    for ticker, shares, price, month_delta in demo_assets:
        add_portfolio_asset(
            ticker,
            shares,
            price,
            _shift_months(base_date, month_delta, 15).strftime("%Y-%m-%d"),
        )

def restore_profile(profile_data: dict) -> dict:
    """Restores a JSON profile export and returns import counts."""
    if not isinstance(profile_data, dict):
        raise ValueError("Profile payload must be a JSON object.")

    transactions = profile_data.get("transactions", [])
    portfolio = profile_data.get("portfolio", [])
    budgets = profile_data.get("budgets", {})
    ml_training_data = profile_data.get("ml_training_data", [])

    if not isinstance(transactions, list) or not isinstance(portfolio, list):
        raise ValueError("Profile payload has invalid transaction or portfolio data.")
    if not isinstance(budgets, dict):
        raise ValueError("Profile payload has invalid budget data.")
    if not isinstance(ml_training_data, list):
        raise ValueError("Profile payload has invalid ML training data.")

    clear_db()
    conn = get_connection()
    cursor = conn.cursor()

    transaction_count = 0
    for row in transactions:
        if not isinstance(row, dict):
            continue
        trans_type = str(row.get("type", "Expense")).title()
        if trans_type not in {"Income", "Expense"}:
            trans_type = "Expense"
        values = (
            str(row.get("date", ""))[:10],
            str(row.get("description", "")).strip(),
            float(row.get("amount", 0.0) or 0.0),
            str(row.get("category", "Shopping")).strip() or "Shopping",
            trans_type,
        )
        if not values[0] or not values[1]:
            continue
        row_id = row.get("id")
        if row_id is None:
            cursor.execute(
                "INSERT INTO transactions (date, description, amount, category, type) VALUES (?, ?, ?, ?, ?)",
                values,
            )
        else:
            cursor.execute(
                "INSERT INTO transactions (id, date, description, amount, category, type) VALUES (?, ?, ?, ?, ?, ?)",
                (int(row_id), *values),
            )
        cursor.execute(
            "INSERT OR REPLACE INTO ml_training_data (description, category) VALUES (?, ?)",
            (values[1].lower(), values[3]),
        )
        transaction_count += 1

    portfolio_count = 0
    for row in portfolio:
        if not isinstance(row, dict):
            continue
        values = (
            str(row.get("ticker", "")).strip().upper(),
            float(row.get("shares", 0.0) or 0.0),
            float(row.get("purchase_price", 0.0) or 0.0),
            str(row.get("purchase_date", ""))[:10],
        )
        if not values[0] or values[1] <= 0 or values[2] <= 0:
            continue
        row_id = row.get("id")
        if row_id is None:
            cursor.execute(
                "INSERT INTO portfolio (ticker, shares, purchase_price, purchase_date) VALUES (?, ?, ?, ?)",
                values,
            )
        else:
            cursor.execute(
                "INSERT INTO portfolio (id, ticker, shares, purchase_price, purchase_date) VALUES (?, ?, ?, ?, ?)",
                (int(row_id), *values),
            )
        portfolio_count += 1

    budget_count = 0
    for category, amount in budgets.items():
        cursor.execute(
            "INSERT OR REPLACE INTO budgets (category, amount) VALUES (?, ?)",
            (str(category), float(amount or 0.0)),
        )
        budget_count += 1

    ml_count = 0
    for row in ml_training_data:
        if not isinstance(row, dict):
            continue
        description = str(row.get("description", "")).strip().lower()
        category = str(row.get("category", "")).strip()
        if description and category:
            cursor.execute(
                "INSERT OR REPLACE INTO ml_training_data (description, category) VALUES (?, ?)",
                (description, category),
            )
            ml_count += 1

    conn.commit()
    conn.close()
    return {
        "transactions": transaction_count,
        "portfolio": portfolio_count,
        "budgets": budget_count,
        "ml_training_data": ml_count,
    }

if __name__ == "__main__":
    init_db()
    print("Database initialized at:", DB_PATH)
