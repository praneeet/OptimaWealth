import pytest
import pandas as pd
import numpy as np
import os
import sqlite3
from unittest.mock import patch, MagicMock

# Set environment before imports
import os
os.environ["TESTING"] = "true"

import src.database as db
import src.categorizer as cat
import src.optimizer as opt
import src.forecasting as forec
import src.utils as utils

def test_database_init():
    """Verify that tables are correctly initialized and connection is working."""
    db.init_db()
    assert os.path.exists(db.DB_PATH)
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Check tables list
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    assert "transactions" in tables
    assert "budgets" in tables
    assert "portfolio" in tables
    assert "ml_training_data" in tables
    conn.close()

def test_transaction_crud():
    """Verify adding, fetching, and deleting transactions works properly."""
    db.init_db()
    db.clear_db()
    
    # Add transaction
    db.add_transaction("2026-06-01", "Coffee Shop", 4.50, "Food & Dining", "Expense")
    db.add_transaction("2026-06-02", "Salary Payment", 3000.00, "Income", "Income")
    
    df = db.get_all_transactions()
    assert len(df) == 2
    assert df.loc[df["description"] == "Coffee Shop", "amount"].values[0] == 4.50
    assert df.loc[df["description"] == "Salary Payment", "type"].values[0] == "Income"
    
    # Delete transaction
    tx_id = df.loc[df["description"] == "Coffee Shop", "id"].values[0]
    db.delete_transaction(int(tx_id))
    
    df_after = db.get_all_transactions()
    assert len(df_after) == 1
    assert "Coffee Shop" not in df_after["description"].values

def test_transaction_and_portfolio_updates():
    """Verify update flows used by the Streamlit CRUD forms."""
    db.init_db()
    db.clear_db()

    db.add_transaction("2026-06-01", "Coffee Shop", 4.50, "Food & Dining", "Expense")
    tx_id = int(db.get_all_transactions().iloc[0]["id"])
    updated = db.update_transaction(tx_id, "2026-06-02", "Coffee and sandwich", 12.75, "Food & Dining", "Expense")
    assert updated is True

    df_tx = db.get_all_transactions()
    assert df_tx.iloc[0]["description"] == "Coffee and sandwich"
    assert df_tx.iloc[0]["amount"] == 12.75

    db.add_portfolio_asset("TCS.NS", 2.0, 3500.0, "2026-01-01")
    asset_id = int(db.get_portfolio().iloc[0]["id"])
    asset_updated = db.update_portfolio_asset(asset_id, "INFY.NS", 3.0, 1450.0, "2026-02-01")
    assert asset_updated is True

    df_assets = db.get_portfolio()
    assert df_assets.iloc[0]["ticker"] == "INFY.NS"
    assert df_assets.iloc[0]["shares"] == 3.0

def test_demo_seed_and_profile_restore():
    """Verify the demo workspace and JSON restore workflow populate core tables."""
    db.init_db()
    db.seed_demo_data()

    df_tx = db.get_all_transactions()
    df_portfolio = db.get_portfolio()
    budgets = db.get_budgets()
    ml_training = db.get_ml_training_data()

    assert len(df_tx) >= 50
    assert len(df_portfolio) >= 5
    assert len(budgets) >= 6
    assert len(ml_training) >= 10

    profile = {
        "transactions": df_tx.head(3).to_dict(orient="records"),
        "portfolio": df_portfolio.head(2).to_dict(orient="records"),
        "budgets": {"Food & Dining": 12000.0},
        "ml_training_data": ml_training.head(2).to_dict(orient="records"),
    }
    counts = db.restore_profile(profile)

    assert counts["transactions"] == 3
    assert counts["portfolio"] == 2
    assert counts["budgets"] == 1
    assert len(db.get_all_transactions()) == 3
    assert db.get_budgets()["Food & Dining"] == 12000.0

