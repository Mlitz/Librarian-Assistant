# ABOUTME: This file defines the TokenDialog for entering the API Bearer Token.
# ABOUTME: It provides a simple dialog with input field, OK, and Cancel buttons.

from PyQt5.QtWidgets import (QDialog, QLabel, QLineEdit, QPushButton, 
                             QVBoxLayout, QHBoxLayout, QDialogButtonBox)
from PyQt5.QtCore import pyqtSignal, Qt

class TokenDialog(QDialog):
    """
    A dialog for users to input their Hardcover.app Bearer Token.
    Emits a 'token_accepted' signal with the token string when OK is clicked.
    """
    token_accepted = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set API Token")
        self.setMinimumWidth(400) # Optional: give it a decent minimum width

        # Main layout
        main_layout = QVBoxLayout(self)

        # Instruction Label
        self.instruction_label = QLabel("Enter your Hardcover.app Bearer Token:")
        self.instruction_label.setObjectName("instructionLabel") # For testability
        self.instruction_label.setWordWrap(True) # Ensure text wraps if too long
        main_layout.addWidget(self.instruction_label)

        # Token Input LineEdit
        self.token_input_line_edit = QLineEdit()
        self.token_input_line_edit.setObjectName("tokenLineEdit") # For testability
        self.token_input_line_edit.setPlaceholderText("Paste your token here") # Optional
        main_layout.addWidget(self.token_input_line_edit)

        # Dialog Buttons (OK and Cancel)
        # Using QDialogButtonBox for standard button layout and roles
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        
        # Get the actual QPushButton objects for objectName and testability if needed
        ok_button = self.button_box.button(QDialogButtonBox.Ok)
        ok_button.setObjectName("okButton") # Set object name for test

        cancel_button = self.button_box.button(QDialogButtonBox.Cancel)
        cancel_button.setObjectName("cancelButton") # Set object name for test
        
        self.button_box.accepted.connect(self.handle_ok_clicked) # QDialogButtonBox.accepted signal
        self.button_box.rejected.connect(self.reject)         # QDialogButtonBox.rejected signal

        main_layout.addWidget(self.button_box)
        
        self.setLayout(main_layout)

        # The dialog should inherit the application's dark theme stylesheet automatically.

    def handle_ok_clicked(self):
        """
        Handles the OK button click. Emits the token and accepts the dialog.
        """
        token = self.token_input_line_edit.text().strip()
        # Optionally, you could add validation here (e.g., check if token is empty)
        # if not token:
        #     # Handle empty token case, e.g., show a QMessageBox or shake the dialog
        #     # For now, we'll allow empty tokens as per current test scope.
        #     pass 
        self.token_accepted.emit(token)
        self.accept() # Standard QDialog method to close with Accepted result

    # For testability by objectName if not using QDialogButtonBox's buttons directly
    # However, the tests currently use findChild with the names set on QDialogButtonBox's buttons.
    def findChild(self, child_type, child_name):
        """Override findChild to also check buttons within QDialogButtonBox if needed."""
        if child_type == QPushButton:
            if child_name == "okButton" and self.button_box.button(QDialogButtonBox.Ok):
                return self.button_box.button(QDialogButtonBox.Ok)
            if child_name == "cancelButton" and self.button_box.button(QDialogButtonBox.Cancel):
                return self.button_box.button(QDialogButtonBox.Cancel)
        return super().findChild(child_type, child_name)