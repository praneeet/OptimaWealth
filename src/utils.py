import streamlit as st
import pandas as pd

def inject_custom_css():
    """Injects custom CSS to style the Streamlit interface for a premium dark mode, glassmorphic look."""
    st.html(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
        
        /* Font family setup & Global styles */
        html, body, [class*="css"], .stMarkdown {
            font-family: 'Outfit', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            color: #f1f3f9;
        }
        
        /* Force premium dark background across all main containers */
        .stApp, .stMain, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            background-color: #030712 !important;
        }
        
        /* Premium custom scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        ::-webkit-scrollbar-track {
            background: rgba(11, 15, 25, 0.5);
        }
        ::-webkit-scrollbar-thumb {
            background: rgba(139, 92, 246, 0.3);
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: rgba(139, 92, 246, 0.5);
        }
        
        /* Glassmorphic cards with subtle micro-interaction */
        .glass-card {
            background: linear-gradient(135deg, rgba(30, 34, 45, 0.75) 0%, rgba(20, 24, 33, 0.75) 100%);
            backdrop-filter: blur(24px) saturate(180%);
            -webkit-backdrop-filter: blur(24px) saturate(180%);
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.45);
            color: #f1f3f9;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        }
        
        .glass-card:hover {
            transform: translateY(-2px);
            border-color: rgba(139, 92, 246, 0.3);
            box-shadow: 0 20px 60px 0 rgba(139, 92, 246, 0.15);
        }
        
        /* Premium Stat KPI Card design */
        .stat-card {
            background: linear-gradient(135deg, rgba(23, 28, 41, 0.95) 0%, rgba(13, 17, 28, 0.95) 100%);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 12px;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.05);
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        }
        
        .stat-card:hover {
            transform: translateY(-3px);
            border-color: rgba(255, 255, 255, 0.1);
        }
        
        .stat-income {
            border-left: 5px solid #10b981;
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.06) 0%, rgba(13, 17, 28, 0.95) 100%);
        }
        .stat-income:hover {
            box-shadow: 0 12px 30px rgba(16, 185, 129, 0.15);
        }
        
        .stat-expense {
            border-left: 5px solid #ef4444;
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.06) 0%, rgba(13, 17, 28, 0.95) 100%);
        }
        .stat-expense:hover {
            box-shadow: 0 12px 30px rgba(239, 68, 68, 0.15);
        }
        
        .stat-portfolio {
            border-left: 5px solid #f59e0b;
            background: linear-gradient(135deg, rgba(245, 158, 11, 0.06) 0%, rgba(13, 17, 28, 0.95) 100%);
        }
        .stat-portfolio:hover {
            box-shadow: 0 12px 30px rgba(245, 158, 11, 0.15);
        }
        
        .stat-savings {
            border-left: 5px solid #8b5cf6;
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.06) 0%, rgba(13, 17, 28, 0.95) 100%);
        }
        .stat-savings:hover {
            box-shadow: 0 12px 30px rgba(139, 92, 246, 0.15);
        }
        
        .stat-label {
            font-size: 0.8rem;
            color: #9ca3af;
            text-transform: uppercase;
            font-weight: 600;
            letter-spacing: 0.08em;
        }
        
        .stat-val {
            font-size: 1.9rem;
            font-weight: 700;
            color: #ffffff;
            margin-top: 6px;
            letter-spacing: -0.01em;
        }
        
        /* Title styling with gradient text */
        .gradient-text {
            background: linear-gradient(90deg, #a78bfa 0%, #818cf8 50%, #60a5fa 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
        }
        
        /* Reset gradient text clipping/fill for emojis to prevent them from becoming invisible in Chrome */
        .logo-emoji {
            display: inline-block;
            background: none !important;
            -webkit-background-clip: border-box !important;
            -webkit-text-fill-color: initial !important;
            color: initial !important;
        }

        .empty-panel {
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.10) 0%, rgba(17, 24, 39, 0.88) 52%, rgba(245, 158, 11, 0.10) 100%);
            border: 1px solid rgba(255, 255, 255, 0.10);
            border-radius: 8px;
            padding: 28px;
            margin-bottom: 18px;
            box-shadow: 0 14px 46px rgba(0, 0, 0, 0.32);
        }

        .empty-panel h2 {
            margin: 4px 0 8px 0;
            font-size: 1.55rem;
            line-height: 1.25;
            color: #ffffff;
            letter-spacing: 0;
        }

        .empty-panel p {
            margin: 0;
            color: #cbd5e1;
            max-width: 780px;
            line-height: 1.6;
        }

        .empty-eyebrow {
            color: #34d399;
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }
        
        /* Table / DataFrame container styling override */
        .stDataFrame {
            background-color: transparent;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            overflow: hidden;
        }
        
        /* Customized alerts */
        .alert-card {
            padding: 14px 18px;
            border-radius: 8px;
            margin-bottom: 15px;
            font-size: 0.92rem;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 10px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
        }
        .alert-success {
            background: linear-gradient(90deg, rgba(16, 185, 129, 0.15) 0%, rgba(16, 185, 129, 0.05) 100%);
            border: 1px solid rgba(16, 185, 129, 0.35);
            color: #34d399;
        }
        .alert-warning {
            background: linear-gradient(90deg, rgba(245, 158, 11, 0.15) 0%, rgba(245, 158, 11, 0.05) 100%);
            border: 1px solid rgba(245, 158, 11, 0.35);
            color: #fbbf24;
        }
        .alert-danger {
            background: linear-gradient(90deg, rgba(239, 68, 68, 0.15) 0%, rgba(239, 68, 68, 0.05) 100%);
            border: 1px solid rgba(239, 68, 68, 0.35);
            color: #fca5a5;
        }
        
        /* Action buttons custom styling */
        div.stButton > button {
            background: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%) !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 10px 20px !important;
            font-weight: 600 !important;
            letter-spacing: 0.03em !important;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2) !important;
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
        }
        div.stButton > button:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 20px rgba(139, 92, 246, 0.4) !important;
            background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%) !important;
            color: white !important;
        }
        div.stButton > button:active {
            transform: translateY(1px) !important;
        }
        
        /* Customize Streamlit Tabs into a premium Segmented Control button bar */
        div[role="tablist"] {
            background-color: #111827 !important;
            border-radius: 8px !important;
            padding: 5px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            margin-bottom: 25px !important;
            display: flex !important;
            width: 100% !important;
            border-bottom: none !important;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important;
            backdrop-filter: blur(8px) !important;
            -webkit-backdrop-filter: blur(8px) !important;
        }
        
        button[role="tab"] {
            font-size: 0.95rem !important;
            font-weight: 600 !important;
            color: #9ca3af !important;
            border-bottom: none !important;
            padding: 10px 20px !important;
            border-radius: 8px !important;
            transition: all 0.25s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
            background-color: transparent !important;
            margin: 0 2px !important;
            border: none !important;
            flex-grow: 1 !important;
            text-align: center !important;
        }
        
        /* Force color inheritance for nested paragraph elements in tab buttons */
        button[role="tab"] *, 
        button[role="tab"] p {
            color: inherit !important;
            font-size: inherit !important;
            font-weight: inherit !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        
        button[role="tab"]:hover {
            color: #ffffff !important;
            background-color: rgba(255, 255, 255, 0.08) !important;
            border-bottom: none !important;
        }
        
        button[role="tab"][aria-selected="true"] {
            color: #ffffff !important;
            background-color: #8b5cf6 !important;
            background-image: linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%) !important;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.35) !important;
            border-bottom: none !important;
        }
        
        /* Hide the default underline highlights */
        div.stTabs div[data-baseweb="tab-highlight"],
        div.stTabs div[data-testid="stTabHighlight"] {
            display: none !important;
            height: 0px !important;
        }
        
        /* Streamlit Input fields styling */
        div[data-testid="stTextInput"] input, 
        div[data-testid="stNumberInput"] input,
        div[data-testid="stDateInput"] input {
            background-color: rgba(20, 24, 33, 0.7) !important;
            color: #ffffff !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 8px !important;
            padding: 10px 14px !important;
            transition: all 0.3s ease !important;
        }
        div[data-testid="stTextInput"] input:focus, 
        div[data-testid="stNumberInput"] input:focus,
        div[data-testid="stDateInput"] input:focus {
            border-color: #8b5cf6 !important;
            box-shadow: 0 0 10px rgba(139, 92, 246, 0.25) !important;
            outline: none !important;
        }
        
        /* File Uploader styling */
        div[data-testid="stFileUploader"] {
            background: rgba(30, 34, 45, 0.4) !important;
            border: 1.5px dashed rgba(139, 92, 246, 0.3) !important;
            border-radius: 8px !important;
            padding: 16px !important;
            transition: all 0.3s ease !important;
        }
        div[data-testid="stFileUploader"]:hover {
            border-color: #8b5cf6 !important;
            background: rgba(30, 34, 45, 0.6) !important;
        }
        
        /* Selectbox styling */
        div[data-testid="stSelectbox"] > div {
            background-color: rgba(20, 24, 33, 0.7) !important;
            color: #ffffff !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 8px !important;
        }
        
        /* Make top header transparent and hide default settings icons */
        [data-testid="stHeader"] {
            background-color: transparent !important;
        }
        [data-testid="stHeader"] [data-testid="stHeaderActionElements"],
        [data-testid="stHeader"] [data-testid="stToolbar"] {
            display: none !important;
        }
        
        /* Hide default Streamlit footer */
        footer {
            visibility: hidden !important;
            height: 0px !important;
            padding: 0px !important;
        }
        </style>
        """
    )

def get_currency_symbol() -> str:
    """Returns the currently active currency symbol from Streamlit session state, defaulting to '₹'."""
    try:
        if st.session_state and "currency_symbol" in st.session_state:
            return st.session_state["currency_symbol"]
    except Exception:
        pass
    return "₹"

def format_currency(amount: float) -> str:
    """Formats a float value as a currency string with the active currency symbol."""
    symbol = get_currency_symbol()
    if amount < 0:
        return f"-{symbol}{abs(amount):,.2f}"
    return f"{symbol}{amount:,.2f}"

def render_stat_card(label: str, value: float, card_type: str = "default"):
    """Helper to render a beautiful HTML metric card inside Streamlit."""
    class_map = {
        "income": "stat-income",
        "expense": "stat-expense",
        "portfolio": "stat-portfolio",
        "savings": "stat-savings",
        "default": ""
    }
    class_name = class_map.get(card_type.lower(), "")
    
    st.markdown(
        f"""
        <div class="stat-card {class_name}">
            <div class="stat-label">{label}</div>
            <div class="stat-val">{format_currency(value)}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

