import numpy as np
import pandas as pd
import scipy.optimize as sco
import yfinance as yf
from datetime import datetime, timedelta

def generate_mock_prices(tickers: list[str], period_days: int = 365) -> pd.DataFrame:
    """Generates synthetic stock price history using Geometric Brownian Motion (GBM) for offline fallback."""
    np.random.seed(42)
    dates = [datetime.today() - timedelta(days=i) for i in range(period_days)]
    dates.reverse()
    
    # Base prices and parameters for realistic Indian stocks
    assets_config = {
        "RELIANCE.NS": {"start": 2500.0, "mu": 0.12, "sigma": 0.18},
        "TCS.NS": {"start": 3400.0, "mu": 0.10, "sigma": 0.16},
        "HDFCBANK.NS": {"start": 1600.0, "mu": 0.11, "sigma": 0.17},
        "INFY.NS": {"start": 1400.0, "mu": 0.09, "sigma": 0.19},
        "ICICIBANK.NS": {"start": 950.0, "mu": 0.13, "sigma": 0.20},
        "TATAMOTORS.NS": {"start": 600.0, "mu": 0.15, "sigma": 0.25},
        "SBIN.NS": {"start": 580.0, "mu": 0.10, "sigma": 0.22},
        "BHARTIARTL.NS": {"start": 850.0, "mu": 0.12, "sigma": 0.21},
        "ITC.NS": {"start": 450.0, "mu": 0.08, "sigma": 0.15},
        "LT.NS": {"start": 2400.0, "mu": 0.11, "sigma": 0.18},
        "HINDUNILVR.NS": {"start": 2500.0, "mu": 0.07, "sigma": 0.14}
    }
    
    dt = 1 / 252
    prices_dict = {}
    
    for ticker in tickers:
        ticker_upper = ticker.upper().strip()
        config = assets_config.get(ticker_upper)
        if not config:
            # Try matching base ticker on NSE
            base = ticker_upper.split(".")[0]
            config = assets_config.get(f"{base}.NS", {"start": 500.0, "mu": 0.10, "sigma": 0.20})
            
        S0 = config["start"]
        mu = config["mu"]
        sigma = config["sigma"]
        
        # GBM path simulation
        prices = [S0]
        for _ in range(1, period_days):
            # dS = S * (mu*dt + sigma*dW)
            dW = np.random.normal(0, np.sqrt(dt))
            S_t = prices[-1] * np.exp((mu - 0.5 * sigma**2) * dt + sigma * dW)
            prices.append(S_t)
            
        prices_dict[ticker] = prices
        
    df = pd.DataFrame(prices_dict, index=dates)
    df.index.name = "Date"
    return df

def fetch_historical_prices(tickers: list[str], period: str = "1y") -> pd.DataFrame:
    """Fetches historical closing prices from yfinance, falls back to GBM simulation on failure."""
    if not tickers:
        return pd.DataFrame()
        
    tickers = [t.upper().strip() for t in tickers]
    
    try:
        # Fetch data using yfinance
        # yfinance can sometimes be rate-limited, fail, or run offline
        data = yf.download(tickers, period=period, progress=False)
        
        # yfinance returns Close column as a Series (if 1 ticker) or DataFrame (if multiple)
        if "Close" in data:
            prices = data["Close"]
        else:
            # fallback structure check
            prices = data
            
        if isinstance(prices, pd.Series):
            prices = prices.to_frame(name=tickers[0])
            
        # Drop tickers with all null values and forward-fill missing records
        prices = prices[tickers].ffill().bfill()
        
        # If the fetched data is empty or has all NaNs, raise error to trigger mock fallback
        if prices.empty or prices.isna().all().all() or len(prices) < 10:
            raise ValueError("Empty or invalid yfinance output")
            
        return prices
        
    except Exception as e:
        print(f"yfinance failed (Error: {e}). Falling back to simulated pricing...")
        days_map = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730}
        days = days_map.get(period, 365)
        return generate_mock_prices(tickers, period_days=days)

def calculate_portfolio_performance(weights: np.ndarray, mean_returns: pd.Series, cov_matrix: pd.DataFrame, risk_free_rate: float = 0.04) -> tuple[float, float, float]:
    """Calculates annualized portfolio return, volatility, and Sharpe ratio."""
    # Annualized portfolio return
    port_return = np.sum(mean_returns * weights) * 252
    # Annualized portfolio volatility
    port_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix * 252, weights)))
    # Sharpe ratio
    sharpe_ratio = (port_return - risk_free_rate) / port_volatility
    return port_return, port_volatility, sharpe_ratio

