# In tests/test_main_window.py
import unittest
from unittest.mock import patch # Import patch
from PyQt5.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton, QGroupBox
from librarian_assistant.main import MainWindow # Make sure this import path is correct

# QApplication instance is required for PyQt tests
app = QApplication([])

class TestMainWindow(unittest.TestCase):
    def setUp(self):
        """Set up the test environment for MainWindow tests."""
        self.window = MainWindow()

    def tearDown(self):
        """Clean up after tests."""
        self.window.close()
        # It's good practice to delete the window to free resources,
        # especially if many tests create windows.
        del self.window

    # ... (other existing tests, if any) ...

    def test_book_id_input_elements_present(self):
        """
        Test that the Book ID label, QLineEdit, and Fetch Data button are present
        in the API & Book ID Input Area.
        """
        # Find the "API & Book ID Input Area" QGroupBox
        api_input_area = self.window.findChild(QGroupBox, "apiInputArea")
        self.assertIsNotNone(api_input_area, "API & Book ID Input Area QGroupBox not found.")

        # Check for the Book ID QLabel
        book_id_label = api_input_area.findChild(QLabel, "bookIdLabel")
        self.assertIsNotNone(book_id_label, "Book ID QLabel not found.")
        self.assertEqual(book_id_label.text(), "Book ID:")

        # Check for the Book ID QLineEdit
        book_id_line_edit = api_input_area.findChild(QLineEdit, "bookIdLineEdit")
        self.assertIsNotNone(book_id_line_edit, "Book ID QLineEdit not found.")

        # Check for the Fetch Data QPushButton
        fetch_data_button = api_input_area.findChild(QPushButton, "fetchDataButton")
        self.assertIsNotNone(fetch_data_button, "Fetch Data QPushButton not found.")
        self.assertEqual(fetch_data_button.text(), "Fetch Data")

    def test_book_id_line_edit_accepts_only_numbers(self):
        """
        Test that the Book ID QLineEdit only accepts numerical input.
        """
        book_id_line_edit = self.window.findChild(QLineEdit, "bookIdLineEdit")
        self.assertIsNotNone(book_id_line_edit, "Book ID QLineEdit not found.")

        # Test with non-numeric input
        book_id_line_edit.setText("abc")
        self.assertEqual(book_id_line_edit.text(), "", "QLineEdit should be empty after non-numeric input.")

        # Test with numeric input
        book_id_line_edit.setText("123")
        self.assertEqual(book_id_line_edit.text(), "123", "QLineEdit should accept numeric input.")

        # Test with mixed input (should ideally only take numbers or be empty)
        book_id_line_edit.setText("1a2b3")
        # Depending on how QIntValidator works or how we implement it,
        # it might result in "123" or "" or "1".
        # For a strict "only numbers allowed at all" policy, it should be empty or reject.
        # If it's a QIntValidator, it might allow partial valid input or clear on invalid.
        # Let's assume for now it should clear if invalid characters are part of the string.
        self.assertEqual(book_id_line_edit.text(), "", "QLineEdit should be empty after mixed input if strict.")
       
    @patch('librarian_assistant.main.logger.info') # Decorator for mocking logger.info
    def test_fetch_data_button_logs_book_id_and_token_status(self, mock_main_logger_info): # mock_main_logger_info is passed by decorator
        """
        Test that clicking the "Fetch Data" button logs the current Book ID
        and token status.
        """
        # Use patch.object as a context manager for self.window.config_manager.load_token
        with patch.object(self.window.config_manager, 'load_token') as mock_load_token:
            book_id_line_edit = self.window.findChild(QLineEdit, "bookIdLineEdit")
            self.assertIsNotNone(book_id_line_edit, "Book ID QLineEdit not found.")
            
            fetch_data_button = self.window.findChild(QPushButton, "fetchDataButton")
            self.assertIsNotNone(fetch_data_button, "Fetch Data QPushButton not found.")

            # Scenario 1: Token is set, Book ID is entered
            mock_load_token.return_value = "fake_token_for_test" # Simulate a token being present
            # We don't strictly need to call _update_token_display for this test's logic,
            # as the slot will call load_token directly.
            
            test_book_id_scenario1 = "12345"
            book_id_line_edit.setText(test_book_id_scenario1)
            
            fetch_data_button.click() # Simulate the button click
            
            expected_log_message_scenario1 = f"Fetch Data clicked. Book ID: '{test_book_id_scenario1}'. Token status: Set."
            mock_main_logger_info.assert_any_call(expected_log_message_scenario1)
            
            # Clear mock calls for the next scenario
            mock_main_logger_info.reset_mock()

            # Scenario 2: No token is set, Book ID is empty
            mock_load_token.return_value = None # Simulate no token
            
            test_book_id_scenario2 = ""
            book_id_line_edit.setText(test_book_id_scenario2) # Empty Book ID
            
            fetch_data_button.click() # Simulate the button click
            
            expected_log_message_scenario2 = f"Fetch Data clicked. Book ID: '{test_book_id_scenario2}'. Token status: Not Set."
            mock_main_logger_info.assert_any_call(expected_log_message_scenario2)



if __name__ == '__main__':
    unittest.main()
