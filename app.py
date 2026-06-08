import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
import json

# Import local modules
import src.database as db
import src.categorizer as cat
import src.optimizer as opt
import src.forecasting as forec
import src.utils as utils

import importlib
importlib.reload(db)
importlib.reload(cat)
importlib.reload(opt)
importlib.reload(forec)
importlib.reload(utils)

# Page Configuration
st.set_page_config(
    page_title="OptimaWealth | Wealth & Expense Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database schema
db.init_db()

# Initialize session state for currency (defaults to INR)
if "currency_name" not in st.session_state:
    st.session_state["currency_name"] = "INR"
if "currency_symbol" not in st.session_state:
    st.session_state["currency_symbol"] = "₹"
if "bank_uploader_key" not in st.session_state:
    st.session_state["bank_uploader_key"] = 0
if "cc_uploader_key" not in st.session_state:
    st.session_state["cc_uploader_key"] = 0
if "portfolio_uploader_key" not in st.session_state:
    st.session_state["portfolio_uploader_key"] = 0

# Inject custom styling
utils.inject_custom_css()

CURRENCY_OPTIONS = {
    "INR": "₹",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
}

CATEGORIES_LIST = [
    "Food & Dining", "Groceries", "Transportation", "Bills & Utilities",
    "Housing", "Shopping", "Entertainment", "Income", "Investments"
]

def _refresh_categorizer():
    categorizer = cat.get_categorizer()
    categorizer.train()

def _load_demo_workspace(button_key: str, container=st):
    if container.button("Load Demo Workspace", key=button_key, use_container_width=True):
        db.seed_demo_data()
        st.session_state["currency_name"] = "INR"
        st.session_state["currency_symbol"] = "₹"
        _refresh_categorizer()
        st.toast("Demo workspace loaded with transactions, budgets, holdings, and ML training data.", icon="✅")
        st.rerun()

def render_sidebar_controls():
    """Renders global workspace controls."""
    st.sidebar.markdown("## OptimaWealth")
    st.sidebar.caption("Personal finance analytics workspace")

    labels = [f"{name} ({symbol})" for name, symbol in CURRENCY_OPTIONS.items()]
    current_name = st.session_state.get("currency_name", "INR")
    current_label = f"{current_name} ({CURRENCY_OPTIONS.get(current_name, '₹')})"
    selected_label = st.sidebar.selectbox(
        "Display Currency",
        labels,
        index=labels.index(current_label) if current_label in labels else 0,
    )
    selected_name = selected_label.split(" ")[0]
    st.session_state["currency_name"] = selected_name
    st.session_state["currency_symbol"] = CURRENCY_OPTIONS[selected_name]

    st.sidebar.markdown("### Demo & Import")
    _load_demo_workspace("sidebar_load_demo", st.sidebar)
    st.sidebar.download_button(
        "Download CSV Template",
        data=utils.build_sample_csv_template(st.session_state["currency_symbol"]),
        file_name="optimawealth_transactions_template.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.sidebar.markdown("### Built With")
    st.sidebar.caption("Streamlit · SQLite · scikit-learn · SciPy · Plotly · yfinance")
    st.sidebar.caption("Released under the MIT License · © 2026 Praneet Pravin")

def render_empty_workspace(context_key: str):
    """Renders a resume-friendly empty state with clear next actions."""
    st.markdown(
        """
        <div class="empty-panel">
            <div class="empty-eyebrow">Workspace setup</div>
            <h2>Start with your data or explore a complete finance demo.</h2>
            <p>
                Load the curated demo profile to showcase transaction intelligence, budget alerts,
                portfolio optimization, risk metrics, stress testing, and forecasting immediately.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    setup_col1, setup_col2, setup_col3 = st.columns(3)
    with setup_col1:
        _load_demo_workspace(f"{context_key}_load_demo")
    with setup_col2:
        st.download_button(
            "Download CSV Template",
            data=utils.build_sample_csv_template(utils.get_currency_symbol()),
            file_name="optimawealth_transactions_template.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with setup_col3:
        st.info("Use the Transactions tab to import CSV/PDF statements or log records manually.")

def build_export_payload(df_transactions: pd.DataFrame, df_assets: pd.DataFrame, active_budgets: dict) -> str:
    export_data = {
        "transactions": df_transactions.to_dict(orient="records") if not df_transactions.empty else [],
        "portfolio": df_assets.to_dict(orient="records") if not df_assets.empty else [],
        "budgets": active_budgets,
        "ml_training_data": db.get_ml_training_data().to_dict(orient="records"),
    }
    return json.dumps(export_data, indent=2)

def render_data_management_panel(df_transactions: pd.DataFrame, df_assets: pd.DataFrame, active_budgets: dict):
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 🗃️ Data & Profile Management")

    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.markdown("#### Export Profile")
        st.write("Download transactions, holdings, budgets, and ML training overrides as a portable JSON backup.")
        st.download_button(
            label="📥 Export Financial Data",
            data=build_export_payload(df_transactions, df_assets, active_budgets),
            file_name=f"optimawealth_profile_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True,
        )

    with m_col2:
        st.markdown("#### Restore Profile")
        st.write("Restore a previous OptimaWealth JSON export. This replaces the current workspace data.")
        uploaded_profile = st.file_uploader("Choose profile JSON", type=["json"], key="profile_restore_json")
        if uploaded_profile is not None:
            if st.button("Restore From Backup", key="restore_profile_button", use_container_width=True):
                try:
                    profile_data = json.loads(uploaded_profile.getvalue().decode("utf-8"))
                    counts = db.restore_profile(profile_data)
                    _refresh_categorizer()
                    st.success(
                        "Restored profile: "
                        f"{counts['transactions']} transactions, {counts['portfolio']} holdings, "
                        f"{counts['budgets']} budgets."
                    )
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not restore profile: {exc}")

    with m_col3:
        st.markdown("#### Reset Workspace")
        st.write("Permanently delete transactions, budgets, holdings, and ML overrides from SQLite.")
        confirm_reset = st.checkbox(
            "Confirm permanent reset",
            key="confirm_reset_workspace",
        )
        if st.button("Clear Database", disabled=not confirm_reset, key="clear_database_button", use_container_width=True):
            db.clear_db()
            _refresh_categorizer()
            st.toast("Workspace database cleared.", icon="✅")
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

def render_health_panel(df_transactions: pd.DataFrame, active_budgets: dict, active_portfolio_value: float, holdings_count: int):
    health = utils.calculate_financial_health(df_transactions, active_budgets, active_portfolio_value, holdings_count)
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### Financial Health Command Center")
    score_col, metric_col, action_col = st.columns([1, 1.2, 1.3])
    with score_col:
        fig_health = go.Figure(go.Indicator(
            mode="gauge+number",
            value=health["score"],
            number={"suffix": "/100", "font": {"size": 34}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 0},
                "bar": {"color": "#10b981" if health["score"] >= 70 else "#f59e0b"},
                "bgcolor": "rgba(255,255,255,0.06)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 45], "color": "rgba(239,68,68,0.18)"},
                    {"range": [45, 70], "color": "rgba(245,158,11,0.18)"},
                    {"range": [70, 100], "color": "rgba(16,185,129,0.18)"},
                ],
            },
            title={"text": health["grade"]},
        ))
        fig_health.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=230,
            margin=dict(l=10, r=10, t=30, b=10),
        )
        st.plotly_chart(fig_health, use_container_width=True)
    with metric_col:
        st.metric("Average Monthly Savings", utils.format_currency(health["avg_savings"]))
        st.metric("Savings Rate", f"{health['savings_rate'] * 100:.1f}%")
        st.metric("Cash Buffer", f"{health['cash_buffer_months']:.1f} months")
    with action_col:
        st.markdown("#### Recommended Actions")
        for action in health["actions"]:
            st.markdown(f"- {action}")
    st.markdown('</div>', unsafe_allow_html=True)

render_sidebar_controls()

# Header Section
st.markdown(
    """
    <div style='text-align: center; margin-bottom: 30px; margin-top: 10px;'>
        <h1 style='font-size: 3.2rem; margin-bottom: 5px; color: #ffffff;'><span class='gradient-text'>OptimaWealth</span> <span class='logo-emoji'>📊</span></h1>
        <p style='color: #9ca3af; font-size: 1.15rem; font-weight: 500; margin-bottom: 5px;'>Advanced Personal Wealth & Cashflow Intelligence System</p>
        <p style='color: #6366f1; font-size: 0.95rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;'>Consolidated Portfolio Management</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Fetch latest transactions & portfolio data
df_tx = db.get_all_transactions()
df_portfolio = db.get_portfolio()
budgets = db.get_budgets()

# Quick calculation of KPIs
if not df_tx.empty:
    total_income = df_tx[df_tx["type"] == "Income"]["amount"].sum()
    total_expense = df_tx[df_tx["type"] == "Expense"]["amount"].sum()
    net_savings = total_income - total_expense
else:
    total_income = 0.0
    total_expense = 0.0
    net_savings = 0.0

# Fetch latest portfolio valuation
portfolio_val = 0.0
portfolio_cost = 0.0
tickers = list(df_portfolio["ticker"].unique()) if not df_portfolio.empty else []

if tickers:
    prices_df = opt.fetch_historical_prices(tickers, period="1mo")
    if not prices_df.empty:
        latest_prices = prices_df.iloc[-1]
        for _, row in df_portfolio.iterrows():
            ticker = row["ticker"]
            shares = row["shares"]
            cost = row["purchase_price"] * shares
            portfolio_cost += cost
            if ticker in latest_prices:
                portfolio_val += latest_prices[ticker] * shares
            else:
                portfolio_val += cost  # fallback to cost if ticker data fails
    else:
        # Fallback if historical fetch fails completely
        for _, row in df_portfolio.iterrows():
            cost = row["shares"] * row["purchase_price"]
            portfolio_cost += cost
            portfolio_val += cost
else:
    portfolio_val = 0.0

# Render top statistics panel
kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
with kpi_col1:
    utils.render_stat_card("Total Income", total_income, "income")
with kpi_col2:
    utils.render_stat_card("Total Expenses", total_expense, "expense")
with kpi_col3:
    utils.render_stat_card("Net Savings", net_savings, "savings")
with kpi_col4:
    utils.render_stat_card("Portfolio Value", portfolio_val, "portfolio")

# Fetch active currency symbol
curr_sym = utils.get_currency_symbol()

# Create main tabbed interface
tab_overview, tab_transactions, tab_wealth, tab_forecast = st.tabs([
    "📊 Financial Overview",
    "💸 Transactions & ML Auto-Categorizer",
    "📈 Wealth & Portfolio Optimizer",
    "🔮 Future Projections (Forecasting)"
])

# ----------------- TAB 1: FINANCIAL OVERVIEW -----------------
with tab_overview:
    if df_tx.empty:
        render_empty_workspace("overview")
        render_data_management_panel(df_tx, df_portfolio, budgets)
    else:
        render_health_panel(df_tx, budgets, portfolio_val, len(tickers))

        # Spending Anomaly Detection
        anomalies_df = forec.detect_expense_anomalies(df_tx, contamination=0.03)
        if not anomalies_df.empty:
            st.markdown(
                '<div class="alert-card alert-danger">⚠️ <b>ML Anomaly Alert:</b> Unsupervised spending anomaly detection (Isolation Forest) flagged '
                f'<b>{len(anomalies_df)} unusual transaction(s)</b>.</div>',
                unsafe_allow_html=True
            )
            with st.expander("🔍 Inspect Suspicious Spending Anomalies"):
                st.dataframe(
                    anomalies_df.style.format({"amount": f"{curr_sym}{{:,.2f}}"}),
                    use_container_width=True,
                    hide_index=True
                )
        
        # Create layouts
        col_charts_left, col_charts_right = st.columns([2, 1])
        
        with col_charts_left:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("### Income vs. Expenses Trend")
            
            # Prepare monthly aggregation
            df_trend = df_tx.copy()
            df_trend["date"] = pd.to_datetime(df_trend["date"])
            df_trend["Month"] = df_trend["date"].dt.to_period("M").dt.to_timestamp()
            
            trend_agg = df_trend.groupby(["Month", "type"])["amount"].sum().unstack(fill_value=0.0).reset_index()
            
            # Ensure both Income and Expense columns exist
            if "Income" not in trend_agg.columns:
                trend_agg["Income"] = 0.0
            if "Expense" not in trend_agg.columns:
                trend_agg["Expense"] = 0.0
                
            trend_agg = trend_agg.sort_values("Month")
            
            # Render Area Chart
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=trend_agg["Month"], y=trend_agg["Income"],
                mode='lines', name='Income', line=dict(color='#10b981', width=3),
                fill='tozeroy', fillcolor='rgba(16, 185, 129, 0.1)'
            ))
            fig_trend.add_trace(go.Scatter(
                x=trend_agg["Month"], y=trend_agg["Expense"],
                mode='lines', name='Expenses', line=dict(color='#ef4444', width=3),
                fill='tozeroy', fillcolor='rgba(239, 68, 68, 0.1)'
            ))
            
            fig_trend.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=10, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickprefix=curr_sym)
            )
            st.plotly_chart(fig_trend, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with col_charts_right:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("### Spending Allocation")
            
            # Expense by Category
            df_exp = df_tx[df_tx["type"] == "Expense"]
            if not df_exp.empty:
                cat_agg = df_exp.groupby("category")["amount"].sum().reset_index()
                
                fig_pie = px.pie(
                    cat_agg, values='amount', names='category',
                    hole=0.6,
                    color_discrete_sequence=px.colors.qualitative.G10
                )
                fig_pie.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=10, r=10, t=10, b=10),
                    legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5)
                )
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.write("No expense records to analyze.")
            st.markdown('</div>', unsafe_allow_html=True)
            
        # Budgets Progress Section
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### Budget Progress Tracker")
        
        # Calculate current spending vs budget limits
        # Get active month's expenses
        current_month_str = datetime.today().strftime("%Y-%m")
        df_current_month = df_tx[
            (df_tx["type"] == "Expense") & 
            (df_tx["date"].str.startswith(current_month_str))
        ]
        
        month_spent = df_current_month.groupby("category")["amount"].sum().to_dict()
        
        if budgets:
            budget_data = []
            for category, limit in budgets.items():
                spent = month_spent.get(category, 0.0)
                pct = (spent / limit) * 100 if limit > 0 else 0.0
                budget_data.append({
                    "Category": category,
                    "Spent": spent,
                    "Budget Limit": limit,
                    "Percentage Used": pct
                })
                
            df_budget_status = pd.DataFrame(budget_data)
            
            # Plotly horizontal bar chart for budgets
            fig_budget = go.Figure()
            
            # Budget limits as backing transparent bars
            fig_budget.add_trace(go.Bar(
                y=df_budget_status["Category"],
                x=df_budget_status["Budget Limit"],
                name="Budget Limit",
                orientation='h',
                marker=dict(color='rgba(255, 255, 255, 0.08)', line=dict(color='rgba(255,255,255,0.15)', width=1))
            ))
            
            # Spent progress bars (colored by budget overflow)
            colors = []
            for _, row in df_budget_status.iterrows():
                if row["Percentage Used"] > 100:
                    colors.append('#ef4444')  # Red
                elif row["Percentage Used"] > 80:
                    colors.append('#f59e0b')  # Amber
                else:
                    colors.append('#10b981')  # Green
                    
            fig_budget.add_trace(go.Bar(
                y=df_budget_status["Category"],
                x=df_budget_status["Spent"],
                name="Amount Spent",
                orientation='h',
                marker=dict(color=colors)
            ))
            
            fig_budget.update_layout(
                barmode='overlay',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=10, b=10),
                xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickprefix=curr_sym),
                yaxis=dict(showgrid=False),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_budget, use_container_width=True)
            
            # Detailed budget table
            st.dataframe(
                df_budget_status.style.format({
                    "Spent": f"{curr_sym}{{:,.2f}}",
                    "Budget Limit": f"{curr_sym}{{:,.2f}}",
                    "Percentage Used": "{:.1f}%"
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No budgets configured. Set category budgets in the Transactions tab to track spending limits.")
        st.markdown('</div>', unsafe_allow_html=True)
        render_data_management_panel(df_tx, df_portfolio, budgets)



# ----------------- TAB 2: TRANSACTIONS & AUTO-CATEGORIZATION -----------------
with tab_transactions:
    col_tx_left, col_tx_right = st.columns([1, 2])
    
    # Left Column: Add Transaction & ML Engine
    with col_tx_left:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### ✍️ Log New Transaction")
        
        tx_date = st.date_input("Date", datetime.today())
        tx_desc = st.text_input("Description (e.g., Starbucks Coffee)", key="desc_input")
        tx_amount = st.number_input(f"Amount ({curr_sym})", min_value=0.01, value=10.0, step=10.0, format="%.2f")
        tx_type = st.radio("Type", ["Expense", "Income"], horizontal=True)
        
        # ML Engine classification loop
        predicted_category = "Shopping"
        confidence = 0.50
        
        if tx_desc.strip():
            categorizer = cat.get_categorizer()
            # Predict
            pred_res = categorizer.predict(tx_desc)
            predicted_category = pred_res[0]
            confidence = pred_res[1]
            
            # Style classification alerts
            if confidence >= 0.75:
                st.markdown(
                    f'<div class="alert-card alert-success">🧠 ML Prediction: <b>{predicted_category}</b> ({confidence*100:.1f}% confidence)</div>',
                    unsafe_allow_html=True
                )
            elif confidence >= 0.45:
                st.markdown(
                    f'<div class="alert-card alert-warning">🧠 ML Prediction: <b>{predicted_category}</b> ({confidence*100:.1f}% confidence)</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div class="alert-card alert-danger">🧠 ML Suggestion: <b>{predicted_category}</b> (Low confidence: {confidence*100:.1f}%)</div>',
                    unsafe_allow_html=True
                )
        
        # Category Selector dropdown (defaulting to ML predicted class)
        if tx_type == "Income":
            predicted_category = "Income"
            category_choices = ["Income"]
        else:
            category_choices = [c for c in CATEGORIES_LIST if c != "Income"]
            if predicted_category == "Income":
                predicted_category = "Shopping"
        
        try:
            default_idx = category_choices.index(predicted_category)
        except ValueError:
            default_idx = category_choices.index("Shopping") if "Shopping" in category_choices else 0
            
        tx_category = st.selectbox("Category Override", category_choices, index=default_idx)
        
        if st.button("Log Transaction", use_container_width=True):
            if tx_desc.strip():
                # Add to DB
                db.add_transaction(
                    tx_date.strftime("%Y-%m-%d"),
                    tx_desc.strip(),
                    tx_amount,
                    tx_category,
                    tx_type
                )
                
                # Check if user overrode our ML prediction - if so, add to dataset & retrain
                if tx_desc.strip() and tx_category != predicted_category:
                    categorizer = cat.get_categorizer()
                    categorizer.add_override(tx_desc.strip(), tx_category)
                    st.toast("🧠 ML Model retrained on category correction override!", icon="✅")
                    
                st.success(f"Logged transaction: {tx_desc} ({curr_sym}{tx_amount:.2f})")
                st.rerun()
            else:
                st.error("Please enter a transaction description.")
                
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Set budgets card
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### ⚙️ Configure Budgets")
        budget_category = st.selectbox("Target Category", [c for c in CATEGORIES_LIST if c != "Income"])
        current_budget_limit = budgets.get(budget_category, 0.0)
        budget_limit_val = st.number_input(f"Monthly Budget Limit ({curr_sym})", min_value=0.0, value=current_budget_limit, step=50.0)
        
        if st.button("Update Budget Limit", use_container_width=True):
            db.set_budget(budget_category, budget_limit_val)
            st.success(f"Updated {budget_category} budget limit to {curr_sym}{budget_limit_val:,.2f}")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    # Right Column: View Transactions & CSV Imports
    with col_tx_right:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### 📥 Bulk Import Transactions (Bank Statement CSV)")
        st.markdown(
            "Upload a bank statement CSV to automatically parse and categorize multiple transactions. "
            "Template format: `Date,Description,Amount,Type` (Type should be `Income` or `Expense`)."
        )
        st.download_button(
            "Download Import Template",
            data=utils.build_sample_csv_template(curr_sym),
            file_name="optimawealth_transactions_template.csv",
            mime="text/csv",
            use_container_width=True,
            key="transactions_template_download",
        )
        
        uploaded_file = st.file_uploader("Choose a bank statement CSV file", type=["csv"], key=f"bank_csv_{st.session_state['bank_uploader_key']}")
        if uploaded_file is not None:
            try:
                # Use our smart parser which cleans and standardizes columns
                df_cleaned, det_name, det_symbol = utils.parse_uploaded_csv(uploaded_file.getvalue())
                
                # Verify standard columns are present
                cols = list(df_cleaned.columns)
                has_date = "Date" in cols
                has_desc = "Description" in cols
                has_amount = "Amount" in cols
                has_type = "Type" in cols
                
                if not (has_date and has_desc and has_amount and has_type):
                    st.error("Invalid columns! CSV must contain headers: Date, Description, Amount, Type")
                else:
                    
                    if det_name and det_symbol and st.session_state["currency_name"] != det_name:
                        st.session_state["currency_name"] = det_name
                        st.session_state["currency_symbol"] = det_symbol
                        st.toast(f"🔄 Currency auto-adapted to {det_name} ({det_symbol}) based on file upload!", icon="ℹ️")
                        st.rerun()
                        
                    st.success("CSV Uploaded successfully! Previewing predictions:")
                    
                    # Apply ML predictions in-memory
                    categorizer = cat.get_categorizer()
                    parsed_rows = []
                    
                    for idx, row in df_cleaned.iterrows():
                        desc = str(row["Description"])
                        row_type = str(row["Type"]).strip().title()
                        if row_type not in {"Income", "Expense"}:
                            row_type = "Expense"
                        pred_cat, confidence = categorizer.predict(desc)
                        auto_category = "Income" if row_type == "Income" else pred_cat
                        if row_type == "Expense" and auto_category == "Income":
                            auto_category = "Shopping"
                        
                        # Use Type from CSV to override classification logic if necessary
                        parsed_rows.append({
                            "Date": str(row["Date"]),
                            "Description": desc,
                            "Amount": float(row["Amount"]),
                            "Type": row_type,
                            "Auto Category": auto_category,
                            "Confidence": f"{confidence * 100:.0f}%"
                        })
                        
                    df_preview = pd.DataFrame(parsed_rows)
                    st.dataframe(df_preview, use_container_width=True, hide_index=True)
                    
                    if st.button("Confirm and Import All", use_container_width=True):
                        # Bulk insert with deduplication check
                        existing_df = db.get_all_transactions()
                        imported_count = 0
                        duplicate_count = 0
                        
                        for _, r in df_preview.iterrows():
                            # Check if duplicate (same date, description, amount, type)
                            is_duplicate = False
                            if not existing_df.empty:
                                matches = existing_df[
                                    (existing_df["date"] == r["Date"]) &
                                    (existing_df["description"] == r["Description"]) &
                                    (existing_df["amount"] == r["Amount"]) &
                                    (existing_df["type"] == r["Type"])
                                ]
                                if not matches.empty:
                                    is_duplicate = True
                                    
                            if not is_duplicate:
                                db.add_transaction(
                                    r["Date"],
                                    r["Description"],
                                    r["Amount"],
                                    r["Auto Category"],
                                    r["Type"]
                                )
                                imported_count += 1
                            else:
                                duplicate_count += 1
                                
                        if duplicate_count > 0:
                            st.success(f"Successfully imported {imported_count} new transactions (skipped {duplicate_count} duplicate entries)!")
                        else:
                            st.success(f"Successfully imported {imported_count} transactions!")
                        
                        # Clear file uploader by incrementing key version
                        st.session_state["bank_uploader_key"] += 1
                        st.rerun()
            except Exception as e:
                st.error(f"Error reading CSV file: {e}")
                
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Credit Card Statement PDF Import
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### 💳 Bulk Import Credit Card PDF")
        st.markdown(
            "Upload a credit card statement PDF to automatically parse transactions. "
            "Spends will be imported as `Expense` and payments/refunds as `Income`, with ML auto-categorization."
        )
        cc_uploaded_file = st.file_uploader("Choose a Credit Card Statement PDF", type=["pdf"], key=f"cc_pdf_{st.session_state['cc_uploader_key']}")
        if cc_uploaded_file is not None:
            try:
                # Use PDF parser
                df_cc = utils.parse_credit_card_pdf(cc_uploaded_file.getvalue())
                
                if df_cc.empty:
                    st.warning("No transactions found in the uploaded credit card statement PDF.")
                else:
                    st.success(f"Parsed {len(df_cc)} transactions from credit card PDF statement! Previewing predictions:")
                    
                    # Apply ML predictions in-memory
                    categorizer = cat.get_categorizer()
                    parsed_rows = []
                    
                    for idx, row in df_cc.iterrows():
                        desc = str(row["Description"])
                        row_type = str(row["Type"]).strip().title()
                        if row_type not in {"Income", "Expense"}:
                            row_type = "Expense"
                        pred_cat, confidence = categorizer.predict(desc)
                        auto_category = "Income" if row_type == "Income" else pred_cat
                        if row_type == "Expense" and auto_category == "Income":
                            auto_category = "Shopping"
                        
                        parsed_rows.append({
                            "Date": str(row["Date"]),
                            "Description": desc,
                            "Amount": float(row["Amount"]),
                            "Type": row_type,
                            "Auto Category": auto_category,
                            "Confidence": f"{confidence * 100:.0f}%"
                        })
                        
                    df_preview_cc = pd.DataFrame(parsed_rows)
                    st.dataframe(df_preview_cc, use_container_width=True, hide_index=True)
                    
                    if st.button("Confirm and Import All CC Transactions", use_container_width=True):
                        # Bulk insert with deduplication check
                        existing_df = db.get_all_transactions()
                        imported_count = 0
                        duplicate_count = 0
                        
                        for _, r in df_preview_cc.iterrows():
                            # Check if duplicate (same date, description, amount, type)
                            is_duplicate = False
                            if not existing_df.empty:
                                matches = existing_df[
                                    (existing_df["date"] == r["Date"]) &
                                    (existing_df["description"] == r["Description"]) &
                                    (existing_df["amount"] == r["Amount"]) &
                                    (existing_df["type"] == r["Type"])
                                ]
                                if not matches.empty:
                                    is_duplicate = True
                                    
                            if not is_duplicate:
                                db.add_transaction(
                                    r["Date"],
                                    r["Description"],
                                    r["Amount"],
                                    r["Auto Category"],
                                    r["Type"]
                                )
                                imported_count += 1
                            else:
                                duplicate_count += 1
                                
                        if duplicate_count > 0:
                            st.success(f"Successfully imported {imported_count} new transactions (skipped {duplicate_count} duplicate entries)!")
                        else:
                            st.success(f"Successfully imported {imported_count} transactions!")
                        
                        # Clear file uploader by incrementing key version
                        st.session_state["cc_uploader_key"] += 1
                        st.rerun()
            except Exception as e:
                st.error(f"Error reading PDF file: {e}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### 📜 Transaction Log")
        
        if df_tx.empty:
            st.write("No transaction entries logged yet.")
        else:
            # Filters
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                filter_type = st.multiselect("Filter Type", ["Income", "Expense"], default=["Income", "Expense"])
            with f_col2:
                all_cats = list(df_tx["category"].unique())
                filter_cat = st.multiselect("Filter Category", all_cats, default=all_cats)
                
            df_filtered = df_tx[
                (df_tx["type"].isin(filter_type)) & 
                (df_tx["category"].isin(filter_cat))
            ]
            
            # Format and display
            df_display = df_filtered.copy()
            df_display["amount"] = df_display["amount"].apply(utils.format_currency)
            
            st.dataframe(
                df_display[["id", "date", "description", "category", "amount", "type"]],
                use_container_width=True,
                hide_index=True
            )

            st.markdown("#### Edit Transaction")
            tx_lookup = {
                int(row["id"]): f"#{int(row['id'])} - {row['date']} - {str(row['description'])[:42]}"
                for _, row in df_tx.iterrows()
            }
            selected_edit_id = st.selectbox(
                "Transaction ID to edit",
                options=list(tx_lookup.keys()),
                format_func=lambda tx_id: tx_lookup.get(int(tx_id), str(tx_id)),
                key="edit_transaction_id",
            )
            edit_row = df_tx[df_tx["id"] == selected_edit_id].iloc[0]
            edit_date_default = pd.to_datetime(edit_row["date"], errors="coerce")
            if pd.isna(edit_date_default):
                edit_date_default = datetime.today().date()
            else:
                edit_date_default = edit_date_default.date()

            edit_col1, edit_col2 = st.columns(2)
            with edit_col1:
                edit_date = st.date_input(
                    "Edit Date",
                    edit_date_default,
                    key=f"edit_date_{selected_edit_id}",
                )
                edit_desc = st.text_input(
                    "Edit Description",
                    value=str(edit_row["description"]),
                    key=f"edit_desc_{selected_edit_id}",
                )
                edit_amount = st.number_input(
                    f"Edit Amount ({curr_sym})",
                    min_value=0.01,
                    value=float(edit_row["amount"]),
                    step=10.0,
                    format="%.2f",
                    key=f"edit_amount_{selected_edit_id}",
                )
            with edit_col2:
                edit_type = st.radio(
                    "Edit Type",
                    ["Expense", "Income"],
                    index=0 if edit_row["type"] == "Expense" else 1,
                    horizontal=True,
                    key=f"edit_type_{selected_edit_id}",
                )
                edit_category_choices = ["Income"] if edit_type == "Income" else [c for c in CATEGORIES_LIST if c != "Income"]
                current_edit_category = edit_row["category"] if edit_row["category"] in edit_category_choices else edit_category_choices[0]
                edit_category = st.selectbox(
                    "Edit Category",
                    edit_category_choices,
                    index=edit_category_choices.index(current_edit_category),
                    key=f"edit_category_{selected_edit_id}",
                )

                if st.button("Save Transaction Changes", key=f"save_tx_{selected_edit_id}", use_container_width=True):
                    if edit_desc.strip():
                        updated = db.update_transaction(
                            int(selected_edit_id),
                            edit_date.strftime("%Y-%m-%d"),
                            edit_desc.strip(),
                            float(edit_amount),
                            edit_category,
                            edit_type,
                        )
                        if updated:
                            _refresh_categorizer()
                            st.success(f"Updated transaction ID: {selected_edit_id}")
                            st.rerun()
                        else:
                            st.error(f"Transaction ID {selected_edit_id} not found.")
                    else:
                        st.error("Description cannot be blank.")
            
            # Delete record option
            st.markdown("#### ❌ Delete Transaction")
            del_id = st.number_input("Transaction ID to delete", min_value=1, step=1)
            if st.button("Delete Transaction"):
                # verify if it exists
                if del_id in df_tx["id"].values:
                    db.delete_transaction(int(del_id))
                    st.success(f"Deleted transaction ID: {del_id}")
                    st.rerun()
                else:
                    st.error(f"Transaction ID {del_id} not found.")
        st.markdown('</div>', unsafe_allow_html=True)

# ----------------- TAB 3: WEALTH & PORTFOLIO OPTIMIZER -----------------
with tab_wealth:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 💰 Wealth Portfolio Holdings")
    
    col_w_left, col_w_right = st.columns([1, 2])
    
    # Left Column: Add Asset form
    with col_w_left:
        ticker_choices = utils.load_indian_tickers()
        selected_ticker = st.selectbox(
            "Asset Ticker (search or select)",
            options=ticker_choices,
            index=None,
            placeholder="Select a stock ticker...",
            key="asset_ticker_select",
            help="For other Indian stocks, select 'Custom' and use the NSE suffix (e.g., WIPRO.NS) or BSE suffix (e.g., 500180.BO)"
        )
        if selected_ticker == "Custom (type below)...":
            w_ticker = st.text_input("Enter Custom Ticker (e.g., WIPRO.NS or 500180.BO)", key="asset_ticker_custom_input")
        elif selected_ticker is None:
            w_ticker = ""
        else:
            w_ticker = selected_ticker.split(" ")[0]

        w_shares = st.number_input("Shares Owned", min_value=0.0001, value=1.0, step=1.0, format="%.4f")
        w_price = st.number_input(f"Purchase Price ({curr_sym})", min_value=0.01, value=10.0, step=10.0, format="%.2f")
        w_date = st.date_input("Purchase Date", datetime.today())
        
        if st.button("Add to Portfolio", use_container_width=True):
            if w_ticker and w_ticker.strip():
                db.add_portfolio_asset(
                    w_ticker.strip().upper(),
                    w_shares,
                    w_price,
                    w_date.strftime("%Y-%m-%d")
                )
                st.success(f"Added {w_shares} shares of {w_ticker.upper()} to portfolio!")
                st.rerun()
            else:
                st.error("Please select or enter a valid ticker.")
                
        # Bulk Import holdings
        st.markdown("---")
        st.markdown("### 📥 Bulk Import Holdings")
        st.write("Upload a CSV file to import multiple stock/crypto holdings at once.")
        st.download_button(
            "Download Holdings Template",
            data=utils.build_sample_holdings_csv_template(),
            file_name="optimawealth_holdings_template.csv",
            mime="text/csv",
            use_container_width=True,
            key="holdings_template_download",
        )
        
        holdings_uploaded = st.file_uploader(
            "Choose a holdings CSV file",
            type=["csv"],
            key=f"portfolio_csv_{st.session_state['portfolio_uploader_key']}"
        )
        
        if holdings_uploaded is not None:
            try:
                df_imported = utils.parse_holdings_csv(holdings_uploaded.getvalue())
                if not df_imported.empty:
                    # Get existing holdings to prevent duplicate entries
                    existing_df = db.get_portfolio()
                    
                    existing_set = set()
                    if not existing_df.empty:
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
                            # Add to in-memory set in case CSV itself contains duplicates
                            existing_set.add(key)
                            
                    if new_records:
                        for row in new_records:
                            db.add_portfolio_asset(
                                row["Ticker"],
                                row["Shares"],
                                row["Purchase Price"],
                                row["Purchase Date"]
                            )
                        msg = f"Successfully imported {len(new_records)} holdings!"
                        if skipped_duplicates > 0:
                            msg += f" (Skipped {skipped_duplicates} duplicate records)"
                        st.toast(msg, icon="✅")
                    else:
                        st.warning("All records in the CSV were duplicates of existing holdings.")
                        
                    # Reset the file uploader and rerun
                    st.session_state["portfolio_uploader_key"] += 1
                    st.rerun()
                else:
                    st.error("No valid holdings records found in the uploaded file.")
            except Exception as e:
                st.error(f"Error parsing holdings file: {e}")
                
        # Delete asset option
        if not df_portfolio.empty:
            st.markdown("#### Edit Asset Purchase")
            asset_lookup = {
                int(row["id"]): f"#{int(row['id'])} - {row['ticker']} - {row['shares']:,.4f} shares"
                for _, row in df_portfolio.iterrows()
            }
            selected_asset_id = st.selectbox(
                "Asset record to edit",
                options=list(asset_lookup.keys()),
                format_func=lambda asset_id: asset_lookup.get(int(asset_id), str(asset_id)),
                key="edit_asset_id",
            )
            asset_row = df_portfolio[df_portfolio["id"] == selected_asset_id].iloc[0]
            asset_date_default = pd.to_datetime(asset_row["purchase_date"], errors="coerce")
            if pd.isna(asset_date_default):
                asset_date_default = datetime.today().date()
            else:
                asset_date_default = asset_date_default.date()

            edit_asset_ticker = st.text_input(
                "Edit Ticker",
                value=str(asset_row["ticker"]),
                key=f"edit_asset_ticker_{selected_asset_id}",
            )
            edit_asset_shares = st.number_input(
                "Edit Shares",
                min_value=0.0001,
                value=float(asset_row["shares"]),
                step=1.0,
                format="%.4f",
                key=f"edit_asset_shares_{selected_asset_id}",
            )
            edit_asset_price = st.number_input(
                f"Edit Purchase Price ({curr_sym})",
                min_value=0.01,
                value=float(asset_row["purchase_price"]),
                step=10.0,
                format="%.2f",
                key=f"edit_asset_price_{selected_asset_id}",
            )
            edit_asset_date = st.date_input(
                "Edit Purchase Date",
                asset_date_default,
                key=f"edit_asset_date_{selected_asset_id}",
            )
            if st.button("Save Asset Changes", key=f"save_asset_{selected_asset_id}", use_container_width=True):
                if edit_asset_ticker.strip():
                    updated = db.update_portfolio_asset(
                        int(selected_asset_id),
                        edit_asset_ticker,
                        float(edit_asset_shares),
                        float(edit_asset_price),
                        edit_asset_date.strftime("%Y-%m-%d"),
                    )
                    if updated:
                        st.success(f"Updated asset record ID: {selected_asset_id}")
                        st.rerun()
                    else:
                        st.error(f"Asset record ID {selected_asset_id} not found.")
                else:
                    st.error("Ticker cannot be blank.")

            st.markdown("#### Delete Asset Purchase")
            del_asset_id = st.number_input("Asset Record ID to delete", min_value=1, step=1)
            if st.button("Delete Asset Record", use_container_width=True):
                if del_asset_id in df_portfolio["id"].values:
                    db.delete_portfolio_asset(int(del_asset_id))
                    st.success(f"Deleted asset record ID: {del_asset_id}")
                    st.rerun()
                else:
                    st.error(f"Asset Record ID {del_asset_id} not found.")
                    
    # Right Column: Valuation and Allocations
    with col_w_right:
        if df_portfolio.empty:
            st.info("Your portfolio is currently empty. Please add purchases.")
        else:
            # Group by ticker to see holdings aggregates
            holdings = df_portfolio.groupby("ticker").agg(
                total_shares=("shares", "sum"),
                avg_cost=("purchase_price", lambda x: np.sum(x * df_portfolio.loc[x.index, "shares"]) / np.sum(df_portfolio.loc[x.index, "shares"]))
            ).reset_index()
            
            # Fetch latest prices for valuation
            prices_df = opt.fetch_historical_prices(list(holdings["ticker"]), period="1y")
            
            if not prices_df.empty:
                latest_prices = prices_df.iloc[-1]
                
                valuation_rows = []
                for _, row in holdings.iterrows():
                    ticker = row["ticker"]
                    shares = row["total_shares"]
                    avg_cost = row["avg_cost"]
                    cost_basis = avg_cost * shares
                    
                    cur_price = latest_prices.get(ticker, avg_cost)
                    market_val = cur_price * shares
                    profit_loss = market_val - cost_basis
                    pct_change = (profit_loss / cost_basis) * 100 if cost_basis > 0 else 0.0
                    
                    valuation_rows.append({
                        "Ticker": ticker,
                        "Shares": shares,
                        "Avg Cost Price": utils.format_currency(avg_cost),
                        "Current Price": utils.format_currency(cur_price),
                        "Cost Basis": cost_basis,
                        "Market Value": market_val,
                        f"Profit/Loss ({curr_sym})": profit_loss,
                        "Profit/Loss (%)": f"{pct_change:+.2f}%"
                    })
                    
                df_val = pd.DataFrame(valuation_rows)
                
                # Display Holdings Valuation
                st.markdown("#### Portfolio Current Valuation")
                st.dataframe(
                    df_val.style.format({
                        "Cost Basis": f"{curr_sym}{{:,.2f}}",
                        "Market Value": f"{curr_sym}{{:,.2f}}",
                        f"Profit/Loss ({curr_sym})": f"{curr_sym}{{:+,.2f}}",
                        "Shares": "{:,.4f}"
                    }),
                    use_container_width=True,
                    hide_index=True
                )
                
                # Plot allocation pie chart
                fig_alloc = px.pie(
                    df_val, values="Market Value", names="Ticker",
                    title="Asset Allocation (Market Value Basis)",
                    hole=0.4,
                    color_discrete_sequence=px.colors.sequential.Sunsetdark
                )
                fig_alloc.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=10, r=10, t=30, b=10)
                )
                st.plotly_chart(fig_alloc, use_container_width=True)
            else:
                st.error("Failed to fetch current stock prices. Check network connection.")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Portfolio Optimization section
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 🧮 Modern Portfolio Theory (MPT) Optimizer")
    
    if df_portfolio.empty or len(df_portfolio["ticker"].unique()) < 2:
        st.warning("Please include at least 2 distinct tickers in your portfolio to compute allocations and solve the Efficient Frontier.")
    else:
        st.markdown(
            "Based on 1-year historical pricing, we use SciPy solvers to determine "
            "the risk-adjusted optimal asset distributions."
        )
        
        opt_tickers = list(df_portfolio["ticker"].unique())
        prices_df_opt = opt.fetch_historical_prices(opt_tickers, period="1y")
        
        if not prices_df_opt.empty and len(prices_df_opt.columns) >= 2:
            # Solve portfolio weights
            opt_results = opt.optimize_portfolio(prices_df_opt)
            frontier_points = opt.get_efficient_frontier(prices_df_opt)
            
            opt_col1, opt_col2 = st.columns([1, 1])
            
            with opt_col1:
                st.markdown("#### Optimization Portfolio Allocations")
                
                # Calculate current allocations
                total_val = df_val["Market Value"].sum() if 'df_val' in locals() else 1.0
                current_allocs = {row["Ticker"]: (row["Market Value"] / total_val) for _, row in df_val.iterrows()}
                
                max_sh_w = opt_results["max_sharpe"]["weights"]
                min_v_w = opt_results["min_volatility"]["weights"]
                
                compare_rows = []
                for ticker in opt_tickers:
                    compare_rows.append({
                        "Asset Ticker": ticker,
                        "Current Weight (%)": current_allocs.get(ticker, 0.0) * 100,
                        "Max Sharpe Weight (%)": max_sh_w.get(ticker, 0.0) * 100,
                        "Min Volatility Weight (%)": min_v_w.get(ticker, 0.0) * 100
                    })
                    
                df_compare = pd.DataFrame(compare_rows)
                st.dataframe(
                    df_compare.style.format({
                        "Current Weight (%)": "{:.2f}%",
                        "Max Sharpe Weight (%)": "{:.2f}%",
                        "Min Volatility Weight (%)": "{:.2f}%"
                    }),
                    use_container_width=True,
                    hide_index=True
                )
                
                # Statistics table
                perf_rows = [
                    {
                        "Strategy": "Current Portfolio (Estimated)",
                        "Expected Return (Ann)": "N/A" if 'df_val' not in locals() else f"{opt.calculate_portfolio_performance(np.array([current_allocs.get(t, 0.0) for t in opt_tickers]), np.log(prices_df_opt/prices_df_opt.shift(1)).mean(), np.log(prices_df_opt/prices_df_opt.shift(1)).cov())[0]*100:.2f}%",
                        "Volatility / Risk (Ann)": "N/A" if 'df_val' not in locals() else f"{opt.calculate_portfolio_performance(np.array([current_allocs.get(t, 0.0) for t in opt_tickers]), np.log(prices_df_opt/prices_df_opt.shift(1)).mean(), np.log(prices_df_opt/prices_df_opt.shift(1)).cov())[1]*100:.2f}%",
                        "Sharpe Ratio": "N/A" if 'df_val' not in locals() else f"{opt.calculate_portfolio_performance(np.array([current_allocs.get(t, 0.0) for t in opt_tickers]), np.log(prices_df_opt/prices_df_opt.shift(1)).mean(), np.log(prices_df_opt/prices_df_opt.shift(1)).cov())[2]:.2f}"
                    },
                    {
                        "Strategy": "Maximum Sharpe Ratio (Tangency)",
                        "Expected Return (Ann)": f"{opt_results['max_sharpe']['return']*100:.2f}%",
                        "Volatility / Risk (Ann)": f"{opt_results['max_sharpe']['volatility']*100:.2f}%",
                        "Sharpe Ratio": f"{opt_results['max_sharpe']['sharpe']:.2f}"
                    },
                    {
                        "Strategy": "Minimum Volatility (Min Variance)",
                        "Expected Return (Ann)": f"{opt_results['min_volatility']['return']*100:.2f}%",
                        "Volatility / Risk (Ann)": f"{opt_results['min_volatility']['volatility']*100:.2f}%",
                        "Sharpe Ratio": f"{opt_results['min_volatility']['sharpe']:.2f}"
                    }
                ]
                st.dataframe(pd.DataFrame(perf_rows), use_container_width=True, hide_index=True)
                
            with opt_col2:
                # Efficient Frontier Chart
                if frontier_points:
                    df_front = pd.DataFrame(frontier_points)
                    
                    fig_front = go.Figure()
                    
                    # Efficient Frontier curve
                    fig_front.add_trace(go.Scatter(
                        x=df_front["volatility"], y=df_front["return"],
                        mode='lines', name='Efficient Frontier',
                        line=dict(color='#8b5cf6', width=3, dash='dash')
                    ))
                    
                    # Max Sharpe Portfolio star
                    fig_front.add_trace(go.Scatter(
                        x=[opt_results["max_sharpe"]["volatility"]],
                        y=[opt_results["max_sharpe"]["return"]],
                        mode='markers', name='Max Sharpe Portfolio',
                        marker=dict(color='#10b981', size=14, symbol='star')
                    ))
                    
                    # Min Volatility Portfolio circle
                    fig_front.add_trace(go.Scatter(
                        x=[opt_results["min_volatility"]["volatility"]],
                        y=[opt_results["min_volatility"]["return"]],
                        mode='markers', name='Min Volatility Portfolio',
                        marker=dict(color='#3b82f6', size=12, symbol='circle')
                    ))
                    
                    fig_front.update_layout(
                        title="Efficient Frontier & Optimized Portfolios",
                        xaxis_title="Annualized Volatility (Risk)",
                        yaxis_title="Expected Annualized Return",
                        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickformat=".0%"),
                        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickformat=".0%"),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=20, r=20, t=40, b=20),
                        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
                    )
                    st.plotly_chart(fig_front, use_container_width=True)
        else:
            st.error("Failed to fetch historical market data. Check tickers or network connectivity.")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Portfolio Risk Management & Monte Carlo simulations
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 🛡️ Portfolio Risk Management & Monte Carlo Simulations")
    
    if df_portfolio.empty or len(df_portfolio["ticker"].unique()) < 1:
        st.warning("Please add holdings to check portfolio risk stats.")
    else:
        risk_tickers = list(df_portfolio["ticker"].unique())
        prices_df_risk = opt.fetch_historical_prices(risk_tickers, period="1y")
        
        if not prices_df_risk.empty:
            # Recompute weights for current assets
            total_market_val = df_val["Market Value"].sum() if 'df_val' in locals() else 1.0
            current_weights = {row["Ticker"]: (row["Market Value"] / total_market_val) for _, row in df_val.iterrows()}
            
            # Risk Metrics calculations
            risk_metrics = opt.calculate_portfolio_risk_metrics(prices_df_risk, current_weights, portfolio_val, confidence_level=0.95)
            
            risk_col_left, risk_col_right = st.columns([1, 1])
            
            with risk_col_left:
                st.markdown("#### Portfolio Value at Risk (VaR) at 95% Confidence")
                st.markdown(
                    "Value at Risk (VaR) measures the maximum expected dollar loss of your portfolio over a given holding period "
                    "with a 95% probability (under normal market conditions)."
                )
                
                if risk_metrics:
                    # Let's display a nice comparison table
                    risk_table_data = [
                        {
                            "Risk Metric Type": "Parametric VaR (Normal Dist)",
                            "1-Day Expected Loss ($)": utils.format_currency(risk_metrics["parametric"]["usd_1d"]),
                            "1-Day Loss (%)": f"{risk_metrics['parametric']['pct_1d'] * 100:.2f}%",
                            "10-Day Expected Loss ($)": utils.format_currency(risk_metrics["parametric"]["usd_10d"]),
                            "10-Day Loss (%)": f"{risk_metrics['parametric']['pct_10d'] * 100:.2f}%"
                        },
                        {
                            "Risk Metric Type": "Historical VaR (Empirical)",
                            "1-Day Expected Loss ($)": utils.format_currency(risk_metrics["historical"]["usd_1d"]),
                            "1-Day Loss (%)": f"{risk_metrics['historical']['pct_1d'] * 100:.2f}%",
                            "10-Day Expected Loss ($)": utils.format_currency(risk_metrics["historical"]["usd_10d"]),
                            "10-Day Loss (%)": f"{risk_metrics['historical']['pct_10d'] * 100:.2f}%"
                        },
                        {
                            "Risk Metric Type": "Conditional VaR (Expected Shortfall)",
                            "1-Day Expected Loss ($)": utils.format_currency(risk_metrics["cvar"]["usd_1d"]),
                            "1-Day Loss (%)": f"{risk_metrics['cvar']['pct_1d'] * 100:.2f}%",
                            "10-Day Expected Loss ($)": utils.format_currency(risk_metrics["cvar"]["usd_10d"]),
                            "10-Day Loss (%)": f"{risk_metrics['cvar']['pct_10d'] * 100:.2f}%"
                        }
                    ]
                    st.dataframe(pd.DataFrame(risk_table_data), use_container_width=True, hide_index=True)
                    st.info(
                        "💡 **Expected Shortfall (CVaR)** calculates the average loss on days when "
                        "the portfolio breaks past the VaR threshold. It represents the tail risk in a worst-case crash."
                    )
            
            with risk_col_right:
                st.markdown("#### Portfolio Monte Carlo Projection")
                st.markdown(
                    "Simulates 1,000 potential future paths of your wealth based on historical returns drift "
                    "and covariance volatility using Geometric Brownian Motion."
                )
                
                sim_years = st.slider("Monte Carlo Horizon (Years)", min_value=1, max_value=20, value=10, step=1, key="mc_years_slider")
                
                # Run simulations
                df_sim_results = opt.simulate_monte_carlo(prices_df_risk, current_weights, portfolio_val, years=sim_years)
                
                if not df_sim_results.empty:
                    fig_sim = go.Figure()
                    
                    # Conservative
                    fig_sim.add_trace(go.Scatter(
                        x=df_sim_results["Year"], y=df_sim_results["Conservative (10th)"],
                        mode='lines', name='Conservative Path (10th %)',
                        line=dict(color='#ef4444', width=2, dash='dot')
                    ))
                    # Expected
                    fig_sim.add_trace(go.Scatter(
                        x=df_sim_results["Year"], y=df_sim_results["Expected (50th)"],
                        mode='lines', name='Expected Median Path (50th %)',
                        line=dict(color='#3b82f6', width=3)
                    ))
                    # Optimistic
                    fig_sim.add_trace(go.Scatter(
                        x=df_sim_results["Year"], y=df_sim_results["Optimistic (90th)"],
                        mode='lines', name='Optimistic Path (90th %)',
                        line=dict(color='#10b981', width=2, dash='dash')
                    ))
                    
                    fig_sim.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=20, r=20, t=10, b=10),
                        xaxis_title="Time Horizon (Years)",
                        yaxis_title="Portfolio Ending Value",
                        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
                        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickprefix=curr_sym),
                        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
                    )
                    st.plotly_chart(fig_sim, use_container_width=True)
        else:
            st.error("Failed to compile pricing history for portfolio risk metrics.")
            
    st.markdown('</div>', unsafe_allow_html=True)

    # Portfolio Stress Testing Section
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("### 💥 Macro Stress Testing & Shock Simulations")
    st.write(
        "Simulates historical market shocks and black swan events on your current asset weights "
        "to estimate paper drawdowns and potential value loss."
    )
    
    if df_portfolio.empty or portfolio_val <= 0:
        st.warning("Please build a portfolio to perform stress testing.")
    else:
        # Active weights calculation
        total_market_val = df_val["Market Value"].sum() if 'df_val' in locals() else 1.0
        current_weights = {row["Ticker"]: (row["Market Value"] / total_market_val) for _, row in df_val.iterrows()}
        
        stress_scenarios = [
            "2008 Great Recession",
            "2020 COVID-19 Crash",
            "2000 Dot-Com Bubble Burst",
            "Fed Rate Hike & Inflation Shock"
        ]
        
        selected_scenario = st.selectbox("Select Historical Macro Shock Scenario", stress_scenarios)
        
        # Calculate stress results
        stress_results = opt.stress_test_portfolio(current_weights, portfolio_val, selected_scenario)
        
        if stress_results:
            col_stress_left, col_stress_right = st.columns([1, 1])
            
            with col_stress_left:
                st.markdown(f"#### Scenario: **{stress_results['scenario']}**")
                st.write(stress_results["description"])
                
                st.markdown("---")
                # Warning metric cards
                # Loss percentage
                st.markdown(
                    f'<div class="alert-card alert-danger" style="padding: 16px;">'
                    f'<span style="font-size: 0.95rem; text-transform: uppercase; font-weight: 500;">Projected Portfolio Impact</span>'
                    f'<div style="font-size: 2rem; font-weight: 700; margin-top: 4px;">{stress_results["loss_pct"]:.2f}%</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                
                # Loss dollars
                st.markdown(
                    f'<div class="alert-card alert-danger" style="padding: 16px;">'
                    f'<span style="font-size: 0.95rem; text-transform: uppercase; font-weight: 500;">Estimated Value Loss</span>'
                    f'<div style="font-size: 2rem; font-weight: 700; margin-top: 4px;">{utils.format_currency(stress_results["loss_usd"])}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                
                # Remaining value
                st.markdown(
                    f'<div class="alert-card alert-success" style="padding: 16px;">'
                    f'<span style="font-size: 0.95rem; text-transform: uppercase; font-weight: 500;">Post-Shock Portfolio Value</span>'
                    f'<div style="font-size: 2rem; font-weight: 700; margin-top: 4px;">{utils.format_currency(stress_results["remaining_value"])}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                
            with col_stress_right:
                st.markdown("#### Individual Ticker Impact Breakdown")
                st.write("Calculated drawdowns for each of your stock holdings under this scenario:")
                
                breakdown_rows = []
                for ticker, details in stress_results["details"].items():
                    breakdown_rows.append({
                        "Holding Ticker": ticker,
                        "Current Allocation": f"{details['weight'] * 100:.1f}%",
                        "Scenario Drawdown": f"{details['shock_pct']:.1f}%",
                        "Projected Loss ($)": utils.format_currency(details['loss_usd'])
                    })
                
                st.dataframe(pd.DataFrame(breakdown_rows), use_container_width=True, hide_index=True)
                
    st.markdown('</div>', unsafe_allow_html=True)


# ----------------- TAB 4: FUTURE PROJECTIONS -----------------
with tab_forecast:
    if df_tx.empty:
        st.info("Forecasting models require transaction data. Please manually log or import transactions.")
    else:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### 🔮 Advanced Time-Series Projections")
        
        # User configurations for projections
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            growth_rate = st.slider("Target Investment Growth Rate (Annual %)", min_value=0.0, max_value=25.0, value=8.0, step=0.5) / 100.0
        with f_col2:
            forecast_period = st.slider("Forecasting Time Horizon (Months)", min_value=3, max_value=24, value=12, step=1)
            
        st.markdown("---")
        
        proj_col_left, proj_col_right = st.columns(2)
        
        with proj_col_left:
            st.markdown("#### Monthly Expense Trend Forecast")
            st.write(
                "Econometric Linear Regression modeling containing monthly indicator flags "
                "to isolate seasonal spending factors."
            )
            
            # Run forecasting
            df_exp_forecast = forec.forecast_expenses(df_tx, forecast_months=forecast_period)
            
            if not df_exp_forecast.empty:
                # Plotly forecast chart
                fig_exp_f = go.Figure()
                
                # Confidence intervals shading
                fig_exp_f.add_trace(go.Scatter(
                    x=df_exp_forecast["Month"], y=df_exp_forecast["Upper_Bound"],
                    line=dict(color='rgba(0,0,0,0)'),
                    showlegend=False, hoverinfo='skip'
                ))
                fig_exp_f.add_trace(go.Scatter(
                    x=df_exp_forecast["Month"], y=df_exp_forecast["Lower_Bound"],
                    fill='tonexty', fillcolor='rgba(239, 68, 68, 0.08)',
                    line=dict(color='rgba(0,0,0,0)'),
                    name='95% Confidence Interval', hoverinfo='skip'
                ))
                
                # Central forecast line
                fig_exp_f.add_trace(go.Scatter(
                    x=df_exp_forecast["Month"], y=df_exp_forecast["Forecast"],
                    mode='lines+markers', name='Expense Forecast',
                    line=dict(color='#ef4444', width=3, dash='dash')
                ))
                
                # Show recent historical data for context (last 6 months)
                df_exp_hist = df_tx[df_tx["type"] == "Expense"].copy()
                df_exp_hist["date"] = pd.to_datetime(df_exp_hist["date"])
                df_exp_hist["Month"] = df_exp_hist["date"].dt.to_period("M").dt.to_timestamp()
                hist_agg = df_exp_hist.groupby("Month")["amount"].sum().reset_index()
                hist_agg = hist_agg.sort_values("Month").tail(6)
                hist_agg["Month"] = hist_agg["Month"].dt.strftime("%Y-%m")
                
                fig_exp_f.add_trace(go.Scatter(
                    x=hist_agg["Month"], y=hist_agg["amount"],
                    mode='lines+markers', name='Historical Spent',
                    line=dict(color='rgba(255, 255, 255, 0.6)', width=2)
                ))
                
                fig_exp_f.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=20, r=20, t=10, b=10),
                    xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
                    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickprefix=curr_sym),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_exp_f, use_container_width=True)
            else:
                st.write("Insufficient expense history to generate predictions.")
                
        with proj_col_right:
            st.markdown("#### Cumulative Net Worth Projection")
            st.write(
                "Simulates future savings accretion compounded against growth of assets. "
                "Includes error propagation bounds based on cashflow volatility."
            )
            
            df_nw_proj = forec.project_net_worth(df_tx, portfolio_val, annual_growth_rate=growth_rate, forecast_months=forecast_period)
            
            if not df_nw_proj.empty:
                # Plotly forecast chart
                fig_nw_f = go.Figure()
                
                # Confidence intervals shading
                fig_nw_f.add_trace(go.Scatter(
                    x=df_nw_proj["Month"], y=df_nw_proj["Upper_Bound"],
                    line=dict(color='rgba(0,0,0,0)'),
                    showlegend=False, hoverinfo='skip'
                ))
                fig_nw_f.add_trace(go.Scatter(
                    x=df_nw_proj["Month"], y=df_nw_proj["Lower_Bound"],
                    fill='tonexty', fillcolor='rgba(139, 92, 246, 0.08)',
                    line=dict(color='rgba(0,0,0,0)'),
                    name='Uncertainty Range (95% CI)', hoverinfo='skip'
                ))
                
                # Central forecast line
                fig_nw_f.add_trace(go.Scatter(
                    x=df_nw_proj["Month"], y=df_nw_proj["Net_Worth"],
                    mode='lines+markers', name='Net Worth Projection',
                    line=dict(color='#8b5cf6', width=3)
                ))
                
                fig_nw_f.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=20, r=20, t=10, b=10),
                    xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
                    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickprefix=curr_sym),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_nw_f, use_container_width=True)
            else:
                st.write("Insufficient savings history to project net worth.")
                
        # Milestone Calculator
        if not df_nw_proj.empty:
            st.markdown("---")
            st.markdown("#### 🎯 Wealth Milestone Projections")
            
            current_nw = df_nw_proj.iloc[0]["Net_Worth"] - (df_nw_proj.iloc[0]["Net_Worth"] - portfolio_val)/12 # approx start
            if len(df_nw_proj) > 1:
                # average monthly net worth increase
                avg_nw_increase = (df_nw_proj.iloc[-1]["Net_Worth"] - df_nw_proj.iloc[0]["Net_Worth"]) / len(df_nw_proj)
            else:
                avg_nw_increase = 100.0
                
            milestones = [50000, 100000, 250000, 500000, 1000000]
            
            m_cols = st.columns(len(milestones))
            for i, target in enumerate(milestones):
                with m_cols[i]:
                    st.markdown(f"**Target: {curr_sym}{target:,}**")
                    if current_nw >= target:
                        st.markdown("<span style='color:#10b981;font-weight:600;'>Reached! ✅</span>", unsafe_allow_html=True)
                    else:
                        remaining = target - current_nw
                        months_needed = remaining / avg_nw_increase if avg_nw_increase > 0 else float('inf')
                        
                        if months_needed == float('inf'):
                            st.write("N/A (Negative cashflow)")
                        elif months_needed <= 12:
                            st.markdown(f"<span style='color:#8b5cf6;font-weight:600;'>{months_needed:.1f} months</span>", unsafe_allow_html=True)
                        else:
                            years_needed = months_needed / 12
                            st.markdown(f"<span style='color:#9ca3af;'>{years_needed:.1f} years</span>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# Trigger reload for CSS updates - v5
# End of file