def _neg_sharpe(weights: np.ndarray, mean_returns: pd.Series, cov_matrix: pd.DataFrame, risk_free_rate: float) -> float:
    """Negative Sharpe ratio helper function for optimization."""
    return -calculate_portfolio_performance(weights, mean_returns, cov_matrix, risk_free_rate)[2]

def _portfolio_volatility(weights: np.ndarray, mean_returns: pd.Series, cov_matrix: pd.DataFrame) -> float:
    """Portfolio volatility helper function for optimization constraints."""
    return calculate_portfolio_performance(weights, mean_returns, cov_matrix)[1]

def optimize_portfolio(prices_df: pd.DataFrame, risk_free_rate: float = 0.04) -> dict:
    """Computes Max Sharpe and Min Variance portfolio allocations using SciPy optimization."""
    # Calculate daily returns
    returns = np.log(prices_df / prices_df.shift(1)).dropna()
    mean_returns = returns.mean()
    cov_matrix = returns.cov()
    
    num_assets = len(prices_df.columns)
    tickers = list(prices_df.columns)
    
    # Setup constraints (weights sum to 1) and bounds (weights between 0 and 1, no short selling)
    constraints = {"type": "eq", "fun": lambda x: np.sum(x) - 1.0}
    bounds = tuple((0.0, 1.0) for _ in range(num_assets))
    initial_weights = np.ones(num_assets) / num_assets
    
    # 1. Maximize Sharpe Ratio (Minimize Negative Sharpe)
    opt_sharpe = sco.minimize(
        _neg_sharpe,
        initial_weights,
        args=(mean_returns, cov_matrix, risk_free_rate),
        method="SLSQP",
        bounds=bounds,
        constraints=constraints
    )
    
    # 2. Minimize Volatility
    opt_vol = sco.minimize(
        _portfolio_volatility,
        initial_weights,
        args=(mean_returns, cov_matrix),
        method="SLSQP",
        bounds=bounds,
        constraints=constraints
    )
    
    # Extract weights
    max_sharpe_weights = opt_sharpe.x
    min_vol_weights = opt_vol.x
    
    # Performance calculations
    ms_ret, ms_vol, ms_sharpe = calculate_portfolio_performance(max_sharpe_weights, mean_returns, cov_matrix, risk_free_rate)
    mv_ret, mv_vol, mv_sharpe = calculate_portfolio_performance(min_vol_weights, mean_returns, cov_matrix, risk_free_rate)
    
    results = {
        "tickers": tickers,
        "max_sharpe": {
            "weights": {tickers[i]: float(max_sharpe_weights[i]) for i in range(num_assets)},
            "return": float(ms_ret),
            "volatility": float(ms_vol),
            "sharpe": float(ms_sharpe)
        },
        "min_volatility": {
            "weights": {tickers[i]: float(min_vol_weights[i]) for i in range(num_assets)},
            "return": float(mv_ret),
            "volatility": float(mv_vol),
            "sharpe": float(mv_sharpe)
        }
    }
    
    return results

def get_efficient_frontier(prices_df: pd.DataFrame, risk_free_rate: float = 0.04, num_portfolios: int = 30) -> list[dict]:
    """Generates coordinates along the Efficient Frontier curve for chart plotting."""
    returns = np.log(prices_df / prices_df.shift(1)).dropna()
    mean_returns = returns.mean()
    cov_matrix = returns.cov()
    
    num_assets = len(prices_df.columns)
    bounds = tuple((0.0, 1.0) for _ in range(num_assets))
    initial_weights = np.ones(num_assets) / num_assets
    
    # Find max return and min volatility portfolios to establish range
    opt_res = optimize_portfolio(prices_df, risk_free_rate)
    min_ret = opt_res["min_volatility"]["return"]
    max_ret = opt_res["max_sharpe"]["return"] * 1.5 # stretch range slightly
    
    target_returns = np.linspace(min_ret, max_ret, num_portfolios)
    frontier_points = []
    
    for target in target_returns:
        # Constraints: weights sum to 1, AND annualized portfolio return equals target
        constraints = [
            {"type": "eq", "fun": lambda x: np.sum(x) - 1.0},
            {"type": "eq", "fun": lambda x: np.sum(mean_returns * x) * 252 - target}
        ]
        
        opt = sco.minimize(
            _portfolio_volatility,
            initial_weights,
            args=(mean_returns, cov_matrix),
            method="SLSQP",
            bounds=bounds,
            constraints=constraints
        )
        
        if opt.success:
            vol = opt.fun
            frontier_points.append({
                "return": float(target),
                "volatility": float(vol),
                "sharpe": float((target - risk_free_rate) / vol)
            })
            
    return frontier_points

