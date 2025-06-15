"""
Configuration file for pytest.
This file is automatically loaded by pytest and can contain fixtures, hooks, and other setup code.
"""

import os
import sys
import pytest

# Add the project root to the path so imports work correctly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure pytest to recognize the asyncio marker
pytest_plugins = ["pytest_asyncio"] 