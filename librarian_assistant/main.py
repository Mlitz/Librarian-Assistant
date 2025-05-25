# ABOUTME: This file is the main entry point for the Librarian-Assistant application.
# ABOUTME: It defines the main window and initializes the application.

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QLineEdit, 
                             QVBoxLayout, QLabel, QGroupBox, QStatusBar, QPushButton)
from PyQt5.QtGui import QIntValidator, QValidator # Import QIntValidator and QValidator
from PyQt5.QtCore import Qt # For dialog results, though not directly used in this snippet

# Import ConfigManager for Prompt 2.2
from librarian_assistant.config_manager import ConfigManager
# Import TokenDialog for Prompt 2.2
from librarian_assistant.token_dialog import TokenDialog

import logging
logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main application window for Librarian-Assistant.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Librarian-Assistant - Hardcover.app Edition Viewer")
        self.resize(800, 600)

        self.config_manager = ConfigManager()

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.main_view_tab_content = QWidget()
        main_view_layout = QVBoxLayout(self.main_view_tab_content)

        self.api_input_area = QGroupBox("API & Book ID Input Area")
        self.api_input_area.setObjectName("apiInputArea")
        api_layout = QVBoxLayout(self.api_input_area)
        self.token_display_label = QLabel("Token: Not Set")
        self.token_display_label.setObjectName("tokenDisplayLabel")
        api_layout.addWidget(self.token_display_label)

        self.set_token_button = QPushButton("Set/Update Token")
        self.set_token_button.setObjectName("setTokenButton")
        self.set_token_button.clicked.connect(self._open_set_token_dialog)
        api_layout.addWidget(self.set_token_button)

        # Add Book ID input elements as per Prompt 3.1
        self.book_id_label = QLabel("Book ID:")
        self.book_id_label.setObjectName("bookIdLabel")
        api_layout.addWidget(self.book_id_label)

        self.book_id_line_edit = QLineEdit()
        self.book_id_line_edit.setObjectName("bookIdLineEdit")
        # Placeholder text can be useful for users
        # Add QIntValidator to allow only numbers
        self.book_id_line_edit.setValidator(QIntValidator())
        self.book_id_line_edit.textChanged.connect(self._on_book_id_text_changed)
        self.book_id_line_edit.setPlaceholderText("Enter numerical Book ID")
        api_layout.addWidget(self.book_id_line_edit)

        self.fetch_data_button = QPushButton("Fetch Data")
        self.fetch_data_button.setObjectName("fetchDataButton")
        self.fetch_data_button.clicked.connect(self._on_fetch_data_clicked) # Connect signal
        api_layout.addWidget(self.fetch_data_button)

        main_view_layout.addWidget(self.api_input_area)

        self.book_info_area = QGroupBox("General Book Information Area")
        self.book_info_area.setObjectName("bookInfoArea")
        info_layout = QVBoxLayout(self.book_info_area)
        info_layout.addWidget(QLabel("Placeholder for general book information"))
        main_view_layout.addWidget(self.book_info_area)

        self.editions_table_area = QGroupBox("Editions Table Area")
        self.editions_table_area.setObjectName("editionsTableArea")
        table_layout = QVBoxLayout(self.editions_table_area)
        table_layout.addWidget(QLabel("Placeholder for editions table"))
        main_view_layout.addWidget(self.editions_table_area)

        main_view_layout.setStretchFactor(self.api_input_area, 0)
        main_view_layout.setStretchFactor(self.book_info_area, 1)
        main_view_layout.setStretchFactor(self.editions_table_area, 3)

        self.tab_widget.addTab(self.main_view_tab_content, "Main View")

        self.history_tab_content = QWidget()
        history_layout = QVBoxLayout(self.history_tab_content)
        history_label = QLabel("History")
        history_layout.addWidget(history_label)
        self.tab_widget.addTab(self.history_tab_content, "History")

        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

        self._update_token_display()


    def _open_set_token_dialog(self):
        """
        Opens the dialog for setting or updating the API token.
        If the dialog is accepted, the token is processed.
        """
        dialog = TokenDialog(self)
        # Connect the dialog's signal to the handler method
        dialog.token_accepted.connect(self._handle_token_accepted)
        dialog.exec_() # Show the dialog modally

    def _handle_token_accepted(self, token: str):
        """
        Handles the token received from TokenDialog.
        Saves the token and updates the display.
        """
        self.config_manager.save_token(token)
        self._update_token_display()

    def _update_token_display(self):
        """
        Updates the token display label based on the token in ConfigManager.
        """
        current_token = self.config_manager.load_token()
        if current_token: # Checks if token is not None and not an empty string
            self.token_display_label.setText("Token: *******")
        else:
            self.token_display_label.setText("Token: Not Set")

    def _on_book_id_text_changed(self, text: str):
        """
        If the text in book_id_line_edit changes to something
        that QIntValidator deems Invalid, clear the line edit.
        This ensures programmatic setText("abc") results in an empty field,
        aligning with test expectations. QIntValidator itself handles direct 
        user input prevention by not allowing invalid characters to be typed.
        """
        validator = self.book_id_line_edit.validator()
        if validator is not None:
            # 'text' is the new content of the QLineEdit after the change.
            state, _, _ = validator.validate(text, 0) 
            if state == QValidator.Invalid:
                self.book_id_line_edit.blockSignals(True) # Prevent recursion
                self.book_id_line_edit.setText("")
                self.book_id_line_edit.blockSignals(False)

    def _on_fetch_data_clicked(self):
        """
        Handles the "Fetch Data" button click.
        Logs the current Book ID and token status.
        """
        book_id = self.book_id_line_edit.text()
        token = self.config_manager.load_token()

        token_status_message = "Set" if token else "Not Set"
        
        logger.info(
            f"Fetch Data clicked. Book ID: '{book_id}'. Token status: {token_status_message}."
        )

def main():
    """
    Main function to initialize and run the application.
    """
    app = QApplication(sys.argv)

    app.setStyleSheet("""
        QWidget {
            background-color: #3c3c3c; 
            color: #cccccc; 
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
            font-size: 10pt; /* <<< Added to increase default font size */
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
            padding: 8px; /* May need adjustment if font becomes much larger */
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
            font-weight: bold; /* This will remain bold */
            border: 1px solid #555555;
            border-radius: 4px;
            margin-top: 6px; 
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left; 
            padding: 0 3px; /* May need minor adjustment if font is very large */
            left: 10px; 
        }
        QStatusBar {
            color: #cccccc;
        }
        QLabel {
            color: #cccccc;
        }
        QPushButton { 
            background-color: #555555; 
            color: #cccccc;
            border: 1px solid #666666; 
            padding: 4px 8px; /* May need adjustment */
            min-height: 20px; 
        }
        QPushButton:hover { 
            background-color: #6a6a6a; 
        }
        QPushButton:pressed { 
            background-color: #454545; 
        }
        QLineEdit { 
            border: 1px solid #555555; 
            background-color: #454545; 
            color: #cccccc;
            padding: 2px; 
        }
    """)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()