def build_sample_csv_template(currency_symbol: str | None = None) -> str:
    """Returns a small bank-statement CSV template for quick imports."""
    symbol = currency_symbol or get_currency_symbol()
    return "\n".join([
        "Date,Description,Amount,Type",
        f"2026-06-01,Salary Credit,{symbol}85000.00,Income",
        f"2026-06-02,Starbucks Coffee,{symbol}450.00,Expense",
        f"2026-06-03,Uber Ride,{symbol}620.00,Expense",
        f"2026-06-04,Monthly SIP Transfer,{symbol}10000.00,Expense",
    ])

def calculate_financial_health(
    df_transactions,
    budgets: dict,
    portfolio_value: float,
    holding_count: int = 0,
) -> dict:
    """Calculates a practical 0-100 financial health score for dashboard display."""
    import pandas as pd

    if df_transactions is None or df_transactions.empty:
        return {
            "score": 0,
            "grade": "No data",
            "avg_income": 0.0,
            "avg_expense": 0.0,
            "avg_savings": 0.0,
            "savings_rate": 0.0,
            "budget_adherence": 0.0,
            "cash_buffer_months": 0.0,
            "diversification": 0.0,
            "actions": [
                "Load demo data or import transactions to activate the analytics dashboard.",
                "Add budgets and at least two portfolio holdings for a complete assessment.",
            ],
        }

    df = df_transactions.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    if df.empty:
        return {
            "score": 0,
            "grade": "Needs data",
            "avg_income": 0.0,
            "avg_expense": 0.0,
            "avg_savings": 0.0,
            "savings_rate": 0.0,
            "budget_adherence": 0.0,
            "cash_buffer_months": 0.0,
            "diversification": 0.0,
            "actions": ["Fix transaction dates so the time-series analytics can run."],
        }

    df["Month"] = df["date"].dt.to_period("M")
    monthly_income = df[df["type"] == "Income"].groupby("Month")["amount"].sum()
    monthly_expense = df[df["type"] == "Expense"].groupby("Month")["amount"].sum()
    months = sorted(df["Month"].unique())
    monthly = pd.DataFrame(index=months)
    monthly["Income"] = monthly.index.map(monthly_income).fillna(0.0)
    monthly["Expense"] = monthly.index.map(monthly_expense).fillna(0.0)
    monthly["Savings"] = monthly["Income"] - monthly["Expense"]

    avg_income = float(monthly["Income"].mean())
    avg_expense = float(monthly["Expense"].mean())
    avg_savings = float(monthly["Savings"].mean())
    savings_rate = avg_savings / avg_income if avg_income > 0 else 0.0

    total_income = float(df[df["type"] == "Income"]["amount"].sum())
    total_expense = float(df[df["type"] == "Expense"]["amount"].sum())
    cash_buffer_months = max(0.0, (total_income - total_expense) / avg_expense) if avg_expense > 0 else 0.0

    current_month = pd.Timestamp.today().to_period("M")
    current_expenses = df[(df["type"] == "Expense") & (df["Month"] == current_month)]
    if budgets:
        adhered = 0
        tracked = 0
        for category, limit in budgets.items():
            if float(limit or 0.0) <= 0:
                continue
            tracked += 1
            spent = float(current_expenses[current_expenses["category"] == category]["amount"].sum())
            if spent <= float(limit):
                adhered += 1
        budget_adherence = adhered / tracked if tracked else 0.0
    else:
        budget_adherence = 0.0

    diversification = min(max(holding_count, 0) / 5.0, 1.0) if portfolio_value > 0 else 0.0

    savings_points = min(max((savings_rate + 0.05) / 0.30, 0.0), 1.0) * 35
    budget_points = budget_adherence * 25
    buffer_points = min(cash_buffer_months / 6.0, 1.0) * 20
    portfolio_points = diversification * 20
    score = int(round(min(savings_points + budget_points + buffer_points + portfolio_points, 100)))

    if score >= 80:
        grade = "Excellent"
    elif score >= 65:
        grade = "Strong"
    elif score >= 45:
        grade = "Watchlist"
    else:
        grade = "Needs attention"

    actions = []
    if savings_rate < 0.15:
        actions.append("Lift the average savings rate toward 15% or higher.")
    if budgets and budget_adherence < 0.8:
        actions.append("Review categories crossing their monthly budget limits.")
    elif not budgets:
        actions.append("Set category budgets to activate budget adherence scoring.")
    if cash_buffer_months < 3:
        actions.append("Build a cash buffer of at least three months of expenses.")
    if holding_count < 3:
        actions.append("Add more portfolio holdings to improve diversification tracking.")
    if not actions:
        actions.append("Maintain the current savings discipline and rebalance periodically.")

    return {
        "score": score,
        "grade": grade,
        "avg_income": avg_income,
        "avg_expense": avg_expense,
        "avg_savings": avg_savings,
        "savings_rate": savings_rate,
        "budget_adherence": budget_adherence,
        "cash_buffer_months": cash_buffer_months,
        "diversification": diversification,
        "actions": actions,
    }

