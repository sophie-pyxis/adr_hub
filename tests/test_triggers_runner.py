#!/usr/bin/env python
"""
Standalone test runner for trigger service tests.
Avoids the circular import chain in main conftest.py.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

# Run just the trigger tests
if __name__ == "__main__":
    # Use minimal configuration - don't load problematic conftest.py
    pytest.main(
        [
            "tests/test_triggers.py",
            "-v",
            "--tb=short",
            "--import-mode=importlib",  # Use importlib mode to avoid conftest issues
            "-p",
            "no:cacheprovider",  # Disable cache to avoid issues
        ]
    )