def test_ml_categorizer():
    """Verify rule-based fallback and ML prediction capability."""
    categorizer = cat.TransactionCategorizer()
    
    # Test keyword rule fallback
    cat_val, conf = categorizer.predict("starbucks coffee store")
    assert cat_val == "Food & Dining"
    assert conf == 1.0
    
    # Test default fallback
    cat_val_def, conf_def = categorizer.predict("unknown merchant name")
    assert cat_val_def == "Shopping"
    assert conf_def == 0.50
    
    # Test model training on mock data frame
    mock_data = pd.DataFrame({
        "description": [
            "starbucks coffee", "mcdonalds burger", "local diner lunch",
            "whole foods grocery", "kroger supermarket", "walmart market",
            "netflix premium", "spotify music subscription", "comcast internet cable",
            "uber trip transit", "lyft ride taxi", "shell gas station"
        ],
        "category": [
            "Food & Dining", "Food & Dining", "Food & Dining",
            "Groceries", "Groceries", "Groceries",
            "Bills & Utilities", "Bills & Utilities", "Bills & Utilities",
            "Transportation", "Transportation", "Transportation"
        ]
    })
    
    # Manually seed ML database with mock dataframe for testing pipeline fit
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ml_training_data")
    for _, row in mock_data.iterrows():
        cursor.execute(
            "INSERT OR REPLACE INTO ml_training_data (description, category) VALUES (?, ?)",
            (row["description"], row["category"])
        )
    conn.commit()
    conn.close()
    
    # Train
    categorizer.train()
    assert categorizer.is_trained == True
    
    # Predict with trained ML model
    pred, prob = categorizer.predict("diner food")
    assert pred == "Food & Dining"
    assert prob > 0.35

def test_portfolio_optimizer():
    """Verify portfolio calculations and math solver."""
    # Generate dummy prices DataFrame
    np.random.seed(42)
    dates = pd.date_range(start="2025-01-01", periods=100, freq="D")
    prices_df = pd.DataFrame({
        "AAPL": np.cumsum(np.random.normal(0.0005, 0.01, 100)) + 150,
        "MSFT": np.cumsum(np.random.normal(0.0006, 0.008, 100)) + 300
    }, index=dates)
    
    returns = np.log(prices_df / prices_df.shift(1)).dropna()
    mean_returns = returns.mean()
    cov_matrix = returns.cov()
    
    # Test performance calculation
    weights = np.array([0.5, 0.5])
    p_ret, p_vol, p_sharpe = opt.calculate_portfolio_performance(weights, mean_returns, cov_matrix, risk_free_rate=0.04)
    assert isinstance(p_ret, float)
    assert isinstance(p_vol, float)
    assert isinstance(p_sharpe, float)
    assert p_vol > 0
    
    # Test optimization
    res = opt.optimize_portfolio(prices_df, risk_free_rate=0.04)
    assert "max_sharpe" in res
    assert "min_volatility" in res
    assert np.allclose(sum(res["max_sharpe"]["weights"].values()), 1.0)
    assert np.allclose(sum(res["min_volatility"]["weights"].values()), 1.0)

def test_forecasting():
    """Verify time-series expense forecasting is working and robust to small datasets."""
    # Empty transaction case
    df_empty = pd.DataFrame()
    res_empty = forec.forecast_expenses(df_empty, forecast_months=6)
    assert res_empty.empty
    
    # Seed db manually and test forecasting
    db.init_db()
    db.clear_db()
    db.add_transaction("2026-03-01", "Rent payment housing", 1000.0, "Housing", "Expense")
    db.add_transaction("2026-04-01", "Rent payment housing", 1000.0, "Housing", "Expense")
    db.add_transaction("2026-05-01", "Rent payment housing", 1000.0, "Housing", "Expense")
    db.add_transaction("2026-03-15", "Salary", 3000.0, "Income", "Income")
    db.add_transaction("2026-04-15", "Salary", 3000.0, "Income", "Income")
    db.add_transaction("2026-05-15", "Salary", 3000.0, "Income", "Income")
    df_tx = db.get_all_transactions()
    
    # Forecast expenses
    df_f = forec.forecast_expenses(df_tx, forecast_months=6)
    assert not df_f.empty
    assert len(df_f) == 6
    assert list(df_f.columns) == ["Month", "Forecast", "Upper_Bound", "Lower_Bound"]
    
    # Forecast net worth
    df_nw = forec.project_net_worth(df_tx, current_portfolio_value=15000.0, annual_growth_rate=0.08, forecast_months=6)
    assert not df_nw.empty
    assert len(df_nw) == 6

