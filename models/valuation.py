"""
DCF Valuation - combines FCF projections, WACC, and terminal value.
"""
from typing import Dict, List, Any
import numpy as np


def calculate_enterprise_value(
    fcf_projections: List[float],
    wacc: float,
    terminal_value: float,
    base_year: int = 2024,
) -> Dict[str, Any]:
    """
    Calculate enterprise value by discounting FCF and terminal value.

    Returns:
    - discounted_fcf: List of discounted FCF for each year
    - discounted_tv: Terminal value discounted to present
    - enterprise_value: Sum of discounted FCF + discounted TV
    - npv_per_year: NPV contribution from each year
    """
    discounted_fcf = []
    npv_breakdown = []

    for i, fcf in enumerate(fcf_projections):
        year = base_year + i + 1
        discount_factor = (1 + wacc) ** (i + 1)
        discounted = fcf / discount_factor
        discounted_fcf.append(discounted)
        npv_breakdown.append({"year": year, "fcf": fcf, "discounted": discounted})

    # Discount terminal value (at end of projection period)
    n = len(fcf_projections)
    discounted_tv = terminal_value / ((1 + wacc) ** n)

    enterprise_value = sum(discounted_fcf) + discounted_tv

    return {
        "discounted_fcf": discounted_fcf,
        "discounted_tv": discounted_tv,
        "enterprise_value": enterprise_value,
        "npv_breakdown": npv_breakdown,
        "sum_fcf_pv": sum(discounted_fcf),
    }


def calculate_equity_value(
    enterprise_value: float,
    total_debt: float,
    cash: float,
    minority_interest: float = 0,
    preferred_shares: float = 0,
) -> float:
    """
    Calculate equity value from enterprise value.

    Equity Value = EV - Debt + Cash - Minority Interest - Preferred Shares
    """
    return enterprise_value - total_debt + cash - minority_interest - preferred_shares


def calculate_implied_share_price(
    equity_value: float,
    shares_outstanding: float,
) -> float:
    """Calculate implied share price from equity value."""
    if shares_outstanding <= 0:
        return 0
    return equity_value / shares_outstanding


def full_dcf_valuation(
    fcf_projections: Dict[str, List[float]],
    wacc: float,
    terminal_growth: float,
    total_debt: float,
    cash: float,
    shares_outstanding: float,
    current_price: float = None,
) -> Dict[str, Any]:
    """
    Complete DCF valuation from FCF to implied share price.

    Returns comprehensive valuation results.
    """
    # Terminal value (perpetuity growth method)
    final_fcf = fcf_projections["free_cash_flow"][-1]
    terminal_value = final_fcf * (1 + terminal_growth) / (wacc - terminal_growth)

    # Enterprise value
    ev_result = calculate_enterprise_value(
        fcf_projections["free_cash_flow"], wacc, terminal_value
    )

    # Equity value
    equity_value = calculate_equity_value(
        ev_result["enterprise_value"], total_debt, cash
    )

    # Implied share price
    implied_price = calculate_implied_share_price(equity_value, shares_outstanding)

    # Calculate upside/downside
    if current_price:
        upside = (implied_price - current_price) / current_price
    else:
        upside = None

    return {
        "terminal_value": terminal_value,
        "enterprise_value": ev_result["enterprise_value"],
        "equity_value": equity_value,
        "implied_share_price": implied_price,
        "current_price": current_price,
        "upside_downside": upside,
        "fcf_projections": fcf_projections,
        "wacc": wacc,
        "terminal_growth": terminal_growth,
        "npv_breakdown": ev_result["npv_breakdown"],
        "sum_fcf_pv": ev_result["sum_fcf_pv"],
        "discounted_tv": ev_result["discounted_tv"],
    }


def sensitivity_analysis(
    fcf_projections: Dict[str, List[float]],
    base_wacc: float,
    base_terminal_growth: float,
    total_debt: float,
    cash: float,
    shares_outstanding: float,
    wacc_range: List[float] = None,
    growth_range: List[float] = None,
) -> Dict[str, List[float]]:
    """
    Create sensitivity table for WACC vs terminal growth.

    Returns a matrix of implied share prices.
    """
    if wacc_range is None:
        wacc_range = [base_wacc - 0.02, base_wacc - 0.01, base_wacc, base_wacc + 0.01, base_wacc + 0.02]
    if growth_range is None:
        growth_range = [base_terminal_growth - 0.01, base_terminal_growth, base_terminal_growth + 0.01]

    sensitivity = {}
    for wacc in wacc_range:
        row = []
        for growth in growth_range:
            if wacc > growth:  # Valid combination
                result = full_dcf_valuation(
                    fcf_projections, wacc, growth, total_debt, cash, shares_outstanding
                )
                row.append(result["implied_share_price"])
            else:
                row.append(None)  # Invalid: WACC <= growth
        sensitivity[f"{wacc:.1%}"] = row

    return {
        "wacc_range": [f"{w:.1%}" for w in wacc_range],
        "growth_range": [f"{g:.1%}" for g in growth_range],
        "matrix": sensitivity,
    }
