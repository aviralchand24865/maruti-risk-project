# Maruti Suzuki FX Risk & Hedging Dashboard — Student Guide

**Course:** FIN7003 — Derivatives and Financial Risk Management  
**Company:** Maruti Suzuki India Limited (MSIL)  
**Main model:** Japanese yen (JPY) payable risk, quoted as Indian rupees per yen  
**App:** Streamlit and Plotly

This project is an educational model. It is not Maruti Suzuki's live treasury system, it does not predict the exact exchange rate, and it is not a recommendation to trade a derivative.

## Run the app

Use Python 3.10 or later.

```bash
pip install -r requirements.txt
streamlit run app.py
```

Keep `app.py`, `risk_math.py`, and `jpy_inr_historical_data.csv` in the same folder.

Run the automated tests:

```bash
python -m unittest discover -s tests -v
```

## The model in plain language

The question is: **If Maruti has to pay yen in the future, how much could that payment cost in rupees, and how much uncertainty could a forward contract remove?**

The app follows five steps:

1. Set the size of an illustrative yen payment and the market assumptions.
2. Generate many possible JPY/INR paths using Monte Carlo simulation.
3. Convert each simulated rate into a rupee payment.
4. Repeat the payment calculation with a chosen percentage covered by a forward.
5. Compare the cost and risk before choosing a hedge strategy.

The user can change inputs in the sidebar; Streamlit recalculates the charts and metrics.

## Tab 1 — Company exposure and annual-report evidence

### Actual FY2025–26 balance-sheet currency information

The dashboard now uses the FY2025–26 annual-report table for JPY monetary assets and liabilities. The values are in ₹ million in the report.

| Item | 31 March 2026 | 31 March 2025 |
|---|---:|---:|
| JPY financial assets | ₹22,103m | ₹20,124m |
| Gross JPY financial liabilities | ₹11,176m | ₹8,810m |
| Forward contracts against liabilities | ₹(3,028)m | ₹(3,491)m |
| JPY liabilities after forwards | ₹8,148m | ₹5,319m |
| Net JPY asset position (assets less liabilities after forwards) | ₹13,955m | ₹14,805m |

At 31 March 2026, the disclosed JPY assets exceeded the remaining JPY liabilities by ₹13,955 million, or about ₹1,395.5 crore. The report also shows that a 10% strengthening of the rupee has a JPY-related profit/loss impact of about **−₹139.6 crore**, while a 10% weakening has an impact of about **+₹139.6 crore**.

**Why the app has a separate payable simulation:** a year-end balance-sheet snapshot and a future planned payment are different things. The simulation models an illustrative JPY payable to show how a forward works; the ¥10 billion default is a scenario input, not the company's actual net open currency position. Do not describe the scenario amount as a verified company exposure.

The report shows multiple currency positions (JPY, USD, euro and GBP). A USD or euro receipt does not automatically offset a yen payment. A natural hedge should match currency, amount and payment timing.