def detect_and_clean_currency(df: st.dataframe) -> tuple:
    """Scans dataframe headers and 'Amount' values for currency symbols.
    Cleans the 'Amount' column to float and returns (cleaned_df, currency_name, currency_symbol).
    """
    import pandas as pd
    df = df.copy()
    
    # Clean column headers
    df.columns = [c.strip() for c in df.columns]
    
    # Find amount column
    amount_col = None
    for col in df.columns:
        if col.lower().startswith("amount"):
            amount_col = col
            break
            
    if not amount_col:
        amount_col = "Amount"
        
    detected_name = None
    detected_symbol = None
    
    currency_mappings = {
        "₹": ("INR", "₹"),
        "inr": ("INR", "₹"),
        "$": ("USD", "$"),
        "usd": ("USD", "$"),
        "€": ("EUR", "€"),
        "eur": ("EUR", "€"),
        "£": ("GBP", "£"),
        "gbp": ("GBP", "£")
    }
    
    # Check header column name for currency clues
    for phrase, (name, symbol) in currency_mappings.items():
        if phrase in amount_col.lower():
            detected_name = name
            detected_symbol = symbol
            break
            
    # Check values in the amount column
    cleaned_amounts = []
    if amount_col in df.columns:
        for val in df[amount_col]:
            if pd.isna(val):
                cleaned_amounts.append(0.0)
                continue
            val_str = str(val).strip()
            
            # If not detected yet, check the cell content for symbols
            if not detected_name:
                for phrase, (name, symbol) in currency_mappings.items():
                    if phrase in val_str.lower():
                        detected_name = name
                        detected_symbol = symbol
                        break
            
            # Remove symbols and commas
            clean_val = val_str
            for sym in ["$", "₹", "€", "£", "¥", "A$", "C$"]:
                clean_val = clean_val.replace(sym, "")
            clean_val = clean_val.replace(",", "").strip()
            
            try:
                cleaned_amounts.append(float(clean_val))
            except ValueError:
                cleaned_amounts.append(0.0)
    else:
        # If amount column is missing, populate with zeros
        cleaned_amounts = [0.0] * len(df)
        
    # Rename header to standard 'Amount' and store cleaned values
    if amount_col != "Amount":
        df = df.rename(columns={amount_col: "Amount"})
    df["Amount"] = cleaned_amounts
    
    return df, detected_name, detected_symbol


