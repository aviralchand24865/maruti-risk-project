# Maruti Suzuki FX Risk & Hedging Dashboard

**Course:** FIN7003 — Derivatives and Financial Risk Management  
**Company:** Maruti Suzuki India Limited (MSIL)  
**Primary modeled exposure:** Japanese yen (JPY) payable, quoted as INR per JPY  
**App:** Streamlit + Plotly

This is an educational risk model, not Maruti Suzuki's live treasury system or a recommendation to trade derivatives. Historical company disclosures provide context; the modeled exposure amount and rate assumptions are user-controlled scenario inputs.

## Run locally

Use Python 3.10 or later.

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app expects `risk_math.py` and `jpy_inr_historical_data.csv` to be in the same folder as `app.py`.

Run the unit tests from the repository root:

```bash
python -m unittest discover -s tests -v
```

## Dashboard sections

### 1. Executive Summary & Disclosures

Summarizes historical company disclosures, explains why JPY payables can create transaction exposure, and distinguishes transaction, translation and economic exposure. The annual-report figures shown in this section are background information; they do not automatically determine the scenario exposure entered in the sidebar.

Before using figures in a presentation, verify the annual-report period, note number, standalone versus consolidated scope, units and denomination against the source. Imports can involve multiple currencies; the dashboard simplifies the exposure to one JPY payable.

### 2. Monte Carlo Exchange Rate Simulation

Generates daily JPY/INR paths over 252 trading days using Geometric Brownian Motion:

```text
S(t+dt) = S(t) * exp(((r_INR - r_JPY) - 0.5*sigma^2)*dt
                       + sigma*sqrt(dt)*Z)
```

where `Z` is a standard-normal random shock, `sigma` is annualized volatility, and `dt = 1/252` for the one-year/252-step model.

The one-year forward benchmark uses a continuously compounded covered-interest-parity approximation:

```text
F = S0 * exp((r_INR - r_JPY) * T)
```

The sidebar supports two volatility modes:

- **Manual assumption (default):** uses the volatility selected by the user; the default is 15%.
- **Estimate from historical CSV:** computes consecutive log returns from the bundled positive JPY/INR rates and annualizes the sample standard deviation by `sqrt(252)`. It validates and sorts dates, removes duplicate dates, and skips invalid observations. This is a historical estimate from the local file, not a live data feed.

With the bundled data currently in the project, the estimate is about **15.47% annualized** (777 usable consecutive returns). It will change if the CSV is updated.

### 3. Hedging Analysis & Payoff Comparison

The modeled exposure is a JPY payable. A share `h` is hedged using a one-year forward at rate `F`; the remaining share is settled at the simulated terminal spot `ST`.

```text
Unhedged cost = N * ST / 10,000,000

Hedged cost = (h*N*F + (1-h)*N*ST) / 10,000,000
```

The denominator converts rupees to crore rupees. This simplified model assumes the forward exactly matches the exposure amount and maturity, and excludes transaction costs, bid/ask spreads, collateral, counterparty risk, accounting treatment and basis/timing mismatch.

The app reports:
- Mean outflow and population standard deviation.
- 95th- and 99th-percentile outflow thresholds.
- 95% expected shortfall: the mean of simulated outflows at or above the 95th-percentile threshold.
- Maximum outflow observed in the finite simulation sample.
- Comparison charts and CDF for hedged and unhedged outflows.

**Metric interpretation:** A 95th-percentile outflow is a threshold exceeded by approximately 5% of simulated results. Expected shortfall describes the average high-cost tail. Maximum simulated outflow is not a theoretical worst case. The displayed standard-deviation reduction is not variance reduction.

### 4. Interest Rate Sensitivity & Capital Structure

Uses an adjustable positive rate shift from 25 to 250 basis points and shows a simple one-year interest/yield sensitivity for stated borrowing and treasury-investment balances. A basis point is 0.01 percentage points; 100 bps equals 1 percentage point.

This calculation is principal × rate shift for one year. **It is not a duration-based estimate of mutual-fund market-value sensitivity**, nor does it model instrument repricing, portfolio mix, maturity, or cash-flow timing. Actual rate risk depends on the composition and repricing of the company's instruments.

## Sidebar inputs

| Input | Default | Effect |
|---|---:|---|
| JPY exposure | ¥10 billion | Scales modeled rupee cash flows linearly |
| Spot rate | ₹0.5500 per JPY | Starting value of each simulated path |
| Forward hedge ratio | 50% | Fixes the rate for that share of the payable |
| Manual annual volatility | 15% | Controls the dispersion of simulated paths in manual mode |
| Indian rate | 6.50% | Contributes to forward pricing and simulation drift |
| Japanese rate | 0.25% | Contributes to forward pricing and simulation drift |
| Simulation paths | 1,000 | Controls sampling stability of statistics |
| Random seed | 42 | Makes results reproducible for the same code and inputs |

## Improvements in this version

- Centralized forward-rate, GBM, cash-flow and risk-summary formulas in `risk_math.py` so they can be tested without running the UI.
- Added a historical-volatility option that actually reads the included CSV, while keeping the manual 15% default.
- Replaced the old `CFaR` proxy with an explicitly named 95% expected-shortfall calculation.
- Renamed high-outflow percentile outputs so they are not presented as loss-based VaR without a defined loss baseline.
- Renamed standard-deviation reduction accurately, and separated it from variance reduction.
- Distinguished a sample maximum from a theoretical worst case.
- Corrected the net-debt/equity display to show the ratio implied by the stated net-debt input.
- Added a chart to show simple annual interest/yield sensitivity across rate shifts.
- Added unit tests for forward pricing, reproducible simulation, hedge edge cases, expected shortfall and historical volatility estimation.

## Validation and limitations

The model is conditional on its inputs and on a lognormal GBM structure. It is not a forecast guarantee. A production treasury model would also validate sourced market data, actual currency amounts and maturity dates, exposure netting, derivative quotes/costs, scenario back-testing, multiple-currency effects, and instrument-specific interest-rate risk.

The company figures in the Executive Summary are historical facts as represented in the dashboard and must be checked against Maruti Suzuki's official reports before external use: [Maruti Suzuki investor reports](https://www.marutisuzuki.com/corporate/investors/company-reports).

## Project files

- `app.py` — Streamlit dashboard and visualizations.
- `risk_math.py` — pure financial calculations used by the dashboard.
- `tests/test_risk_math.py` — automated unit tests.
- `jpy_inr_historical_data.csv` — historical JPY/INR observations used for optional volatility estimation.
- `requirements.txt` — runtime and analysis dependencies.
