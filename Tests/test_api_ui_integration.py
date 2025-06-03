# ABOUTME: Integration tests for API-UI interactions and token management workflows
# ABOUTME: Tests end-to-end scenarios involving API client, token dialog, and main window

from unittest.mock import patch
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from librarian_assistant.main import MainWindow
from librarian_assistant.exceptions import ApiAuthError, NetworkError


class TestApiUiIntegration:
    """Test API-UI integration scenarios."""

    def test_no_token_to_successful_api_call_workflow(self, qapp):
        """Test workflow: No token → Set token → Successful API call."""
        main_window = MainWindow()
        main_window.show()

        # Initially no token
        with patch.object(main_window.config_manager, 'load_token', return_value=None):
            main_window._update_token_display()
            assert "Not Set" in main_window.token_display_label.text()

        # User sets token via dialog
        test_token = "Bearer test_token_123"
        with patch.object(main_window.config_manager, 'save_token') as mock_save:
            main_window._handle_token_accepted(test_token)
            mock_save.assert_called_once_with(test_token)

        # Token display updates
        with patch.object(main_window.config_manager, 'load_token', return_value=test_token):
            main_window._update_token_display()
            assert "*******" in main_window.token_display_label.text()

        # Successful API call with token
        mock_book_data = {
            'id': 123,
            'title': 'Test Book',
            'slug': 'test-book',
            'editions': []
        }

        with patch.object(main_window.api_client, 'get_book_by_id', return_value=mock_book_data):
            with patch.object(main_window.config_manager, 'load_token', return_value=test_token):
                main_window.book_id_line_edit.setText("123")
                QTest.mouseClick(main_window.fetch_data_button, Qt.MouseButton.LeftButton)

                # Verify success
                assert "successfully" in main_window.status_bar.currentMessage()
                assert "Test Book" in main_window.book_title_label.text()

    def test_token_expiration_reauth_workflow(self, qapp):
        """Test workflow: Token expired → Re-authentication → Retry."""
        main_window = MainWindow()
        main_window.show()

        # Set initial token
        old_token = "Bearer old_token"
        with patch.object(main_window.config_manager, 'load_token', return_value=old_token):
            main_window._update_token_display()

        # First API call fails with auth error
        with patch.object(main_window.api_client, 'get_book_by_id') as mock_api:
            mock_api.side_effect = ApiAuthError("Token expired")

            main_window.book_id_line_edit.setText("456")
            QTest.mouseClick(main_window.fetch_data_button, Qt.MouseButton.LeftButton)

            # Should show auth error
            assert "Authentication Failed" in main_window.status_bar.currentMessage()

        # User updates token
        new_token = "Bearer new_token"
        with patch.object(main_window.config_manager, 'save_token'):
            main_window._handle_token_accepted(new_token)

        # Retry with new token succeeds
        mock_book_data = {
            'id': 456,
            'title': 'Updated Book',
            'slug': 'updated-book',
            'editions': []
        }

        with patch.object(main_window.api_client, 'get_book_by_id', return_value=mock_book_data):
            with patch.object(main_window.config_manager, 'load_token', return_value=new_token):
                QTest.mouseClick(main_window.fetch_data_button, Qt.MouseButton.LeftButton)

                assert "successfully" in main_window.status_bar.currentMessage()
                assert "Updated Book" in main_window.book_title_label.text()

    def test_network_error_recovery_workflow(self, qapp):
        """Test workflow: Network error → User retries → Success."""
        main_window = MainWindow()
        main_window.show()

        # Set token
        with patch.object(main_window.config_manager, 'load_token', return_value="Bearer token"):
            main_window._update_token_display()

        # First attempt fails with network error
        with patch.object(main_window.api_client, 'get_book_by_id') as mock_api:
            mock_api.side_effect = NetworkError("Connection timeout")

            main_window.book_id_line_edit.setText("789")
            QTest.mouseClick(main_window.fetch_data_button, Qt.MouseButton.LeftButton)

            assert "Network error" in main_window.status_bar.currentMessage()
            assert "check your internet connection" in main_window.status_bar.currentMessage()

        # User retries and succeeds
        mock_book_data = {
            'id': 789,
            'title': 'Network Recovery Book',
            'slug': 'network-recovery',
            'editions': []
        }

        with patch.object(main_window.api_client, 'get_book_by_id', return_value=mock_book_data):
            QTest.mouseClick(main_window.fetch_data_button, Qt.MouseButton.LeftButton)

            assert "successfully" in main_window.status_bar.currentMessage()
            assert "Network Recovery Book" in main_window.book_title_label.text()

    def test_api_response_updates_all_ui_elements(self, qapp):
        """Test that API response updates all relevant UI elements."""
        main_window = MainWindow()
        main_window.show()

        # Complex book data
        mock_book_data = {
            'id': 999,
            'title': 'Complete Book',
            'slug': 'complete-book',
            'description': 'A comprehensive test book',
            'editions_count': 5,
            'contributions': [{'author': {'name': 'Test Author'}}],
            'default_audio_edition': {'id': 101, 'edition_format': 'Audiobook'},
            'default_physical_edition': {'id': 102, 'edition_format': 'Hardcover'},
            'editions': [
                {
                    'id': 1001,
                    'title': 'First Edition',
                    'score': 95,
                    'reading_format_id': 1,
                    'pages': 300
                },
                {
                    'id': 1002,
                    'title': 'Audio Edition',
                    'score': 90,
                    'reading_format_id': 2,
                    'audio_seconds': 25200
                }
            ]
        }

        with patch.object(main_window.api_client, 'get_book_by_id', return_value=mock_book_data):
            with patch.object(main_window.config_manager, 'load_token', return_value="Bearer token"):
                # Add to history with mocked history manager
                with patch.object(main_window.history_manager, 'add_search') as mock_history:
                    main_window.book_id_line_edit.setText("999")
                    QTest.mouseClick(main_window.fetch_data_button, Qt.MouseButton.LeftButton)

                    # Verify all UI updates
                    assert "Complete Book" in main_window.book_title_label.text()
                    assert "complete-book" in main_window.book_slug_label.text()
                    assert "Test Author" in main_window.book_authors_label.text()
                    assert "5" in main_window.book_total_editions_label.text()

                    # Verify table has editions
                    assert main_window.editions_table_widget.rowCount() == 2

                    # Verify history was updated
                    mock_history.assert_called_once_with(999, 'Complete Book')

    def test_token_dialog_cancel_maintains_state(self, qapp):
        """Test that canceling token dialog doesn't affect application state."""
        main_window = MainWindow()
        main_window.show()

        # Set initial token
        initial_token = "Bearer initial"
        with patch.object(main_window.config_manager, 'load_token', return_value=initial_token):
            main_window._update_token_display()
            initial_display = main_window.token_display_label.text()

        # Mock dialog rejection (cancel)
        with patch('librarian_assistant.token_dialog.TokenDialog.exec', return_value=0):
            main_window._open_set_token_dialog()

        # Verify state unchanged
        assert main_window.token_display_label.text() == initial_display

        # API calls should still work with existing token
        mock_book_data = {'id': 1, 'title': 'Test', 'slug': 'test', 'editions': []}
        with patch.object(main_window.api_client, 'get_book_by_id', return_value=mock_book_data):
            with patch.object(main_window.config_manager, 'load_token', return_value=initial_token):
                main_window.book_id_line_edit.setText("1")
                QTest.mouseClick(main_window.fetch_data_button, Qt.MouseButton.LeftButton)
                assert "successfully" in main_window.status_bar.currentMessage()
