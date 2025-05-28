# ABOUTME: This file contains tests for the book mappings checkbox functionality.
# ABOUTME: It tests the Select column, checkbox persistence, and Book Mappings tab.
import unittest
from unittest.mock import patch
from PyQt5.QtWidgets import QApplication, QCheckBox, QLabel, QGroupBox
from librarian_assistant.main import MainWindow


class TestBookMappingsCheckbox(unittest.TestCase):
    """Test the book mappings checkbox functionality."""
    
    def setUp(self):
        """Set up the test environment."""
        self.window = MainWindow()
        
        # Mock data for testing
        self.mock_book_data = {
            'title': 'Test Book',
            'slug': 'test-book',
            'id': 123,
            'authors': [{'name': 'Test Author'}],
            'total_editions': 2,
            'description': 'Test description',
            'editions': [
                {
                    'id': 1,
                    'title': 'Edition 1',
                    'score': 100,
                    'isbn_10': '1234567890',
                    'isbn_13': '9781234567890',
                    'asin': 'B001234567',
                    'reading_format_id': 1,
                    'book_mappings': [
                        {'platform': 'goodreads', 'external_id': '12345'},
                        {'platform': 'openlibrary', 'external_id': 'OL12345M'}
                    ]
                },
                {
                    'id': 2,
                    'title': 'Edition 2',
                    'score': 90,
                    'isbn_10': '0987654321',
                    'isbn_13': '9780987654321',
                    'asin': 'B007654321',
                    'reading_format_id': 2,
                    'book_mappings': [
                        {'platform': 'amazon', 'external_id': '0987654321'}
                    ]
                }
            ]
        }
    
    def tearDown(self):
        """Clean up after tests."""
        self.window.close()
        del self.window
    
    def test_select_column_present(self):
        """Test that the Select column is added to the table headers."""
        # Populate table with mock data
        with patch.object(self.window.api_client, 'get_book_by_id', return_value=self.mock_book_data):
            self.window.book_id_line_edit.setText("123")
            self.window._on_fetch_data_clicked()
        
        # Check that Select column is present
        headers = []
        for col in range(self.window.editions_table_widget.columnCount()):
            header = self.window.editions_table_widget.horizontalHeaderItem(col)
            if header:
                headers.append(header.text().replace(" ▲", "").replace(" ▼", ""))
        
        self.assertIn("Select", headers)
        self.assertEqual(headers[0], "Select", "Select column should be the first column")
    
    def test_checkbox_widgets_created(self):
        """Test that checkbox widgets are created for each edition row."""
        # Populate table with mock data
        with patch.object(self.window.api_client, 'get_book_by_id', return_value=self.mock_book_data):
            self.window.book_id_line_edit.setText("123")
            self.window._on_fetch_data_clicked()
        
        # Check that each row has a checkbox widget
        for row in range(self.window.editions_table_widget.rowCount()):
            widget = self.window.editions_table_widget.cellWidget(row, 0)  # Select column is at index 0
            self.assertIsNotNone(widget, f"No widget found in row {row}, column 0")
            
            checkbox = widget.findChild(QCheckBox)
            self.assertIsNotNone(checkbox, f"No checkbox found in row {row}")
            self.assertFalse(checkbox.isChecked(), f"Checkbox in row {row} should be unchecked by default")
    
    def test_select_all_functionality(self):
        """Test that clicking the Select header toggles all checkboxes."""
        # Populate table with mock data
        with patch.object(self.window.api_client, 'get_book_by_id', return_value=self.mock_book_data):
            self.window.book_id_line_edit.setText("123")
            self.window._on_fetch_data_clicked()
        
        # Simulate clicking the Select header
        header = self.window.editions_table_widget.horizontalHeader()
        header.sectionClicked.emit(0)  # Click Select column header
        
        # Check that all checkboxes are now checked
        for row in range(self.window.editions_table_widget.rowCount()):
            widget = self.window.editions_table_widget.cellWidget(row, 0)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox:
                    self.assertTrue(checkbox.isChecked(), f"Checkbox in row {row} should be checked")
        
        # Click header again to uncheck all
        header.sectionClicked.emit(0)
        
        # Check that all checkboxes are now unchecked
        for row in range(self.window.editions_table_widget.rowCount()):
            widget = self.window.editions_table_widget.cellWidget(row, 0)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox:
                    self.assertFalse(checkbox.isChecked(), f"Checkbox in row {row} should be unchecked")
    
    def test_book_mappings_tab_exists(self):
        """Test that the Book Mappings tab is created."""
        # Check that tab exists
        tab_count = self.window.tab_widget.count()
        tab_titles = [self.window.tab_widget.tabText(i) for i in range(tab_count)]
        
        self.assertIn("Book Mappings", tab_titles)
    
    def test_book_mappings_placeholder(self):
        """Test that Book Mappings tab shows placeholder when no editions are selected."""
        # Find the Book Mappings tab
        book_mappings_index = None
        for i in range(self.window.tab_widget.count()):
            if self.window.tab_widget.tabText(i) == "Book Mappings":
                book_mappings_index = i
                break
        
        self.assertIsNotNone(book_mappings_index)
        
        # Switch to Book Mappings tab
        self.window.tab_widget.setCurrentIndex(book_mappings_index)
        
        # Check for placeholder text
        placeholder = self.window.book_mappings_content.findChild(QLabel)
        self.assertIsNotNone(placeholder)
        self.assertIn("Select editions", placeholder.text())
    
    def test_checkbox_updates_book_mappings_tab(self):
        """Test that checking an edition updates the Book Mappings tab."""
        # Populate table with mock data
        with patch.object(self.window.api_client, 'get_book_by_id', return_value=self.mock_book_data):
            self.window.book_id_line_edit.setText("123")
            self.window._on_fetch_data_clicked()
        
        # Check the first edition
        widget = self.window.editions_table_widget.cellWidget(0, 0)
        checkbox = widget.findChild(QCheckBox)
        checkbox.setChecked(True)
        
        # Check that Book Mappings tab is updated
        # Should have at least one card widget
        cards = self.window.book_mappings_content.findChildren(QGroupBox)
        self.assertGreater(len(cards), 0, "Should have at least one card in Book Mappings tab")
    
    def test_checkbox_persistence_through_sorting(self):
        """Test that checkbox states persist through table sorting."""
        # Populate table with mock data
        with patch.object(self.window.api_client, 'get_book_by_id', return_value=self.mock_book_data):
            self.window.book_id_line_edit.setText("123")
            self.window._on_fetch_data_clicked()
        
        # Check the first edition
        widget = self.window.editions_table_widget.cellWidget(0, 0)
        checkbox = widget.findChild(QCheckBox)
        checkbox.setChecked(True)
        
        # Remember which edition was checked
        checked_edition_id = self.window.editions_data[0].get('id')
        
        # Sort by score column (should already be sorted, so this will reverse)
        score_col = None
        for col in range(self.window.editions_table_widget.columnCount()):
            header = self.window.editions_table_widget.horizontalHeaderItem(col)
            if header and "score" in header.text():
                score_col = col
                break
        
        self.assertIsNotNone(score_col)
        
        # Click to sort
        header = self.window.editions_table_widget.horizontalHeader()
        header.sectionClicked.emit(score_col)
        
        # Find the row with our checked edition
        checked_row = None
        for row in range(self.window.editions_table_widget.rowCount()):
            edition_id = self.window.editions_table_widget._get_edition_id_for_row(row)
            if str(edition_id) == str(checked_edition_id):
                checked_row = row
                break
        
        self.assertIsNotNone(checked_row)
        
        # Verify checkbox is still checked
        widget = self.window.editions_table_widget.cellWidget(checked_row, 0)
        checkbox = widget.findChild(QCheckBox)
        self.assertTrue(checkbox.isChecked(), "Checkbox state should persist through sorting")
    
    def test_book_mapping_card_content(self):
        """Test that book mapping cards display correct information."""
        # Populate table with mock data
        with patch.object(self.window.api_client, 'get_book_by_id', return_value=self.mock_book_data):
            self.window.book_id_line_edit.setText("123")
            self.window._on_fetch_data_clicked()
        
        # Check the first edition
        widget = self.window.editions_table_widget.cellWidget(0, 0)
        checkbox = widget.findChild(QCheckBox)
        checkbox.setChecked(True)
        
        # Find the card in Book Mappings tab
        cards = self.window.book_mappings_content.findChildren(QGroupBox)
        self.assertEqual(len(cards), 1)
        
        card = cards[0]
        
        # Check that card contains expected information
        labels = card.findChildren(QLabel)
        card_text = " ".join([label.text() for label in labels])
        
        # Check for edition info in title
        self.assertIn("Book ID: 1", card_text)
        self.assertIn("ISBN-10: 1234567890", card_text)
        self.assertIn("ISBN-13: 9781234567890", card_text)
        self.assertIn("ASIN: B001234567", card_text)
        self.assertIn("Format: Physical", card_text)
        
        # Check for book mappings
        self.assertIn("goodreads", card_text)
        self.assertIn("openlibrary", card_text)


if __name__ == '__main__':
    # Create QApplication if it doesn't exist
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    unittest.main()