def test_anomaly_detection():
    """Verify that Isolation Forest anomaly detection flags spending outliers."""
    # Seed small transaction df with an outlier
    data = {
        "id": [1, 2, 3, 4, 5, 6, 7, 8],
        "date": ["2026-06-01", "2026-06-02", "2026-06-03", "2026-06-04", "2026-06-05", "2026-06-06", "2026-06-07", "2026-06-08"],
        "description": ["Coffee", "Lunch", "Coffee", "Diner", "Coffee", "Taxi", "Grocery", "Extravagant Yacht Purchase"],
        "amount": [4.50, 12.00, 5.00, 15.50, 4.00, 18.00, 85.00, 9500.00],  # 9500 is extreme
        "category": ["Food & Dining", "Food & Dining", "Food & Dining", "Food & Dining", "Food & Dining", "Transportation", "Groceries", "Shopping"],
        "type": ["Expense"] * 8
    }
    df = pd.DataFrame(data)
    
    anomalies = forec.detect_expense_anomalies(df, contamination=0.15)
    assert not anomalies.empty
    # The extravagant yacht purchase should be flagged as the main anomaly
    assert "Extravagant Yacht Purchase" in anomalies["description"].values
    assert anomalies.iloc[0]["amount"] == 9500.00

def test_risk_metrics():
    """Verify that portfolio risk calculators (VaR/CVaR) output valid stats."""
    np.random.seed(42)
    dates = pd.date_range(start="2025-01-01", periods=100, freq="D")
    prices_df = pd.DataFrame({
        "AAPL": np.cumsum(np.random.normal(0.0005, 0.01, 100)) + 150,
        "MSFT": np.cumsum(np.random.normal(0.0006, 0.008, 100)) + 300
    }, index=dates)
    
    weights = {"AAPL": 0.6, "MSFT": 0.4}
    portfolio_value = 10000.0
    
    risk = opt.calculate_portfolio_risk_metrics(prices_df, weights, portfolio_value, confidence_level=0.95)
    
    assert "parametric" in risk
    assert "historical" in risk
    assert "cvar" in risk
    
    assert risk["parametric"]["usd_1d"] > 0
    assert risk["historical"]["usd_1d"] > 0
    assert risk["cvar"]["usd_1d"] > 0
    
    # CVaR is always worse or equal to VaR for standard returns distributions
    assert risk["cvar"]["pct_1d"] >= risk["historical"]["pct_1d"]

def test_monte_carlo_simulation():
    """Verify that Monte Carlo Geometric Brownian Motion simulates correct timeline dimensions."""
    np.random.seed(42)
    dates = pd.date_range(start="2025-01-01", periods=100, freq="D")
    prices_df = pd.DataFrame({
        "AAPL": np.cumsum(np.random.normal(0.0005, 0.01, 100)) + 150,
        "MSFT": np.cumsum(np.random.normal(0.0006, 0.008, 100)) + 300
    }, index=dates)
    
    weights = {"AAPL": 0.5, "MSFT": 0.5}
    portfolio_value = 10000.0
    
    df_sim = opt.simulate_monte_carlo(prices_df, weights, portfolio_value, years=5, num_simulations=100)
    
    assert not df_sim.empty
    assert "Year" in df_sim.columns
    assert "Conservative (10th)" in df_sim.columns
    assert "Expected (50th)" in df_sim.columns
    assert "Optimistic (90th)" in df_sim.columns
    
    # 5 years * 12 steps/year + 1 starting step = 61 rows
    assert len(df_sim) == 61
    assert df_sim.iloc[0]["Expected (50th)"] == portfolio_value

def test_currency_detection_and_formatting():
    """Verify currency formatting functions and CSV detection logic."""
    # Check default currency symbol formatting (defaults to ₹)
    assert utils.format_currency(1500.0) == "₹1,500.00"
    assert utils.format_currency(-50.25) == "-₹50.25"
    
    # Create a mock CSV dataframe with specific currency header
    df_usd_header = pd.DataFrame({
        "Date": ["2026-06-01"],
        "Description": ["Salary"],
        "Amount ($)": ["$3,200.50"],
        "Type": ["Income"]
    })
    
    df_cleaned, name, symbol = utils.detect_and_clean_currency(df_usd_header)
    assert name == "USD"
    assert symbol == "$"
    assert df_cleaned.iloc[0]["Amount"] == 3200.50
    assert "Amount" in df_cleaned.columns
    
    # Create mock CSV with cell currency symbols and standard Amount header
    df_inr_cell = pd.DataFrame({
        "Date": ["2026-06-01"],
        "Description": ["Coffee"],
        "Amount": ["₹120.00"],
        "Type": ["Expense"]
    })
    df_cleaned_inr, name_inr, symbol_inr = utils.detect_and_clean_currency(df_inr_cell)
    assert name_inr == "INR"
    assert symbol_inr == "₹"
    assert df_cleaned_inr.iloc[0]["Amount"] == 120.00

