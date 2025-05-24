# ABOUTME: This file contains unit tests for the main application window.
# ABOUTME: It ensures the main window initializes correctly and has basic UI elements.

import sys
import pytest
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QLabel, 
                             QWidget, QVBoxLayout, QGroupBox, QStatusBar)
from librarian_assistant.main import MainWindow

@pytest.fixture(scope="session")
def qt_app(request):
    app = QApplication.instance()
    if app is None:
        app_argv = sys.argv if hasattr(sys, 'argv') and sys.argv is not None else []
        app = QApplication(app_argv)
    
    def fin():
        if hasattr(sys, 'argv') and sys.argv is not None: 
            current_app = QApplication.instance()
            if current_app:
                 current_app.quit() 
    
    if hasattr(sys, 'argv') and sys.argv is not None:
        request.addfinalizer(fin)
    return app

@pytest.fixture
def main_window_instance(qt_app):
    """Provides an instance of MainWindow for testing."""
    window = MainWindow()
    yield window
    window.close() 

def test_main_window_creation_and_title(main_window_instance):
    window = main_window_instance
    assert window is not None, "Main window should be created."
    expected_title = "Librarian-Assistant - Hardcover.app Edition Viewer"
    assert window.windowTitle() == expected_title, f"Window title should be '{expected_title}'"

def test_tab_widget_exists(main_window_instance):
    window = main_window_instance
    tab_widget = window.findChild(QTabWidget)
    if not tab_widget and window.centralWidget():
        tab_widget = window.centralWidget().findChild(QTabWidget)
    assert tab_widget is not None, "MainWindow should have a QTabWidget."

def test_tab_widget_has_correct_tabs_and_content(main_window_instance): # <--- THIS TEST IS MODIFIED
    window = main_window_instance
    tab_widget = window.findChild(QTabWidget)
    if not tab_widget and window.centralWidget():
        tab_widget = window.centralWidget().findChild(QTabWidget)

    assert tab_widget is not None, "QTabWidget not found."
    assert tab_widget.count() == 2, f"Expected 2 tabs, but found {tab_widget.count()}."

    # Test "Main View" tab
    main_view_tab_content_widget = tab_widget.widget(0) 
    assert main_view_tab_content_widget is not None, "Widget for 'Main View' tab not found."
    assert tab_widget.tabText(0) == "Main View", "First tab title should be 'Main View'."
    
    main_view_labels = main_view_tab_content_widget.findChildren(QLabel)
    # As per Prompt 1.3, the "Main View" tab now contains QGroupBoxes with their own labels.
    # The original simple QLabel("Main View") from Prompt 1.2 is replaced by this structure.
    # So, we just check that there are QLabels present within the tab (inside the group boxes).
    assert len(main_view_labels) > 0, "No QLabels found in 'Main View' tab. It should contain placeholder labels within its group boxes."
    # The specific check for a QLabel with text "Main View" is removed as the content has evolved.
    # The actual content (group boxes) is verified by test_main_view_tab_layout_and_placeholders.

    # Test "History" tab (this part remains the same)
    history_tab_content_widget = tab_widget.widget(1) 
    assert history_tab_content_widget is not None, "Widget for 'History' tab not found."
    assert tab_widget.tabText(1) == "History", "Second tab title should be 'History'."

    history_labels = history_tab_content_widget.findChildren(QLabel)
    assert len(history_labels) > 0, "No QLabel found in 'History' tab." # Should find one
    history_label_found = any(label.text() == "History" for label in history_labels)
    assert history_label_found, "QLabel with text 'History' not found in 'History' tab."


def test_main_view_tab_layout_and_placeholders(main_window_instance):
    window = main_window_instance
    tab_widget = window.centralWidget() 
    assert isinstance(tab_widget, QTabWidget), "Central widget is not a QTabWidget."

    main_view_tab_content = tab_widget.widget(0)
    assert main_view_tab_content is not None, "'Main View' tab content widget not found."
    assert isinstance(main_view_tab_content.layout(), QVBoxLayout), "'Main View' tab should have a QVBoxLayout."

    api_area = main_view_tab_content.findChild(QGroupBox, "apiInputArea")
    assert api_area is not None, "'API & Book ID Input Area' QGroupBox not found."
    assert api_area.title() == "API & Book ID Input Area", "Incorrect title for API input area."

    info_area = main_view_tab_content.findChild(QGroupBox, "bookInfoArea")
    assert info_area is not None, "'General Book Information Area' QGroupBox not found."
    assert info_area.title() == "General Book Information Area", "Incorrect title for book info area."

    table_area = main_view_tab_content.findChild(QGroupBox, "editionsTableArea")
    assert table_area is not None, "'Editions Table Area' QGroupBox not found."
    assert table_area.title() == "Editions Table Area", "Incorrect title for editions table area."

def test_main_window_has_status_bar(main_window_instance):
    window = main_window_instance
    status_bar = window.statusBar()
    assert status_bar is not None, "MainWindow should have a QStatusBar."
    assert isinstance(status_bar, QStatusBar), "statusBar() should return a QStatusBar instance."