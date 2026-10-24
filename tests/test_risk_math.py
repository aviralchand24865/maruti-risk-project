import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from risk_math import (
    approximate_duration_price_change_cr,
    calculate_cash_outflows,
    calculate_forward_execution_cost_cr,
    calculate_forward_rate,
    estimate_annualized_volatility,
    simulate_gbm,
    summarize_outflows,
)


class TestRiskMath(unittest.TestCase):
    def test_forward_rate_uses_domestic_foreign_rate_differential(self):
        forward = calculate_forward_rate(0.55, 0.065, 0.0025, 1.0)
        self.assertAlmostEqual(forward, 0.55 * np.exp(0.0625), places=12)

    def test_gbm_is_reproducible_and_starts_at_spot(self):
        a = simulate_gbm(0.55, 0.065, 0.0025, 0.15, 1.0, 20, 50, 42)
        b = simulate_gbm(0.55, 0.065, 0.0025, 0.15, 1.0, 20, 50, 42)
        self.assertTrue(np.array_equal(a, b))
        self.assertEqual(a.shape, (21, 50))
        self.assertTrue(np.allclose(a[0], 0.55))

    def test_zero_hedge_equals_unhedged(self):
        rates = np.array([0.50, 0.55, 0.60])
        unhedged, hedged, _, _ = calculate_cash_outflows(10_000_000_000, rates, 0.5855, 0.0)
        self.assertTrue(np.allclose(unhedged, hedged))

    def test_full_hedge_has_constant_outflow(self):
        rates = np.array([0.50, 0.55, 0.60])
        _, hedged, locked, variable = calculate_cash_outflows(10_000_000_000, rates, 0.5855, 1.0)
        self.assertTrue(np.allclose(hedged, hedged[0]))
        self.assertTrue(np.allclose(variable, 0.0))
        self.assertTrue(np.allclose(locked, hedged))

    def test_half_hedge_halves_standard_deviation(self):
        rates = np.array([0.49, 0.52, 0.55, 0.60, 0.64])
        unhedged, hedged, _, _ = calculate_cash_outflows(10_000_000_000, rates, 0.5855, 0.5)
        self.assertAlmostEqual(np.std(hedged), 0.5 * np.std(unhedged), places=10)

    def test_expected_shortfall_is_average_of_high_cost_tail(self):
        stats = summarize_outflows(np.arange(1.0, 101.0))
        self.assertAlmostEqual(stats["p95"], 95.05)
        self.assertAlmostEqual(stats["es95"], 98.0)
        self.assertGreaterEqual(stats["es95"], stats["p95"])
        self.assertEqual(stats["max"], 100.0)

    def test_forward_execution_cost_scales_with_hedged_amount_and_bps(self):
        cost = calculate_forward_execution_cost_cr(10_000_000_000, 0.5, 0.5855, 5)
        self.assertAlmostEqual(cost, (10_000_000_000 * 0.5 * 0.5855 * 0.0005) / 10_000_000)
        self.assertAlmostEqual(
            calculate_forward_execution_cost_cr(10_000_000_000, 0.0, 0.5855, 5), 0.0
        )

    def test_duration_price_sensitivity_has_correct_direction(self):
        # ₹1,000 crore portfolio, duration 2 years, rate +100 bps => approx -₹20 crore.
        self.assertAlmostEqual(approximate_duration_price_change_cr(1000, 2, 100), -20.0)
        self.assertAlmostEqual(approximate_duration_price_change_cr(1000, 2, -100), 20.0)

    def test_historical_volatility_estimator_uses_clean_sample_csv(self):
        dates = pd.date_range("2024-01-01", periods=80, freq="B")
        rates = 0.55 * np.exp(np.linspace(0.0, 0.07, len(dates)) + 0.002 * np.sin(np.arange(len(dates))))
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "rates.csv"
            pd.DataFrame({"Date": dates, "JPYINR_Rate": rates}).to_csv(path, index=False)
            value, count, error = estimate_annualized_volatility(path, trading_days=252)
        self.assertIsNone(error)
        self.assertEqual(count, 79)
        self.assertGreater(value, 0.0)


if __name__ == "__main__":
    unittest.main()
