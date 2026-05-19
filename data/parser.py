"""
Parse and normalize financial statement data.
Extracts the key metrics needed for DCF calculations.
"""
import pandas as pd
from typing import Dict, Any, Optional, List
import numpy as np


def parse_financials(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse raw Yahoo Finance data into normalized metrics for DCF.

    Yahoo Finance uses different column names across regions.
    This function normalizes them to a consistent format.
    """
    income = data["income_stmt"]
    balance = data["balance_sheet"]
    cashflow = data["cashflow"]

    # Convert columns to years (most recent first)
    years = [str(col.year) for col in income.columns]

    # Helper to safely extract values with fallbacks
    def get_value(df: pd.DataFrame, primary: str, fallbacks: List[str] = None) -> pd.Series:
        fallbacks = fallbacks or []
        for col in [primary] + fallbacks:
            if col in df.index:
                return df.loc[col]
        # Try case-insensitive match
        for idx in df.index:
            if idx.lower() == col.lower():
                return df.loc[idx]
        return pd.Series([np.nan] * len(df.columns), index=df.columns)

    try:
        # Income Statement
        revenue = get_value(income, "Total Revenue", ["Revenue", "Net Income"])
        ebit = get_value(income, "Operating Income", ["EBIT", "Operating Income"])
        tax_provision = get_value(income, "Tax Provision", ["Income Tax", "Tax Expense"])

        # Cash Flow Statement
        depreciation = get_value(cashflow, "Depreciation", ["Depreciation And Amortization", "D&A"])
        capex = get_value(cashflow, "Capital Expenditure", ["Capex", "CAPEX"])
        # CapEx is negative in cashflow, make positive for calculations
        capex = -capex

        # Working Capital changes (from cashflow or calculated from balance sheet)
        try:
            nwc_change = get_value(cashflow, "Change In Working Capital", ["Changes In Working Capital"])
        except:
            # Calculate from balance sheet components
            try:
                ar = get_value(balance, "Accounts Receivable", ["Receivables"])
                inventory = get_value(balance, "Inventory", ["Inventories"])
                ap = get_value(balance, "Accounts Payable", ["Payables"])

                # NWC = AR + Inventory - AP
                nwc = ar + inventory - ap
                nwc_change = pd.Series([np.nan] * len(nwc.columns), index=nwc.columns)
                for i in range(1, len(nwc.columns)):
                    nwc_change.iloc[i-1] = nwc.iloc[i] - nwc.iloc[i-1]
            except:
                nwc_change = pd.Series([0] * len(years), index=income.columns)

        # Balance Sheet
        total_debt = get_value(balance, "Total Debt", ["Long Term Debt", "Debt"])
        cash = get_value(balance, "Cash And Cash Equivalents", ["Cash", "Cash And Short Term Investments"])

        # Calculate effective tax rate
        ebt = ebit  # Simplified (ignoring interest for now)
        tax_rate = tax_provision / ebt
        tax_rate = tax_rate.clip(0, 0.40)  # Cap at 40%

        # Build normalized data structure
        result = {
            "years": years,
            "revenue": revenue.tolist(),
            "ebit": ebit.tolist(),
            "tax_rate": tax_rate.tolist(),
            "depreciation": depreciation.tolist(),
            "capex": capex.tolist(),
            "nwc_change": nwc_change.tolist(),
            "total_debt": total_debt.tolist(),
            "cash": cash.tolist(),
        }

        # Calculate historical FCF
        result["free_cash_flow"] = calculate_historical_fcf(result)

        return result

    except Exception as e:
        print(f"Error parsing financials: {e}")
        return None


def calculate_historical_fcf(parsed: Dict[str, Any]) -> List[float]:
    """
    Calculate Free Cash Flow from parsed data.
    FCF = EBIT * (1 - tax_rate) + D&A - CapEx - Change in NWC
    """
    fcf = []
    for i in range(len(parsed["years"])):
        ebit = parsed["ebit"][i] if not np.isnan(parsed["ebit"][i]) else 0
        tax = parsed["tax_rate"][i] if not np.isnan(parsed["tax_rate"][i]) else 0.25
        dep = parsed["depreciation"][i] if not np.isnan(parsed["depreciation"][i]) else 0
        capex = parsed["capex"][i] if not np.isnan(parsed["capex"][i]) else 0
        nwc = parsed["nwc_change"][i] if not np.isnan(parsed["nwc_change"][i]) else 0

        fcff = ebit * (1 - tax) + dep - capex - nwc
        fcf.append(fcff)

    return fcf


def calculate_historical_metrics(parsed: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate historical averages and trends for budget defaults.
    """
    revenue = [r for r in parsed["revenue"] if not np.isnan(r)]
    fcf = [f for f in parsed["free_cash_flow"] if not np.isnan(f)]

    # Revenue growth (CAGR over available years)
    if len(revenue) >= 2:
        n_years = len(revenue) - 1
        cagr = (revenue[0] / revenue[-1]) ** (1 / n_years) - 1
    else:
        cagr = 0.0

    # Average margins
    ebit_margins = []
    for i in range(len(parsed["years"])):
        if parsed["revenue"][i] > 0 and not np.isnan(parsed["ebit"][i]):
            ebit_margins.append(parsed["ebit"][i] / parsed["revenue"][i])
    avg_ebit_margin = np.mean(ebit_margins) if ebit_margins else 0.15

    # CapEx as % of revenue
    capex_pcts = []
    for i in range(len(parsed["years"])):
        if parsed["revenue"][i] > 0 and not np.isnan(parsed["capex"][i]):
            capex_pcts.append(parsed["capex"][i] / parsed["revenue"][i])
    avg_capex_pct = np.mean(capex_pcts) if capex_pcts else 0.05

    # D&A as % of revenue
    dep_pcts = []
    for i in range(len(parsed["years"])):
        if parsed["revenue"][i] > 0 and not np.isnan(parsed["depreciation"][i]):
            dep_pcts.append(parsed["depreciation"][i] / parsed["revenue"][i])
    avg_dep_pct = np.mean(dep_pcts) if dep_pcts else 0.03

    # NWC change as % of revenue
    nwc_pcts = []
    for i in range(len(parsed["years"])):
        if parsed["revenue"][i] > 0 and not np.isnan(parsed["nwc_change"][i]):
            nwc_pcts.append(parsed["nwc_change"][i] / parsed["revenue"][i])
    avg_nwc_pct = np.mean(nwc_pcts) if nwc_pcts else 0.01

    return {
        "revenue_cagr": cagr,
        "avg_ebit_margin": avg_ebit_margin,
        "avg_capex_pct": avg_capex_pct,
        "avg_dep_pct": avg_dep_pct,
        "avg_nwc_pct": avg_nwc_pct,
        "avg_tax_rate": np.mean([t for t in parsed["tax_rate"] if not np.isnan(t)]),
    }
