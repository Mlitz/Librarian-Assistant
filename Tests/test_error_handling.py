# ABOUTME: Tests for comprehensive error handling implementation
# ABOUTME: Verifies all error scenarios from spec.md section 5.2 are properly handled

import pytest
from unittest.mock import Mock, patch
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtTest import QTest

from librarian_assistant.main import MainWindow
from librarian_assistant.exceptions import (
    ApiException, ApiAuthError, ApiNotFoundError, 
    NetworkError, ApiProcessingError
)


class TestErrorHandling:
    """Test comprehensive error handling for all scenarios in spec.md 5.2"""
    
    def test_invalid_book_id_format_message(self, qapp):
        """Test that invalid Book ID format shows proper user-friendly message"""
        main_window = MainWindow()
        main_window.show()
        
        # Enter non-numeric book ID
        main_window.book_id_line_edit.setText("abc123")
        
        # Try to fetch
        QTest.mouseClick(main_window.fetch_data_button, Qt.LeftButton)
        
        # Check status bar message
        expected_msg = "Please enter a valid numerical Book ID."
        assert expected_msg in main_window.status_bar.currentMessage()
        
    def test_book_id_not_found_message(self, qapp):
        """Test that Book ID not found shows proper message with ID"""
        main_window = MainWindow()
        main_window.show()
        
        # Mock API client to raise ApiNotFoundError
        with patch.object(main_window.api_client, 'get_book_by_id') as mock_get:
            mock_get.side_effect = ApiNotFoundError(resource_id=99999, 
                                                   message_prefix="Book ID not found")
            
            # Set valid book ID and fetch
            main_window.book_id_line_edit.setText("99999")
            QTest.mouseClick(main_window.fetch_data_button, Qt.LeftButton)
            
            # Check status bar message
            expected_msg = "Book ID 99999 not found."
            assert expected_msg in main_window.status_bar.currentMessage()
            
    def test_bearer_token_not_set_message(self, qapp):
        """Test that missing Bearer Token shows proper message"""
        main_window = MainWindow()
        main_window.show()
        
        # Mock config manager to return None for token
        with patch.object(main_window.config_manager, 'load_token', return_value=None):
            # Update token display
            main_window._update_token_display()
            
            # Try to fetch without token
            main_window.book_id_line_edit.setText("123")
            QTest.mouseClick(main_window.fetch_data_button, Qt.LeftButton)
            
            # Check status bar message
            expected_msg = "API Bearer Token not set. Please set it via the 'Set/Update Token' button."
            assert expected_msg in main_window.status_bar.currentMessage()
            
    def test_invalid_token_auth_error_message(self, qapp):
        """Test that invalid/expired token shows proper authentication error"""
        main_window = MainWindow()
        main_window.show()
        
        # Mock API client to raise ApiAuthError
        with patch.object(main_window.api_client, 'get_book_by_id') as mock_get:
            mock_get.side_effect = ApiAuthError("Authentication failed: Invalid token")
            
            # Set token and try to fetch
            with patch.object(main_window.config_manager, 'load_token', return_value="invalid_token"):
                main_window._update_token_display()
                main_window.book_id_line_edit.setText("123")
                QTest.mouseClick(main_window.fetch_data_button, Qt.LeftButton)
                
                # Check status bar message
                expected_msg = "API Authentication Failed. Please check your Bearer Token."
                assert expected_msg in main_window.status_bar.currentMessage()
                
    def test_network_error_message(self, qapp):
        """Test that network issues show proper error message"""
        main_window = MainWindow()
        main_window.show()
        
        # Mock API client to raise NetworkError
        with patch.object(main_window.api_client, 'get_book_by_id') as mock_get:
            mock_get.side_effect = NetworkError("Connection timeout")
            
            # Try to fetch
            main_window.book_id_line_edit.setText("123")
            QTest.mouseClick(main_window.fetch_data_button, Qt.LeftButton)
            
            # Check status bar message
            expected_msg = "Network error. Unable to connect to Hardcover.app API. Please check your internet connection."
            assert expected_msg in main_window.status_bar.currentMessage()
            
    def test_api_rate_limiting_message(self, qapp):
        """Test that API rate limiting shows proper message"""
        main_window = MainWindow()
        main_window.show()
        
        # Mock API client to raise rate limit error
        with patch.object(main_window.api_client, 'get_book_by_id') as mock_get:
            # Create a mock response with 429 status code
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.headers = {'Retry-After': '60'}
            
            # Create NetworkError with rate limit info
            error = NetworkError("Rate limit exceeded")
            error.response = mock_response
            mock_get.side_effect = error
            
            # Try to fetch
            main_window.book_id_line_edit.setText("123")
            QTest.mouseClick(main_window.fetch_data_button, Qt.LeftButton)
            
            # Check status bar message
            expected_msg = "API rate limit exceeded. Please try again later."
            assert expected_msg in main_window.status_bar.currentMessage()
            
    def test_unexpected_api_response_error(self, qapp):
        """Test that unexpected API responses show detailed error for copying"""
        main_window = MainWindow()
        main_window.show()
        
        # Mock API client to raise ApiProcessingError
        with patch.object(main_window.api_client, 'get_book_by_id') as mock_get:
            mock_get.side_effect = ApiProcessingError("Unexpected response structure: missing 'data' field")
            
            # Mock QMessageBox to prevent actual dialog
            with patch('PyQt5.QtWidgets.QMessageBox.critical') as mock_msgbox:
                # Try to fetch
                main_window.book_id_line_edit.setText("123")
                QTest.mouseClick(main_window.fetch_data_button, Qt.LeftButton)
                
                # Check that detailed error dialog was shown
                mock_msgbox.assert_called_once()
                args = mock_msgbox.call_args[0]
                assert "An unexpected error occurred" in args[2]  # Message text
                assert "Please copy the details below" in args[2]
                assert "ApiProcessingError" in args[2]
                
    def test_failed_token_storage_error(self, qapp):
        """Test that failed token storage shows proper error message"""
        main_window = MainWindow()
        main_window.show()
        
        # Mock config manager save_token to raise exception
        with patch.object(main_window.config_manager, 'save_token') as mock_save:
            mock_save.side_effect = Exception("Keyring access denied")
            
            # Directly call the handler to simulate token acceptance
            main_window._handle_token_accepted("test_token")
            
            # Check status bar message
            expected_msg = "Error saving API token. Please try setting it again."
            assert expected_msg in main_window.status_bar.currentMessage()
                    
    def test_failed_token_retrieval_error(self, qapp):
        """Test that failed token retrieval shows proper error message"""
        main_window = MainWindow()
        
        # Mock config manager load_token to raise exception
        with patch.object(main_window.config_manager, 'load_token') as mock_load:
            mock_load.side_effect = Exception("Keyring unavailable")
            
            # Trigger token display update which tries to load token
            main_window.show()
            main_window._update_token_display()
            
            # Check status bar message
            expected_msg = "Error loading API token. Please try setting it again."
            assert expected_msg in main_window.status_bar.currentMessage()
            
    def test_failed_history_save_error(self, qapp):
        """Test that failed history save shows non-critical error"""
        main_window = MainWindow()
        main_window.show()
        
        # Check if history manager exists
        if main_window.history_manager:
            # Mock history manager add_search to raise exception
            with patch.object(main_window.history_manager, 'add_search') as mock_add:
                mock_add.side_effect = Exception("Permission denied")
                
                # Mock successful API call
                mock_book_data = {
                    'id': 123,
                    'title': 'Test Book',
                    'slug': 'test-book',
                    'editions': []
                }
                
                with patch.object(main_window.api_client, 'get_book_by_id', 
                                return_value=mock_book_data):
                    # Set a token first
                    with patch.object(main_window.config_manager, 'load_token', return_value="test_token"):
                        # Fetch book (which tries to save to history)
                        main_window.book_id_line_edit.setText("123")
                        QTest.mouseClick(main_window.fetch_data_button, Qt.LeftButton)
                        
                        # Check status bar shows error but app continues
                        assert "Error saving search history" in main_window.status_bar.currentMessage()
                        # But book data should still be displayed
                        # The actual text includes additional styling
                        assert 'Test Book' in main_window.book_title_label.text()
                
    def test_failed_history_load_error(self, qapp):
        """Test that failed history load shows non-critical error"""
        # Mock history manager to raise exception on load
        with patch('librarian_assistant.history_manager.HistoryManager.load_history') as mock_load:
            mock_load.side_effect = Exception("Corrupted history file")
            
            main_window = MainWindow()
            main_window.show()
            
            # Switch to history tab
            main_window.tab_widget.setCurrentIndex(1)
            
            # Check that error is logged but app continues
            # The history manager will be None in this case
            assert main_window.history_manager is None
            
    def test_general_exception_handling(self, qapp):
        """Test that general exceptions are caught and show user-friendly error"""
        main_window = MainWindow()
        main_window.show()
        
        # Mock API client to raise generic Exception
        with patch.object(main_window.api_client, 'get_book_by_id') as mock_get:
            mock_get.side_effect = Exception("Unexpected error in processing")
            
            # Mock QMessageBox to prevent actual dialog
            with patch('PyQt5.QtWidgets.QMessageBox.critical') as mock_msgbox:
                # Try to fetch
                main_window.book_id_line_edit.setText("123")
                QTest.mouseClick(main_window.fetch_data_button, Qt.LeftButton)
                
                # Check that error dialog was shown
                mock_msgbox.assert_called_once()
                args = mock_msgbox.call_args[0]
                assert "An unexpected error occurred" in args[2]
                
    def test_error_logging(self, qapp):
        """Test that errors are properly logged with appropriate levels"""
        main_window = MainWindow()
        main_window.show()
        
        with patch('librarian_assistant.main.logger') as mock_logger:
            # Test various error scenarios
            
            # 1. Invalid Book ID - The QIntValidator prevents 'abc' from being entered
            # Instead, let's test with an empty book ID which will log a warning
            main_window.book_id_line_edit.setText("")
            QTest.mouseClick(main_window.fetch_data_button, Qt.LeftButton)
            mock_logger.warning.assert_called()
            
            # 2. Book not found - should log as warning
            with patch.object(main_window.api_client, 'get_book_by_id') as mock_get:
                mock_get.side_effect = ApiNotFoundError(999, "Not found")
                main_window.book_id_line_edit.setText("999")
                QTest.mouseClick(main_window.fetch_data_button, Qt.LeftButton)
                mock_logger.warning.assert_called()
                
            # 3. Network error - should log as error
            with patch.object(main_window.api_client, 'get_book_by_id') as mock_get:
                mock_get.side_effect = NetworkError("Connection failed")
                main_window.book_id_line_edit.setText("123")
                QTest.mouseClick(main_window.fetch_data_button, Qt.LeftButton)
                assert mock_logger.error.call_count > 0