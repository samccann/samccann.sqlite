"""Pytest configuration for samccann.sqlite unit tests."""

import os
import sys

# Add the modules directory to sys.path for importing
sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "plugins", "modules"),
)
