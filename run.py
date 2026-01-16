#!/usr/bin/env python3
"""
Run script for the AI Tutoring Agent
Usage: python run.py --set mini_dev
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from agent import main

if __name__ == "__main__":
    main()
