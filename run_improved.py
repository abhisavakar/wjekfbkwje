#!/usr/bin/env python3
"""
OPTIMIZED Run Script for Perfect Scores
Target: MSE = 0.0, Tutoring = 5.0

Usage: python run_improved.py --set mini_dev
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import improved agent
from agent_improved import main

if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║  Knowunity AI Tutor Agent - OPTIMIZED VERSION             ║
║  Target: MSE = 0.0, Tutoring Score = 5.0                   ║
╚════════════════════════════════════════════════════════════╝
""")
    main()
