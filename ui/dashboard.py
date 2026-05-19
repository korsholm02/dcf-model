"""
Main Streamlit Dashboard for DCF Analysis.
Professional investor interface for quick valuation of any company.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.fetcher import fetch_financials
from data.parser import parse_financials, calculate_historical_metrics
from budget.defaults import generate_default_assumptions, get_scenario_assumptions
from models.cashflow import project_fcf
from models.wacc import calculate_wacc
from models.valuation import full_dcf_valuation, sensitivity_analysis


# Session state initialization
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.ticker = "ITRI"
    # Tab 1 defaults
    st.session_state.rf = 0.04
    st.session_state.mrp = 0.055
    st.session_state.cod = 0.05
    st.session_state.tg = 0.02
    # Tab 3 defaults
    st.session_state.rf_t3 = 0.04
    st.session_state.mrp_t3 = 0.055
    st.session_state.cod_t3 = 0.05
    st.session_state.tg_t3 = 0.02
    st.session_state.tax_t3 = 0.25


@st.cache_data(show_spinner=True)
def load_ticker_data(ticker):
    """Load and parse financial data for a ticker. Cached for performance."""
    try:
        data = fetch_financials(ticker)
        if not data:
            return None, None, None, f"Kunne ikke hente data for {ticker}. Tjek tickeren."
        parsed = parse_financials(data)
        if not parsed:
            return None, None, None, "Kunne ikke parse data - mangler regnskaber"
        metrics = calculate_historical_metrics(parsed)
        return data, parsed, metrics, None
    except Exception as e:
        return None, None, None, f"Fejl: {str(e)}"


st.set_page_config(page_title="DCF Analyzer", page_icon="📈", layout="wide")
st.title("📈 DCF Analyzer")
st.markdown("Professionel DCF-værdiansættelse til investorer")

# Sidebar
st.sidebar.header("Virksomhed")
ticker_input = st.sidebar.text_input("Ticker", value=st.session_state.ticker, help="F.eks. ITRI, NOVO-B.CO, MAERSK-B.CO", key="ticker_input_side")

# Update session state when ticker changes
if ticker_input != st.session_state.ticker:
    st.session_state.ticker = ticker_input

# Load data
data, parsed, metrics, error = load_ticker_data(ticker_input)

if error:
    st.error(f"Fejl: {error}")
    st.stop()

if not data or not parsed or not metrics:
    st.info("👈 Indtast en ticker i sidebar for at starte analysen")
    st.stop()

# Company info
info = data["info"]
current_price = info.get("currentPrice") or info.get("previousClose")
market_cap = info.get("marketCap", 0)
beta = info.get("beta", 1.0)
shares = info.get("sharesOutstanding", 0)
total_debt = parsed["total_debt"][0]
cash = parsed["cash"][0]
base_revenue = parsed["revenue"][0]

# Top metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Current Price", f"${current_price:.2f}" if current_price else "N/A")
col2.metric("Market Cap", f"${market_cap/1e9:.2f}B" if market_cap else "N/A")
col3.metric("Beta", f"{beta:.2f}")
col4.metric("Revenue CAGR", f"{metrics['revenue_cagr']:.1%}")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Værdiansættelse", "📈 Historik", "⚙️ Antagelser", "📉 Sensitivitet"])

# === TAB 1: Værdiansættelse ===
with tab1:
    st.header("DCF Værdiansættelse")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("WACC Parametre")
        risk_free = st.slider("Risikofri rente", 0.01, 0.10, st.session_state.rf, 0.005, key="rf")
        market_premium = st.slider("Markedsrisikopræmie", 0.03, 0.08, st.session_state.mrp, 0.005, key="mrp")
        cost_of_debt = st.slider("Gældsomkostning (før skat)", 0.02, 0.15, st.session_state.cod, 0.005, key="cod")

    with col2:
        st.subheader("Terminal Værdi")
        terminal_growth = st.slider("Terminal vækstrate", 0.0, 0.04, st.session_state.tg, 0.005, key="tg")

    # Update session state when sliders change
    st.session_state.rf = risk_free
    st.session_state.mrp = market_premium
    st.session_state.cod = cost_of_debt
    st.session_state.tg = terminal_growth

    wacc = calculate_wacc(
        market_cap=market_cap, total_debt=total_debt, beta=beta,
        risk_free_rate=risk_free, market_risk_premium=market_premium,
        cost_of_debt=cost_of_debt, tax_rate=metrics["avg_tax_rate"]
    )
    st.metric("WACC", f"{wacc:.1%}")

    assumptions = generate_default_assumptions(metrics)
    projections = project_fcf(2024, base_revenue, assumptions)
    result = full_dcf_valuation(projections, wacc, terminal_growth, total_debt, cash, shares, current_price)

    upside = result["upside_downside"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Implied Share Price", f"${result['implied_share_price']:.2f}",
              f"{upside:.1%} upside" if upside > 0 else f"{abs(upside):.1%} downside")
    c2.metric("Enterprise Value", f"${result['enterprise_value']/1e6:.1f}M")
    c3.metric("Equity Value", f"${result['equity_value']/1e6:.1f}M")

    st.subheader("FCF Prognose")
    fcf_df = pd.DataFrame({
        "Year": projections["year"],
        "FCF": [f/1e6 for f in projections["free_cash_flow"]],
        "Revenue": [r/1e6 for r in projections["revenue"]]
    })
    fig = go.Figure()
    fig.add_trace(go.Bar(x=fcf_df["Year"], y=fcf_df["FCF"], name="FCF ($M)", marker_color="steelblue"))
    fig.add_trace(go.Scatter(x=fcf_df["Year"], y=fcf_df["Revenue"], name="Revenue ($M)",
                              marker_color="darkblue", line=dict(width=3)))
    fig.update_layout(xaxis_title="År", yaxis_title="Millioner USD", hovermode="x unified", height=400)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("NPV Fordeling")
    npv_df = pd.DataFrame(result["npv_breakdown"])
    npv_df["Discounted FCF"] = npv_df["discounted"] / 1e6
    fig2 = go.Figure(data=[go.Bar(x=npv_df["year"], y=npv_df["Discounted FCF"],
                                   name="Discounted FCF", marker_color="forestgreen")])
    fig2.add_hline(y=result["discounted_tv"]/1e6, line_dash="dash", annotation_text="Terminal Value",
                   annotation_position="right", line_color="orange")
    fig2.update_layout(xaxis_title="År", yaxis_title="PV ($M)", height=400)
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Værdi Bro")
    bridge_data = {
        "Metric": ["FCF (PV)", "Terminal Value (PV)", "Net Debt", "Equity Value"],
        "Value": [result["sum_fcf_pv"]/1e6, result["discounted_tv"]/1e6,
                  -(total_debt - cash)/1e6, result["equity_value"]/1e6]
    }
    bridge_df = pd.DataFrame(bridge_data)
    bridge_df["Cumulative"] = bridge_df["Value"].cumsum()
    fig3 = go.Figure(go.Waterfall(x=bridge_df["Metric"], y=bridge_df["Value"],
                                   connector={"line": {"color": "grey"}},
                                   increasing={"marker": {"color": "green"}},
                                   decreasing={"marker": {"color": "red"}},
                                   totals={"marker": {"color": "blue"}}))
    fig3.update_layout(title="Fra DCF til Equity Value", height=400)
    st.plotly_chart(fig3, use_container_width=True)

# === TAB 2: Historik ===
with tab2:
    st.header("Historiske Nøgletal")
    hist_df = pd.DataFrame({
        "År": parsed["years"],
        "Revenue": [r/1e6 for r in parsed["revenue"]],
        "EBIT": [e/1e6 for e in parsed["ebit"]],
        "EBIT Margin": [parsed["ebit"][i]/parsed["revenue"][i] if parsed["revenue"][i] > 0 else 0 for i in range(len(parsed["years"]))],
        "FCF": [f/1e6 for f in parsed["free_cash_flow"]],
        "CapEx": [c/1e6 for c in parsed["capex"]],
    })
    st.dataframe(hist_df.style.format({"Revenue": "${:.1f}M", "EBIT": "${:.1f}M",
                                        "EBIT Margin": "{:.1%}", "FCF": "${:.1f}M", "CapEx": "${:.1f}M"}), hide_index=True)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist_df["År"], y=hist_df["Revenue"], name="Revenue", mode="lines+markers"))
    fig.add_trace(go.Scatter(x=hist_df["År"], y=hist_df["FCF"], name="FCF", mode="lines+markers"))
    fig.update_layout(xaxis_title="År", yaxis_title="Millioner USD", height=400)
    st.plotly_chart(fig, use_container_width=True)

# === TAB 3: Antagelser ===
with tab3:
    st.header("Juster Antagelser")
    st.info("📍 Historiske gennemsnit vises som default - juster efter din vurdering")

    col_w1, col_w2 = st.columns(2)
    with col_w1:
        st.subheader("WACC")
        risk_free_tab3 = st.slider("Risikofri rente", 0.01, 0.10, st.session_state.rf_t3, 0.005, key="rf_t3")
        market_premium_tab3 = st.slider("Markedsrisikopræmie", 0.03, 0.08, st.session_state.mrp_t3, 0.005, key="mrp_t3")
        cost_of_debt_tab3 = st.slider("Gældsomkostning", 0.02, 0.15, st.session_state.cod_t3, 0.005, key="cod_t3")
    with col_w2:
        st.subheader("Terminal")
        terminal_growth_tab3 = st.slider("Terminal vækstrate", 0.0, 0.04, st.session_state.tg_t3, 0.005, key="tg_t3")

    # Update session state when sliders change
    st.session_state.rf_t3 = risk_free_tab3
    st.session_state.mrp_t3 = market_premium_tab3
    st.session_state.cod_t3 = cost_of_debt_tab3
    st.session_state.tg_t3 = terminal_growth_tab3

    wacc_tab3 = calculate_wacc(
        market_cap=market_cap, total_debt=total_debt, beta=beta,
        risk_free_rate=risk_free_tab3, market_risk_premium=market_premium_tab3,
        cost_of_debt=cost_of_debt_tab3, tax_rate=metrics["avg_tax_rate"]
    )
    st.metric("WACC", f"{wacc_tab3:.1%}")

    default_assumptions = generate_default_assumptions(metrics)

    st.subheader("Revenue Vækst")
    growth_cols = st.columns(5)
    growth_assumptions = []
    for i in range(5):
        with growth_cols[i]:
            val = st.number_input(f"År {i+1}", min_value=-0.5, max_value=1.0,
                                   value=float(default_assumptions["revenue_growth"][i]),
                                   format="%.2f", key=f"g_t3_{i}")
            growth_assumptions.append(val)

    st.subheader("EBIT Margin")
    margin_cols = st.columns(5)
    margin_assumptions = []
    for i in range(5):
        with margin_cols[i]:
            val = st.number_input(f"År {i+1}", min_value=0.0, max_value=0.5,
                                   value=float(default_assumptions["ebit_margin"][i]),
                                   format="%.2f", key=f"m_t3_{i}")
            margin_assumptions.append(val)

    col1, col2, col3 = st.columns(3)
    with col1:
        tax_rate = st.number_input("Skatterate", 0.0, 0.4, st.session_state.tax_t3, 0.01, key="tax_t3")
        st.session_state.tax_t3 = tax_rate
    with col2:
        dep_pct = st.number_input("D&A % af Revenue", 0.0, 0.2,
                                   float(default_assumptions["dep_pct"][0]), 0.01, key="dep_t3")
    with col3:
        capex_pct = st.number_input("CapEx % af Revenue", 0.0, 0.3,
                                     float(default_assumptions["capex_pct"][0]), 0.01, key="capex_t3")

    nwc_pct = st.number_input("ΔNWC % af Revenue", -0.1, 0.2,
                               float(default_assumptions["nwc_pct"][0]), 0.01, key="nwc_t3")

    custom_assumptions = {
        "revenue_growth": growth_assumptions, "ebit_margin": margin_assumptions,
        "tax_rate": [tax_rate] * 5, "dep_pct": [dep_pct] * 5,
        "capex_pct": [capex_pct] * 5, "nwc_pct": [nwc_pct] * 5,
    }

    custom_projections = project_fcf(2024, base_revenue, custom_assumptions)
    custom_result = full_dcf_valuation(custom_projections, wacc_tab3, terminal_growth_tab3,
                                        total_debt, cash, shares, current_price)

    st.subheader("Resultat med dine antagelser")
    c1, c2 = st.columns(2)
    c1.metric("Implied Price", f"${custom_result['implied_share_price']:.2f}")
    upside_custom = custom_result["upside_downside"]
    c2.metric("Upside/Downside", f"{upside_custom:.1%}",
              delta=f"${custom_result['implied_share_price'] - current_price:.2f}" if current_price else None)

# === TAB 4: Sensitivitet ===
with tab4:
    st.header("Sensitivitetsanalyse")

    sens = sensitivity_analysis(projections, wacc, terminal_growth, total_debt, cash, shares,
                                 wacc_range=[wacc-0.02, wacc-0.01, wacc, wacc+0.01, wacc+0.02],
                                 growth_range=[terminal_growth-0.005, terminal_growth,
                                               terminal_growth+0.005, terminal_growth+0.01])

    sens_matrix = []
    for w in sens["wacc_range"]:
        row = sens["matrix"][w]
        sens_matrix.append([p if p else None for p in row])

    fig = go.Figure(data=go.Heatmap(
        z=sens_matrix, x=sens["growth_range"], y=sens["wacc_range"],
        colorscale="RdYlGn",
        text=[[f"${p:.2f}" if p else "N/A" for p in row] for row in sens_matrix],
        texttemplate="%{text}", textfont={"size": 10},
        hovertemplate="WACC: %{y}<br>Growth: %{x}<br>Price: $%{z:.2f}<extra></extra>"
    ))
    fig.update_layout(title="Implied Share Price ved forskellig WACC og Terminal Vækst",
                      xaxis_title="Terminal Vækstrate", yaxis_title="WACC", height=500)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Scenario Analyse")
    scenarios = ["base", "bull", "bear"]
    scenario_results = []
    for scenario in scenarios:
        scen_assumptions = get_scenario_assumptions(metrics, scenario)
        scen_projections = project_fcf(2024, base_revenue, scen_assumptions)
        scen_result = full_dcf_valuation(scen_projections, wacc, terminal_growth,
                                          total_debt, cash, shares, current_price)
        scenario_results.append({
            "Scenario": scenario.capitalize(),
            "Implied Price": f"${scen_result['implied_share_price']:.2f}",
            "Upside": f"{scen_result['upside_downside']:.1%}"
        })
    st.table(pd.DataFrame(scenario_results))

# Footer
st.markdown("---")
st.markdown("DCF Analyzer | Bygget til professionelle investorer")