def load_indian_tickers():
    """Loads all NSE and BSE tickers from local CSV or downloads them from NSE India if not present."""
    import os
    import io
    import pandas as pd
    import urllib.request
    
    # Path relative to project root
    csv_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
    csv_path = os.path.join(csv_dir, "nse_stocks.csv")
    
    # Try loading from local path
    df = None
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
        except Exception:
            df = None
        
    if df is None:
        url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                data = response.read().decode('utf-8')
                df = pd.read_csv(io.StringIO(data))
                # Ensure the parent directory exists
                os.makedirs(csv_dir, exist_ok=True)
                df.to_csv(csv_path, index=False)
        except Exception:
            # Safe basic fallback list if download fails completely
            fallback = [
                "RELIANCE.NS (Reliance Industries - NSE)", "RELIANCE.BO (Reliance Industries - BSE)",
                "TCS.NS (TCS - NSE)", "TCS.BO (TCS - BSE)",
                "HDFCBANK.NS (HDFC Bank - NSE)", "HDFCBANK.BO (HDFC Bank - BSE)",
                "INFY.NS (Infosys - NSE)", "INFY.BO (INFY - BSE)",
                "ICICIBANK.NS (ICICI Bank - NSE)", "ICICIBANK.BO (ICICI Bank - BSE)",
                "TATAMOTORS.NS (Tata Motors - NSE)", "TATAMOTORS.BO (Tata Motors - BSE)",
                "SBIN.NS (SBI - NSE)", "SBIN.BO (SBI - BSE)",
                "BHARTIARTL.NS (Bharti Airtel - NSE)", "BHARTIARTL.BO (Bharti Airtel - BSE)",
                "ITC.NS (ITC - NSE)", "ITC.BO (ITC - BSE)",
                "LT.NS (L&T - NSE)", "LT.BO (L&T - BSE)",
                "HINDUNILVR.NS (Hindustan Unilever - NSE)", "HINDUNILVR.BO (Hindustan Unilever - BSE)",
                "Custom (type below)..."
            ]
            return fallback

    choices = []
    for _, row in df.iterrows():
        symbol = str(row['SYMBOL']).strip().upper()
        # Avoid tickers with special characters that might break yfinance downloads or SQL
        if any(char in symbol for char in ['&', ' ', '/', '\\']):
            continue
        company = str(row['NAME OF COMPANY']).strip()
        choices.append(f"{symbol}.NS ({company} - NSE)")
        choices.append(f"{symbol}.BO ({company} - BSE)")
    
    # Sort alphabetically
    choices.sort()
    # Add custom fallback option at the end
    choices.append("Custom (type below)...")
    return choices


