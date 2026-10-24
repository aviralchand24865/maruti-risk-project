"""
========================================================================================
FIN7003: Derivatives and Financial Risk Management
Maruti Suzuki India Limited (MSIL) - Group 4 | BML Munjal University
Interactive Risk Simulation & Derivative Hedging Dashboard
========================================================================================
"""

from pathlib import Path

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from risk_math import (
    approximate_duration_price_change_cr,
    calculate_cash_outflows,
    calculate_forward_execution_cost_cr,
    calculate_forward_rate,
    estimate_annualized_volatility,
    simulate_gbm,
    summarize_outflows,
)

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
    help="Illustrative scenario exposure for this simulation. It is not Maruti Suzuki's actual net open position in the latest annual report."
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
    help="Percentage of the modeled JPY payable whose rupee rate is fixed using a one-year forward."
) / 100.0

forward_cost_bps = st.sidebar.slider(
    "Assumed Forward Execution Cost (basis points)",
    min_value=0,
    max_value=50,
    value=5,
    step=1,
    help="Illustrative extra execution cost, measured in basis points of hedged rupee notional. This is not a live bank quote."
)
st.sidebar.caption(
    "A basis point is 0.01%. The forward rate already includes the modeled interest-rate differential; "
    "this input is an additional assumed execution cost. Replace it with a dealer quote when available."
)

manual_ann_volatility = st.sidebar.slider(
    "Manual Annualized Volatility (σ)",
    min_value=0.05,
    max_value=0.30,
    value=0.1500,
    step=0.0100,
    format="%.2f",
    help="Manual assumption used when Manual Assumption is selected below."
)

historical_csv = Path(__file__).with_name("jpy_inr_historical_data.csv")
historical_volatility, historical_return_count, historical_vol_error = estimate_annualized_volatility(
    historical_csv, trading_days=252
)
volatility_source = st.sidebar.radio(
    "Volatility source",
    options=["Manual assumption", "Estimate from historical CSV"],
    index=0,
    help="Historical mode estimates annualized volatility from consecutive log returns in the bundled JPY/INR data."
)

if volatility_source == "Estimate from historical CSV" and historical_volatility is not None:
    ann_volatility = historical_volatility
    st.sidebar.caption(
        f"Active volatility: {ann_volatility:.2%}, estimated from "
        f"{historical_return_count:,} historical log returns."
    )
elif volatility_source == "Estimate from historical CSV":
    ann_volatility = manual_ann_volatility
    st.sidebar.warning(
        f"{historical_vol_error or 'Historical volatility is unavailable.'} "
        "Using the manual assumption instead."
    )
