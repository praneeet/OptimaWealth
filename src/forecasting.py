import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest

def forecast_expenses(df_transactions: pd.DataFrame, forecast_months: int = 12) -> pd.DataFrame:
    """Forecasts monthly expenses for the next 12 months using Linear Regression with seasonality.
    
    Returns a DataFrame with columns: Month, Forecast, Upper_Bound, Lower_Bound.
    """
    if df_transactions.empty:
        return pd.DataFrame(columns=["Month", "Forecast", "Upper_Bound", "Lower_Bound"])
        
    # Filter for expenses only
    df_exp = df_transactions[df_transactions["type"] == "Expense"].copy()
    if df_exp.empty:
        return pd.DataFrame(columns=["Month", "Forecast", "Upper_Bound", "Lower_Bound"])
        
    # Convert dates and parse YYYY-MM
    df_exp["date"] = pd.to_datetime(df_exp["date"])
    df_exp["Month_Period"] = df_exp["date"].dt.to_period("M")
    
    # Aggregate by month
    monthly_agg = df_exp.groupby("Month_Period")["amount"].sum().reset_index()
    monthly_agg["Month_Date"] = monthly_agg["Month_Period"].dt.to_timestamp()
    
    # Sort chronologically
    monthly_agg = monthly_agg.sort_values("Month_Date").reset_index(drop=True)
    n_samples = len(monthly_agg)
    
    # Fallback to simple mean if we have less than 3 months of historical data
    if n_samples < 3:
        mean_expense = monthly_agg["amount"].mean() if n_samples > 0 else 1000.0
        std_expense = monthly_agg["amount"].std() if n_samples > 1 else 200.0
        if pd.isna(std_expense):
            std_expense = 200.0
            
        future_dates = [datetime.today() + pd.DateOffset(months=i) for i in range(1, forecast_months + 1)]
        forecast_df = pd.DataFrame({
            "Month": [d.strftime("%Y-%m") for d in future_dates],
            "Forecast": [mean_expense] * forecast_months,
            "Upper_Bound": [mean_expense + 1.96 * std_expense] * forecast_months,
            "Lower_Bound": [max(0.0, mean_expense - 1.96 * std_expense)] * forecast_months
        })
        return forecast_df

    # Feature Engineering: Time trend (1, 2, 3...) and Month of the Year (1-12)
    monthly_agg["trend"] = np.arange(1, n_samples + 1)
    monthly_agg["month_val"] = monthly_agg["Month_Date"].dt.month
    
    # One-hot encode the month variable (seasonality)
    # To avoid dummy variable trap, drop first, but using sklearn linear regression we can just use 12 dummy variables
    # We create columns for month_1, month_2 ... month_12
    for m in range(1, 13):
        monthly_agg[f"m_{m}"] = (monthly_agg["month_val"] == m).astype(int)
        
    features = ["trend"] + [f"m_{m}" for m in range(1, 13)]
    
    X = monthly_agg[features]
    y = monthly_agg["amount"]
    
    # Fit regression model
    model = LinearRegression()
    model.fit(X, y)
    
    # Calculate residuals standard error to compute confidence intervals
    preds = model.predict(X)
    residuals = y - preds
    residual_std = np.std(residuals)
    if residual_std == 0:
        residual_std = 0.1 * y.mean()
        
    # Generate future dates and features for forecasting
    last_date = monthly_agg["Month_Date"].max()
    future_dates = [last_date + pd.DateOffset(months=i) for i in range(1, forecast_months + 1)]
    
    future_rows = []
    for i, f_date in enumerate(future_dates):
        trend_val = n_samples + i + 1
        month_val = f_date.month
        row = {"trend": trend_val}
        for m in range(1, 13):
            row[f"m_{m}"] = 1 if m == month_val else 0
        future_rows.append(row)
        
    X_future = pd.DataFrame(future_rows)[features]
    y_forecast = model.predict(X_future)
    
    # Create forecast DataFrame
    forecast_df = pd.DataFrame({
        "Month": [d.strftime("%Y-%m") for d in future_dates],
        "Forecast": np.round(y_forecast, 2),
        "Upper_Bound": np.round(y_forecast + 1.96 * residual_std, 2),
        "Lower_Bound": np.round(np.clip(y_forecast - 1.96 * residual_std, 0.0, None), 2)
    })
    
    return forecast_df