def parse_uploaded_csv(file_bytes: bytes) -> tuple:
    """Parses uploaded bank CSV files, automatically supporting the standard template and custom bank statements.
    
    Returns (df_cleaned, detected_currency_name, detected_currency_symbol)
    """
    import io
    import csv
    import pandas as pd
    from datetime import datetime
    import src.utils as utils

    # Decode file contents
    content = file_bytes.decode("utf-8", errors="ignore")
    lines = content.splitlines()

    # Look for bank statement header
    header_idx = -1
    for i, line in enumerate(lines):
        if "Transaction Date" in line and "Description" in line and "Amount" in line:
            header_idx = i
            break

    if header_idx != -1:
        # Bank statement format
        header_cols = [c.strip().replace('"', '') for c in lines[header_idx].split(",")]
        
        date_idx = -1
        desc_idx = -1
        amount_idx = -1
        type_idx = -1
        
        for idx, col in enumerate(header_cols):
            if col == "Transaction Date":
                date_idx = idx
            elif col == "Description":
                desc_idx = idx
            elif col == "Amount":
                amount_idx = idx
            elif col == "Dr / Cr":
                if type_idx == -1:
                    type_idx = idx

        rows = []
        for line in lines[header_idx + 1:]:
            line = line.strip()
            if not line:
                continue
            
            # Use CSV reader to correctly handle quotes and commas in fields
            parsed_line = list(csv.reader([line]))[0]
            
            if len(parsed_line) <= max(date_idx, desc_idx, amount_idx, type_idx):
                continue
                
            # If the first element is not a number (Sl. No.), it's likely a footer or summary line
            sl_no = parsed_line[0].strip()
            if not sl_no.isdigit():
                continue
                
            date_str = parsed_line[date_idx].strip()
            desc = parsed_line[desc_idx].strip()
            amount_str = parsed_line[amount_idx].strip()
            type_str = parsed_line[type_idx].strip().upper()
            
            # Format Date: DD-MM-YYYY HH:MM:SS -> YYYY-MM-DD
            try:
                date_part = date_str.split(" ")[0]
                if "-" in date_part:
                    dt = datetime.strptime(date_part, "%d-%m-%Y")
                else:
                    dt = datetime.strptime(date_part, "%d/%m/%Y")
                date_formatted = dt.strftime("%Y-%m-%d")
            except Exception:
                date_formatted = date_str
                
            # Clean Amount
            try:
                amt = float(amount_str.replace(",", ""))
            except ValueError:
                amt = 0.0
                
            # Parse Type
            trans_type = "Expense" if type_str == "DR" else "Income"
            
            rows.append({
                "Date": date_formatted,
                "Description": desc,
                "Amount": amt,
                "Type": trans_type
            })
            
        return pd.DataFrame(rows), "INR", "₹"
    else:
        # Standard format
        df = pd.read_csv(io.StringIO(content))
        # Strip columns
        df.columns = [c.strip() for c in df.columns]
        # Clean amount column dynamically if it has currency symbols
        df_cleaned, name, symbol = utils.detect_and_clean_currency(df)
        
        # Standardize columns
        final_cols = []
        for col in df_cleaned.columns:
            if col.lower() == "date":
                final_cols.append("Date")
            elif col.lower() == "description":
                final_cols.append("Description")
            elif col.lower() == "amount":
                final_cols.append("Amount")
            elif col.lower() == "type":
                final_cols.append("Type")
            else:
                final_cols.append(col)
        df_cleaned.columns = final_cols
        return df_cleaned, name, symbol