else:
    ann_volatility = manual_ann_volatility
    if historical_volatility is not None:
        st.sidebar.caption(
            f"Historical estimate for comparison: {historical_volatility:.2%} "
            f"({historical_return_count:,} log returns)."
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
forward_rate = calculate_forward_rate(s0_spot_rate, r_inr, r_jpy, horizon_years)
forward_premium_pct = ((forward_rate / s0_spot_rate) - 1.0) * 100.0
initial_spot_value_cr = (exposure_jpy * s0_spot_rate) / INR_CRORE

# 2. Monte Carlo Simulation Engine (GBM)
simulated_rates = simulate_gbm(
    spot_rate=s0_spot_rate,
    domestic_rate=r_inr,
    foreign_rate=r_jpy,
    volatility=ann_volatility,
    horizon_years=horizon_years,
    trading_days=trading_days,
    num_paths=num_paths,
    seed=int(seed),
)
terminal_rates = simulated_rates[-1, :]

# 3. Cash Outflow Calculations (INR Crores)
hedged_jpy = exposure_jpy * hedge_ratio
unhedged_jpy = exposure_jpy * (1.0 - hedge_ratio)
(
    unhedged_outflow_cr,
    hedged_outflow_cr,
    forward_locked_cost_cr,
    spot_variable_cost_cr,
) = calculate_cash_outflows(
    exposure_jpy=exposure_jpy,
    terminal_rates=terminal_rates,
    forward_rate=forward_rate,
    hedge_ratio=hedge_ratio,
)
forward_execution_cost_cr = calculate_forward_execution_cost_cr(
    exposure_jpy=exposure_jpy,
    hedge_ratio=hedge_ratio,
    forward_rate=forward_rate,
    cost_bps=forward_cost_bps,
)
hedged_outflow_cr = hedged_outflow_cr + forward_execution_cost_cr

# Prepare five hedge choices using the same simulated exchange rates for a fair comparison.
hedge_scenarios = []
for candidate_ratio in [0.0, 0.25, 0.50, 0.75, 1.0]:
    _, candidate_base_outflow, _, _ = calculate_cash_outflows(
        exposure_jpy=exposure_jpy,
        terminal_rates=terminal_rates,
        forward_rate=forward_rate,
        hedge_ratio=candidate_ratio,
    )
    candidate_cost_cr = calculate_forward_execution_cost_cr(
        exposure_jpy=exposure_jpy,
        hedge_ratio=candidate_ratio,
        forward_rate=forward_rate,
        cost_bps=forward_cost_bps,
    )
    candidate_outflow = candidate_base_outflow + candidate_cost_cr
    candidate_stats = summarize_outflows(candidate_outflow)
    hedge_scenarios.append({
        "ratio": candidate_ratio,
        "cost_cr": candidate_cost_cr,
        "mean_cr": candidate_stats["mean"],
        "std_cr": candidate_stats["std"],
        "p95_cr": candidate_stats["p95"],
        "es95_cr": candidate_stats["es95"],
        "p99_cr": candidate_stats["p99"],
        "max_cr": candidate_stats["max"],
    })

# Statistical Metrics
# Outflow percentiles are high-cost thresholds. Expected shortfall is the
# average cash outflow among simulated outcomes at or above the 95th percentile.
stats_unh = summarize_outflows(unhedged_outflow_cr)
stats_hed = summarize_outflows(hedged_outflow_cr)

mean_unh, std_unh = stats_unh["mean"], stats_unh["std"]
var95_unh, var99_unh = stats_unh["p95"], stats_unh["p99"]
max_unh, es95_unh = stats_unh["max"], stats_unh["es95"]

mean_hed, std_hed = stats_hed["mean"], stats_hed["std"]
var95_hed, var99_hed = stats_hed["p95"], stats_hed["p99"]
max_hed, es95_hed = stats_hed["max"], stats_hed["es95"]

std_reduction_pct = (1.0 - (std_hed / std_unh)) * 100.0 if std_unh > 0 else 0.0
var95_savings_cr = var95_unh - var95_hed
es95_savings_cr = es95_unh - es95_hed
max_outflow_difference_cr = max_unh - max_hed
# --------------------------------------------------------------------------------------
# TABS SETUP
# --------------------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Executive Summary & Disclosures",
    "🎲 Monte Carlo Exchange Rate Simulation",
    "🛡️ Hedging Analysis & Payoff Comparison",
    "🏦 Capital Structure & Rate Sensitivity"
])

