import unittest

import numpy as np

from risk_math import (
    calculate_cash_outflows,
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
        terminal_rates = np.array([0.50, 0.55, 0.60])
        unhedged, hedged, _, _ = calculate_cash_outflows(
            10_000_000_000, terminal_rates, 0.5855, 0.0
        )
        self.assertTrue(np.allclose(unhedged, hedged))

    def test_full_hedge_has_constant_outflow(self):
        terminal_rates = np.array([0.50, 0.55, 0.60])
        _, hedged, locked, variable = calculate_cash_outflows(
            10_000_000_000, terminal_rates, 0.5855, 1.0
        )
        self.assertTrue(np.allclose(hedged, hedged[0]))
        self.assertTrue(np.allclose(variable, 0.0))
        self.assertTrue(np.allclose(locked, hedged))

    def test_half_hedge_halves_standard_deviation(self):
        terminal_rates = np.array([0.49, 0.52, 0.55, 0.60, 0.64])
        unhedged, hedged, _, _ = calculate_cash_outflows(
            10_000_000_000, terminal_rates, 0.5855, 0.5
        )
        self.assertAlmostEqual(np.std(hedged), 0.5 * np.std(unhedged), places=10)

    def test_expected_shortfall_is_average_of_high_cost_tail(self):
        values = np.arange(1.0, 101.0)
        summary = summarize_outflows(values)
        self.assertAlmostEqual(summary["p95"], 95.05)
        self.assertAlmostEqual(summary["es95"], 98.0)
        self.assertGreaterEqual(summary["es95"], summary["p95"])
        self.assertEqual(summary["max"], 100.0)

    def test_historical_volatility_estimator_uses_repository_csv(self):
        value, count, error = estimate_annualized_volatility(
            "jpy_inr_historical_data.csv", trading_days=252
        )
        self.assertIsNone(error)
        self.assertGreater(count, 100)
        self.assertGreater(value, 0.0)


if __name__ == "__main__":
    unittest.main()