def parse_credit_card_pdf(file_bytes: bytes):
    """Parses credit card statement PDF and returns a standardized pandas DataFrame."""
    import re
    import pypdf
    import pandas as pd
    from datetime import datetime
    import io

    # Load PDF from bytes
    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    
    # Regex to match transaction lines
    pattern = re.compile(r"^(\d{2}-[A-Za-z]{3}-\d{4})\s+(.+?)\s+([\d,]+\.\d{2})(?:\s+(Cr|CR))?$", re.MULTILINE)
    
    rows = []
    
    # Loop over pages and extract text
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        for line in text.splitlines():
            line = line.strip()
            # If line is header info or page total summary, skip
            if "Total Purchases" in line or "Total Fees" in line or "Total Amount Due" in line:
                continue
                
            match = pattern.match(line)
            if match:
                date_str = match.group(1)
                desc = match.group(2).strip()
                amount_str = match.group(3)
                cr_str = match.group(4)
                
                # Clean amount
                try:
                    amt = float(amount_str.replace(",", ""))
                except ValueError:
                    amt = 0.0
                    
                # Format Date
                try:
                    dt = datetime.strptime(date_str, "%d-%b-%Y")
                    date_formatted = dt.strftime("%Y-%m-%d")
                except Exception:
                    date_formatted = date_str
                    
                # Parse Type: if CR/Cr, it's Income/Payment. Otherwise it's Spend (Expense)
                trans_type = "Income" if cr_str else "Expense"
                
                # Skip credit card bill payments to avoid double counting them as income
                if trans_type == "Income":
                    desc_lower = desc.lower()
                    if any(kw in desc_lower for kw in ["payment", "pymt", "thank you", "auto-debit", "autodebit", "auto debit", "paymt"]):
                        continue
                
                rows.append({
                    "Date": date_formatted,
                    "Description": desc,
                    "Amount": amt,
                    "Type": trans_type
                })
                
    return pd.DataFrame(rows)

