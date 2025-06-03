# ABOUTME: This file provides shared pytest fixtures for PyQt6 tests.
# ABOUTME: It ensures only one QApplication instance exists during test runs.

import pytest
import sys
from PyQt6.QtWidgets import QApplication

# Global reference to QApplication instance
_app = None


@pytest.fixture(scope='session')
def qapp():
    """Provides a QApplication instance for the entire test session."""
    global _app
    if _app is None:
        _app = QApplication.instance()
        if _app is None:
            _app = QApplication(sys.argv)
    return _app


@pytest.fixture(autouse=True)
def ensure_qapp_exists(qapp):
    """Automatically ensures QApplication exists for all tests."""
