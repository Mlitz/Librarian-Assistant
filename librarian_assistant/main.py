# ABOUTME: This file is the main entry point for the Librarian-Assistant application.
# ABOUTME: It defines the main window and initializes the application.

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel

class MainWindow(QMainWindow):
    """
    Main application window for Librarian-Assistant.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Librarian-Assistant - Hardcover.app Edition Viewer")
        self.resize(800, 600) # Optional: give it a default size

        # Create Tab Widget
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget) # Set it as the central widget

        # --- Main View Tab ---
        self.main_view_tab = QWidget()
        main_view_layout = QVBoxLayout(self.main_view_tab) # Set layout for the tab content widget
        main_view_label = QLabel("Main View")
        main_view_layout.addWidget(main_view_label)
        # self.main_view_tab.setLayout(main_view_layout) # QVBoxLayout constructor already sets it
        self.tab_widget.addTab(self.main_view_tab, "Main View")

        # --- History Tab ---
        self.history_tab = QWidget()
        history_layout = QVBoxLayout(self.history_tab) # Set layout for the tab content widget
        history_label = QLabel("History")
        history_layout.addWidget(history_label)
        # self.history_tab.setLayout(history_layout) # QVBoxLayout constructor already sets it
        self.tab_widget.addTab(self.history_tab, "History")

def main():
    """
    Main function to initialize and run the application.
    """
    app = QApplication(sys.argv)

    # Basic dark theme stylesheet
    app.setStyleSheet("""
        QWidget {
            background-color: #3c3c3c; 
            color: #cccccc; 
        }
        QMainWindow {
            background-color: #2b2b2b;
        }
        QTabWidget::pane { /* The tab widget frame */
            border-top: 2px solid #555555;
        }
        QTabBar::tab { /* Style for non-selected tabs */
            background: #4a4a4a;
            color: #cccccc;
            padding: 8px;
            border: 1px solid #555555;
            border-bottom-color: #555555; /* Same as pane border */
        }
        QTabBar::tab:selected { /* Style for selected tab */
            background: #3c3c3c; /* Should match QWidget background or pane */
            color: #ffffff;
            margin-bottom: -1px; /* Make selected tab merge with the pane */
            border-bottom-color: #3c3c3c; /* Match pane background */
        }
        QTabBar::tab:hover {
            background: #5a5a5a;
        }
        QLabel {
            /* You can add specific QLabel styling here if needed */
            /* For now, it will inherit from QWidget */
        }
    """)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()