def build_sample_holdings_csv_template() -> str:
    """Returns a sample holdings CSV template for quick imports."""
    return "\n".join([
        "Ticker,Shares,Purchase Price,Purchase Date",
        "AAPL,10,175.50,2026-01-15",
        "MSFT,5,420.00,2026-02-10",
        "INFY.NS,15,1450.00,2026-03-20",
    ])

def parse_holdings_csv(file_bytes: bytes) -> pd.DataFrame:
    """Parses uploaded holdings CSV file.
    
    Expected columns: Ticker, Shares, Purchase Price, Purchase Date
    Returns a clean DataFrame with standardized columns: Ticker, Shares, Purchase Price, Purchase Date
    """
    import io
    import pandas as pd
    from datetime import datetime

    # Decode file contents
    content = file_bytes.decode("utf-8", errors="ignore")
    df = pd.read_csv(io.StringIO(content))
    
    # Strip column headers of extra spaces
    df.columns = [c.strip() for c in df.columns]
    
    # Map headers case-insensitively and support common aliases
    mapped_cols = {}
    for col in df.columns:
        col_lower = col.lower().strip()
        col_norm = col_lower.replace("_", " ").replace("-", " ")
        if col_norm in ["ticker", "symbol", "asset"] or col_lower in ["ticker", "symbol", "asset"]:
            mapped_cols[col] = "Ticker"
        elif col_norm in ["shares", "qty", "quantity", "shares owned"] or col_lower in ["shares", "qty", "quantity", "shares owned"]:
            mapped_cols[col] = "Shares"
        elif col_norm in ["purchase price", "price", "cost", "avg price", "average price", "buy price", "cost price"] or col_lower in ["purchase_price", "cost_price", "buy_price", "avg_price"]:
            mapped_cols[col] = "Purchase Price"
        elif col_norm in ["purchase date", "date", "buy date"] or col_lower in ["purchase_date", "buy_date"]:
            mapped_cols[col] = "Purchase Date"
            
    df = df.rename(columns=mapped_cols)
    
    # Validate required columns
    required = {"Ticker", "Shares", "Purchase Price", "Purchase Date"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
        
    # Standardize data types
    df = df[list(required)].copy()
    df["Ticker"] = df["Ticker"].astype(str).str.strip().str.upper()
    df["Shares"] = pd.to_numeric(df["Shares"], errors="coerce").astype(float)
    df["Purchase Price"] = pd.to_numeric(df["Purchase Price"], errors="coerce").astype(float)
    
    # Parse and format Date
    formatted_dates = []
    for d in df["Purchase Date"]:
        d_str = str(d).strip()
        try:
            # Try parsing different formats
            for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"):
                try:
                    dt = datetime.strptime(d_str, fmt)
                    formatted_dates.append(dt.strftime("%Y-%m-%d"))
                    break
                except ValueError:
                    continue
            else:
                formatted_dates.append(datetime.today().strftime("%Y-%m-%d"))
        except Exception:
            formatted_dates.append(datetime.today().strftime("%Y-%m-%d"))
            
    df["Purchase Date"] = formatted_dates
    
    # Drop rows with invalid shares or price
    df = df.dropna(subset=["Shares", "Purchase Price"])
    df = df[(df["Shares"] > 0) & (df["Purchase Price"] > 0)]
    
    return df
