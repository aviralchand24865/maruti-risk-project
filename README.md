# FIN7003 Derivatives and Financial Risk Management
## Corporate FX Risk Simulation & Derivative Hedging Model (Interactive Tabbed Dashboard)
### Company: Maruti Suzuki India Limited (MSIL)
**Academic Context:** Group 4 | School of Management, BML Munjal University  
**Focus:** Foreign Exchange Exposure (JPY/INR) & Derivative Hedging under Ind AS 109 / RBI Framework  
**Primary Deliverables:** 
- `app.py` (Full interactive Streamlit Web Dashboard with 5 tabs and real-time sliders)
- `run_dashboard.bat` (One-click desktop launcher to open the dashboard in your default browser)
- `maruti_risk_dashboard.html` (Standalone interactive web dashboard; double-click to open in any browser with zero installation)
- `maruti_suzuki_risk_simulation.ipynb` (Fully executed, standalone Python simulation notebook with in-notebook tabbed widgets)
- `requirements.txt` (Python package dependencies)
- `README.md` (Project guide and presentation walkthrough)
- `jpy_inr_historical_data.csv` (Market historical exchange rate dataset)

---

## 1. Executive Summary & Exposure Justification

### Why Maruti Suzuki and the Japanese Yen (JPY)?
Maruti Suzuki India Limited (MSIL) is India's leading automobile manufacturer. Suzuki Motor Corporation (SMC), Japan, is MSIL's promoter holding a **58.19% equity stake**. Because of this operational and technological partnership, Maruti Suzuki has a structural reliance on Japan, creating significant **Foreign Exchange Transaction Exposure** denominated in the **Japanese Yen (JPY)**.

### Verified Official Company Disclosures (FY 2023–24)
*Source: Maruti Suzuki India Limited Annual Integrated Report FY 2023–24 (Approved by the Board of Directors on April 26, 2024)*  
*Official IR Portal: https://www.marutisuzuki.com/corporate/investors/company-reports*

1. **Direct Component & Raw Material Imports (Note 44 - CIF Value of Imports):**
   - Raw Materials & Components: **₹36,687 million (~₹3,669 Crore)**
   - Capital Goods (Machinery & Plant): **₹15,908 million (~₹1,591 Crore)**
   - Total CIF Imports: **₹52,595 million (~₹5,260 Crore)**
2. **Royalty Expenses to Parent Company (Note 29 & Note 34.2):**
   - Paid/Accrued to Suzuki Motor Corporation, Japan: **₹49,080 million (~₹4,908 Crore)**
3. **Balance Sheet Unhedged Monetary Liabilities (Note 33.2):**
   - Gross foreign currency liabilities in JPY: **₹5,668 million (Standalone)** / **₹9,065 million (Consolidated)**
   - Derivative forward hedges: **₹(2,181) million** (hedging ~38.5% of gross balance sheet liabilities)
   - Net unhedged balance sheet JPY liabilities: **₹3,487 million**

### Direction and Mechanism of Risk
* **Risk Direction:** Maruti Suzuki is **Short JPY / Long INR** on its operational payables and royalty commitments.
* **Impact of Market Movement:**
  * If the **Japanese Yen appreciates against INR** (higher INR per JPY), MSIL requires more Indian Rupees to pay for Japanese components and royalties. This directly drives up the Cost of Materials Consumed, squeezing Gross Margins, Operating EBITDA, and Net Profit.
  * If the **Japanese Yen depreciates against INR**, procurement costs decrease, expanding margins.
* **Natural Hedge Limitations:** While MSIL earns foreign exchange from exports (₹163,010 million in FY24), export revenues are primarily invoiced in **USD and EUR**, while the heavy component import and royalty costs are in **JPY**, creating an active currency mismatch.

---

## 2. Interactive Dashboard Format & Tabs Overview

The dashboard is structured into **4 focused tabs**:

### 📊 Tab 1: Executive Overview & MSIL Disclosures
- Complete corporate structure (58.19% Suzuki Motor Corporation stake).
- Summary of verified disclosures from Notes 44, 29, 34, and 33.
- Exposure direction (Short JPY / Long INR) and why vehicle exports in USD/EUR do not offset JPY import liabilities.
- Breakdown of Transaction, Translation, and Economic exposure.

### 🎲 Tab 2: Monte Carlo Exchange Rate Simulation
- Geometric Brownian Motion (GBM) simulation engine (1,000 paths over 252 trading days).
- Drift derived from Covered Interest Rate Parity (CIRP) using Indian and Japanese sovereign rates (6.50% vs 0.25%).
- Volatility calibrated to 15.0% based on 3-year daily historical market returns.
- Interactive Plotly chart showing price trajectories, Mean Path, Initial Spot $S_0$, Forward Rate $F$, and 95th percentile adverse rate.
- Lognormal terminal distribution histogram with density curve.

