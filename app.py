"""
========================================================================================
FIN7003: Derivatives and Financial Risk Management
Maruti Suzuki India Limited (MSIL) - Group 4 | BML Munjal University
Interactive Risk Simulation & Derivative Hedging Dashboard
========================================================================================
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --------------------------------------------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------------------------------------------
st.set_page_config(
    page_title="Maruti Suzuki FX Risk Dashboard | FIN7003",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for polished corporate financial appearance
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.2rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 14px 18px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-val {
        font-size: 1.5rem;
        font-weight: 700;
        color: #0F172A;
    }
    .metric-lbl {
        font-size: 0.85rem;
        color: #64748B;
        text-transform: uppercase;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        white-space: pre-wrap;
        background-color: #F1F5F9;
        border-radius: 6px 6px 0px 0px;
        padding: 10px 16px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E3A8A !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------------------
# HEADER & SIDEBAR CONTROLS
# --------------------------------------------------------------------------------------
st.markdown('<div class="main-title">🚗 Maruti Suzuki India Limited (MSIL)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">FIN7003 Derivatives and Financial Risk Management | <b>Group 4</b>, BML Munjal University<br><i>Foreign Exchange Risk Simulation (JPY/INR) & Derivative Hedging Model</i></div>', unsafe_allow_html=True)

st.sidebar.header("⚙️ Simulation & Model Inputs")
st.sidebar.markdown("Modify any parameter to see instant live updates across all tabs.")

# Sidebar Parameters
exposure_jpy_bn = st.sidebar.number_input(
    "Foreign Currency Exposure (Billion JPY)",
    min_value=1.0,
    max_value=100.0,
    value=10.0,
    step=1.0,
    help="Default 10.0 Billion JPY reflects ~₹550-600 Crore procurement tranche or balance sheet payables."
)
exposure_jpy = exposure_jpy_bn * 1_000_000_000

s0_spot_rate = st.sidebar.number_input(
    "Starting Spot Rate (INR per 1 JPY)",
    min_value=0.40,
    max_value=0.90,
    value=0.5500,
    step=0.0050,
    format="%.4f",
    help="₹0.5500 / JPY is equivalent to ₹55.00 per 100 JPY."
)

hedge_ratio = st.sidebar.slider(
    "Forward Hedge Ratio (%)",
    min_value=0,
    max_value=100,
    value=50,
    step=5,
    help="Percentage of JPY exposure hedged via 1-Year Currency Forward Contract."
) / 100.0

ann_volatility = st.sidebar.slider(
    "Annualized Volatility (σ)",
    min_value=0.05,
    max_value=0.30,
    value=0.1500,
    step=0.0100,
    format="%.2f",
    help="Historical annualized volatility calibrated to 3-year daily JPY/INR returns (~15.0%)."
)

with st.sidebar.expander("🛠️ Advanced Financial Benchmarks"):
    r_inr = st.number_input("Domestic Risk-Free Rate (India, r_INR)", value=0.0650, step=0.0025, format="%.4f")
    r_jpy = st.number_input("Foreign Risk-Free Rate (Japan, r_JPY)", value=0.0025, step=0.0005, format="%.4f")
    num_paths = st.selectbox("Monte Carlo Paths", options=[500, 1000, 2000], index=1)
    seed = st.number_input("Random Seed (for reproducibility)", value=42, step=1)
    horizon_years = 1.0
    trading_days = 252

# --------------------------------------------------------------------------------------
# MATHEMATICAL ENGINE (CIRP & MONTE CARLO GBM)
# --------------------------------------------------------------------------------------
INR_CRORE = 10_000_000

# 1. Forward Rate via Covered Interest Rate Parity
forward_rate = s0_spot_rate * np.exp((r_inr - r_jpy) * horizon_years)
forward_premium_pct = ((forward_rate / s0_spot_rate) - 1.0) * 100.0
initial_spot_value_cr = (exposure_jpy * s0_spot_rate) / INR_CRORE

# 2. Monte Carlo Simulation Engine (GBM)
np.random.seed(int(seed))
dt = horizon_years / trading_days
drift_dt = ((r_inr - r_jpy) - 0.5 * (ann_volatility ** 2)) * dt
diffusion_dt = ann_volatility * np.sqrt(dt)

simulated_rates = np.zeros((trading_days + 1, num_paths))
simulated_rates[0, :] = s0_spot_rate

for step in range(1, trading_days + 1):
    z = np.random.standard_normal(num_paths)
    simulated_rates[step, :] = simulated_rates[step - 1, :] * np.exp(drift_dt + diffusion_dt * z)

terminal_rates = simulated_rates[-1, :]

# 3. Cash Outflow Calculations (INR Crores)
# Unhedged Outflow
unhedged_outflow_cr = (exposure_jpy * terminal_rates) / INR_CRORE

# Hedged Outflow
hedged_jpy = exposure_jpy * hedge_ratio
unhedged_jpy = exposure_jpy * (1.0 - hedge_ratio)
forward_locked_cost_cr = (hedged_jpy * forward_rate) / INR_CRORE
spot_variable_cost_cr = (unhedged_jpy * terminal_rates) / INR_CRORE
hedged_outflow_cr = forward_locked_cost_cr + spot_variable_cost_cr

# Statistical Metrics
mean_unh = np.mean(unhedged_outflow_cr)
std_unh = np.std(unhedged_outflow_cr)
var95_unh = np.percentile(unhedged_outflow_cr, 95)
var99_unh = np.percentile(unhedged_outflow_cr, 99)
max_unh = np.max(unhedged_outflow_cr)
cfar95_unh = var95_unh - mean_unh

mean_hed = np.mean(hedged_outflow_cr)
std_hed = np.std(hedged_outflow_cr)
var95_hed = np.percentile(hedged_outflow_cr, 95)
var99_hed = np.percentile(hedged_outflow_cr, 99)
max_hed = np.max(hedged_outflow_cr)
cfar95_hed = var95_hed - mean_hed

vol_reduction_pct = (1.0 - (std_hed / std_unh)) * 100.0 if std_unh > 0 else 0.0
var95_savings_cr = var95_unh - var95_hed
worst_case_savings_cr = max_unh - max_hed

# --------------------------------------------------------------------------------------
# TABS SETUP
# --------------------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Executive Summary & Disclosures",
    "🎲 Monte Carlo Exchange Rate Simulation",
    "🛡️ Hedging Analysis & Payoff Comparison",
    "🏦 Interest Rate Sensitivity & Capital Structure"
])

# ======================================================================================
# TAB 1: EXECUTIVE SUMMARY & DISCLOSURES
# ======================================================================================
with tab1:
    st.subheader("1. Company Background & Foreign Exchange Risk Profile")
    st.markdown("""
    **Maruti Suzuki India Limited (MSIL)** is India’s largest passenger vehicle manufacturer. Suzuki Motor Corporation (SMC), Japan, 
    serves as the holding company with a **58.19% equity stake**. This corporate relationship results in major, ongoing commercial transactions denominated in the **Japanese Yen (JPY)**.
    """)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Parent Equity Holding", "58.19%", "Suzuki Motor Corp (Japan)")
    with col2:
        st.metric("Annual Direct CIF Imports", "₹5,260 Cr", "Raw Materials & Machinery (Note 44)")
    with col3:
        st.metric("Annual Royalty to SMC", "₹4,908 Cr", "Technical Fees (Note 29/34)")
    with col4:
        st.metric("Net Debt Position", "-₹423 Cr", "Virtually Debt-Free (Net Cash)")

    st.markdown("---")
    st.subheader("2. Verified Official Disclosures (Annual Integrated Report FY 2023–24)")
    
    disc_df = pd.DataFrame([
        {
            "Financial Statement Schedule": "Note 44: CIF Value of Imports",
            "Item": "Raw Materials, Components & Capital Goods",
            "Reported Value (FY 2023-24)": "₹52,595 Million (~₹5,260 Cr)",
            "Currency / Exposure Details": "JPY, USD, EUR (JPY carries primary import weight for engine/transmission components)"
        },
        {
            "Financial Statement Schedule": "Note 29 & Note 34.2: Related Party Expenses",
            "Item": "Technical Royalty to Suzuki Motor Corp (Japan)",
            "Reported Value (FY 2023-24)": "₹49,080 Million (~₹4,908 Cr)",
            "Currency / Exposure Details": "JPY (Committed annual technical collaboration outflow)"
        },
        {
            "Financial Statement Schedule": "Note 33.2: Foreign Currency Risk Exposure",
            "Item": "Gross Foreign Currency Payables (Standalone)",
            "Reported Value (FY 2023-24)": "₹5,668 Million (JPY Payables)",
            "Currency / Exposure Details": "JPY 10.28 Billion gross payables at closing spot rate"
        },
        {
            "Financial Statement Schedule": "Note 33.2: Derivative Contracts Outstanding",
            "Item": "Forward Exchange Contracts (Hedged Payables)",
            "Reported Value (FY 2023-24)": "₹(2,181) Million (in JPY)",
            "Currency / Exposure Details": "MSIL hedged ~38.5% of gross JPY liabilities as of March 31, 2024"
        },
        {
            "Financial Statement Schedule": "Note 33.2: Net Unhedged Payables",
            "Item": "Net Open Liability Exposure (Standalone)",
            "Reported Value (FY 2023-24)": "₹3,487 Million (JPY Net Open)",
            "Currency / Exposure Details": "₹5,034 Million on consolidated group basis"
        }
    ])
    st.table(disc_df)

    st.markdown("---")
    st.subheader("3. Direction and Nature of Risk")
    c_a, c_b, c_c = st.columns(3)
    with c_a:
        st.info("""
        **Risk Direction: Short JPY / Long INR**  
        MSIL has payment obligations in JPY.  
        * **JPY Appreciation (Upward Spike):** MSIL requires more INR to settle imports, eroding gross margins and operating EBITDA.  
        * **JPY Depreciation:** Procurement costs decrease, benefiting profitability.
        """)
    with c_b:
        st.warning("""
        **Natural Hedge Limitations**  
        MSIL earned ₹163,010 Million from vehicle exports in FY24. However, export sales are billed in **USD and EUR** (Africa, Europe, Middle East), while import commitments are concentrated in **JPY**, leaving an active currency mismatch.
        """)
    with c_c:
        st.success("""
        **Exposure Classification**  
        * **Transaction Exposure:** Contractual JPY import invoices & royalty payments due within 1 year (Subject of this simulation).  
        * **Translation Exposure:** Balance sheet revaluation under Ind AS 21.  
        * **Economic Exposure:** Long-term cost competitiveness vs domestic peers.
        """)

# ======================================================================================
# TAB 2: MONTE CARLO SIMULATION
# ======================================================================================
with tab2:
    st.subheader("1-Year Monte Carlo Exchange Rate Simulation (GBM Engine)")
    st.markdown(f"""
    Simulating **{num_paths:,} independent price trajectories** over **252 trading days** (1-Year Horizon) using **Geometric Brownian Motion (GBM)** under Covered Interest Rate Parity drift:
    $$S_{{t+\\Delta t}} = S_t \\exp\\left( \\left((r_{{\\text{{INR}}}} - r_{{\\text{{JPY}}}}) - \\frac{1}{2}\\sigma^2\\right)\\Delta t + \\sigma\\sqrt{{\\Delta t}} Z_t \\right)$$
    """)

    # Top metrics
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Starting Spot Rate (S0)", f"₹{s0_spot_rate:.4f} / JPY", f"₹{s0_spot_rate*100:.2f} per 100 JPY")
    m2.metric("Theoretical Forward (F)", f"₹{forward_rate:.4f} / JPY", f"+{forward_premium_pct:.2f}% CIRP Premium")
    m3.metric("Simulated Mean (E[S_T])", f"₹{np.mean(terminal_rates):.4f} / JPY", f"Bias: {((np.mean(terminal_rates)/forward_rate)-1)*100:.2f}%")
    m4.metric("95% Adverse Tail Rate", f"₹{np.percentile(terminal_rates, 95):.4f} / JPY", "Top 5% JPY Spike")
    m5.metric("Simulated Max Rate", f"₹{np.max(terminal_rates):.4f} / JPY", "Worst-case shock")

    # Plotly Visualisation of Paths & Distribution
    col_p1, col_p2 = st.columns([3, 2])

    with col_p1:
        fig_paths = go.Figure()
        time_axis = np.arange(trading_days + 1)
        
        # Plot 40 sample paths
        for i in range(min(40, num_paths)):
            fig_paths.add_trace(go.Scatter(
                x=time_axis,
                y=simulated_rates[:, i],
                mode='lines',
                line=dict(width=1, color='rgba(30, 58, 138, 0.12)'),
                showlegend=False,
                hoverinfo='skip'
            ))
        
        # Mean path
        mean_path = np.mean(simulated_rates, axis=1)
        fig_paths.add_trace(go.Scatter(
            x=time_axis,
            y=mean_path,
            mode='lines',
            line=dict(color='#DC2626', width=3),
            name=f'Mean Path (Final: ₹{mean_path[-1]:.4f})'
        ))

        # Benchmarks
        fig_paths.add_trace(go.Scatter(
            x=[0, trading_days],
            y=[s0_spot_rate, s0_spot_rate],
            mode='lines',
            line=dict(color='#16A34A', width=2, dash='dash'),
            name=f'Initial Spot (S0 = ₹{s0_spot_rate:.4f})'
        ))
        fig_paths.add_trace(go.Scatter(
            x=[0, trading_days],
            y=[forward_rate, forward_rate],
            mode='lines',
            line=dict(color='#EA580C', width=2, dash='dashdot'),
            name=f'1-Yr Forward (F = ₹{forward_rate:.4f})'
        ))
        fig_paths.add_trace(go.Scatter(
            x=[0, trading_days],
            y=[np.percentile(terminal_rates, 95), np.percentile(terminal_rates, 95)],
            mode='lines',
            line=dict(color='#9333EA', width=2, dash='dot'),
            name=f'95th Percentile Adverse (₹{np.percentile(terminal_rates, 95):.4f})'
        ))

        fig_paths.update_layout(
            title="<b>Simulated JPY/INR Trajectories (1-Year Horizon)</b>",
            xaxis_title="Trading Days",
            yaxis_title="INR per 1 JPY",
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            margin=dict(l=40, r=40, t=50, b=80),
            height=460
        )
        st.plotly_chart(fig_paths, use_container_width=True)

    with col_p2:
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Histogram(
            x=terminal_rates,
            nbinsx=35,
            marker_color='#2563EB',
            opacity=0.7,
            name='Terminal Rate S_T'
        ))
        fig_hist.add_vline(x=s0_spot_rate, line_width=2, line_dash="dash", line_color="#16A34A", annotation_text="Spot S0", annotation_position="top left")
        fig_hist.add_vline(x=forward_rate, line_width=2, line_dash="dashdot", line_color="#EA580C", annotation_text="Forward F", annotation_position="top right")
        fig_hist.add_vline(x=np.percentile(terminal_rates, 95), line_width=2, line_dash="dot", line_color="#9333EA", annotation_text="95% VaR", annotation_position="top right")

        fig_hist.update_layout(
            title="<b>Terminal JPY/INR Distribution at T = 1 Year</b>",
            xaxis_title="Exchange Rate (INR / JPY)",
            yaxis_title="Frequency",
            margin=dict(l=40, r=40, t=50, b=80),
            height=460
        )
        st.plotly_chart(fig_hist, use_container_width=True)

# ======================================================================================
# TAB 3: HEDGING ANALYSIS & PAYOFF COMPARISON
# ======================================================================================
with tab3:
    st.subheader(f"Derivative Hedging Strategy: {hedge_ratio:.0%} Forward Contract Hedge")
    st.markdown(f"""
    Maruti Suzuki enters into a **1-Year Currency Forward Contract** (Long JPY / Short INR) at $F = ₹{forward_rate:.4f}$ / JPY.
    * **Hedged Portion:** JPY {hedged_jpy:,.0f} ({hedge_ratio:.0%}) locked at ₹{forward_locked_cost_cr:,.2f} Crore.
    * **Unhedged Portion:** JPY {unhedged_jpy:,.0f} ({(1-hedge_ratio):.0%}) settled at variable spot $S_T$.
    """)

    # Metric Cards
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Expected Outflow (Mean)", f"₹{mean_hed:,.2f} Cr", f"vs Unhedged ₹{mean_unh:,.2f} Cr (Neutral)")
    with k2:
        st.metric("Cash Flow Volatility (StdDev)", f"₹{std_hed:,.2f} Cr", f"-{vol_reduction_pct:.1f}% Variance Reduction", delta_color="inverse")
    with k3:
        st.metric("95% Value at Risk (VaR Outflow)", f"₹{var95_hed:,.2f} Cr", f"Savings: ₹{var95_savings_cr:,.2f} Cr", delta_color="inverse")
    with k4:
        st.metric("Worst-Case Cash Outflow", f"₹{max_hed:,.2f} Cr", f"Savings: ₹{worst_case_savings_cr:,.2f} Cr", delta_color="inverse")

    st.markdown("---")

    col_h1, col_h2 = st.columns(2)

    with col_h1:
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Histogram(
            x=unhedged_outflow_cr,
            nbinsx=40,
            marker_color='#DC2626',
            opacity=0.5,
            name=f'Unhedged (σ = ₹{std_unh:.1f} Cr)'
        ))
        fig_comp.add_trace(go.Histogram(
            x=hedged_outflow_cr,
            nbinsx=40,
            marker_color='#16A34A',
            opacity=0.6,
            name=f'Hedged {hedge_ratio:.0%} (σ = ₹{std_hed:.1f} Cr)'
        ))
        fig_comp.add_vline(x=var95_unh, line_width=2, line_dash="dash", line_color="#DC2626", annotation_text="Unhedged 95% VaR")
        fig_comp.add_vline(x=var95_hed, line_width=2, line_dash="dash", line_color="#16A34A", annotation_text=f"Hedged 95% VaR")

        fig_comp.update_layout(
            title="<b>Cash Outflow Distribution: Unhedged vs Hedged</b>",
            xaxis_title="Total INR Cash Outflow (₹ Crore)",
            yaxis_title="Path Count",
            barmode='overlay',
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            margin=dict(l=40, r=40, t=50, b=80),
            height=440
        )
        st.plotly_chart(fig_comp, use_container_width=True)

    with col_h2:
        sorted_unh = np.sort(unhedged_outflow_cr)
        sorted_hed = np.sort(hedged_outflow_cr)
        cdf_prob = np.linspace(0, 1, num_paths)

        fig_cdf = go.Figure()
        fig_cdf.add_trace(go.Scatter(
            x=sorted_unh,
            y=cdf_prob,
            mode='lines',
            line=dict(color='#DC2626', width=2.5),
            name='Unhedged Cumulative Probability'
        ))
        fig_cdf.add_trace(go.Scatter(
            x=sorted_hed,
            y=cdf_prob,
            mode='lines',
            line=dict(color='#16A34A', width=2.5),
            name=f'Hedged ({hedge_ratio:.0%}) Cumulative Probability'
        ))
        fig_cdf.add_hline(y=0.95, line_width=1.5, line_dash="dot", line_color="#4B5563", annotation_text="95% Confidence Threshold")

        fig_cdf.update_layout(
            title="<b>Cumulative Distribution Function (CDF) & Tail Protection</b>",
            xaxis_title="Total INR Cash Outflow (₹ Crore)",
            yaxis_title="Cumulative Probability",
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            margin=dict(l=40, r=40, t=50, b=80),
            height=440
        )
        st.plotly_chart(fig_cdf, use_container_width=True)

    # Detailed Comparison Table
    st.subheader("Statistical Risk Reduction Matrix")
    comp_table = pd.DataFrame([
        {
            "Performance Metric": "Expected Outflow (Mean)",
            "Unhedged (0% Hedged)": f"₹{mean_unh:,.2f} Cr",
            f"Hedged ({hedge_ratio:.0%} Forward)": f"₹{mean_hed:,.2f} Cr",
            "Variance / Impact": f"₹{(mean_hed - mean_unh):,.2f} Cr",
            "Managerial Takeaway": "CIRP forward pricing is expected-cost neutral"
        },
        {
            "Performance Metric": "Cash Flow Volatility (Std Dev)",
            "Unhedged (0% Hedged)": f"₹{std_unh:,.2f} Cr",
            f"Hedged ({hedge_ratio:.0%} Forward)": f"₹{std_hed:,.2f} Cr",
            "Variance / Impact": f"-{vol_reduction_pct:.1f}%",
            "Managerial Takeaway": f"Directly cuts cash flow volatility by {hedge_ratio:.0%}"
        },
        {
            "Performance Metric": "95% Value at Risk (VaR 95%)",
            "Unhedged (0% Hedged)": f"₹{var95_unh:,.2f} Cr",
            f"Hedged ({hedge_ratio:.0%} Forward)": f"₹{var95_hed:,.2f} Cr",
            "Variance / Impact": f"Savings of ₹{var95_savings_cr:,.2f} Cr",
            "Managerial Takeaway": "Protects operating margins in 95 out of 100 scenarios"
        },
        {
            "Performance Metric": "Cash Flow at Risk (95% Tail Spike)",
            "Unhedged (0% Hedged)": f"₹{cfar95_unh:,.2f} Cr",
            f"Hedged ({hedge_ratio:.0%} Forward)": f"₹{cfar95_hed:,.2f} Cr",
            "Variance / Impact": f"-{(1 - cfar95_hed/cfar95_unh)*100:.1f}%",
            "Managerial Takeaway": "Compresses unexpected budget spikes above expected cost"
        },
        {
            "Performance Metric": "Worst-Case Simulated Outflow",
            "Unhedged (0% Hedged)": f"₹{max_unh:,.2f} Cr",
            f"Hedged ({hedge_ratio:.0%} Forward)": f"₹{max_hed:,.2f} Cr",
            "Variance / Impact": f"Savings of ₹{worst_case_savings_cr:,.2f} Cr",
            "Managerial Takeaway": "Shields the firm against catastrophic currency collapse"
        }
    ])
    st.table(comp_table)

# ======================================================================================
# TAB 4: INTEREST RATE SENSITIVITY & CAPITAL STRUCTURE
# ======================================================================================
with tab4:
    st.subheader("1. Maruti Suzuki Capital Structure & Debt Assessment (Note 33.1 & 33.3)")
    st.markdown("""
    A core requirement of financial risk analysis is evaluating whether interest rate hedging is necessary. 
    Maruti Suzuki's audited financial disclosures demonstrate an extraordinary capital structure:
    """)

    ci1, ci2, ci3, ci4 = st.columns(4)
    with ci1:
        st.metric("Total Debt Borrowings", "₹33.1 Cr", "₹331 Million (Note 33.1)")
    with ci2:
        st.metric("Total Equity Base", "₹83,982 Cr", "₹839,820 Million")
    with ci3:
        st.metric("Debt-to-Equity Ratio", "-0.005", "Negative Net Debt")
    with ci4:
        st.metric("Debt Mutual Fund Assets", "₹53,320 Cr", "₹533,203 Million (Treasury)")

    st.markdown("---")
    st.subheader("2. Empirical Interest Rate Sensitivity Calculation")

    borrowings_m = 331.0
    debt_mf_m = 533203.0
    pat_m = 132094.0

    bps_shift = st.slider("Select Interest Rate Shift (basis points)", min_value=25, max_value=250, value=100, step=25)
    shift_dec = bps_shift / 10000.0

    debt_impact_cr = (borrowings_m * shift_dec) / 10.0
    treasury_impact_cr = (debt_mf_m * shift_dec) / 10.0
    debt_pat_pct = (borrowings_m * shift_dec / pat_m) * 100.0
    treasury_pat_pct = (debt_mf_m * shift_dec / pat_m) * 100.0

    ir_comp = pd.DataFrame([
        {
            "Balance Sheet Item": "Borrowings (Liability Debt Service)",
            "Disclosed Value (FY24)": f"₹{borrowings_m:,.1f} M (₹{borrowings_m/10:,.2f} Cr)",
            f"{bps_shift} bps Rate Shift Impact": f"₹{debt_impact_cr:,.2f} Crore / year",
            "% of Net Profit (PAT)": f"{debt_pat_pct:.4f}%",
            "Hedging Conclusion": "Negligible liability risk. Interest Rate Swaps (IRS) are economically unjustified."
        },
        {
            "Balance Sheet Item": "Debt Mutual Fund Investments (Treasury Assets)",
            "Disclosed Value (FY24)": f"₹{debt_mf_m:,.1f} M (₹{debt_mf_m/10:,.2f} Cr)",
            f"{bps_shift} bps Rate Shift Impact": f"₹{treasury_impact_cr:,.2f} Crore / year",
            "% of Net Profit (PAT)": f"{treasury_pat_pct:.2f}%",
            "Hedging Conclusion": "Significant treasury asset yield sensitivity (disclosed in Note 33.2)."
        }
    ])
    st.table(ir_comp)

    st.info("""
    **Academic Limitation & Project Conclusion:**  
    Maruti Suzuki is a **net cash surplus company**. Inventing artificial debt or proposing liability interest rate swaps would contradict official company facts. 
    As required by the assignment guidelines, we report this structural reality directly rather than manufacturing artificial debt exposure.
    """)


