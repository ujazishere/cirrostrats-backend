#!/usr/bin/env python3
"""
Notebook Import Path Update Helper

This script helps update import paths in Jupyter notebooks after they were moved
to the notebooks/ directory during project restructuring.

Usage:
1. Run this script from the notebooks/ directory
2. It will add the parent directory to Python path
3. Import your project modules normally

Add this to the first cell of each notebook:
"""

import sys
import os

# Add parent directory (project root) to Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

print(f"Added to Python path: {parent_dir}")
print("You can now import project modules normally:")
print("  from config.database import db_UJ")
print("  from routes.root.root_class import Root_class")
print("  from routes.route import get_search_suggestions")
