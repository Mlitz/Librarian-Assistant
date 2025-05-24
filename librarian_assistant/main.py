# ABOUTME: This file is the main entry point for the Librarian-Assistant application.
# ABOUTME: It defines the main window and initializes the application.

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, 
                             QVBoxLayout, QLabel, QGroupBox, QStatusBar) # Added QGroupBox, QStatusBar

class MainWindow(QMainWindow):
    """
    Main application window for Librarian-Assistant.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Librarian-Assistant - Hardcover.app Edition Viewer")
        self.resize(800, 600)

        # Create Tab Widget
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # --- Main View Tab ---
        self.main_view_tab_content = QWidget() # Renamed for clarity
        # Ensure this tab content widget has a QVBoxLayout
        main_view_layout = QVBoxLayout(self.main_view_tab_content)
        # self.main_view_tab_content.setLayout(main_view_layout) # Constructor does this

        # Remove the old general QLabel for "Main View" if it was just a placeholder
        # Find and remove the old label if it exists and is directly in main_view_layout
        # This assumes the old label was the only widget. If not, this needs care.
        # For now, we'll just add new group boxes. If the old label is still there,
        # it won't break tests but might look odd. Let's assume it's replaced by the new structure.
        
        # Placeholder: API & Book ID Input Area
        self.api_input_area = QGroupBox("API & Book ID Input Area")
        self.api_input_area.setObjectName("apiInputArea")
        # To make it distinguishable and have some content for now:
        api_layout = QVBoxLayout(self.api_input_area)
        api_layout.addWidget(QLabel("Placeholder for API input controls"))
        main_view_layout.addWidget(self.api_input_area)

        # Placeholder: General Book Information Area
        self.book_info_area = QGroupBox("General Book Information Area")
        self.book_info_area.setObjectName("bookInfoArea")
        info_layout = QVBoxLayout(self.book_info_area)
        info_layout.addWidget(QLabel("Placeholder for general book information"))
        main_view_layout.addWidget(self.book_info_area)

        # Placeholder: Editions Table Area
        self.editions_table_area = QGroupBox("Editions Table Area")
        self.editions_table_area.setObjectName("editionsTableArea")
        table_layout = QVBoxLayout(self.editions_table_area)
        table_layout.addWidget(QLabel("Placeholder for editions table"))
        main_view_layout.addWidget(self.editions_table_area)
        
        # Adjust stretch factors to make the table area larger
        main_view_layout.setStretchFactor(self.api_input_area, 0) # Minimal height
        main_view_layout.setStretchFactor(self.book_info_area, 1) # Some height
        main_view_layout.setStretchFactor(self.editions_table_area, 3) # Largest height

        self.tab_widget.addTab(self.main_view_tab_content, "Main View")

        # --- History Tab ---
        self.history_tab_content = QWidget() # Renamed for clarity
        history_layout = QVBoxLayout(self.history_tab_content)
        history_label = QLabel("History") # This is the placeholder content from Prompt 1.2
        history_layout.addWidget(history_label)
        self.tab_widget.addTab(self.history_tab_content, "History")

        # --- Status Bar ---
        # QMainWindow creates a status bar automatically when statusBar() is first called.
        # Calling it here ensures it exists for tests and can be used.
        self.status_bar = self.statusBar() 
        self.status_bar.showMessage("Ready") # Optional: initial message

def main():
    """
    Main function to initialize and run the application.
    """
    app = QApplication(sys.argv)

    # Basic dark theme stylesheet (includes QTabBar styling from previous step)
    app.setStyleSheet("""
        QWidget {
            background-color: #3c3c3c; 
            color: #cccccc; 
        }
        QMainWindow {
            background-color: #2b2b2b;
        }
        QTabWidget::pane {
            border-top: 2px solid #555555;
        }
        QTabBar::tab {
            background: #4a4a4a;
            color: #cccccc;
            padding: 8px;
            border: 1px solid #555555;
            border-bottom-color: #555555; 
        }
        QTabBar::tab:selected {
            background: #3c3c3c; 
            color: #ffffff;
            margin-bottom: -1px; 
            border-bottom-color: #3c3c3c;
        }
        QTabBar::tab:hover {
            background: #5a5a5a;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #555555;
            border-radius: 4px;
            margin-top: 6px; /* Space for the title */
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left; /* Position at the top left */
            padding: 0 3px;
            left: 10px; /* Indent from the left edge */
        }
        QStatusBar {
            /* Add specific QStatusBar styling here if needed */
            /* For now, it will inherit from QWidget or QMainWindow */
        }
        QLabel {
            /* For now, it will inherit from QWidget */
        }
    """)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()