"""
Free Cash Flow projection based on user assumptions.
"""
from typing import Dict, List, Any
import numpy as np


def project_fcf(
    base_year: int,
    base_revenue: float,
    assumptions: Dict[str, List[float]],
    num_years: int = 5,
) -> Dict[str, List[float]]:
    """
    Project Free Cash Flow for num_years based on assumptions.

    Assumptions dict should contain lists of length num_years with:
    - revenue_growth: Revenue growth rate for each year
    - ebit_margin: EBIT margin for each year
    - tax_rate: Tax rate for each year
    - dep_pct: D&A as % of revenue
    - capex_pct: CapEx as % of revenue
    - nwc_pct: Change in NWC as % of revenue

    Returns dict with projected financials for each year.
    """
    projections = {
        "year": [],
        "revenue": [],
        "ebit": [],
        "tax": [],
        "nopat": [],
        "depreciation": [],
        "capex": [],
        "nwc_change": [],
        "free_cash_flow": [],
    }

    prev_revenue = base_revenue

    for i in range(num_years):
        year = base_year + i + 1

        # Revenue
        growth = assumptions["revenue_growth"][i]
        revenue = prev_revenue * (1 + growth)

        # EBIT
        ebit_margin = assumptions["ebit_margin"][i]
        ebit = revenue * ebit_margin

        # Tax
        tax_rate = assumptions["tax_rate"][i]
        tax = ebit * tax_rate
        nopat = ebit - tax  # NOPAT = Net Operating Profit After Tax

        # D&A
        dep_pct = assumptions["dep_pct"][i]
        depreciation = revenue * dep_pct

        # CapEx
        capex_pct = assumptions["capex_pct"][i]
        capex = revenue * capex_pct

        # NWC change
        nwc_pct = assumptions["nwc_pct"][i]
        nwc_change = revenue * nwc_pct

        # Free Cash Flow
        # FCF = NOPAT + D&A - CapEx - Change in NWC
        fcf = nopat + depreciation - capex - nwc_change

        projections["year"].append(year)
        projections["revenue"].append(revenue)
        projections["ebit"].append(ebit)
        projections["tax"].append(tax)
        projections["nopat"].append(nopat)
        projections["depreciation"].append(depreciation)
        projections["capex"].append(capex)
        projections["nwc_change"].append(nwc_change)
        projections["free_cash_flow"].append(fcf)

        prev_revenue = revenue

    return projections


def calculate_terminal_value(
    final_fcf: float,
    terminal_growth_rate: float,
    wacc: float,
    method: str = "perpetuity",
    exit_multiple: float = None,
    final_ebitda: float = None,
) -> float:
    """
    Calculate terminal value.

    Methods:
    - perpetuity: TV = FCF_n * (1 + g) / (WACC - g)
    - exit_multiple: TV = EBITDA_n * Exit Multiple
    """
    if method == "perpetuity":
        if wacc <= terminal_growth_rate:
            raise ValueError(
                f"WACC ({wacc:.2%}) must be greater than terminal growth ({terminal_growth_rate:.2%})"
            )
        terminal_value = final_fcf * (1 + terminal_growth_rate) / (
            wacc - terminal_growth_rate
        )
    elif method == "exit_multiple":
        if final_ebitda is None or exit_multiple is None:
            raise ValueError("exit_multiple method requires final_ebitda and exit_multiple")
        terminal_value = final_ebitda * exit_multiple
    else:
        raise ValueError(f"Unknown method: {method}")

    return terminal_value
