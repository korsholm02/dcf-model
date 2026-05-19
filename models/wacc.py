"""
WACC (Weighted Average Cost of Capital) calculation.
Uses CAPM for cost of equity.
"""
from typing import Optional, Dict, Any
import numpy as np

# Default market parameters (can be overridden)
DEFAULT_RISK_FREE_RATE = 0.04  # 4% - approx 10Y treasury
DEFAULT_MARKET_RISK_PREMIUM = 0.055  # 5.5% - historical average
DEFAULT_TAX_RATE = 0.25  # 25% corporate tax


def calculate_wacc(
    market_cap: float,
    total_debt: float,
    beta: float,
    risk_free_rate: float = DEFAULT_RISK_FREE_RATE,
    market_risk_premium: float = DEFAULT_MARKET_RISK_PREMIUM,
    cost_of_debt: float = 0.05,
    tax_rate: float = DEFAULT_TAX_RATE,
    size_premium: float = 0.0,
    company_specific_premium: float = 0.0,
) -> float:
    """
    Calculate WACC using CAPM for cost of equity.

    Formula:
    WACC = (E/V) * Re + (D/V) * Rd * (1-t)

    Where:
    - E = Market value of equity
    - D = Market value of debt
    - V = E + D (total value)
    - Re = Cost of equity (from CAPM)
    - Rd = Cost of debt
    - t = Tax rate

    CAPM: Re = Rf + β * (Rm - Rf) + premiums
    """
    # Total capital
    equity = market_cap
    debt = total_debt
    total_value = equity + debt

    if total_value == 0:
        return 0.10  # Default to 10% if no capital structure

    # Weights
    weight_equity = equity / total_value
    weight_debt = debt / total_value

    # Cost of equity (CAPM)
    cost_of_equity = (
        risk_free_rate
        + beta * market_risk_premium
        + size_premium
        + company_specific_premium
    )

    # After-tax cost of debt
    after_tax_cost_of_debt = cost_of_debt * (1 - tax_rate)

    # WACC
    wacc = weight_equity * cost_of_equity + weight_debt * after_tax_cost_of_debt

    return wacc


def get_default_beta(industry: str = None) -> float:
    """
    Get default beta based on industry if not available from data.
    """
    industry_betas = {
        "technology": 1.2,
        "healthcare": 0.9,
        "finance": 1.1,
        "consumer": 0.8,
        "industrial": 1.0,
        "energy": 1.3,
        "utilities": 0.6,
        "telecom": 0.7,
    }
    if industry:
        industry_lower = industry.lower()
        for key, beta in industry_betas.items():
            if key in industry_lower:
                return beta
    return 1.0  # Market beta


def calculate_cost_of_equity(
    beta: float,
    risk_free_rate: float = DEFAULT_RISK_FREE_RATE,
    market_risk_premium: float = DEFAULT_MARKET_RISK_PREMIUM,
    size_premium: float = 0.0,
    company_specific_premium: float = 0.0,
) -> float:
    """Calculate cost of equity using CAPM."""
    return (
        risk_free_rate
        + beta * market_risk_premium
        + size_premium
        + company_specific_premium
    )
