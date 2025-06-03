# ABOUTME: This file contains unit tests for the HistoryManager class.
# ABOUTME: It tests history storage, retrieval, search, sorting, and persistence functionality.
import unittest
import tempfile
import os
from unittest.mock import patch

from librarian_assistant.history_manager import HistoryManager


class TestHistoryManager(unittest.TestCase):
    """Test cases for HistoryManager."""

    def setUp(self):
        """Set up test fixtures with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.history_manager = HistoryManager(storage_dir=self.temp_dir)

    def tearDown(self):
        """Clean up temporary files."""
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test HistoryManager initializes correctly."""
        # Check storage directory exists
        self.assertTrue(os.path.exists(self.temp_dir))

        # Check history file path is set correctly
        expected_path = os.path.join(self.temp_dir, 'search_history.json')
        self.assertEqual(self.history_manager.history_file, expected_path)

        # Check initial history is empty
        self.assertEqual(len(self.history_manager.get_history()), 0)

    def test_add_search(self):
        """Test adding searches to history."""
        # Add first search
        self.history_manager.add_search(123, "Harry Potter and the Philosopher's Stone")

        history = self.history_manager.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['book_id'], 123)
        self.assertEqual(history[0]['book_title'], "Harry Potter and the Philosopher's Stone")
        self.assertIn('search_time', history[0])

        # Add second search
        self.history_manager.add_search(456, "The Hobbit")

        history = self.history_manager.get_history()
        self.assertEqual(len(history), 2)
        # Newest should be first
        self.assertEqual(history[0]['book_id'], 456)
        self.assertEqual(history[1]['book_id'], 123)

    def test_duplicate_search_updates_position(self):
        """Test that searching the same book again moves it to the front."""
        # Add multiple searches
        self.history_manager.add_search(123, "Book 1")
        self.history_manager.add_search(456, "Book 2")
        self.history_manager.add_search(789, "Book 3")

        # Check order
        history = self.history_manager.get_history()
        self.assertEqual([entry['book_id'] for entry in history], [789, 456, 123])

        # Search for Book 1 again
        self.history_manager.add_search(123, "Book 1")

        # Book 1 should now be at the front
        history = self.history_manager.get_history()
        self.assertEqual([entry['book_id'] for entry in history], [123, 789, 456])
        self.assertEqual(len(history), 3)  # Should still only have 3 entries

    def test_clear_history(self):
        """Test clearing history."""
        # Add some searches
        self.history_manager.add_search(123, "Book 1")
        self.history_manager.add_search(456, "Book 2")

        # Verify history has entries
        self.assertEqual(len(self.history_manager.get_history()), 2)

        # Clear history
        self.history_manager.clear_history()

        # Verify history is empty
        self.assertEqual(len(self.history_manager.get_history()), 0)

    def test_search_history(self):
        """Test searching through history."""
        # Add test data
        self.history_manager.add_search(123, "Harry Potter and the Philosopher's Stone")
        self.history_manager.add_search(456, "The Hobbit")
        self.history_manager.add_search(789, "Lord of the Rings")

        # Search by title
        results = self.history_manager.search_history("Harry")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['book_id'], 123)

        # Search by book ID
        results = self.history_manager.search_history("456")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['book_id'], 456)

        # Search by partial title (case insensitive)
        results = self.history_manager.search_history("lord")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['book_id'], 789)

        # Search that matches multiple
        results = self.history_manager.search_history("the")
        self.assertEqual(len(results), 3)  # All three titles contain "the"

        # Empty search returns all
        results = self.history_manager.search_history("")
        self.assertEqual(len(results), 3)

        # No matches
        results = self.history_manager.search_history("Nonexistent")
        self.assertEqual(len(results), 0)

    def test_sort_history(self):
        """Test sorting history."""
        # Add test data with specific order
        self.history_manager.add_search(789, "Charlie Book")
        self.history_manager.add_search(123, "Alpha Book")
        self.history_manager.add_search(456, "Beta Book")

        # Sort by book ID
        sorted_history = self.history_manager.sort_history('book_id')
        book_ids = [entry['book_id'] for entry in sorted_history]
        self.assertEqual(book_ids, [123, 456, 789])

        # Sort by title
        sorted_history = self.history_manager.sort_history('title')
        titles = [entry['book_title'] for entry in sorted_history]
        self.assertEqual(titles, ["Alpha Book", "Beta Book", "Charlie Book"])

        # Sort by date (default order - newest first)
        sorted_history = self.history_manager.sort_history('date')
        # Should maintain the insertion order (456, 123, 789 since 456 was added last)
        book_ids = [entry['book_id'] for entry in sorted_history]
        self.assertEqual(book_ids, [456, 123, 789])

    def test_get_entry_by_book_id(self):
        """Test getting specific entry by book ID."""
        # Add test data
        self.history_manager.add_search(123, "Test Book")
        self.history_manager.add_search(456, "Another Book")

        # Find existing entry
        entry = self.history_manager.get_entry_by_book_id(123)
        self.assertIsNotNone(entry)
        self.assertEqual(entry['book_title'], "Test Book")

        # Try to find non-existing entry
        entry = self.history_manager.get_entry_by_book_id(999)
        self.assertIsNone(entry)

    def test_get_history_count(self):
        """Test getting history count."""
        # Initially empty
        self.assertEqual(self.history_manager.get_history_count(), 0)

        # Add entries
        self.history_manager.add_search(123, "Book 1")
        self.assertEqual(self.history_manager.get_history_count(), 1)

        self.history_manager.add_search(456, "Book 2")
        self.assertEqual(self.history_manager.get_history_count(), 2)

        # Clear and check
        self.history_manager.clear_history()
        self.assertEqual(self.history_manager.get_history_count(), 0)

    def test_persistence(self):
        """Test that history persists across instances."""
        # Add data to first instance
        self.history_manager.add_search(123, "Persistent Book")
        self.history_manager.add_search(456, "Another Persistent Book")

        # Create new instance with same storage directory
        new_manager = HistoryManager(storage_dir=self.temp_dir)

        # Check data was loaded
        history = new_manager.get_history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]['book_id'], 456)  # Most recent first
        self.assertEqual(history[1]['book_id'], 123)

    def test_file_operations_error_handling(self):
        """Test error handling for file operations."""
        # Test with invalid directory
        with patch('os.makedirs', side_effect=PermissionError("Permission denied")):
            with patch('logging.Logger.error'):
                # This should still work but log errors
                HistoryManager(storage_dir="/invalid/directory")
                # Error should be logged during save operations

    def test_malformed_history_file(self):
        """Test handling of malformed history file."""
        # Create malformed JSON file
        with open(self.history_manager.history_file, 'w') as f:
            f.write("invalid json content")

        # Create new manager - should handle error gracefully
        with patch('logging.Logger.error') as mock_logger:
            new_manager = HistoryManager(storage_dir=self.temp_dir)
            # Should start with empty history
            self.assertEqual(len(new_manager.get_history()), 0)
            mock_logger.assert_called()

    def test_default_storage_directory(self):
        """Test default storage directory selection."""
        # Test with no storage_dir provided
        with patch.dict(os.environ, {'APPDATA': '/test/appdata'}, clear=False):
            with patch('os.name', 'nt'):  # Windows
                with patch('os.makedirs'):
                    with patch('os.path.exists', return_value=False):
                        manager = HistoryManager()
                        expected_dir = '/test/appdata/LibrarianAssistant'
                        self.assertEqual(manager.storage_dir, expected_dir)

        # Test Unix-like system
        with patch.dict(os.environ, {'XDG_DATA_HOME': '/test/data'}, clear=False):
            with patch('os.name', 'posix'):
                with patch('os.makedirs'):
                    with patch('os.path.exists', return_value=False):
                        manager = HistoryManager()
                        expected_dir = '/test/data/LibrarianAssistant'
                        self.assertEqual(manager.storage_dir, expected_dir)


if __name__ == '__main__':
    unittest.main()