# ======================================================================================
# TAB 1: EXECUTIVE SUMMARY & DISCLOSURES
# ======================================================================================
with tab1:
    st.subheader("1. What is the risk, in simple language?")
    st.markdown("""
    Maruti Suzuki pays for some goods and services in foreign currencies. This dashboard focuses on a **JPY payable**:
    Maruti needs yen in the future and will pay more rupees if the yen becomes more expensive.

    **Important:** the ¥10 billion input in the simulation is an illustrative payment scenario. It is not the same as the
    company's total currency position in its annual report. The annual report shows several currencies and both
    assets (money to receive) and liabilities (money to pay).
    """)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Suzuki Motor Corp. holding", "58.53%", "At 31 March 2026")
    with col2:
        st.metric("JPY financial assets", "₹2,210.3 Cr", "₹22,103 million")
    with col3:
        st.metric("Gross JPY liabilities", "₹1,117.6 Cr", "₹11,176 million")
    with col4:
        st.metric("JPY liabilities after forwards", "₹814.8 Cr", "₹8,148 million")

    st.markdown("---")
    st.subheader("2. Actual JPY balance-sheet snapshot")
    st.caption(
        "Figures are from the FY2025–26 annual report's foreign-currency exposure table. "
        "Amounts below are reported in ₹ million and then explained in ₹ crore."
    )
    actual_fx_df = pd.DataFrame([
        {
            "What the report shows": "JPY financial assets (money due to the company)",
            "31 Mar 2026 (₹ million)": 22103,
            "31 Mar 2025 (₹ million)": 20124,
            "Simple meaning": "JPY-denominated balances the company expects to receive or holds."
        },
        {
            "What the report shows": "Gross JPY liabilities (money the company must pay)",
            "31 Mar 2026 (₹ million)": 11176,
            "31 Mar 2025 (₹ million)": 8810,
            "Simple meaning": "JPY-denominated payables before the listed forward contracts."
        },
        {
            "What the report shows": "Less: forwards against JPY liabilities",
            "31 Mar 2026 (₹ million)": -3028,
            "31 Mar 2025 (₹ million)": -3491,
            "Simple meaning": "Existing contracts that reduce the yen liability exposure."
        },
        {
            "What the report shows": "JPY liabilities after forwards",
            "31 Mar 2026 (₹ million)": 8148,
            "31 Mar 2025 (₹ million)": 5319,
            "Simple meaning": "Liabilities left after subtracting the listed forward contracts."
        },
        {
            "What the report shows": "Net JPY asset position (assets minus liabilities after forwards)",
            "31 Mar 2026 (₹ million)": 13955,
            "31 Mar 2025 (₹ million)": 14805,
            "Simple meaning": "On this balance-sheet snapshot, JPY assets exceed the remaining JPY liabilities."
        }
    ])
    st.dataframe(actual_fx_df, use_container_width=True, hide_index=True)

    st.info(
        "Why this matters: at 31 March 2026, reported JPY assets exceeded reported JPY liabilities after forward "
        "contracts by about ₹1,395.5 crore. That means the year-end balance-sheet snapshot is a net JPY asset position. "
        "The separate payable simulation below studies a future JPY payment; it should not be described as the company's "
        "total net currency position."
    )

    st.subheader("3. What did the annual report say about currency sensitivity?")
    sens1, sens2 = st.columns(2)
    with sens1:
        st.metric("If the rupee strengthens by 10%", "-₹139.6 Cr", "Reported JPY impact on profit/loss")
    with sens2:
        st.metric("If the rupee weakens by 10%", "+₹139.6 Cr", "Reported JPY impact on profit/loss")
    st.caption(
        "This is the company's reported sensitivity for outstanding JPY monetary items at year-end, not a forecast. "
        "The report gives the impact in ₹ million (−1,396 / +1,396), equal to approximately ₹139.6 crore."
    )
    st.markdown(
        "Source: [Maruti Suzuki official annual reports](https://www.marutisuzuki.com/corporate/investors/company-reports) "
        "— Annual Integrated Report FY2025–26, standalone financial statements, foreign currency risk exposure and sensitivity."
    )

    st.markdown("---")
    st.subheader("4. Three kinds of currency risk")
    c_a, c_b, c_c = st.columns(3)
    with c_a:
        st.info(
            "**Transaction risk**\n\nA bill must be paid or received later. If the exchange rate changes before settlement, "
            "the amount in rupees changes. This is what the JPY payable simulation focuses on."
        )
    with c_b:
        st.info(
            "**Translation risk**\n\nForeign-currency balances are converted into rupees for financial reporting. "
            "The reported rupee value can change even when the foreign-currency amount does not."
        )
    with c_c:
        st.info(
            "**Economic risk**\n\nCurrency movements can change future component costs, prices and competitiveness. "
            "A simple one-year cash-flow simulation cannot capture every long-term business effect."
        )

    st.subheader("5. How to use the dashboard")
    st.markdown("""
    1. Set the size of the illustrative yen payment and the market assumptions in the left-hand controls.
    2. Open **Monte Carlo Simulation** to see many possible exchange-rate outcomes—not one guaranteed prediction.
    3. Open **Hedging Analysis** to compare a payment with no hedge against different forward hedge percentages.
    4. Use the cost and risk comparison to discuss which choice fits a budget limit.
    5. Open **Capital Structure & Rate Sensitivity** to see the separate interest-rate scenario and its assumptions.
    """)