def project_net_worth(df_transactions: pd.DataFrame, current_portfolio_value: float, annual_growth_rate: float = 0.08, forecast_months: int = 12) -> pd.DataFrame:
    """Projects monthly net worth over the next 12 months.
    
    Net worth is calculated as:
    NW_(t) = NW_(t-1) + Monthly_Savings_(t) + Portfolio_Appreciation_(t)
    """
    if df_transactions.empty:
        # Fallback empty case
        future_dates = [datetime.today() + pd.DateOffset(months=i) for i in range(1, forecast_months + 1)]
        df_proj = pd.DataFrame({
            "Month": [d.strftime("%Y-%m") for d in future_dates],
            "Net_Worth": [current_portfolio_value] * forecast_months,
            "Upper_Bound": [current_portfolio_value] * forecast_months,
            "Lower_Bound": [current_portfolio_value] * forecast_months
        })
        return df_proj
        
    df_tx = df_transactions.copy()
    df_tx["date"] = pd.to_datetime(df_tx["date"])
    df_tx["Month_Period"] = df_tx["date"].dt.to_period("M")
    
    # Aggregate monthly income and expenses
    monthly_inc = df_tx[df_tx["type"] == "Income"].groupby("Month_Period")["amount"].sum()
    monthly_exp = df_tx[df_tx["type"] == "Expense"].groupby("Month_Period")["amount"].sum()
    
    # Merge aggregations
    monthly_periods = sorted(df_tx["Month_Period"].unique())
    monthly_flows = pd.DataFrame(index=monthly_periods)
    monthly_flows["Income"] = monthly_flows.index.map(monthly_inc).fillna(0.0)
    monthly_flows["Expense"] = monthly_flows.index.map(monthly_exp).fillna(0.0)
    monthly_flows["Savings"] = monthly_flows["Income"] - monthly_flows["Expense"]
    
    # Calculate historical averages
    avg_monthly_savings = monthly_flows["Savings"].mean()
    savings_std = monthly_flows["Savings"].std()
    if pd.isna(savings_std) or savings_std == 0:
        savings_std = 500.0  # fallback uncertainty
        
    # Get current starting point (accumulated savings + portfolio value)
    # We estimate historical net cash savings accumulated in db
    total_inc = df_tx[df_tx["type"] == "Income"]["amount"].sum()
    total_exp = df_tx[df_tx["type"] == "Expense"]["amount"].sum()
    accumulated_cash = max(0.0, total_inc - total_exp)
    
    current_net_worth = accumulated_cash + current_portfolio_value
    
    # Forecast future expenses using our helper function
    expense_forecast = forecast_expenses(df_transactions, forecast_months)
    
    # Forecast future income (simple mean historical income)
    mean_monthly_income = monthly_flows["Income"].mean() if len(monthly_flows) > 0 else 5000.0
    
    # Project compounding return on portfolio + monthly additions
    monthly_rate = annual_growth_rate / 12.0
    
    proj_net_worth = []
    proj_upper = []
    proj_lower = []
    
    temp_cash = accumulated_cash
    temp_portfolio = current_portfolio_value
    
    # We propagate variance over time (variance adds linearly for independent random variables)
    cumulative_variance = 0.0
    
    future_dates = [datetime.today() + pd.DateOffset(months=i) for i in range(1, forecast_months + 1)]
    
    for i in range(forecast_months):
        # Forecasted expense for this month
        exp_t = expense_forecast.loc[i, "Forecast"] if i < len(expense_forecast) else monthly_flows["Expense"].mean()
        
        # Savings this month = Income - Expense
        savings_t = mean_monthly_income - exp_t
        
        # Portfolio compounds and expands
        portfolio_growth = temp_portfolio * monthly_rate
        temp_portfolio += portfolio_growth
        
        # Net savings are added to cash holdings
        temp_cash += savings_t
        
        # Total Net Worth
        nw_t = temp_cash + temp_portfolio
        proj_net_worth.append(nw_t)
        
        # Calculate bounds (accumulated uncertainty)
        cumulative_variance += (savings_std ** 2)
        std_err = np.sqrt(cumulative_variance)
        
        proj_upper.append(nw_t + 1.96 * std_err)
        proj_lower.append(max(0.0, nw_t - 1.96 * std_err))
        
    df_proj = pd.DataFrame({
        "Month": [d.strftime("%Y-%m") for d in future_dates],
        "Net_Worth": np.round(proj_net_worth, 2),
        "Upper_Bound": np.round(proj_upper, 2),
        "Lower_Bound": np.round(proj_lower, 2)
    })
    
    return df_proj

def detect_expense_anomalies(df_transactions: pd.DataFrame, contamination: float = 0.03) -> pd.DataFrame:
    """Detects unusual/anomalous expenses using the Isolation Forest unsupervised ML algorithm.
    
    Returns a DataFrame containing only the anomalous transactions.
    """
    if df_transactions.empty:
        return pd.DataFrame()
        
    # Filter for expenses
    df_exp = df_transactions[df_transactions["type"] == "Expense"].copy()
    if len(df_exp) < 5:
        # Not enough transactions to fit Isolation Forest reliably
        return pd.DataFrame()
        
    try:
        # Feature Engineering:
        # 1. Transaction Amount
        # 2. Ratio of Amount to Category Median Expense (identifies outliers relative to peer transactions)
        category_medians = df_exp.groupby("category")["amount"].transform("median")
        df_exp["category_ratio"] = df_exp["amount"] / (category_medians + 0.01)
        
        # 3. Day of week
        df_exp["date_parsed"] = pd.to_datetime(df_exp["date"])
        df_exp["weekday"] = df_exp["date_parsed"].dt.weekday
        
        features = ["amount", "category_ratio", "weekday"]
        X = df_exp[features]
        
        # Fit Isolation Forest
        model = IsolationForest(contamination=contamination, random_state=42)
        df_exp["anomaly_score"] = model.fit_predict(X)
        
        # In Isolation Forest: -1 is an anomaly, 1 is regular
        anomalies = df_exp[df_exp["anomaly_score"] == -1].copy()
        
        # Sort anomalies by amount descending
        anomalies = anomalies.sort_values(by="amount", ascending=False)
        
        return anomalies[["id", "date", "description", "category", "amount"]]
    except Exception as e:
        print(f"Error detecting transaction anomalies: {e}")
        return pd.DataFrame()

