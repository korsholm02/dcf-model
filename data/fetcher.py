"""
Data fetching from Yahoo Finance.
Supports both listed companies (auto-fetch) and manual input for non-listed.
"""
import yfinance as yf
import pandas as pd
from typing import Optional, Dict, Any


def fetch_financials(ticker: str) -> Optional[Dict[str, Any]]:
    """
    Fetch all required financial data for a ticker.

    Returns dict with:
    - income_stmt: Annual income statement
    - balance_sheet: Annual balance sheet
    - cashflow: Annual cash flow statement
    - key_stats: Key statistics (beta, shares, etc.)
    - price: Current price info
    """
    try:
        stock = yf.Ticker(ticker)

        # Fetch financial statements
        income_stmt = stock.financials
        balance_sheet = stock.balance_sheet
        cashflow = stock.cashflow

        # Fetch key statistics
        info = stock.info

        # Validate we have data
        if income_stmt.empty or balance_sheet.empty:
            print(f"Warning: No financial data found for {ticker}")
            return None

        return {
            "ticker": ticker,
            "company_name": info.get("longName", ticker),
            "currency": info.get("currency", "USD"),
            "income_stmt": income_stmt,
            "balance_sheet": balance_sheet,
            "cashflow": cashflow,
            "info": info,
        }
    except Exception as e:
        print(f"Error fetching data for {ticker}: {e}")
        return None


def get_current_price(ticker: str) -> Optional[float]:
    """Get current stock price."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return info.get("currentPrice") or info.get("previousClose")
    except Exception as e:
        print(f"Error fetching price for {ticker}: {e}")
        return None


def get_market_cap(ticker: str) -> Optional[float]:
    """Get market cap in the currency of the stock."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return info.get("marketCap")
    except Exception as e:
        print(f"Error fetching market cap for {ticker}: {e}")
        return None


def get_shares_outstanding(ticker: str) -> Optional[float]:
    """Get shares outstanding."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return info.get("sharesOutstanding")
    except Exception as e:
        print(f"Error fetching shares for {ticker}: {e}")
        return None