# ======================================================================================
# TAB 2: MONTE CARLO SIMULATION
# ======================================================================================
with tab2:
    st.subheader("1-Year Monte Carlo Exchange Rate Simulation")
    st.markdown(
        "In simple language, Monte Carlo repeats the calculation many times with different random market movements. "
        "Each path is one possible year for JPY/INR. The model does not know the future exchange rate and does not promise "
        "that any one path will happen."
    )
    st.markdown(f"""
    Simulating **{num_paths:,} independent price trajectories** over **252 trading days** (1-Year Horizon) using **Geometric Brownian Motion (GBM)** with a drift based on the domestic–foreign interest-rate differential. The active annualized volatility is **{ann_volatility:.2%}** ({volatility_source.lower()}):
    $$S_{{t+\\Delta t}} = S_t \\exp\\left( \\left((r_{{\\text{{INR}}}} - r_{{\\text{{JPY}}}}) - \\frac{1}{2}\\sigma^2\\right)\\Delta t + \\sigma\\sqrt{{\\Delta t}} Z_t \\right)$$
    """)

    # Top metrics
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Starting Spot Rate (S0)", f"₹{s0_spot_rate:.4f} / JPY", f"₹{s0_spot_rate*100:.2f} per 100 JPY")
    m2.metric("Theoretical Forward (F)", f"₹{forward_rate:.4f} / JPY", f"+{forward_premium_pct:.2f}% CIRP Premium")
    m3.metric("Simulated Mean (E[S_T])", f"₹{np.mean(terminal_rates):.4f} / JPY", f"Bias: {((np.mean(terminal_rates)/forward_rate)-1)*100:.2f}%")
    m4.metric("95th-Pct Terminal Rate", f"₹{np.percentile(terminal_rates, 95):.4f} / JPY", "Upper 5% rate threshold")
    m5.metric("Maximum Simulated Rate", f"₹{np.max(terminal_rates):.4f} / JPY", "Sample maximum, not a limit")

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
            name=f'95th Percentile Terminal Rate (₹{np.percentile(terminal_rates, 95):.4f})'
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
        fig_hist.add_vline(x=np.percentile(terminal_rates, 95), line_width=2, line_dash="dot", line_color="#9333EA", annotation_text="95th pct. rate", annotation_position="top right")

        fig_hist.update_layout(
            title="<b>Terminal JPY/INR Distribution at T = 1 Year</b>",
            xaxis_title="Exchange Rate (INR / JPY)",
            yaxis_title="Frequency",
            margin=dict(l=40, r=40, t=50, b=80),
            height=460
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    st.caption(
        f"Volatility source: {volatility_source}. The historical estimate is calculated from consecutive "
        "log returns in the bundled CSV and annualized using √252. The forward rate uses a continuously "
        "compounded interest-rate-parity approximation. Simulations are conditional on these assumptions."
    )

# ======================================================================================
# TAB 3: HEDGING ANALYSIS & PAYOFF COMPARISON
# ======================================================================================
with tab3:
    st.subheader(f"Derivative Hedging Strategy: {hedge_ratio:.0%} Forward Contract Hedge")
    st.markdown(f"""
    **What this means:** the forward contract agrees today's rate for the hedged yen amount. This protects that part of the
    payment if JPY becomes more expensive, but it also means the company cannot fully benefit if JPY becomes cheaper.

    - **Hedged amount:** JPY {hedged_jpy:,.0f} ({hedge_ratio:.0%}), locked at ₹{forward_rate:.4f} per JPY.
    - **Unhedged amount:** JPY {unhedged_jpy:,.0f} ({(1-hedge_ratio):.0%}), paid at the future market rate in each simulated path.
    - **Estimated extra execution cost:** ₹{forward_execution_cost_cr:,.2f} crore using the input of {forward_cost_bps} basis points.
    """)
    st.caption(
        "The execution cost is illustrative because no bank quote was provided. The forward rate already includes the "
        "modeled interest-rate difference; do not add the forward premium again as a separate fee."
    )

    # Main hedge KPIs
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        k1.metric(
            "Average Payment",
            f"₹{mean_hed:,.2f} Cr",
            f"vs no hedge: ₹{mean_hed - mean_unh:+,.2f} Cr",
            delta_color="inverse"
        )
    with k2:
        k2.metric(
            "Extra Hedge Cost",
            f"₹{forward_execution_cost_cr:,.2f} Cr",
            f"{forward_cost_bps} bps assumed",
            help="Illustrative execution cost; replace with a bank/dealer quote."
        )
    with k3:
        k3.metric(
            "Cash-Flow Variability",
            f"₹{std_hed:,.2f} Cr",
            f"{std_reduction_pct:.1f}% lower than no hedge",
            delta_color="inverse"
        )
    with k4:
        k4.metric(
            "95th-Pct Payment",
            f"₹{var95_hed:,.2f} Cr",
            f"Change: ₹{var95_hed - var95_unh:+,.2f} Cr",
            delta_color="inverse"
        )
    with k5:
        k5.metric(
            "Largest Simulated Payment",
            f"₹{max_hed:,.2f} Cr",
            f"vs no hedge: ₹{max_hed - max_unh:+,.2f} Cr",
            delta_color="inverse"
        )

    st.caption(
        "Interpretation: the 95th-percentile outflow is a high-cost threshold, not a guarantee. "
        "The 95% expected shortfall below is the average outflow among simulated results at or above that threshold. "
        "Maximum simulated outflow is the largest result in this finite sample, not a theoretical worst case."
    )
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
        fig_comp.add_vline(x=var95_unh, line_width=2, line_dash="dash", line_color="#DC2626", annotation_text="Unhedged 95th pct.")
        fig_comp.add_vline(x=var95_hed, line_width=2, line_dash="dash", line_color="#16A34A", annotation_text="Hedged 95th pct.")

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
        cdf_prob = np.arange(1, num_paths + 1) / (num_paths + 1)

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
            "Unhedged": f"₹{mean_unh:,.2f} Cr",
            f"Hedged ({hedge_ratio:.0%} Forward)": f"₹{mean_hed:,.2f} Cr",
            "Difference (Hedged - Unhedged)": f"₹{mean_hed - mean_unh:+,.2f} Cr",
            "Interpretation": "Average modeled cash cost; not a guarantee of the final payment."
        },
        {
            "Performance Metric": "Cash Flow Std. Deviation",
            "Unhedged": f"₹{std_unh:,.2f} Cr",
            f"Hedged ({hedge_ratio:.0%} Forward)": f"₹{std_hed:,.2f} Cr",
            "Difference (Hedged - Unhedged)": f"₹{std_hed - std_unh:+,.2f} Cr",
            "Interpretation": f"Standard deviation is {std_reduction_pct:.1f}% lower under the modeled hedge."
        },
        {
            "Performance Metric": "95th-Percentile Outflow",
            "Unhedged": f"₹{var95_unh:,.2f} Cr",
            f"Hedged ({hedge_ratio:.0%} Forward)": f"₹{var95_hed:,.2f} Cr",
            "Difference (Hedged - Unhedged)": f"₹{var95_hed - var95_unh:+,.2f} Cr",
            "Interpretation": "About 5% of simulated outflows exceed this threshold."
        },
        {
            "Performance Metric": "95% Expected Shortfall (Worst 5% Mean)",
            "Unhedged": f"₹{es95_unh:,.2f} Cr",
            f"Hedged ({hedge_ratio:.0%} Forward)": f"₹{es95_hed:,.2f} Cr",
            "Difference (Hedged - Unhedged)": f"₹{es95_hed - es95_unh:+,.2f} Cr",
            "Interpretation": "Average outflow among scenarios at or above each case's 95th percentile."
        },
        {
            "Performance Metric": "99th-Percentile Outflow",
            "Unhedged": f"₹{var99_unh:,.2f} Cr",
            f"Hedged ({hedge_ratio:.0%} Forward)": f"₹{var99_hed:,.2f} Cr",
            "Difference (Hedged - Unhedged)": f"₹{var99_hed - var99_unh:+,.2f} Cr",
            "Interpretation": "A more extreme high-cost threshold than the 95th percentile."
        },
        {
            "Performance Metric": "Maximum Simulated Outflow",
            "Unhedged": f"₹{max_unh:,.2f} Cr",
            f"Hedged ({hedge_ratio:.0%} Forward)": f"₹{max_hed:,.2f} Cr",
            "Difference (Hedged - Unhedged)": f"₹{max_hed - max_unh:+,.2f} Cr",
            "Interpretation": "Largest outflow observed in this simulation sample; not an absolute worst case."
        }
    ])
    st.table(comp_table)

    st.markdown("---")
    st.subheader("Compare five hedge choices")
    st.markdown(
        "This table reuses the same simulated exchange rates for every option. That makes the comparison fair: "
        "only the hedge percentage and its assumed execution cost change."
    )
    scenario_display = pd.DataFrame([
        {
            "Hedge %": f"{row['ratio']:.0%}",
            "Extra execution cost (₹ Cr)": round(row["cost_cr"], 2),
            "Average payment (₹ Cr)": round(row["mean_cr"], 2),
            "95th-percentile payment (₹ Cr)": round(row["p95_cr"], 2),
            "Worst-5%-average payment (₹ Cr)": round(row["es95_cr"], 2),
            "Cash-flow standard deviation (₹ Cr)": round(row["std_cr"], 2),
            "Largest simulated payment (₹ Cr)": round(row["max_cr"], 2),
        }
        for row in hedge_scenarios
    ])
    st.dataframe(scenario_display, use_container_width=True, hide_index=True)

    fig_tradeoff = make_subplots(specs=[[{"secondary_y": True}]])
    candidate_percentages = [row["ratio"] * 100 for row in hedge_scenarios]
    fig_tradeoff.add_trace(
        go.Bar(
            x=candidate_percentages,
            y=[row["p95_cr"] for row in hedge_scenarios],
            name="95th-percentile payment (₹ Cr)",
        ),
        secondary_y=False,
    )
    fig_tradeoff.add_trace(
        go.Scatter(
            x=candidate_percentages,
            y=[row["cost_cr"] for row in hedge_scenarios],
            mode="lines+markers",
            name="Extra execution cost (₹ Cr)",
        ),
        secondary_y=True,
    )
    fig_tradeoff.update_layout(
        title="Risk and cost: how the hedge percentage changes the result",
        xaxis_title="Forward hedge ratio (%)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        margin=dict(l=40, r=40, t=55, b=80),
        height=400,
    )
    fig_tradeoff.update_yaxes(title_text="95th-percentile payment (₹ crore)", secondary_y=False)
    fig_tradeoff.update_yaxes(title_text="Assumed execution cost (₹ crore)", secondary_y=True)
    st.plotly_chart(fig_tradeoff, use_container_width=True)

    st.subheader("Simple decision helper")
    p95_values = [row["p95_cr"] for row in hedge_scenarios]
    lower_limit = float(np.floor(min(p95_values) * 2.0) / 2.0)
    upper_limit = float(np.ceil(max(p95_values) * 2.0) / 2.0)
    if upper_limit <= lower_limit:
        upper_limit = lower_limit + 0.5
    matching_current = min(hedge_scenarios, key=lambda row: abs(row["ratio"] - hedge_ratio))
    default_limit = float(np.clip(round(matching_current["p95_cr"] * 2.0) / 2.0, lower_limit, upper_limit))
    max_95_payment = st.slider(
        "What is the highest 95th-percentile payment you are willing to plan for? (₹ crore)",
        min_value=lower_limit,
        max_value=upper_limit,
        value=default_limit,
        step=0.5,
        help="This is a budget/risk limit you choose. It is not supplied by Maruti Suzuki."
    )
    qualifying = [row for row in hedge_scenarios if row["p95_cr"] <= max_95_payment]
    if qualifying:
        preferred = min(qualifying, key=lambda row: row["cost_cr"])
        st.success(
            f"Among the five tested choices, **{preferred['ratio']:.0%} hedge** has the lowest estimated "
            f"execution cost (₹{preferred['cost_cr']:.2f} crore) while keeping the 95th-percentile payment at "
            f"₹{preferred['p95_cr']:.2f} crore, within your selected limit."
        )
    else:
        most_protective = min(hedge_scenarios, key=lambda row: row["p95_cr"])
        st.warning(
            f"None of the five tested choices meets that limit. The lowest 95th-percentile payment in this grid "
            f"is ₹{most_protective['p95_cr']:.2f} crore at a {most_protective['ratio']:.0%} hedge. "
            "Consider revising the limit or assumptions and reviewing the required hedge with treasury."
        )
    st.caption(
        "This helper compares only 0%, 25%, 50%, 75% and 100% hedges. It is a learning aid, not an automatic "
        "treasury recommendation. A real decision needs verified payment timing, actual currency exposure and a dealer quote."
    )