def calculate_portfolio_risk_metrics(prices_df: pd.DataFrame, weights_dict: dict, portfolio_value: float, confidence_level: float = 0.95) -> dict:
    """Calculates Parametric VaR, Historical VaR, and Conditional VaR (CVaR) for the portfolio."""
    if prices_df.empty or not weights_dict:
        return {}
        
    # Calculate daily returns
    returns = np.log(prices_df / prices_df.shift(1)).dropna()
    tickers = list(prices_df.columns)
    
    # Map weights dict to array in columns order
    weights = np.array([weights_dict.get(t, 0.0) for t in tickers])
    # Normalize weights
    if np.sum(weights) > 0:
        weights = weights / np.sum(weights)
    else:
        weights = np.ones(len(tickers)) / len(tickers)
        
    # Calculate daily portfolio returns
    port_daily_returns = returns.dot(weights)
    
    mean_daily_return = port_daily_returns.mean()
    std_daily_return = port_daily_returns.std()
    
    # 1. Parametric VaR (Normal Distribution)
    # Z-score for confidence level
    # 95% -> 1.64485, 99% -> 2.32635
    z_score = 1.64485 if confidence_level == 0.95 else 2.32635
    
    # Daily Parametric VaR
    parametric_var_pct_1d = (z_score * std_daily_return) - mean_daily_return
    parametric_var_usd_1d = parametric_var_pct_1d * portfolio_value
    
    # 10-Day Parametric VaR (Square root of time scaling)
    parametric_var_pct_10d = parametric_var_pct_1d * np.sqrt(10)
    parametric_var_usd_10d = parametric_var_pct_10d * portfolio_value
    
    # 2. Historical VaR
    # Sorted returns, find percentile (e.g. 5th percentile for 95% confidence)
    cutoff_percentile = (1 - confidence_level) * 100
    hist_var_pct_1d = -np.percentile(port_daily_returns, cutoff_percentile)
    hist_var_usd_1d = hist_var_pct_1d * portfolio_value
    
    hist_var_pct_10d = hist_var_pct_1d * np.sqrt(10)
    hist_var_usd_10d = hist_var_pct_10d * portfolio_value
    
    # 3. Conditional VaR (Expected Shortfall)
    # Average return of the worst returns below the VaR threshold
    var_threshold = -hist_var_pct_1d
    worst_returns = port_daily_returns[port_daily_returns <= var_threshold]
    if len(worst_returns) > 0:
        cvar_pct_1d = -worst_returns.mean()
    else:
        cvar_pct_1d = hist_var_pct_1d  # fallback
    cvar_usd_1d = cvar_pct_1d * portfolio_value
    
    cvar_pct_10d = cvar_pct_1d * np.sqrt(10)
    cvar_usd_10d = cvar_pct_10d * portfolio_value
    
    return {
        "parametric": {
            "pct_1d": float(parametric_var_pct_1d),
            "usd_1d": float(parametric_var_usd_1d),
            "pct_10d": float(parametric_var_pct_10d),
            "usd_10d": float(parametric_var_usd_10d)
        },
        "historical": {
            "pct_1d": float(hist_var_pct_1d),
            "usd_1d": float(hist_var_usd_1d),
            "pct_10d": float(hist_var_pct_10d),
            "usd_10d": float(hist_var_usd_10d)
        },
        "cvar": {
            "pct_1d": float(cvar_pct_1d),
            "usd_1d": float(cvar_usd_1d),
            "pct_10d": float(cvar_pct_10d),
            "usd_10d": float(cvar_usd_10d)
        }
    }

def simulate_monte_carlo(prices_df: pd.DataFrame, weights_dict: dict, portfolio_value: float, years: int = 10, num_simulations: int = 1000) -> pd.DataFrame:
    """Simulates future wealth paths for the portfolio using Geometric Brownian Motion.
    
    Returns a DataFrame containing Year, 10th (Conservative), 50th (Expected), and 90th (Optimistic) percentiles.
    """
    if prices_df.empty or not weights_dict or portfolio_value <= 0:
        return pd.DataFrame()
        
    returns = np.log(prices_df / prices_df.shift(1)).dropna()
    tickers = list(prices_df.columns)
    
    # Match weights
    weights = np.array([weights_dict.get(t, 0.0) for t in tickers])
    if np.sum(weights) > 0:
        weights = weights / np.sum(weights)
    else:
        weights = np.ones(len(tickers)) / len(tickers)
        
    # Annualized portfolio mean return and volatility
    mean_returns = returns.mean()
    cov_matrix = returns.cov()
    
    port_ret, port_vol, _ = calculate_portfolio_performance(weights, mean_returns, cov_matrix)
    
    # Simulation settings (monthly intervals)
    steps_per_year = 12
    total_steps = int(years * steps_per_year)
    dt = 1 / steps_per_year
    
    np.random.seed(42)
    sim_paths = np.zeros((total_steps + 1, num_simulations))
    sim_paths[0, :] = portfolio_value
    
    drift = (port_ret - 0.5 * port_vol**2) * dt
    diffusion = port_vol * np.sqrt(dt)
    
    for t in range(1, total_steps + 1):
        Z = np.random.normal(0, 1, num_simulations)
        sim_paths[t, :] = sim_paths[t-1, :] * np.exp(drift + diffusion * Z)
        
    # Calculate percentiles at each step
    timeline = [t * dt for t in range(total_steps + 1)]
    
    p10 = np.percentile(sim_paths, 10, axis=1)  # Conservative
    p50 = np.percentile(sim_paths, 50, axis=1)  # Expected
    p90 = np.percentile(sim_paths, 90, axis=1)  # Optimistic
    
    df_sim = pd.DataFrame({
        "Year": timeline,
        "Conservative (10th)": np.round(p10, 2),
        "Expected (50th)": np.round(p50, 2),
        "Optimistic (90th)": np.round(p90, 2)
    })
    
    return df_sim

