#!/usr/bin/env python3
"""
DCF Analyzer - Main entry point.
Run with: streamlit run main.py
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the dashboard
from ui.dashboard import *

# This file is meant to be run with Streamlit:
#   streamlit run main.py
#
# Or you can run directly:
#   python -m streamlit run main.py
