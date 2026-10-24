"""Pure financial calculations for the Maruti Suzuki FX risk dashboard.

The functions in this module are deliberately independent of Streamlit so they can
be tested and reused without launching the dashboard.
"""
from pathlib import Path

import numpy as np
import pandas as pd


RUPEES_PER_CRORE = 10_000_000


def calculate_forward_rate(spot_rate, domestic_rate, foreign_rate, horizon_years=1.0):
    """Continuous-compounding covered-interest-parity approximation.

    Spot is quoted as INR per unit of foreign currency (JPY), so the model uses
    F = S0 * exp((r_INR - r_JPY) * T).
    """
    if spot_rate <= 0:
        raise ValueError("spot_rate must be positive.")
    if horizon_years < 0:
        raise ValueError("horizon_years cannot be negative.")
    return float(spot_rate * np.exp((domestic_rate - foreign_rate) * horizon_years))


def estimate_annualized_volatility(csv_path, trading_days=252):
    """Estimate annualized volatility from positive JPY/INR observations.

    Uses the sample standard deviation of consecutive log returns multiplied by
    sqrt(trading_days). Returns (volatility, return_count, error_message).
    """
    try:
        data = pd.read_csv(csv_path)
        required = {"Date", "JPYINR_Rate"}
        if not required.issubset(data.columns):
            return None, 0, "CSV must contain Date and JPYINR_Rate columns."

        dates = pd.to_datetime(data["Date"], errors="coerce")
        rates = pd.to_numeric(data["JPYINR_Rate"], errors="coerce")
        valid = pd.DataFrame({"Date": dates, "Rate": rates}).dropna()
        valid = valid.loc[valid["Rate"] > 0].sort_values("Date")
        valid = valid.drop_duplicates("Date", keep="last")
        log_returns = np.log(valid["Rate"] / valid["Rate"].shift(1)).replace(
            [np.inf, -np.inf], np.nan
        ).dropna()

        if len(log_returns) < 30:
            return None, int(len(log_returns)), "At least 30 valid returns are required."

        volatility = float(log_returns.std(ddof=1) * np.sqrt(trading_days))
        if not np.isfinite(volatility) or volatility <= 0:
            return None, int(len(log_returns)), "Estimated volatility was not valid."

        return volatility, int(len(log_returns)), None
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        return None, 0, f"Historical data could not be loaded: {exc}"


def simulate_gbm(spot_rate, domestic_rate, foreign_rate, volatility,
                 horizon_years=1.0, trading_days=252, num_paths=1000, seed=42):
    """Generate GBM rate paths using a local random-number generator."""
    if spot_rate <= 0:
        raise ValueError("spot_rate must be positive.")
    if volatility < 0:
        raise ValueError("volatility cannot be negative.")
    if horizon_years <= 0 or trading_days <= 0 or num_paths <= 0:
        raise ValueError("horizon_years, trading_days and num_paths must be positive.")

    rng = np.random.default_rng(int(seed))
    dt = horizon_years / trading_days
    drift_dt = ((domestic_rate - foreign_rate) - 0.5 * volatility**2) * dt
    diffusion_dt = volatility * np.sqrt(dt)

    paths = np.empty((trading_days + 1, num_paths), dtype=float)
    paths[0, :] = spot_rate

    for step in range(1, trading_days + 1):
        z = rng.standard_normal(num_paths)
        paths[step, :] = paths[step - 1, :] * np.exp(drift_dt + diffusion_dt * z)

    return paths


def calculate_cash_outflows(exposure_jpy, terminal_rates, forward_rate, hedge_ratio):
    """Return unhedged and forward-hedged INR outflows in crore.

    Assumes a payable in JPY, a matched one-year forward, no transaction costs,
    and no counterparty/default or timing mismatch.
    """
    if exposure_jpy < 0:
        raise ValueError("exposure_jpy cannot be negative.")
    if not 0.0 <= hedge_ratio <= 1.0:
        raise ValueError("hedge_ratio must be between 0 and 1.")
    rates = np.asarray(terminal_rates, dtype=float)
    if rates.size == 0 or not np.all(np.isfinite(rates)) or np.any(rates <= 0):
        raise ValueError("terminal_rates must be a non-empty array of positive finite rates.")

    unhedged = exposure_jpy * rates / RUPEES_PER_CRORE
    hedged_amount_jpy = exposure_jpy * hedge_ratio
    unhedged_amount_jpy = exposure_jpy * (1.0 - hedge_ratio)
    locked_cost = hedged_amount_jpy * forward_rate / RUPEES_PER_CRORE
    variable_cost = unhedged_amount_jpy * rates / RUPEES_PER_CRORE
    hedged = locked_cost + variable_cost
    return unhedged, hedged, locked_cost, variable_cost


def summarize_outflows(outflows):
    """Summarize modeled cash outflows including 95% expected shortfall.

    Percentiles are high-cost thresholds. Expected shortfall is the arithmetic
    mean of observations at or above the 95th percentile.
    """
    values = np.asarray(outflows, dtype=float)
    if values.size == 0 or not np.all(np.isfinite(values)):
        raise ValueError("outflows must be a non-empty array of finite values.")

    p95 = float(np.percentile(values, 95))
    return {
        "mean": float(np.mean(values)),
        "std": float(np.std(values, ddof=0)),
        "p95": p95,
        "p99": float(np.percentile(values, 99)),
        "max": float(np.max(values)),
        "es95": float(np.mean(values[values >= p95])),
    }



def calculate_forward_execution_cost_cr(exposure_jpy, hedge_ratio, forward_rate, cost_bps):
    """Estimate extra execution cost in ₹ crore as bps of the forward rupee notional.

    cost_bps is an explicit user assumption, not a live dealer quote. The forward
    rate itself already contains the modeled interest-rate differential.
    """
    if exposure_jpy < 0:
        raise ValueError("exposure_jpy cannot be negative.")
    if not 0.0 <= hedge_ratio <= 1.0:
        raise ValueError("hedge_ratio must be between 0 and 1.")
    if forward_rate <= 0:
        raise ValueError("forward_rate must be positive.")
    if cost_bps < 0:
        raise ValueError("cost_bps cannot be negative.")
    hedged_rupee_notional = exposure_jpy * hedge_ratio * forward_rate
    return float(hedged_rupee_notional * (cost_bps / 10_000.0) / RUPEES_PER_CRORE)


def approximate_duration_price_change_cr(portfolio_value_cr, modified_duration_years, rate_shift_bps):
    """Approximate bond/fund price change from a yield move, in ₹ crore.

    First-order duration approximation: change in value ≈ -duration × change in
    yield × portfolio value. Duration is an assumption unless fund data provides it.
    A positive rate shift therefore produces a negative estimated price change.
    """
    if portfolio_value_cr < 0:
        raise ValueError("portfolio_value_cr cannot be negative.")
    if modified_duration_years < 0:
        raise ValueError("modified_duration_years cannot be negative.")
    shift_decimal = rate_shift_bps / 10_000.0
    return float(-modified_duration_years * shift_decimal * portfolio_value_cr)
