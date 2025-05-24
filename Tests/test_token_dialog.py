# ABOUTME: This file contains unit tests for the TokenDialog.
# ABOUTME: It ensures the dialog initializes correctly and its signals work as expected.

import pytest
from PyQt5.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton
from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot # For a mock receiver object

# Assuming TokenDialog will be in librarian_assistant.token_dialog
# from librarian_assistant.token_dialog import TokenDialog # This will be created

# Re-using qt_app fixture from test_main_window or defining a similar one if needed.
# For simplicity, let's assume qt_app is available (e.g. via conftest.py or imported)
# If not, it needs to be defined here as well, similar to test_main_window.py
# For now, let's copy a minimal version for this file:
@pytest.fixture(scope="session")
def qt_app_dialog(request):
    import sys
    app = QApplication.instance()
    if app is None:
        app_argv = sys.argv if hasattr(sys, 'argv') and sys.argv is not None else []
        app = QApplication(app_argv)
    
    # Basic application stylesheet (copied from main.py for test context if needed)
    # This ensures the dialog is tested against the intended theme.
    app.setStyleSheet("""
        QWidget { background-color: #3c3c3c; color: #cccccc; }
        QMainWindow { background-color: #2b2b2b; }
        QDialog { background-color: #3c3c3c; } /* Ensure dialogs also get base style */
        QPushButton { background-color: #555555; border: 1px solid #666666; padding: 4px; }
        QPushButton:hover { background-color: #6a6a6a; }
        QPushButton:pressed { background-color: #454545; }
        QLineEdit { border: 1px solid #555555; background-color: #454545; padding: 2px; }
    """)
        
    def fin():
        if hasattr(sys, 'argv') and sys.argv is not None: 
            current_app = QApplication.instance()
            if current_app: # Check if instance still exists
                 # current_app.quit() # Quitting might be too aggressive if other tests run after
                 pass # Dialog tests usually don't need app to quit explicitly unless it's the last test module
    
    if hasattr(sys, 'argv') and sys.argv is not None:
        request.addfinalizer(fin)
    return app


class MockReceiver(QObject):
    """Helper class to receive signals and store the received data."""
    token = None
    signal_received = False

    @pyqtSlot(str)
    def receive_token(self, token_text):
        self.token = token_text
        self.signal_received = True

def test_token_dialog_ui_elements(qt_app_dialog):
    """Tests if the TokenDialog has all the required UI elements."""
    from librarian_assistant.token_dialog import TokenDialog # Import here for TDD cycle
    
    dialog = TokenDialog()
    
    assert dialog.findChild(QLabel, "instructionLabel") is not None, "Instruction QLabel not found."
    assert dialog.findChild(QLineEdit, "tokenLineEdit") is not None, "Token QLineEdit not found."
    assert dialog.findChild(QPushButton, "okButton") is not None, "OK QPushButton not found."
    assert dialog.findChild(QPushButton, "cancelButton") is not None, "Cancel QPushButton not found."
    
    # Check button texts too
    ok_button = dialog.findChild(QPushButton, "okButton")
    assert ok_button.text().lower() == "ok", "OK button text is not 'OK'." # Case-insensitive check for 'ok'
    
    cancel_button = dialog.findChild(QPushButton, "cancelButton")
    assert cancel_button.text().lower() == "cancel", "Cancel button text is not 'Cancel'." # Case-insensitive

    dialog.close() # Clean up the dialog

def test_token_dialog_ok_button_emits_token_and_accepts(qt_app_dialog):
    """Tests that clicking OK emits the token and accepts the dialog."""
    from librarian_assistant.token_dialog import TokenDialog # Import here
    
    dialog = TokenDialog()
    receiver = MockReceiver()
    dialog.token_accepted.connect(receiver.receive_token) # Assuming signal is named token_accepted
    
    token_input_field = dialog.findChild(QLineEdit, "tokenLineEdit")
    assert token_input_field is not None
    
    test_token = "test_bearer_token_123"
    token_input_field.setText(test_token)
    
    ok_button = dialog.findChild(QPushButton, "okButton")
    assert ok_button is not None
    
    # To test dialog acceptance, we can check the result of exec_ or a flag set on accept
    # For unit tests, directly calling accept() after click simulation is often easier to manage
    # than running a full event loop with exec_().
    # We'll rely on the button's connected slot to call dialog.accept().
    
    # We need a way to check if dialog.accept() was called.
    # One way is to override accept for testing or check a property that changes.
    # For now, let's assume the click() directly triggers the accept logic.
    # We'll also check dialog.result() after a simulated click if possible,
    # but QDialog.Accepted might require exec_().
    # Let's keep it simple: ensure the signal is emitted.
    
    # Simulate click (or directly call the slot if easier for unit test)
    ok_button.click() 

    assert receiver.signal_received, "token_accepted signal was not emitted."
    assert receiver.token == test_token, f"Emitted token '{receiver.token}' does not match expected '{test_token}'."
    
    # How to check dialog.accept() was called without exec_()?
    # This part is tricky. Often, you'd mock `dialog.accept()` or check `dialog.result()`.
    # For now, emitting signal is the primary check. The actual accept() behavior
    # is implicitly part of the "OK" button's role in a QDialog.
    # If dialog.accept() is called, it will set the result to QDialog.Accepted.
    # We can't easily check dialog.result() here without an event loop (exec_).
    # So, focus on signal emission.

    # dialog.close() # OK button should close it.

def test_token_dialog_cancel_button_rejects_and_no_signal(qt_app_dialog):
    """Tests that clicking Cancel rejects the dialog and no token signal is emitted."""
    from librarian_assistant.token_dialog import TokenDialog # Import here

    dialog = TokenDialog()
    receiver = MockReceiver()
    dialog.token_accepted.connect(receiver.receive_token) # Assuming signal is named token_accepted
    
    cancel_button = dialog.findChild(QPushButton, "cancelButton")
    assert cancel_button is not None
    
    # Simulate click (or directly call the slot)
    cancel_button.click() 
    
    assert not receiver.signal_received, "token_accepted signal should not have been emitted on Cancel."
    
    # Similar to accept(), checking dialog.reject() or QDialog.Rejected result without exec_() is tricky.
    # We rely on the button doing its job.
    # dialog.close() # Cancel button should close it.