def test_financial_health_score_and_template():
    """Verify dashboard health scoring and import template helpers."""
    sample_transactions = pd.DataFrame({
        "date": ["2026-06-01", "2026-06-02", "2026-06-03", "2026-06-04"],
        "description": ["Salary", "Rent", "Groceries", "ETF SIP"],
        "amount": [100000.0, 30000.0, 12000.0, 15000.0],
        "category": ["Income", "Housing", "Groceries", "Investments"],
        "type": ["Income", "Expense", "Expense", "Expense"],
    })

    health = utils.calculate_financial_health(
        sample_transactions,
        {"Housing": 35000.0, "Groceries": 15000.0, "Investments": 20000.0},
        portfolio_value=250000.0,
        holding_count=4,
    )

    assert health["score"] > 50
    assert health["grade"] in {"Strong", "Excellent", "Watchlist", "Needs attention"}
    assert health["savings_rate"] > 0

    template = utils.build_sample_csv_template("$")
    assert template.splitlines()[0] == "Date,Description,Amount,Type"
    assert "$85000.00" in template

@patch("src.optimizer.yf.download")
def test_fetch_historical_prices_mocked(mock_download):
    """Verify fetch_historical_prices works correctly using a mocked yfinance response."""
    # Mock return value of yfinance download with standard stock close prices
    mock_data = pd.DataFrame(
        {"AAPL": [150.0, 155.0], "MSFT": [300.0, 305.0]},
        columns=["AAPL", "MSFT"]
    )
    # yfinance download returns a MultiIndex columns DataFrame when downloading multiple tickers
    mock_data.columns = pd.MultiIndex.from_tuples([("Close", "AAPL"), ("Close", "MSFT")])
    mock_download.return_value = mock_data
    
    res = opt.fetch_historical_prices(["AAPL", "MSFT"], period="1mo")
    assert res.empty is False or res is not None
    assert "AAPL" in res.columns
    assert "MSFT" in res.columns
    assert mock_download.called


def test_parse_uploaded_csv_custom():
    """Verify that parse_uploaded_csv correctly parses custom bank statement data."""
    # Create sample custom bank CSV content
    custom_csv = """" ",,Account Statement
Praneet Pravin
P9 006 Paeonia,,,,Cust. Reln. No.,833882272
"Prateek Grand City ",,,,Account No.,3349936986
"Siddharth Vihar ",,,,Period,From 07/03/2026 To 07/06/2026
Ghaziabad,,,,Currency,INR
Uttar Pradesh,,,,Branch,Ghaziabad - Indirapuram
India,,,,Nomination Regd,Y
201009,,,,Nominee Name,PRAVIN KUMAR GHOSH
"",,,,Joint Holder(S),
"",,,,IFSC,KKBK0005289
"",,,,MICR,110485082
""
Sl. No.,Transaction Date,Value Date,Description,Chq / Ref No.,Amount,Dr / Cr,Balance,Dr / Cr
1,06-06-2026 22:04:25,06-06-2026,BILL PAID TO CREDIT CARD XX0488,CCBILL-1780763664795,500.00,DR,0.46,CR
2,06-06-2026 22:04:07,06-06-2026,UPI/Nikhil Kumar Si/615762270582/UPI,UPI-615719372785,500.00,CR,500.46,CR
3,06-06-2026 22:01:32,06-06-2026,BILL PAID TO CREDIT CARD XX0488,CCBILL-1780763491925,520.00,DR,0.46,CR
"""
    df, name, symbol = utils.parse_uploaded_csv(custom_csv.encode("utf-8"))
    
    assert name == "INR"
    assert symbol == "₹"
    assert len(df) == 3
    assert list(df.columns) == ["Date", "Description", "Amount", "Type"]
    # Check individual rows
    assert df.iloc[0]["Date"] == "2026-06-06"
    assert df.iloc[0]["Amount"] == 500.0
    assert df.iloc[0]["Type"] == "Expense"
    
    assert df.iloc[1]["Date"] == "2026-06-06"
    assert df.iloc[1]["Amount"] == 500.0
    assert df.iloc[1]["Type"] == "Income"


