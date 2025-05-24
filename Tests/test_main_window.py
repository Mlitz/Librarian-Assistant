# ABOUTME: This file contains unit tests for the main application window.
# ABOUTME: It ensures the main window initializes correctly.

import pytest
from PyQt5.QtWidgets import QApplication
import sys # <--- Add this import
import os  # <--- Add this import

@pytest.fixture(scope="session")
def qt_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

def test_main_window_creation_and_title(qt_app):
    """
    Tests if the MainWindow can be created and has the correct title.
    """
    print(f"\nDEBUG: Current Working Directory: {os.getcwd()}") # <--- Add this
    print(f"DEBUG: sys.path:")                                 # <--- Add this
    for p in sys.path:                                         # <--- Add this
        print(f"  {p}")                                        # <--- Add this
    print("DEBUG: Attempting import...")                       # <--- Add this

    from librarian_assistant.main import MainWindow # This is line 23 (or around it)

    window = MainWindow()
    assert window is not None, "Main window should be created."
    expected_title = "Librarian-Assistant - Hardcover.app Edition Viewer"
    assert window.windowTitle() == expected_title, f"Window title should be '{expected_title}'"
    window.close()