### 🛡️ Tab 3: Hedging Analysis & Payoff Comparison
- 1-Year OTC Currency Forward Contract (Long JPY / Short INR).
- Interactive Hedge Ratio slider (0% to 100%).
- Key metric cards: Expected Outflow (Mean), Cash Flow Volatility (Std Dev), 95% Value at Risk (VaR), and Worst-Case Outflow.
- Comparative distribution histograms (Unhedged vs Hedged).
- Cumulative Distribution Function (CDF) showing tail-risk compression.
- Comprehensive statistical performance matrix.

### 🏦 Tab 4: Interest Rate Sensitivity & Capital Structure
- Evaluates Maruti Suzuki's debt profile from Note 33.1 & 33.3:
  - Total Borrowings: Only **₹331 million (₹33.1 Crore)**.
  - Shareholders' Equity: **₹83,982 Crore**.
  - Surplus Debt Mutual Funds: **₹53,320 Crore** (Net Cash Surplus).
- Interactive basis-points sensitivity slider: A 100 bps rate increase changes debt service by just **₹0.33 Crore** (0.002% of profit). In contrast, a 100 bps shift on treasury investments impacts yield by **₹533.2 Crore**.
- Explains why liability interest rate swaps are economically unjustified, addressing the assignment's limitation requirement.

---

## 3. How to Launch & Run the Dashboard

You have **3 convenient ways** to run the model:

### Method 1: One-Click Desktop Launcher (Streamlit App)
Double-click [**`run_dashboard.bat`**](file:///c:/Users/Aviral/Downloads/derivtive%20project/run_dashboard.bat).  
It will automatically launch the Streamlit server and open the interactive dashboard in your default browser at `http://localhost:8501`.

*(Alternatively, run from terminal:* `streamlit run app.py`*)*

### Method 2: Standalone Interactive HTML Dashboard (Zero Installation)
Double-click [**`maruti_risk_dashboard.html`**](file:///c:/Users/Aviral/Downloads/derivtive%20project/maruti_risk_dashboard.html).  
It opens immediately in Google Chrome, Microsoft Edge, or Safari with tabs, interactive sliders, dynamic charts, and calculations running live inside the browser.

### Method 3: Jupyter Notebook with Embedded Tabbed Widget
Open [**`maruti_suzuki_risk_simulation.ipynb`**](file:///c:/Users/Aviral/Downloads/derivtive%20project/maruti_suzuki_risk_simulation.ipynb) in VS Code or Jupyter Notebook.  
Section I contains an interactive tabbed widget (`ipywidgets.Tab`) that allows you to click between tabs directly inside the notebook.

---

## 4. Key Findings & Baseline Results Summary

*Baseline: JPY 10.0 Billion Exposure | Spot S0 = ₹0.5500 / JPY | 1-Yr Forward F = ₹0.5855 / JPY | Volatility = 15.0% | Hedge Ratio = 50%*

| Risk Metric | Unhedged (0% Hedged) | Hedged (50% Forward) | Risk Reduction / Impact | Managerial Significance |
| :--- | :---: | :---: | :---: | :--- |
| **Initial Spot Value** | ₹550.00 Cr | ₹550.00 Cr | Baseline | Initial valuation at $S_0$ |
| **Expected Outflow (Mean)** | **₹585.72 Cr** | **₹585.59 Cr** | **₹0.13 Cr (Neutral)** | CIRP forward pricing does not penalize expected returns |
| **Cash Flow Volatility ($\sigma$)** | **₹89.21 Cr** | **₹44.61 Cr** | **-50.0%** | Variance is cut exactly in half |
| **95% Value at Risk (VaR 95%)** | **₹743.70 Cr** | **₹664.59 Cr** | **Savings of ₹79.11 Cr** | Major downside tail-risk protection |
| **Cash Flow at Risk (Tail Spike)** | ₹157.98 Cr | ₹78.99 Cr | -50.0% | Compresses unexpected cash spike above mean |
| **99% Value at Risk (VaR 99%)** | ₹818.06 Cr | ₹701.78 Cr | **Savings of ₹116.29 Cr** | Defense against 1-in-100 year currency shocks |
| **Worst-Case Simulated Outflow** | **₹892.45 Cr** | **₹738.96 Cr** | **Savings of ₹153.49 Cr** | Eliminates severe margin compression |

---

## 5. File Manifest
* `app.py`: Full interactive Streamlit Web Dashboard with 4 tabs and real-time sliders.
* `run_dashboard.bat`: One-click Windows batch script to launch the dashboard.
* `maruti_risk_dashboard.html`: Standalone single-file interactive HTML dashboard with tabs, sliders, and canvas charts.
* `maruti_suzuki_risk_simulation.ipynb`: Complete executable Jupyter Notebook with all calculations, code cells, tables, embedded plots, and in-notebook tabbed widgets.
* `requirements.txt`: Python package requirements.
* `README.md`: Complete documentation and presentation guide.
* `jpy_inr_historical_data.csv`: Daily historical exchange rate data for JPY/INR over 3 years.
* `MSIL_IR_2023-24.pdf`: Downloaded official Maruti Suzuki Annual Integrated Report FY 2023–24.
