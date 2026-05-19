"""
Generate default assumptions from historical data.
Used for hybrid budgeting - shows historical baseline as starting point.
"""
from typing import Dict, Any, List
import numpy as np


def generate_default_assumptions(
    historical_metrics: Dict[str, float],
    num_years: int = 5,
) -> Dict[str, List[float]]:
    """
    Generate default forecast assumptions based on historical metrics.

    Uses a conservative fade approach:
    - High growth companies: growth fades toward GDP growth (~2%)
    - Low/stable growth: maintains historical average

    Returns assumptions dict ready for FCF projection.
    """
    base_growth = historical_metrics.get("revenue_cagr", 0.05)
    base_margin = historical_metrics.get("avg_ebit_margin", 0.10)
    base_tax = historical_metrics.get("avg_tax_rate", 0.25)
    base_dep = historical_metrics.get("avg_dep_pct", 0.03)
    base_capex = historical_metrics.get("avg_capex_pct", 0.05)
    base_nwc = historical_metrics.get("avg_nwc_pct", 0.01)

    # Fade growth toward terminal rate (GDP growth ~2%)
    terminal_growth = 0.02
    growth_fade = (base_growth - terminal_growth) / num_years

    assumptions = {
        "revenue_growth": [],
        "ebit_margin": [],
        "tax_rate": [],
        "dep_pct": [],
        "capex_pct": [],
        "nwc_pct": [],
    }

    for i in range(num_years):
        # Growth fades linearly toward terminal
        growth = max(base_growth - growth_fade * i, terminal_growth)
        assumptions["revenue_growth"].append(growth)

        # Margins stay stable (could add mean reversion if desired)
        assumptions["ebit_margin"].append(base_margin)

        # Tax rate stable
        assumptions["tax_rate"].append(base_tax)

        # Operating assumptions stable
        assumptions["dep_pct"].append(base_dep)
        assumptions["capex_pct"].append(base_capex)
        assumptions["nwc_pct"].append(base_nwc)

    return assumptions


def create_conservative_assumptions(
    historical_metrics: Dict[str, float],
    num_years: int = 5,
) -> Dict[str, List[float]]:
    """
    Create conservative assumptions (bear case baseline).
    - 20% lower growth than historical
    - 10% lower margins
    """
    base = generate_default_assumptions(historical_metrics, num_years)

    # Apply conservative haircuts
    base["revenue_growth"] = [g * 0.8 for g in base["revenue_growth"]]
    base["ebit_margin"] = [m * 0.9 for m in base["ebit_margin"]]

    return base


def create_aggressive_assumptions(
    historical_metrics: Dict[str, float],
    num_years: int = 5,
) -> Dict[str, List[float]]:
    """
    Create aggressive assumptions (bull case baseline).
    - 20% higher growth than historical (capped at 25%)
    - 10% higher margins
    """
    base = generate_default_assumptions(historical_metrics, num_years)

    # Apply aggressive boosts
    base["revenue_growth"] = [min(g * 1.2, 0.25) for g in base["revenue_growth"]]
    base["ebit_margin"] = [m * 1.1 for m in base["ebit_margin"]]

    return base


def get_scenario_assumptions(
    historical_metrics: Dict[str, float],
    scenario: str = "base",
    num_years: int = 5,
) -> Dict[str, List[float]]:
    """
    Get assumptions for a specific scenario.
    """
    if scenario == "bear":
        return create_conservative_assumptions(historical_metrics, num_years)
    elif scenario == "bull":
        return create_aggressive_assumptions(historical_metrics, num_years)
    else:
        return generate_default_assumptions(historical_metrics, num_years)