def stress_test_portfolio(weights_dict: dict, total_value: float, scenario_name: str) -> dict:
    """Simulates portfolio drawdowns under different historical macroeconomic shock scenarios."""
    if not weights_dict or total_value <= 0:
        return {}
        
    # Scenario configurations: maps tickers to historical asset drawdowns.
    # Defaults are used for unmapped custom assets.
    scenarios = {
        "2008 Great Recession": {
            "shocks": {"RELIANCE.NS": -0.60, "TCS.NS": -0.55, "HDFCBANK.NS": -0.50, "INFY.NS": -0.55, "ICICIBANK.NS": -0.58, "SBIN.NS": -0.62, "TATAMOTORS.NS": -0.70},
            "default": -0.45,
            "description": "Liquidity crisis sparked by subprime mortgage defaults. High correlations across all risk assets globally."
        },
        "2020 COVID-19 Crash": {
            "shocks": {"RELIANCE.NS": -0.35, "TCS.NS": -0.22, "HDFCBANK.NS": -0.38, "INFY.NS": -0.25, "ICICIBANK.NS": -0.42, "SBIN.NS": -0.40, "TATAMOTORS.NS": -0.55},
            "default": -0.30,
            "description": "Rapid market panic triggered by pandemic lockdowns, followed by a swift expansionary monetary policy recovery."
        },
        "2000 Dot-Com Bubble Burst": {
            "shocks": {"RELIANCE.NS": -0.20, "TCS.NS": -0.70, "HDFCBANK.NS": -0.15, "INFY.NS": -0.80, "ICICIBANK.NS": -0.18, "SBIN.NS": -0.25, "TATAMOTORS.NS": -0.30},
            "default": -0.35,
            "description": "Severe valuation shock concentrated heavily in technology, internet, and growth equities."
        },
        "Fed Rate Hike & Inflation Shock": {
            "shocks": {"RELIANCE.NS": -0.15, "TCS.NS": -0.18, "HDFCBANK.NS": -0.12, "INFY.NS": -0.20, "ICICIBANK.NS": -0.14, "SBIN.NS": -0.16, "TATAMOTORS.NS": -0.22},
            "default": -0.15,
            "description": "Rising inflation leading to aggressive central bank tightening, raising discount rates and hurting high-multiple assets."
        }
    }
    
    config = scenarios.get(scenario_name)
    if not config:
        return {}
        
    shocks = config["shocks"]
    default_shock = config["default"]
    
    # Calculate portfolio weighted loss
    port_loss_pct = 0.0
    individual_losses = {}
    
    # Ensure weights sum to 1.0 for loss ratio calculation
    total_w = sum(weights_dict.values())
    
    for ticker, weight in weights_dict.items():
        t_upper = ticker.upper().strip()
        # Find appropriate shock for this ticker with BSE-to-NSE fallback
        shock = shocks.get(t_upper)
        if shock is None:
            base = t_upper.split(".")[0]
            shock = shocks.get(f"{base}.NS", default_shock)
        
        normalized_weight = weight / total_w if total_w > 0 else 0
        port_loss_pct += normalized_weight * shock
        individual_losses[t_upper] = {
            "weight": normalized_weight,
            "shock_pct": shock * 100,
            "loss_usd": normalized_weight * shock * total_value
        }
        
    portfolio_loss_usd = port_loss_pct * total_value
    remaining_value = total_value + portfolio_loss_usd
    
    return {
        "scenario": scenario_name,
        "description": config["description"],
        "loss_pct": float(port_loss_pct * 100),
        "loss_usd": float(portfolio_loss_usd),
        "remaining_value": float(remaining_value),
        "details": individual_losses
    }


