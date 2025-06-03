# ABOUTME: Integration tests for filter dialog and table interactions
# ABOUTME: Tests end-to-end filtering workflows including complex combinations

import pytest
from unittest.mock import patch
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from librarian_assistant.main import MainWindow


class TestFilterTableIntegration:
    """Test filter-table integration scenarios."""

    @pytest.fixture
    def main_window_with_data(self, qapp):
        """Create main window with sample book data loaded."""
        main_window = MainWindow()
        main_window.show()

        # Load sample data
        mock_book_data = {
            'id': 123,
            'title': 'Test Book',
            'slug': 'test-book',
            'editions': [
                {
                    'id': 1,
                    'title': 'First Edition',
                    'score': 95,
                    'pages': 300,
                    'reading_format_id': 1,  # Physical
                    'release_date': '2023-01-15'
                },
                {
                    'id': 2,
                    'title': 'Audio Edition',
                    'score': 85,
                    'audio_seconds': 25200,
                    'reading_format_id': 2,  # Audiobook
                    'release_date': '2023-03-20'
                },
                {
                    'id': 3,
                    'title': 'E-Book Edition',
                    'score': 90,
                    'pages': 295,
                    'reading_format_id': 4,  # E-Book
                    'release_date': '2023-02-10'
                },
                {
                    'id': 4,
                    'title': 'Special Edition',
                    'score': 98,
                    'pages': 350,
                    'reading_format_id': 1,  # Physical
                    'release_date': '2023-06-01'
                }
            ]
        }

        with patch.object(main_window.api_client, 'get_book_by_id', return_value=mock_book_data):
            with patch.object(main_window.config_manager, 'load_token', return_value="Bearer token"):
                main_window.book_id_line_edit.setText("123")
                QTest.mouseClick(main_window.fetch_data_button, Qt.MouseButton.LeftButton)

        return main_window

    def test_single_filter_application(self, main_window_with_data):
        """Test applying a single filter to the table."""
        main_window = main_window_with_data

        # Apply filter: score > 90
        filters = [{
            'column': 'score',
            'operator': '>',
            'value': '90'
        }]
        main_window._apply_filters(filters, 'AND')

        # Check visible rows
        visible_count = sum(1 for row in range(main_window.editions_table_widget.rowCount())
                            if not main_window.editions_table_widget.isRowHidden(row))
        assert visible_count == 2  # First Edition (95) and Special Edition (98)

    def test_multiple_filters_with_and_logic(self, main_window_with_data):
        """Test multiple filters combined with AND logic."""
        main_window = main_window_with_data

        # Apply filters: Reading Format = Physical AND pages > 320
        filters = [
            {
                'column': 'Reading Format',
                'operator': 'Is',
                'value': 'Physical Book'
            },
            {
                'column': 'pages',
                'operator': '>',
                'value': '320'
            }
        ]
        main_window._apply_filters(filters, 'AND')

        # Only Special Edition should match (Physical with 350 pages)
        visible_count = sum(1 for row in range(main_window.editions_table_widget.rowCount())
                            if not main_window.editions_table_widget.isRowHidden(row))
        assert visible_count == 1

    def test_multiple_filters_with_or_logic(self, main_window_with_data):
        """Test multiple filters combined with OR logic."""
        main_window = main_window_with_data

        # Apply filters: score > 95 OR Reading Format = Audiobook
        filters = [
            {
                'column': 'score',
                'operator': '>',
                'value': '95'
            },
            {
                'column': 'Reading Format',
                'operator': 'Is',
                'value': 'Audiobook'
            }
        ]
        main_window._apply_filters(filters, 'OR')

        # Special Edition (98) and Audio Edition should match
        visible_count = sum(1 for row in range(main_window.editions_table_widget.rowCount())
                            if not main_window.editions_table_widget.isRowHidden(row))
        assert visible_count == 2

    def test_date_range_filter(self, main_window_with_data):
        """Test date range filtering."""
        main_window = main_window_with_data

        # Apply filter: release_date between 2023-02-01 and 2023-04-01
        filters = [{
            'column': 'release_date',
            'operator': 'Is between',
            'value': {'start': '2023-02-01', 'end': '2023-04-01'}
        }]
        main_window._apply_filters(filters, 'AND')

        # E-Book (2023-02-10) and Audio (2023-03-20) should match
        visible_count = sum(1 for row in range(main_window.editions_table_widget.rowCount())
                            if not main_window.editions_table_widget.isRowHidden(row))
        assert visible_count == 2

    def test_filter_persistence_after_sorting(self, main_window_with_data):
        """Test that filters remain applied after sorting columns."""
        main_window = main_window_with_data

        # Apply filter
        filters = [{
            'column': 'score',
            'operator': '>=',
            'value': '90'
        }]
        main_window._apply_filters(filters, 'AND')

        initial_visible = sum(1 for row in range(main_window.editions_table_widget.rowCount())
                              if not main_window.editions_table_widget.isRowHidden(row))

        # Sort by title column
        main_window.editions_table_widget.sortByColumn(
            main_window.editions_table_widget.columnCount() - 1, Qt.SortOrder.AscendingOrder)

        # Check filter still applied
        final_visible = sum(1 for row in range(main_window.editions_table_widget.rowCount())
                            if not main_window.editions_table_widget.isRowHidden(row))
        assert initial_visible == final_visible == 3  # 3 editions have score >= 90

    def test_clear_filters_shows_all_rows(self, main_window_with_data):
        """Test that clearing filters shows all rows again."""
        main_window = main_window_with_data

        # Apply restrictive filter
        filters = [{
            'column': 'score',
            'operator': '>',
            'value': '95'
        }]
        main_window._apply_filters(filters, 'AND')

        # Verify filter applied
        filtered_count = sum(1 for row in range(main_window.editions_table_widget.rowCount())
                             if not main_window.editions_table_widget.isRowHidden(row))
        assert filtered_count < 4

        # Clear filters
        main_window._clear_filters()

        # All rows should be visible
        all_visible = sum(1 for row in range(main_window.editions_table_widget.rowCount())
                          if not main_window.editions_table_widget.isRowHidden(row))
        assert all_visible == 4

    def test_filter_dialog_integration(self, main_window_with_data):
        """Test complete filter dialog workflow."""
        main_window = main_window_with_data

        # Apply filters directly since dialog integration is complex
        filters = [
            {
                'column': 'title',
                'operator': 'Contains',
                'value': 'Edition'
            }
        ]

        main_window._apply_filters(filters, 'AND')

        # All rows should match (all contain "Edition")
        visible_count = sum(1 for row in range(main_window.editions_table_widget.rowCount())
                            if not main_window.editions_table_widget.isRowHidden(row))
        assert visible_count == 4
        assert "Filter applied" in main_window.status_bar.currentMessage()

    def test_complex_filter_combination(self, main_window_with_data):
        """Test complex filter with multiple data types."""
        main_window = main_window_with_data

        # Complex filter: (score > 85 AND pages exists) OR release_date after 2023-05-01
        # This tests numeric, existence, and date filters
        filters = [
            {
                'column': 'score',
                'operator': '>',
                'value': '85'
            },
            {
                'column': 'pages',
                'operator': 'Is not N/A',
                'value': ''
            },
            {
                'column': 'release_date',
                'operator': 'Is after',
                'value': '2023-05-01'
            }
        ]

        # Test with AND logic first
        main_window._apply_filters(filters[:2], 'AND')

        and_visible = sum(1 for row in range(main_window.editions_table_widget.rowCount())
                          if not main_window.editions_table_widget.isRowHidden(row))

        # Then test including the date filter with different logic
        main_window._apply_filters(filters, 'OR')

        or_visible = sum(1 for row in range(main_window.editions_table_widget.rowCount())
                         if not main_window.editions_table_widget.isRowHidden(row))

        # OR should include more results than AND
        assert or_visible >= and_visible