@patch("pypdf.PdfReader")
def test_parse_credit_card_pdf(mock_pdf_reader):
    """Verify that parse_credit_card_pdf correctly parses transactions from PDF pages."""
    mock_page_1 = MagicMock()
    mock_page_1.extract_text.return_value = (
        "Statement Summary\n"
        "Total Purchases: 26,298.76\n"
        "Total Fees: 0.00\n"
        "Total Amount Due: 10,000.00\n"
    )
    
    mock_page_2 = MagicMock()
    mock_page_2.extract_text.return_value = (
        "06-May-2026 AMAZON SELLER SERVICES BENGALURU 1,299.00\n"
        "08-May-2026 INTERNET PAYMENT 5,000.00 Cr\n"
        "10-May-2026 SWIGGY GURUGRAM 450.50\n"
    )
    
    mock_reader_instance = MagicMock()
    mock_reader_instance.pages = [mock_page_1, mock_page_2]
    mock_pdf_reader.return_value = mock_reader_instance
    
    df = utils.parse_credit_card_pdf(b"fake_pdf_data")
    
    assert len(df) == 2
    assert list(df.columns) == ["Date", "Description", "Amount", "Type"]
    
    # Row 0 - Spend (Expense)
    assert df.iloc[0]["Date"] == "2026-05-06"
    assert df.iloc[0]["Description"] == "AMAZON SELLER SERVICES BENGALURU"
    assert df.iloc[0]["Amount"] == 1299.00
    assert df.iloc[0]["Type"] == "Expense"
    
    # Row 1 - Spend (Expense)
    assert df.iloc[1]["Date"] == "2026-05-10"
    assert df.iloc[1]["Description"] == "SWIGGY GURUGRAM"
    assert df.iloc[1]["Amount"] == 450.50
    assert df.iloc[1]["Type"] == "Expense"
    
    # Ensure the bill payment transaction was skipped
    assert "INTERNET PAYMENT" not in df["Description"].values


def test_parse_holdings_csv():
    """Verify that parse_holdings_csv parses custom and standard headings correctly."""
    # Standard CSV content
    csv_data = b"Ticker,Shares,Purchase Price,Purchase Date\nAAPL,10,175.50,2026-01-15\nINFY.NS,15.5,1450.00,2026-03-20\n"
    df = utils.parse_holdings_csv(csv_data)
    
    assert len(df) == 2
    assert set(df.columns) == {"Ticker", "Shares", "Purchase Price", "Purchase Date"}
    assert df.iloc[0]["Ticker"] == "AAPL"
    assert df.iloc[0]["Shares"] == 10.0
    assert df.iloc[0]["Purchase Price"] == 175.50
    assert df.iloc[0]["Purchase Date"] == "2026-01-15"
    
    # Alternate/case-insensitive CSV headings
    csv_alt_data = b"asset,qty,cost_price,buy_date\nMSFT,5,420.00,10/02/2026\n"
    df_alt = utils.parse_holdings_csv(csv_alt_data)
    assert len(df_alt) == 1
    assert df_alt.iloc[0]["Ticker"] == "MSFT"
    assert df_alt.iloc[0]["Shares"] == 5.0
    assert df_alt.iloc[0]["Purchase Price"] == 420.00
    
    # Invalid rows (shares/price <= 0) should be dropped
    csv_invalid = b"Ticker,Shares,Purchase Price,Purchase Date\nAAPL,0,175.50,2026-01-15\nMSFT,5,-10,2026-02-10\n"
    df_invalid = utils.parse_holdings_csv(csv_invalid)
    assert len(df_invalid) == 0


def test_import_holdings_duplicate_handling():
    """Verify that duplicate holdings are correctly identified and skipped."""
    db.init_db()
    db.clear_db()
    
    # Add a holding manually first
    db.add_portfolio_asset("TCS.NS", 10.0, 3500.00, "2026-05-15")
    
    # Verify it is in database
    existing_df = db.get_portfolio()
    assert len(existing_df) == 1
    
    # Mimic the import loop logic
    csv_data = b"Ticker,Shares,Purchase Price,Purchase Date\nTCS.NS,10,3500.00,2026-05-15\nAAPL,5,175.00,2026-06-01\n"
    df_imported = utils.parse_holdings_csv(csv_data)
    
    existing_set = set()
    for _, r in existing_df.iterrows():
        existing_set.add((
            str(r["ticker"]).upper().strip(),
            float(r["shares"]),
            float(r["purchase_price"]),
            str(r["purchase_date"]).strip()
        ))
        
    new_records = []
    skipped_duplicates = 0
    
    for _, row in df_imported.iterrows():
        key = (
            str(row["Ticker"]).upper().strip(),
            float(row["Shares"]),
            float(row["Purchase Price"]),
            str(row["Purchase Date"]).strip()
        )
        if key in existing_set:
            skipped_duplicates += 1
        else:
            new_records.append(row)
            existing_set.add(key)
            
    assert len(new_records) == 1
    assert skipped_duplicates == 1
    assert new_records[0]["Ticker"] == "AAPL"