**Source:** [Maruti Suzuki official company reports](https://www.marutisuzuki.com/corporate/investors/company-reports), Annual Integrated Report FY2025–26, standalone financial statements' foreign-currency exposure and sensitivity tables. Always confirm the table, reporting scope and units before external presentation.

### The three risk types

- **Transaction risk:** a bill is due later and the exchange rate changes before payment.
- **Translation risk:** a foreign-currency balance changes in rupee value when accounts are prepared.
- **Economic risk:** currency changes future costs, prices and competitiveness.

This simulation focuses on transaction risk for a JPY payable. It does not model every risk the business faces.

## Tab 2 — Monte Carlo exchange-rate simulation

Monte Carlo creates many possible futures using random shocks. It does not choose one rate and claim that it will happen.

The model uses Geometric Brownian Motion (GBM) over one year with 252 daily steps:

```text
S(t+dt) = S(t) × exp(((r_INR - r_JPY) - 0.5 × volatility²) × dt
                       + volatility × sqrt(dt) × random shock)
```

- **Starting spot:** the exchange rate today, quoted as INR per JPY.
- **Volatility:** how widely the simulated rate is allowed to move.
- **Interest-rate difference:** affects the drift and the theoretical forward rate.
- **Random seed:** keeps results reproducible with the same code and inputs.
- **Number of paths:** more paths generally make the estimated averages and percentiles more stable, but do not guarantee a better forecast.

The theoretical one-year forward rate is estimated as:

```text
Forward rate = Spot rate × exp((Indian rate - Japanese rate) × years)
```

This is a simplified continuously compounded interest-rate-parity formula. A real bank quote may also reflect market conventions, credit terms, spreads, and transaction charges.

### Volatility source

The sidebar offers two choices:

- **Manual assumption:** 15% by default.
- **Estimate from historical CSV:** uses the bundled JPY/INR data, calculates consecutive log returns, and annualizes their sample standard deviation by multiplying by `sqrt(252)`.

The current bundled data produces an estimate around **15.47% annualized**. This is a historical estimate from the local CSV, not a live market feed. The user should check the data dates and quality before presenting it.

### Reading the charts

- **Simulated paths:** thin lines show possible journeys for the exchange rate; only a sample of paths is drawn so the chart remains readable.
- **Mean path:** average exchange rate at each daily step.
- **Terminal-rate histogram:** how frequently the simulation produced different one-year ending rates.
- **95th-percentile rate:** a threshold exceeded by about 5% of simulated ending rates.

A higher JPY/INR rate generally makes a JPY payable more expensive in rupees.

## Tab 3 — Forward hedge and cost comparison

A forward contract agrees today's exchange rate for a future currency exchange. The model assumes Maruti owes yen, so it buys yen forward and fixes the rate for the hedged amount.

For a JPY payable:

```text
Unhedged rupee cost = JPY exposure × future spot rate

Hedged rupee cost =
    (hedged JPY amount × forward rate)
    + (remaining JPY amount × future spot rate)
```

The amounts are converted to ₹ crore by dividing the rupee value by 10,000,000.

The hedge ratio sets the proportion covered by the forward. At 0%, everything is exposed to future spot. At 100%, the modeled payable is locked at the forward rate. At intermediate values, part is fixed and part is variable.

### Explicit execution cost

The sidebar includes an **assumed forward execution cost** in basis points of the forward rupee notional. The default is 5 basis points (0.05%), which is an illustrative assumption—not a quote from a bank. Replace it with an actual quote if one is available.

The forward rate already reflects the modeled interest-rate difference. Do not add the forward premium a second time as a fee. The separate execution cost represents extra assumed dealing costs such as spreads or charges.

### Risk metrics in the app

- **Average payment:** mean of all simulated rupee outflows.
- **Cash-flow standard deviation:** how much the payments vary across simulations.
- **95th-percentile payment:** a high-cost threshold; around 5% of simulated payments are above it.
- **95% expected shortfall:** average payment among outcomes at or above that 95th-percentile threshold.
- **99th-percentile payment:** a more extreme high-cost threshold.
- **Largest simulated payment:** the largest payment in this finite set of scenarios, not the worst possible future outcome.

The model now calls out standard-deviation reduction separately from variance reduction. With the simple linear model and a matched forward, a 50% hedge halves the standard deviation of the variable cash outflow; that is not the same as halving variance.

### Comparing five hedge choices

The app compares 0%, 25%, 50%, 75% and 100% hedges using the same simulated rates. For every choice it shows the assumed extra execution cost, average payment, 95th-percentile payment, expected shortfall, standard deviation, and sample maximum.

The **Simple decision helper** lets a student set a maximum acceptable 95th-percentile payment. It then identifies the lowest estimated execution cost among the five tested hedge choices that meets that limit. If none meets it, the app says so.

This is a learning aid—not an automatic treasury recommendation. A real decision requires the actual exposure, payment dates, company risk policy and dealer quotes.

## Tab 4 — Capital structure and interest-rate sensitivity

The FY2025–26 report indicates that Maruti had no long-term borrowings at year-end, may raise short-term rupee borrowings for temporary cash-flow mismatches, and has a large debt mutual-fund portfolio. The model does not invent a large loan to force an interest-rate swap recommendation.

The dashboard uses:
- Net worth of about ₹105,109.8 crore.
- Debt mutual-fund investments of about ₹71,723.8 crore, combining current and non-current investments.
- The report's stated sensitivity of about ₹717.2 crore for a 1% change in mutual-fund NAV.

### Interactive yield sensitivity

The user can change the yield shock (basis points) and an assumed modified duration. A basis point is 0.01 percentage points, so 100 basis points = 1 percentage point.

```text
Approximate change in fund value
    = - modified duration × change in yield × portfolio value
```

The estimate is negative when yields rise and positive when yields fall. The default duration of one year is illustrative because a single duration for the whole fund portfolio is not provided by this simple model. Use individual fund factsheets for a better estimate.

This is a first-order duration approximation, not a full portfolio revaluation. It does not prove that a swap is worthwhile.

## Rubric mapping — how the project addresses the assessment criteria

1. **Clarity of exposure analysis:** shows JPY assets, gross JPY liabilities, existing forwards, residual liabilities, net balance-sheet JPY position and the separate payable scenario.
2. **Soundness and transparency:** displays assumptions and formulas, supports reproducible simulation, provides an optional historical-volatility estimate, and includes unit tests for key calculations.
3. **Practicality and cost-awareness:** compares five forward hedge ratios, adds an editable assumed execution cost, shows the risk/cost trade-off, and offers a budget-limit decision helper.
4. **Quality of communication:** uses plain-language explanations, labelled KPI cards, rate paths, histograms, distribution charts, comparison tables and a clear decision guide.

## Assumptions and limitations to say in a presentation

- The ¥10 billion exposure is a chosen scenario, not a verified current net exposure.
- The model uses a lognormal GBM structure and can miss jumps or unusually large currency shocks.
- The forward is assumed to match the payment amount and maturity exactly.
- The execution cost is an assumption until a real quote is entered.
- It does not model every derivative detail, such as collateral, counterparty default, hedge accounting, basis risk or timing mismatch.
- The rate-sensitivity chart depends on the user-entered duration assumption.
- Historical disclosure figures should be verified against the cited annual-report table before being used outside the project.

## Project files

- `app.py` — Streamlit dashboard and charts.
- `risk_math.py` — testable financial formulas.
- `tests/test_risk_math.py` — unit tests for forward rates, simulation, hedging, cost and sensitivity.
- `jpy_inr_historical_data.csv` — historical observations used for optional volatility estimation.
- `requirements.txt` — Python dependencies.
