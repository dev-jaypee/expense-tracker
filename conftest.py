"""
Pytest configuration file.

This file's only job is to make sure the project root (where app.py
lives) is on Python's import path, no matter how or from where pytest
is invoked. Pytest automatically loads conftest.py before collecting
any tests, so this runs before tests/test_app.py tries to import app.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
