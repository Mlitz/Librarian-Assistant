# ABOUTME: Integration tests for history management and main window interactions
# ABOUTME: Tests end-to-end history workflows including search, selection, and persistence

from unittest.mock import patch
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from librarian_assistant.main import MainWindow
from librarian_assistant.history_manager import HistoryManager


class TestHistoryIntegration:
    """Test history-main view integration scenarios."""

    def test_successful_search_adds_to_history(self, qapp):
        """Test that successful book searches are added to history."""
        main_window = MainWindow()
        main_window.show()

        # Mock book data
        mock_book_data = {
            'id': 123,
            'title': 'History Test Book',
            'slug': 'history-test',
            'editions': []
        }

        # Initial history count
        initial_count = main_window.history_list.rowCount()

        # Perform search
        with patch.object(main_window.api_client, 'get_book_by_id', return_value=mock_book_data):
            with patch.object(main_window.config_manager, 'load_token', return_value="Bearer token"):
                main_window.book_id_line_edit.setText("123")
                QTest.mouseClick(main_window.fetch_data_button, Qt.MouseButton.LeftButton)

        # Wait for UI update
        QTest.qWait(100)

        # History should be updated
        final_count = main_window.history_list.rowCount()
        assert final_count >= initial_count  # At least same or more items

        # Check history content
        found = False
        for row in range(main_window.history_list.rowCount()):
            book_id_item = main_window.history_list.item(row, 0)
            title_item = main_window.history_list.item(row, 1)
            if book_id_item and book_id_item.text() == "123":
                assert title_item.text() == "History Test Book"
                found = True
                break
        assert found

    def test_history_item_double_click_loads_book(self, qapp):
        """Test that double-clicking history item loads the book."""
        main_window = MainWindow()
        main_window.show()

        # Add items to history
        if main_window.history_manager:
            main_window.history_manager.add_search(456, "Previous Book")
            main_window.history_manager.add_search(789, "Target Book")
            main_window._populate_history_list()

        # Find the target book row
        target_row = None
        for row in range(main_window.history_list.rowCount()):
            if main_window.history_list.item(row, 0).text() == "789":
                target_row = row
                break

        assert target_row is not None

        # Mock API response for the book
        mock_book_data = {
            'id': 789,
            'title': 'Target Book',
            'slug': 'target-book',
            'editions': []
        }

        # Double-click the history item
        with patch.object(main_window.api_client, 'get_book_by_id', return_value=mock_book_data):
            with patch.object(main_window.config_manager, 'load_token', return_value="Bearer token"):
                item = main_window.history_list.item(target_row, 0)
                main_window._on_history_item_double_clicked(item)

                # Should switch to main tab
                assert main_window.tab_widget.currentIndex() == 0

                # Book ID should be set
                assert main_window.book_id_line_edit.text() == "789"

                # Book should be loaded
                assert "Target Book" in main_window.book_title_label.text()

    def test_history_search_filter(self, qapp):
        """Test history search/filter functionality."""
        main_window = MainWindow()
        main_window.show()

        # Add multiple items to history
        if main_window.history_manager:
            main_window.history_manager.add_search(100, "Python Programming")
            main_window.history_manager.add_search(200, "Java Development")
            main_window.history_manager.add_search(300, "Python Cookbook")
            main_window.history_manager.add_search(400, "C++ Guide")
            main_window._populate_history_list()

        # Initial count
        assert main_window.history_list.rowCount() >= 4

        # Filter for "Python"
        main_window.history_search_box.setText("Python")
        main_window._filter_history("Python")

        # Count visible Python books
        python_count = main_window.history_list.rowCount()
        assert python_count == 2

        # Verify filtered items
        for row in range(python_count):
            title_item = main_window.history_list.item(row, 1)
            assert "Python" in title_item.text()

    def test_history_sort_by_book_id(self, qapp):
        """Test sorting history by book ID."""
        main_window = MainWindow()
        main_window.show()

        # Add items in non-sorted order
        if main_window.history_manager:
            main_window.history_manager.add_search(300, "Book C")
            main_window.history_manager.add_search(100, "Book A")
            main_window.history_manager.add_search(200, "Book B")
            main_window._populate_history_list()

        # Sort by Book ID
        main_window.history_sort_combo.setCurrentText("Sort by Book ID")
        main_window._sort_history("Sort by Book ID")

        # Verify sorted order - check if existing history affects the sort
        # Find our test items
        items = []
        for row in range(main_window.history_list.rowCount()):
            book_id = main_window.history_list.item(row, 0).text()
            if book_id in ["100", "200", "300"]:
                items.append(int(book_id))

        # Verify they're in sorted order
        assert items == sorted(items)

    def test_history_sort_by_title(self, qapp):
        """Test sorting history by title."""
        main_window = MainWindow()
        main_window.show()

        # Add items
        if main_window.history_manager:
            main_window.history_manager.add_search(1, "Zebra Book")
            main_window.history_manager.add_search(2, "Apple Book")
            main_window.history_manager.add_search(3, "Mango Book")
            main_window._populate_history_list()

        # Sort by Title
        main_window.history_sort_combo.setCurrentText("Sort by Title")
        main_window._sort_history("Sort by Title")

        # Verify alphabetical order - find our test items
        titles = []
        for row in range(main_window.history_list.rowCount()):
            title = main_window.history_list.item(row, 1).text()
            if title in ["Apple Book", "Mango Book", "Zebra Book"]:
                titles.append(title)

        # Verify they're in alphabetical order
        assert titles == sorted(titles)

    def test_clear_history_functionality(self, qapp):
        """Test clearing search history."""
        main_window = MainWindow()
        main_window.show()

        # Add items to history
        if main_window.history_manager:
            main_window.history_manager.add_search(1, "Book 1")
            main_window.history_manager.add_search(2, "Book 2")
            main_window._populate_history_list()

            # Verify items exist
            assert main_window.history_list.rowCount() >= 2

            # Clear history
            main_window._clear_history()

            # Verify history is empty
            assert main_window.history_list.rowCount() == 0
            assert main_window.history_manager.get_history_count() == 0
            assert "cleared" in main_window.status_bar.currentMessage()

    def test_history_persistence_simulation(self, qapp):
        """Test that history would persist across sessions (simulated)."""
        # First session
        main_window1 = MainWindow()

        if main_window1.history_manager:
            # Add searches
            main_window1.history_manager.add_search(111, "Persistent Book 1")
            main_window1.history_manager.add_search(222, "Persistent Book 2")

            # Get history file path
            history_file = main_window1.history_manager.history_file

        # Simulate app restart by creating new window with same history file
        with patch.object(HistoryManager, '__init__', lambda self, storage_dir=None: None):
            main_window2 = MainWindow()

            # Manually set up history manager with same file
            main_window2.history_manager = HistoryManager()
            main_window2.history_manager.history_file = history_file
            main_window2.history_manager.load_history()

            # History should contain previous searches
            history = main_window2.history_manager.get_history()
            assert len(history) >= 2
            assert any(entry['book_id'] == 111 for entry in history)
            assert any(entry['book_id'] == 222 for entry in history)

    def test_duplicate_search_updates_position(self, qapp):
        """Test that searching same book again moves it to top of history."""
        main_window = MainWindow()
        main_window.show()

        # Add initial searches
        if main_window.history_manager:
            main_window.history_manager.add_search(100, "Book A")
            main_window.history_manager.add_search(200, "Book B")
            main_window.history_manager.add_search(300, "Book C")

            # Search for Book A again
            mock_book_data = {
                'id': 100,
                'title': 'Book A',
                'slug': 'book-a',
                'editions': []
            }

            with patch.object(main_window.api_client, 'get_book_by_id', return_value=mock_book_data):
                with patch.object(main_window.config_manager, 'load_token', return_value="Bearer token"):
                    main_window.book_id_line_edit.setText("100")
                    QTest.mouseClick(main_window.fetch_data_button, Qt.MouseButton.LeftButton)

            # Book A should now be at top
            main_window._populate_history_list()
            assert main_window.history_list.item(0, 0).text() == "100"
            assert main_window.history_list.item(0, 1).text() == "Book A"