# ======================================================================================
# TAB 4: CAPITAL STRUCTURE & INTEREST-RATE SENSITIVITY
# ======================================================================================
with tab4:
    st.subheader("1. What does Maruti's latest report tell us?")
    st.markdown("""
    Maruti Suzuki's FY2025–26 report says the company had no long-term borrowings at year-end, can use short-term rupee
    borrowing for cash-flow mismatches, and holds a large portfolio of debt mutual funds. So we should not invent a
    large loan just to demonstrate an interest-rate hedge. This section shows an illustrative sensitivity of the
    investment portfolio to a change in market yields.
    """)

    ci1, ci2, ci3, ci4 = st.columns(4)
    with ci1:
        st.metric("Net worth (FY26)", "₹1,05,109.8 Cr", "₹1,051,098 million")
    with ci2:
        st.metric("Debt mutual funds (FY26)", "₹71,723.8 Cr", "Current + non-current investments")
    with ci3:
        st.metric("Long-term borrowings", "None reported", "At 31 March 2026")
    with ci4:
        st.metric("Reported NAV sensitivity", "₹717.2 Cr", "For a 1% NAV movement")

    st.markdown(
        "Source: [Maruti Suzuki official annual reports](https://www.marutisuzuki.com/corporate/investors/company-reports) "
        "— Annual Integrated Report FY2025–26. The report states that a 1% change in NAV of mutual-fund investments "
        "would change profit by ₹7,172 million (about ₹717.2 crore)."
    )

    st.markdown("---")
    st.subheader("2. Try an interest-rate change")
    st.caption(
        "A simple finance rule: when market yields rise, the prices of existing fixed-income investments usually fall. "
        "The duration formula below estimates that effect. The report does not provide one single duration for this "
        "whole portfolio, so duration is a user-set assumption—not a reported company figure."
    )

    portfolio_value_cr = 71723.8
    bps_shift = st.slider(
        "Change in market yield (basis points)",
        min_value=-250,
        max_value=250,
        value=100,
        step=25,
        help="Positive means yields rise; negative means yields fall. 100 basis points = 1 percentage point."
    )
    assumed_duration = st.slider(
        "Assumed modified duration of the portfolio (years)",
        min_value=0.25,
        max_value=5.0,
        value=1.0,
        step=0.25,
        help="Use fund factsheets to estimate this more precisely. The default 1 year is illustrative, not a reported value."
    )

    estimated_nav_change_cr = approximate_duration_price_change_cr(
        portfolio_value_cr=portfolio_value_cr,
        modified_duration_years=assumed_duration,
        rate_shift_bps=bps_shift,
    )
    rate_move = "yields rise" if bps_shift > 0 else "yields fall" if bps_shift < 0 else "yields do not change"
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Rate scenario", f"{bps_shift:+,} bps", rate_move.capitalize())
    with c2:
        st.metric("Estimated portfolio value change", f"₹{estimated_nav_change_cr:+,.2f} Cr", "Duration approximation")
    with c3:
        st.metric("Starting portfolio value", f"₹{portfolio_value_cr:,.1f} Cr", "FY26 debt mutual funds")

    st.markdown("""
    **Formula in plain language**

    Estimated change in value ≈ − portfolio duration × change in yield × portfolio value.

    For example, with a duration assumption of 1 year, a 1 percentage-point rise in yields implies an approximate
    1% fall in portfolio value. If duration were 3 years, the same yield move would imply an approximate 3% fall.
    This is a small-change estimate; it is not a full revaluation of the mutual-fund holdings.
    """)

    rate_moves = np.arange(-250, 251, 25)
    rate_changes = [
        approximate_duration_price_change_cr(portfolio_value_cr, assumed_duration, move)
        for move in rate_moves
    ]
    fig_rate = go.Figure()
    fig_rate.add_trace(go.Scatter(
        x=rate_moves,
        y=rate_changes,
        mode="lines+markers",
        name="Estimated value change",
    ))
    fig_rate.add_vline(x=0, line_dash="dash", line_color="#64748B")
    fig_rate.add_hline(y=0, line_dash="dash", line_color="#64748B")
    fig_rate.update_layout(
        title="Estimated portfolio value change under different yield scenarios",
        xaxis_title="Change in market yield (basis points)",
        yaxis_title="Estimated change in value (₹ crore)",
        margin=dict(l=40, r=40, t=55, b=40),
        height=380,
    )
    st.plotly_chart(fig_rate, use_container_width=True)

    st.warning(
        "Limitations: the duration is an assumption, and the portfolio contains different funds and maturities. "
        "A precise valuation requires fund-level holdings and duration data. This model does not automatically prove "
        "that an interest-rate swap is worthwhile. Only hedge a measurable exposure, and compare the dealer quote and "
        "remaining risk before recommending a transaction."
    )
