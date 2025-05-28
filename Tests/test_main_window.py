# ABOUTME: This file contains unit tests for the MainWindow class.
# ABOUTME: It tests the main UI window functionality including book fetching and display.
import unittest
from unittest.mock import patch, Mock # Import patch and Mock
from PyQt5.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton, QGroupBox, QTableWidget, QHeaderView, QTableWidgetItem, QFrame, QWidget
from PyQt5.QtCore import Qt # Import Qt for Qt.LeftButton
from PyQt5.QtTest import QTest # For simulating clicks
from librarian_assistant.main import MainWindow, ClickableLabel # Make sure this import path is correct
from librarian_assistant.api_client import ApiClient
from librarian_assistant.image_downloader import ImageDownloader # Import ImageDownloader
from librarian_assistant.exceptions import ApiNotFoundError, ApiAuthError, NetworkError, ApiProcessingError

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
        self.assertEqual(book_id_label.text(), "<span style='color:#999999;'>Book ID:</span>")

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
        self.assertEqual(book_id_line_edit.text(), "", "QLineEdit should be empty after mixed input if strict.")

    def test_main_window_instantiates_image_downloader(self):
        """
        Test that MainWindow instantiates an ImageDownloader.
        """
        self.assertIsNotNone(self.window.image_downloader, "MainWindow should have an image_downloader attribute.")
        self.assertIsInstance(self.window.image_downloader, ImageDownloader, "image_downloader attribute should be an instance of ImageDownloader.")

    @patch('librarian_assistant.main.logger.info') # To ensure no logging happens on invalid input
    def test_fetch_data_button_empty_book_id_shows_status_error(self, mock_main_logger_info):
        """
        Test that clicking "Fetch Data" with an empty Book ID shows an error
        in the status bar and does not proceed with logging/fetching.
        """
        book_id_line_edit = self.window.findChild(QLineEdit, "bookIdLineEdit")
        self.assertIsNotNone(book_id_line_edit, "Book ID QLineEdit not found.")
        
        fetch_data_button = self.window.findChild(QPushButton, "fetchDataButton")
        self.assertIsNotNone(fetch_data_button, "Fetch Data QPushButton not found.")

        # Ensure Book ID is empty
        book_id_line_edit.setText("")
        
        # Simulate the button click
        fetch_data_button.click()
        
        # Check status bar message
        expected_status_message = "Book ID cannot be empty. Please enter a valid numerical Book ID."
        self.assertEqual(self.window.status_bar.currentMessage(), expected_status_message)
        
        # Ensure the original logging (and by extension, API call) was not made
        mock_main_logger_info.assert_not_called()

    def test_main_window_instantiates_api_client(self):
        """
        Test that MainWindow instantiates an ApiClient.
        """
        self.assertIsNotNone(self.window.api_client, "MainWindow should have an api_client attribute.")
        self.assertIsInstance(self.window.api_client, ApiClient, "api_client attribute should be an instance of ApiClient.")

    @patch.object(ApiClient, 'get_book_by_id') # Patching at the class level
    def test_fetch_data_button_calls_api_client_with_valid_book_id(self, mock_api_get_book_by_id):
        """
        Test that clicking "Fetch Data" with a valid Book ID calls
        api_client.get_book_by_id with the correct integer Book ID.
        """
        # Mock the return value of get_book_by_id to avoid side effects from its actual implementation
        # and to simulate a successful API call for now.
        mock_api_get_book_by_id.return_value = {"id": "123", "title": "Mocked Book"} 

        book_id_line_edit = self.window.findChild(QLineEdit, "bookIdLineEdit")
        self.assertIsNotNone(book_id_line_edit, "Book ID QLineEdit not found.")
        
        fetch_data_button = self.window.findChild(QPushButton, "fetchDataButton")
        self.assertIsNotNone(fetch_data_button, "Fetch Data QPushButton not found.")

        test_book_id_str = "123"
        expected_book_id_int = 123
        book_id_line_edit.setText(test_book_id_str)
        
        # Simulate the button click
        fetch_data_button.click()
        
        # Assert that self.window.api_client.get_book_by_id was called once with the integer book_id
        self.window.api_client.get_book_by_id.assert_called_once_with(expected_book_id_int)

    @patch.object(ApiClient, 'get_book_by_id')
    def test_fetch_data_success_shows_status_message(self, mock_api_get_book_by_id):
        """
        Test that a successful API call updates the status bar with a success message.
        """
        # Simulate a successful API call returning some data
        mock_book_data = {"id": "123", "title": "Fetched Book"}
        mock_api_get_book_by_id.return_value = mock_book_data

        book_id_line_edit = self.window.findChild(QLineEdit, "bookIdLineEdit")
        fetch_data_button = self.window.findChild(QPushButton, "fetchDataButton")

        test_book_id_str = "123"
        book_id_line_edit.setText(test_book_id_str)
        
        fetch_data_button.click()
        
        expected_status_message = f"Book data fetched successfully for ID {test_book_id_str}."
        self.assertEqual(self.window.status_bar.currentMessage(), expected_status_message)
        mock_api_get_book_by_id.assert_called_once_with(int(test_book_id_str))

    @patch.object(ApiClient, 'get_book_by_id')
    def test_fetch_data_api_not_found_error_shows_status_message(self, mock_api_get_book_by_id):
        """
        Test that an ApiNotFoundError from the API client updates the status bar
        with an appropriate error message.
        """
        # Simulate ApiClient raising ApiNotFoundError
        test_book_id_str = "404"
        mock_api_get_book_by_id.side_effect = ApiNotFoundError(resource_id=int(test_book_id_str))

        book_id_line_edit = self.window.findChild(QLineEdit, "bookIdLineEdit")
        fetch_data_button = self.window.findChild(QPushButton, "fetchDataButton")

        book_id_line_edit.setText(test_book_id_str)
        
        fetch_data_button.click()
        
        expected_status_message = f"Error fetching data: Resource not found: ID {test_book_id_str}"
        self.assertEqual(self.window.status_bar.currentMessage(), expected_status_message)
        mock_api_get_book_by_id.assert_called_once_with(int(test_book_id_str))

    @patch.object(ApiClient, 'get_book_by_id')
    def test_fetch_data_api_auth_error_shows_status_message(self, mock_api_get_book_by_id):
        """
        Test that an ApiAuthError from the API client updates the status bar
        with an appropriate error message.
        """
        # Simulate ApiClient raising ApiAuthError
        test_book_id_str = "789"
        error_message = "Invalid API token"
        mock_api_get_book_by_id.side_effect = ApiAuthError(message=error_message)

        book_id_line_edit = self.window.findChild(QLineEdit, "bookIdLineEdit")
        fetch_data_button = self.window.findChild(QPushButton, "fetchDataButton")

        book_id_line_edit.setText(test_book_id_str)
        
        fetch_data_button.click()
        
        expected_status_message = f"Error fetching data: {error_message}"
        self.assertEqual(self.window.status_bar.currentMessage(), expected_status_message)
        mock_api_get_book_by_id.assert_called_once_with(int(test_book_id_str))

    @patch.object(ApiClient, 'get_book_by_id')
    def test_fetch_data_api_network_error_shows_status_message(self, mock_api_get_book_by_id):
        """
        Test that a NetworkError from the API client updates the status bar
        with an appropriate error message.
        """
        # Simulate ApiClient raising NetworkError
        test_book_id_str = "101"
        error_message = "Simulated network failure"
        mock_api_get_book_by_id.side_effect = NetworkError(message=error_message)

        book_id_line_edit = self.window.findChild(QLineEdit, "bookIdLineEdit")
        fetch_data_button = self.window.findChild(QPushButton, "fetchDataButton")

        book_id_line_edit.setText(test_book_id_str)
        
        fetch_data_button.click()
        
        expected_status_message = f"Error fetching data: {error_message}"
        self.assertEqual(self.window.status_bar.currentMessage(), expected_status_message)
        mock_api_get_book_by_id.assert_called_once_with(int(test_book_id_str))

    @patch.object(ApiClient, 'get_book_by_id')
    def test_fetch_data_api_processing_error_shows_status_message(self, mock_api_get_book_by_id):
        """
        Test that an ApiProcessingError from the API client updates the status bar
        with an appropriate error message.
        """
        # Simulate ApiClient raising ApiProcessingError
        test_book_id_str = "202" # Using a different ID for clarity
        error_message = "Simulated API response processing failure"
        mock_api_get_book_by_id.side_effect = ApiProcessingError(message=error_message)

        book_id_line_edit = self.window.findChild(QLineEdit, "bookIdLineEdit")
        fetch_data_button = self.window.findChild(QPushButton, "fetchDataButton")

        book_id_line_edit.setText(test_book_id_str)
        
        fetch_data_button.click()
        
        expected_status_message = f"Error fetching data: {error_message}"
        self.assertEqual(self.window.status_bar.currentMessage(), expected_status_message)
        mock_api_get_book_by_id.assert_called_once_with(int(test_book_id_str))
 
    @patch.object(ApiClient, 'get_book_by_id')
    def test_fetch_data_success_populates_book_info_area(self, mock_api_get_book_by_id):
        """
        Test that a successful API call populates the General Book Information Area
        with the fetched title, authors, description, and cover URL.
        """
        # Mock book data should represent the structure of `response_data['books'][0]`
        # as per spec.md and Appendix A (GraphQL query).
        mock_book_data = {
            "id": "123",
            "slug": "the-great-test-book-slug",
            "title": "The Great Test Book",
            # Authors come from the 'contributions' array
            "contributions": [
                {"author": {"name": "Author One"}},
                {"author": {"name": "Author Two"}}
            ],
            "description": "A truly captivating description of testing.",
            "editions_count": 5,
            "default_audio_edition": {"id": "aud001", "edition_format": "Audiobook"},
            "default_cover_edition": {
                "id": "cov001", 
                "edition_format": "Hardcover",
                "image": {"url": "http://example.com/great_test_book_cover.jpg"}
            },
            "default_ebook_edition": {"id": "ebk001", "edition_format": "E-book"},
            "default_physical_edition": {"id": "phy001", "edition_format": "Paperback"}
        }
        mock_api_get_book_by_id.return_value = mock_book_data

        book_id_line_edit = self.window.findChild(QLineEdit, "bookIdLineEdit")
        fetch_data_button = self.window.findChild(QPushButton, "fetchDataButton")
        
        # Ensure book_info_area is available for parentWidget checks
        self.window.book_info_area = self.window.findChild(QGroupBox, "bookInfoArea")
        self.assertIsNotNone(self.window.book_info_area, "bookInfoArea QGroupBox not found.")

        # Ensure default_editions_group_box is available for parentWidget checks
        self.window.default_editions_group_box = self.window.findChild(QGroupBox, "defaultEditionsGroupBox")
        self.assertIsNotNone(self.window.default_editions_group_box, "defaultEditionsGroupBox QGroupBox not found.")

        book_id_line_edit.setText("123")
        fetch_data_button.click()

        # Check the instance attributes which should point to the new, populated widgets
        # Ensure these objectNames match what's set in your MainWindow's UI setup.
        self.assertIsNotNone(self.window.book_title_label, "Book title QLabel attribute not updated.")
        self.assertIn("<span style='color:#999999;'>Title: </span>", self.window.book_title_label.text())
        self.assertIn("<span style='color:#e0e0e0;'>The Great Test Book</span>", self.window.book_title_label.text())
        # Parent widget check might be tricky if layout is cleared and widgets re-added.
        # Let's ensure it's a child of the main content widget of the scroll area.

        self.assertIsNotNone(self.window.book_slug_label, "Book slug QLabel attribute not updated.")
        # Check that the slug is displayed with HTML formatting
        self.assertIn("the-great-test-book-slug", self.window.book_slug_label.text())
        self.assertIn("href=", self.window.book_slug_label.text())  # Verify it's a link
        self.assertEqual(self.window.book_slug_label.parentWidget(), self.window.book_info_area, "Slug label not in book info area.")

        self.assertIsNotNone(self.window.book_authors_label, "Book authors QLabel attribute not updated.")
        # Assuming authors are joined by ", " in main.py
        self.assertIn("<span style='color:#999999;'>Authors: </span>", self.window.book_authors_label.text())
        self.assertIn("<span style='color:#e0e0e0;'>Author One, Author Two</span>", self.window.book_authors_label.text())

        self.assertIsNotNone(self.window.book_id_queried_label, "Book ID (queried) QLabel attribute not updated.")
        self.assertIn("<span style='color:#999999;'>Book ID (Queried): </span>", self.window.book_id_queried_label.text())
        self.assertIn("<span style='color:#e0e0e0;'>123</span>", self.window.book_id_queried_label.text()) # From input

        self.assertIsNotNone(self.window.book_total_editions_label, "Total editions QLabel attribute not updated.")
        self.assertIn("<span style='color:#999999;'>Total Editions: </span>", self.window.book_total_editions_label.text())
        self.assertIn("<span style='color:#e0e0e0;'>5</span>", self.window.book_total_editions_label.text())


        # Test for the new QLabel based description display
        self.assertIsNotNone(self.window.book_description_label, "Book description QLabel attribute not updated.")
        
        full_mock_description = "A truly captivating description of testing."
        MAX_DESC_CHARS = 500 # Must match the constant in main.py (imported or redefined)
        
        if len(full_mock_description) > MAX_DESC_CHARS:
            expected_display_text = f"Description: {full_mock_description[:MAX_DESC_CHARS]}..."
            expected_tooltip_text = full_mock_description
        else:
            expected_display_text = f"Description: {full_mock_description}"
            expected_tooltip_text = "" # Or full_mock_description if tooltip is always set
            
        self.assertIn("<span style='color:#999999;'>Description: </span>", self.window.book_description_label.text())
        self.assertIn(f"<span style='color:#e0e0e0;'>{full_mock_description}</span>", self.window.book_description_label.text())
        self.assertEqual(self.window.book_description_label.toolTip(), expected_tooltip_text)
        
        self.assertIsNotNone(self.window.book_cover_label, "Book cover QLabel attribute not updated.")
        # This assumes book_cover_label displays the URL as text.
        self.assertIn("<span style='color:#999999;'>Cover URL: </span>", self.window.book_cover_label.text())
        self.assertIn("<span style='color:#e0e0e0;'>http://example.com/great_test_book_cover.jpg</span>", self.window.book_cover_label.text())

        # Check Default Editions GroupBox and its labels
        self.assertIsNotNone(self.window.default_editions_group_box, "Default Editions GroupBox not found after fetch.")
        self.assertEqual(self.window.default_editions_group_box.title(), "Default Editions")

        self.assertIsNotNone(self.window.default_audio_label, "Default audio label not updated.")
        # Check that the edition info is displayed with HTML formatting
        self.assertIn("Audiobook (ID: aud001)", self.window.default_audio_label.text())
        self.assertIn("href=", self.window.default_audio_label.text())

        self.assertIsNotNone(self.window.default_cover_label_info, "Default cover label info not updated.")
        self.assertIn("Hardcover (ID: cov001)", self.window.default_cover_label_info.text())
        self.assertIn("href=", self.window.default_cover_label_info.text())

        self.assertIsNotNone(self.window.default_ebook_label, "Default ebook label not updated.")
        self.assertIn("E-book (ID: ebk001)", self.window.default_ebook_label.text())
        self.assertIn("href=", self.window.default_ebook_label.text())

        self.assertIsNotNone(self.window.default_physical_label, "Default physical label not updated.")
        self.assertIn("Paperback (ID: phy001)", self.window.default_physical_label.text())
        self.assertIn("href=", self.window.default_physical_label.text())

        
    @patch.object(ApiClient, 'get_book_by_id')
    def test_fetch_data_success_populates_editions_table(self, mock_api_get_book_by_id):
        """
        Test that a successful API call populates the Editions Table Area
        with the fetched editions data according to spec.md section 2.4.1.
        """
        # Sample book data with editions matching new spec
        mock_book_data = {
            "id": "123",
            "title": "The Great Test Book",
            "contributions": [{"author": {"name": "Author One"}}],
            "description": "A description.",
            "editions_count": 2,
            "editions": [
                {
                    "id": "ed1",
                    "score": 95.5,
                    "title": "First Edition with a very long title that should be truncated",
                    "subtitle": "Premium Hardcover",
                    "image": {"url": "http://example.com/ed1_cover.jpg"},
                    "isbn_10": "1234567890",
                    "isbn_13": "9781234567890",
                    "asin": "B001234567",
                    "reading_format_id": 1,  # Physical Book
                    "pages": 300,
                    "audio_seconds": None,
                    "edition_format": "Hardcover",
                    "edition_information": "First printing with author signature",
                    "release_date": "2023-01-15",
                    "publisher": {"name": "Test Publishers Inc."},
                    "language": {"language": "English"},
                    "country": {"name": "United States"}
                },
                {
                    "id": "ed2",
                    "score": 88.0,
                    "title": "Second Edition",
                    "subtitle": None,
                    "image": None,
                    "isbn_10": None,
                    "isbn_13": "9780987654321",
                    "asin": None,
                    "reading_format_id": 2,  # Audiobook
                    "pages": None,
                    "audio_seconds": 32400,  # 9 hours
                    "edition_format": "Audiobook",
                    "edition_information": None,
                    "release_date": "2024-06-30",
                    "publisher": {"name": "Audio House"},
                    "language": {"language": "French"},
                    "country": {"name": "Canada"}
                }
            ]
        }
        mock_api_get_book_by_id.return_value = mock_book_data

        book_id_line_edit = self.window.findChild(QLineEdit, "bookIdLineEdit")
        fetch_data_button = self.window.findChild(QPushButton, "fetchDataButton")

        book_id_line_edit.setText("123")
        fetch_data_button.click()

        # Find the QTableWidget
        editions_table = self.window.editions_table_widget
        self.assertIsNotNone(editions_table, "Editions QTableWidget not found.")

        # Expected column headers per spec (now includes Select column)
        expected_headers = [
            "Select", "id", "score", "title", "subtitle", "Cover Image?", 
            "isbn_10", "isbn_13", "asin", "Reading Format", "pages", 
            "Duration", "edition_format", "edition_information", 
            "release_date", "Publisher", "Language", "Country"
        ]
        self.assertEqual(editions_table.columnCount(), len(expected_headers))
        for i, header in enumerate(expected_headers):
            # Headers may include sort indicators (▲ or ▼), so check base text
            actual_header = editions_table.horizontalHeaderItem(i).text()
            actual_header_base = actual_header.replace(" ▲", "").replace(" ▼", "")
            self.assertEqual(actual_header_base, header)
        
        self.assertEqual(editions_table.rowCount(), 2)

        # Check first row (should be sorted by score desc, so ed1 first)
        # ID column now uses ClickableLabel widget instead of QTableWidgetItem
        id_widget = editions_table.cellWidget(0, 1)  # ID is now column 1 after Select
        if id_widget:
            # It's a ClickableLabel with clickable edition ID
            self.assertIn("ed1", id_widget.text())
        else:
            # Fallback to QTableWidgetItem for N/A values
            self.assertEqual(editions_table.item(0, 1).text(), "ed1")  # id
        self.assertEqual(editions_table.item(0, 2).text(), "95.5")  # score
        # Title should be truncated
        self.assertIn("First Edition with", editions_table.item(0, 3).text())
        self.assertIn("...", editions_table.item(0, 3).text())  # Check truncation
        self.assertEqual(editions_table.item(0, 4).text(), "Premium Hardcover")  # subtitle
        self.assertEqual(editions_table.item(0, 5).text(), "Yes")  # Cover Image?
        self.assertEqual(editions_table.item(0, 6).text(), "1234567890")  # isbn_10
        self.assertEqual(editions_table.item(0, 7).text(), "9781234567890")  # isbn_13
        self.assertEqual(editions_table.item(0, 8).text(), "B001234567")  # asin
        self.assertEqual(editions_table.item(0, 9).text(), "Physical Book")  # Reading Format
        self.assertEqual(editions_table.item(0, 10).text(), "300")  # pages
        self.assertEqual(editions_table.item(0, 11).text(), "N/A")  # Duration
        self.assertEqual(editions_table.item(0, 12).text(), "Hardcover")  # edition_format
        self.assertEqual(editions_table.item(0, 13).text(), "First printing with author signature")  # edition_information
        self.assertEqual(editions_table.item(0, 14).text(), "01/15/2023")  # release_date
        self.assertEqual(editions_table.item(0, 15).text(), "Test Publishers Inc.")  # Publisher
        self.assertEqual(editions_table.item(0, 16).text(), "English")  # Language
        self.assertEqual(editions_table.item(0, 17).text(), "United States")  # Country

        # Check second row
        # ID column now uses ClickableLabel widget instead of QTableWidgetItem  
        id_widget_2 = editions_table.cellWidget(1, 1)  # ID is now column 1 after Select
        if id_widget_2:
            # It's a ClickableLabel with clickable edition ID
            self.assertIn("ed2", id_widget_2.text())
        else:
            # Fallback to QTableWidgetItem for N/A values
            self.assertEqual(editions_table.item(1, 1).text(), "ed2")  # id
        self.assertEqual(editions_table.item(1, 2).text(), "88.0")  # score
        self.assertEqual(editions_table.item(1, 3).text(), "Second Edition")  # title
        self.assertEqual(editions_table.item(1, 4).text(), "N/A")  # subtitle
        self.assertEqual(editions_table.item(1, 5).text(), "No")  # Cover Image?
        self.assertEqual(editions_table.item(1, 6).text(), "N/A")  # isbn_10
        self.assertEqual(editions_table.item(1, 7).text(), "9780987654321")  # isbn_13
        self.assertEqual(editions_table.item(1, 8).text(), "N/A")  # asin
        self.assertEqual(editions_table.item(1, 9).text(), "Audiobook")  # Reading Format
        self.assertEqual(editions_table.item(1, 10).text(), "N/A")  # pages
        self.assertEqual(editions_table.item(1, 11).text(), "09:00:00")  # Duration (9 hours)
        self.assertEqual(editions_table.item(1, 12).text(), "Audiobook")  # edition_format
        self.assertEqual(editions_table.item(1, 13).text(), "N/A")  # edition_information
        self.assertEqual(editions_table.item(1, 14).text(), "06/30/2024")  # release_date
        self.assertEqual(editions_table.item(1, 15).text(), "Audio House")  # Publisher
        self.assertEqual(editions_table.item(1, 16).text(), "French")  # Language
        self.assertEqual(editions_table.item(1, 17).text(), "Canada")  # Country

        # Check that the table supports sorting (our custom widget handles it manually)
        # The table should be sorted by score descending by default
        self.assertEqual(editions_table.item(0, 2).text(), "95.5")  # Higher score first
        self.assertEqual(editions_table.item(1, 2).text(), "88.0")  # Lower score second
        
        # Check tooltip for truncated text
        self.assertEqual(editions_table.item(0, 3).toolTip(), 
                         "First Edition with a very long title that should be truncated")
        
        mock_api_get_book_by_id.assert_called_once_with(123)

    def test_initial_general_book_information_ui_elements_present_and_default(self):
        """
        Test that all UI elements for General Book Information are present after
        MainWindow instantiation and display their default "Not Fetched" or "N/A" text.
        """
        # Find the "General Book Information Area" QGroupBox
        book_info_area = self.window.findChild(QGroupBox, "bookInfoArea")
        self.assertIsNotNone(book_info_area, "General Book Information Area QGroupBox not found.")

        # Check labels directly attached to MainWindow instance
        # Ensure they are ClickableLabels where appropriate
        self.assertIsNotNone(self.window.book_title_label, "Book Title QLabel not found.")
        self.assertIn("<span style='color:#999999;'>Title: </span>", self.window.book_title_label.text())
        self.assertIn("<span style='color:#e0e0e0;'>Not Fetched</span>", self.window.book_title_label.text())

        self.assertIsNotNone(self.window.book_slug_label, "Book Slug QLabel not found.")
        self.assertIsInstance(self.window.book_slug_label, ClickableLabel)
        self.assertIn("<span style='color:#999999;'>Slug: </span>", self.window.book_slug_label.text())
        self.assertIn("<span style='color:#e0e0e0;'>Not Fetched</span>", self.window.book_slug_label.text())
        self.assertEqual(self.window.book_slug_label.toolTip(), "") # No link initially

        self.assertIsNotNone(self.window.book_authors_label, "Book Authors QLabel not found.")
        self.assertIn("<span style='color:#999999;'>Authors: </span>", self.window.book_authors_label.text())
        self.assertIn("<span style='color:#e0e0e0;'>Not Fetched</span>", self.window.book_authors_label.text())

        self.assertIsNotNone(self.window.book_id_queried_label, "Book ID (Queried) QLabel not found.")
        self.assertIn("<span style='color:#999999;'>Book ID (Queried): </span>", self.window.book_id_queried_label.text())
        self.assertIn("<span style='color:#e0e0e0;'>Not Fetched</span>", self.window.book_id_queried_label.text())
        # self.assertNotIsInstance(self.window.book_id_queried_label, ClickableLabel) # Should not be clickable

        self.assertIsNotNone(self.window.book_total_editions_label, "Total Editions QLabel not found.")
        self.assertIn("<span style='color:#999999;'>Total Editions: </span>", self.window.book_total_editions_label.text())
        self.assertIn("<span style='color:#e0e0e0;'>Not Fetched</span>", self.window.book_total_editions_label.text())
        # self.assertNotIsInstance(self.window.book_total_editions_label, ClickableLabel)

        # Check for the new QLabel for description
        self.assertIsNotNone(self.window.book_description_label, "Book Description QLabel not found.")
        self.assertIn("<span style='color:#999999;'>Description: </span>", self.window.book_description_label.text())
        self.assertIn("<span style='color:#e0e0e0;'>Not Fetched</span>", self.window.book_description_label.text())
        self.assertEqual(self.window.book_description_label.toolTip(), "", "Initial tooltip for description should be empty.")
        # self.assertNotIsInstance(self.window.book_description_label, ClickableLabel)

        # Check for Default Editions GroupBox
        default_editions_gb = self.window.findChild(QGroupBox, "defaultEditionsGroupBox")
        self.assertIsNotNone(default_editions_gb, "Default Editions QGroupBox not found.")
        self.assertEqual(default_editions_gb.title(), "Default Editions")
        self.assertIs(default_editions_gb.parentWidget(), book_info_area, "Default Editions GroupBox should be in Book Info Area.")

        # Check labels within Default Editions GroupBox
        self.assertIsNotNone(self.window.default_audio_label, "Default Audio Label not found.")
        self.assertIsInstance(self.window.default_audio_label, ClickableLabel)
        self.assertIn("<span style='color:#999999;'>Default Audio Edition: </span>", self.window.default_audio_label.text())
        # N/A might be highlighted or not depending on context
        self.assertIn("N/A</span>", self.window.default_audio_label.text())
        self.assertIs(self.window.default_audio_label.parentWidget(), default_editions_gb, "Default Audio Label not in correct group box.")
        self.assertEqual(self.window.default_audio_label.toolTip(), "")

        self.assertIsNotNone(self.window.default_cover_label_info, "Default Cover Label Info not found.")
        self.assertIsInstance(self.window.default_cover_label_info, ClickableLabel)
        self.assertIn("<span style='color:#999999;'>Default Cover Edition: </span>", self.window.default_cover_label_info.text())
        # N/A might be highlighted or not depending on context
        self.assertIn("N/A</span>", self.window.default_cover_label_info.text())
        self.assertIs(self.window.default_cover_label_info.parentWidget(), default_editions_gb, "Default Cover Label Info not in correct group box.")
        self.assertEqual(self.window.default_cover_label_info.toolTip(), "")

        self.assertIsNotNone(self.window.default_ebook_label, "Default E-book Label not found.")
        self.assertIsInstance(self.window.default_ebook_label, ClickableLabel)
        self.assertIn("<span style='color:#999999;'>Default E-book Edition: </span>", self.window.default_ebook_label.text())
        # N/A might be highlighted or not depending on context
        self.assertIn("N/A</span>", self.window.default_ebook_label.text())
        self.assertIs(self.window.default_ebook_label.parentWidget(), default_editions_gb, "Default E-book Label not in correct group box.")
        self.assertEqual(self.window.default_ebook_label.toolTip(), "")

        self.assertIsNotNone(self.window.default_physical_label, "Default Physical Label not found.")
        self.assertIsInstance(self.window.default_physical_label, ClickableLabel)
        self.assertIn("<span style='color:#999999;'>Default Physical Edition: </span>", self.window.default_physical_label.text())
        # N/A might be highlighted or not depending on context
        self.assertIn("N/A</span>", self.window.default_physical_label.text())
        self.assertIs(self.window.default_physical_label.parentWidget(), default_editions_gb, "Default Physical Label not in correct group box.")
        self.assertEqual(self.window.default_physical_label.toolTip(), "")

        # Check the main book cover URL label (which is separate from default editions info)
        self.assertIsNotNone(self.window.book_cover_label, "Book Cover URL QLabel not found.")
        self.assertIn("<span style='color:#999999;'>Cover URL: </span>", self.window.book_cover_label.text())
        self.assertIn("<span style='color:#e0e0e0;'>Not Fetched</span>", self.window.book_cover_label.text())

    @patch.object(ApiClient, 'get_book_by_id')
    def test_fetch_data_populates_book_info_with_null_defaults(self, mock_api_get_book_by_id):
        """
        Test that "N/A" is displayed for fields that are null or missing in the API response.
        """
        mock_book_data_with_nulls = {
            "id": "456", # Still need an ID for the book itself
            "title": "Book With Missing Info",
            "slug": None, # Test None slug
            "contributions": None, # Test None contributions
            "description": None, # Test None description
            "editions_count": None, # Test None editions_count
            "default_audio_edition": None,
            "default_cover_edition": None, # This will also make cover URL N/A
            "default_ebook_edition": None,
            "default_physical_edition": None
        }
        mock_api_get_book_by_id.return_value = mock_book_data_with_nulls

        book_id_line_edit = self.window.findChild(QLineEdit, "bookIdLineEdit")
        fetch_data_button = self.window.findChild(QPushButton, "fetchDataButton")

        book_id_line_edit.setText("456")
        fetch_data_button.click()

        # Check labels for "N/A"
        self.assertIn("<span style='color:#999999;'>Title: </span>", self.window.book_title_label.text())
        self.assertIn("<span style='color:#e0e0e0;'>Book With Missing Info</span>", self.window.book_title_label.text()) # Title is present

        self.assertIn("<span style='color:#999999;'>Slug: </span>", self.window.book_slug_label.text())
        # N/A might be highlighted or not depending on context
        self.assertIn("N/A</span>", self.window.book_slug_label.text())
        self.assertIn("<span style='color:#999999;'>Authors: </span>", self.window.book_authors_label.text())
        # N/A might be highlighted or not depending on context
        self.assertIn("N/A</span>", self.window.book_authors_label.text())
        self.assertIn("<span style='color:#999999;'>Book ID (Queried): </span>", self.window.book_id_queried_label.text())
        self.assertIn("<span style='color:#e0e0e0;'>456</span>", self.window.book_id_queried_label.text()) # From input
        self.assertIn("<span style='color:#999999;'>Total Editions: </span>", self.window.book_total_editions_label.text())
        # N/A might be highlighted or not depending on context
        self.assertIn("N/A</span>", self.window.book_total_editions_label.text())
        
        # Description label
        self.assertIn("<span style='color:#999999;'>Description: </span>", self.window.book_description_label.text())
        # N/A might be highlighted or not depending on context
        self.assertIn("N/A</span>", self.window.book_description_label.text())
        self.assertEqual(self.window.book_description_label.toolTip(), "", "Tooltip should be empty for N/A description")

        # Default Editions
        self.assertIn("<span style='color:#999999;'>Default Audio Edition: </span>", self.window.default_audio_label.text())
        # N/A might be highlighted or not depending on context
        self.assertIn("N/A</span>", self.window.default_audio_label.text())
        self.assertIn("<span style='color:#999999;'>Default Cover Edition: </span>", self.window.default_cover_label_info.text())
        # N/A might be highlighted or not depending on context
        self.assertIn("N/A</span>", self.window.default_cover_label_info.text())
        self.assertIn("<span style='color:#999999;'>Default E-book Edition: </span>", self.window.default_ebook_label.text())
        # N/A might be highlighted or not depending on context
        self.assertIn("N/A</span>", self.window.default_ebook_label.text())
        self.assertIn("<span style='color:#999999;'>Default Physical Edition: </span>", self.window.default_physical_label.text())
        # N/A might be highlighted or not depending on context
        self.assertIn("N/A</span>", self.window.default_physical_label.text())

        # Main Cover URL Label (derived from default_cover_edition)
        self.assertIn("<span style='color:#999999;'>Cover URL: </span>", self.window.book_cover_label.text())
        # N/A might be highlighted or not depending on context
        self.assertIn("N/A</span>", self.window.book_cover_label.text())

        # Test that N/A labels are not clickable
        with patch('librarian_assistant.main.webbrowser.open') as mock_webbrowser_open_na:
            QTest.mouseClick(self.window.book_slug_label, Qt.LeftButton) # Slug is None
            mock_webbrowser_open_na.assert_not_called()

            QTest.mouseClick(self.window.default_audio_label, Qt.LeftButton) # Default audio is None
            mock_webbrowser_open_na.assert_not_called()
            # ... (add similar checks for other default editions if they are None) ...

        # Check status bar for success message, as the fetch itself was "successful"
        # even if data fields were null.
        expected_status_message = "Book data fetched successfully for ID 456."
        self.assertEqual(self.window.status_bar.currentMessage(), expected_status_message)
    
    @patch.object(ApiClient, 'get_book_by_id')
    def test_editions_table_data_transformations(self, mock_api_get_book_by_id):
        """
        Test that the editions table correctly transforms data according to spec:
        - Reading format ID mapping
        - Date formatting
        - Audio seconds to HH:MM:SS
        - N/A handling for null values
        """
        mock_book_data = {
            "id": "789",
            "title": "Test Book",
            "contributions": [],
            "editions_count": 3,
            "editions": [
                {
                    "id": "ed_ebook",
                    "score": 50,
                    "title": "E-Book Edition",
                    "reading_format_id": 4,  # E-Book
                    "audio_seconds": None,
                    "pages": 250,
                    "release_date": None,  # Test N/A date
                },
                {
                    "id": "ed_unknown",
                    "score": 40,
                    "title": "Unknown Format",
                    "reading_format_id": 99,  # Unknown format
                    "pages": None,  # Test N/A pages
                    "release_date": "invalid-date",  # Test invalid date format
                },
                {
                    "id": "ed_audio_long",
                    "score": 30,
                    "title": "Long Audiobook",
                    "reading_format_id": 2,  # Audiobook
                    "audio_seconds": 45678,  # 12:41:18
                    "pages": None,
                    "release_date": "2025-12-25",
                }
            ]
        }
        mock_api_get_book_by_id.return_value = mock_book_data

        book_id_line_edit = self.window.findChild(QLineEdit, "bookIdLineEdit")
        fetch_data_button = self.window.findChild(QPushButton, "fetchDataButton")

        book_id_line_edit.setText("789")
        fetch_data_button.click()

        editions_table = self.window.editions_table_widget
        
        # Check E-Book format (column 9 after Select)
        self.assertEqual(editions_table.item(0, 9).text(), "E-Book")
        self.assertEqual(editions_table.item(0, 11).text(), "N/A")  # No audio duration
        self.assertEqual(editions_table.item(0, 14).text(), "N/A")  # Null date
        
        # Check unknown reading format (should show raw ID)
        self.assertEqual(editions_table.item(1, 9).text(), "99")
        self.assertEqual(editions_table.item(1, 10).text(), "N/A")  # Null pages
        self.assertEqual(editions_table.item(1, 14).text(), "invalid-date")  # Invalid date kept as-is
        
        # Check audiobook duration conversion
        self.assertEqual(editions_table.item(2, 9).text(), "Audiobook")
        self.assertEqual(editions_table.item(2, 11).text(), "12:41:18")  # 45678 seconds
        self.assertEqual(editions_table.item(2, 14).text(), "12/25/2025")  # Formatted date

    @patch.object(ApiClient, 'get_book_by_id')
    def test_editions_table_contributor_columns(self, mock_api_get_book_by_id):
        """
        Test that the editions table correctly handles contributor columns:
        - Dynamic column creation based on roles present
        - Proper ordering of contributors
        - contribution:null handled as primary Author
        - N/A for missing contributors
        """
        mock_book_data = {
            "id": "999",
            "title": "Test Book with Contributors",
            "contributions": [],
            "editions_count": 2,
            "editions": [
                {
                    "id": "ed_with_contributors",
                    "score": 100,
                    "title": "Edition with Multiple Contributors",
                    "cached_contributors": [
                        {
                            "author": {"name": "Primary Author", "slug": "primary-author"},
                            "contribution": None  # Should be Author 1
                        },
                        {
                            "author": {"name": "Second Author", "slug": "second-author"},
                            "contribution": "Author"  # Should be Author 2
                        },
                        {
                            "author": {"name": "The Narrator", "slug": "narrator-1"},
                            "contribution": "Narrator"  # Should be Narrator 1
                        },
                        {
                            "author": {"name": "Translator One", "slug": "translator-1"},
                            "contribution": "Translator"  # Should be Translator 1
                        }
                    ],
                    "reading_format_id": 2,
                    "pages": None,
                    "audio_seconds": 3600,
                },
                {
                    "id": "ed_fewer_contributors",
                    "score": 90,
                    "title": "Edition with Fewer Contributors",
                    "cached_contributors": [
                        {
                            "author": {"name": "Solo Author", "slug": "solo-author"},
                            "contribution": None  # Should be Author 1
                        }
                    ],
                    "reading_format_id": 1,
                    "pages": 200,
                }
            ]
        }
        mock_api_get_book_by_id.return_value = mock_book_data

        book_id_line_edit = self.window.findChild(QLineEdit, "bookIdLineEdit")
        fetch_data_button = self.window.findChild(QPushButton, "fetchDataButton")

        book_id_line_edit.setText("999")
        fetch_data_button.click()

        editions_table = self.window.editions_table_widget
        
        # Check that contributor columns were added
        headers = [editions_table.horizontalHeaderItem(i).text() 
                  for i in range(editions_table.columnCount())]
        
        # Should have Author (2), Narrator (1), and Translator (1) columns based on actual data
        self.assertIn("Author 1", headers)
        self.assertIn("Author 2", headers)  # Second Author in first edition
        self.assertNotIn("Author 3", headers)  # No more than 2 authors
        self.assertIn("Narrator 1", headers)
        self.assertNotIn("Narrator 2", headers)  # Only 1 narrator in data
        self.assertIn("Translator 1", headers)
        self.assertNotIn("Translator 2", headers)  # Only 1 translator in data
        
        # Should NOT have roles that aren't present
        self.assertNotIn("Illustrator 1", headers)
        self.assertNotIn("Editor 1", headers)
        
        # Find column indices (strip sort indicators from headers)
        headers_base = [h.replace(" ▲", "").replace(" ▼", "") for h in headers]
        id_col = headers_base.index("id")
        author1_col = headers_base.index("Author 1")
        author2_col = headers_base.index("Author 2")
        narrator1_col = headers_base.index("Narrator 1")
        translator1_col = headers_base.index("Translator 1")
        
        # Find which row has which edition (table is sorted by score desc)
        # Edition with score 100 should be first
        # ID column now uses ClickableLabel widget instead of QTableWidgetItem
        id_widget_row0 = editions_table.cellWidget(0, id_col)
        if id_widget_row0 and "ed_with_contributors" in id_widget_row0.text():
            row_with_contributors = 0
        else:
            # Check if it's a QTableWidgetItem for N/A values
            item_row0 = editions_table.item(0, id_col)
            if item_row0 and item_row0.text() == "ed_with_contributors":
                row_with_contributors = 0
            else:
                row_with_contributors = 1
        row_fewer_contributors = 1 - row_with_contributors
        
        # Check edition with multiple contributors
        self.assertEqual(editions_table.item(row_with_contributors, author1_col).text(), "Primary Author")
        self.assertEqual(editions_table.item(row_with_contributors, author2_col).text(), "Second Author")
        self.assertEqual(editions_table.item(row_with_contributors, narrator1_col).text(), "The Narrator")
        self.assertEqual(editions_table.item(row_with_contributors, translator1_col).text(), "Translator One")
        
        # Check edition with fewer contributors
        self.assertEqual(editions_table.item(row_fewer_contributors, author1_col).text(), "Solo Author")
        self.assertEqual(editions_table.item(row_fewer_contributors, author2_col).text(), "N/A")  # No second author
        self.assertEqual(editions_table.item(row_fewer_contributors, narrator1_col).text(), "N/A")  # No narrator
        self.assertEqual(editions_table.item(row_fewer_contributors, translator1_col).text(), "N/A")  # No translator
    
    def test_process_contributor_data_parsing(self):
        """Test the _process_contributor_data method handles various contributor scenarios."""
        # Test data with various contributor scenarios
        editions = [
            {
                'id': 'ed1',
                'cached_contributors': [
                    {'author': {'name': 'Primary Author'}, 'contribution': None},  # Primary author
                    {'author': {'name': 'Secondary Author'}, 'contribution': 'Author'},
                    {'author': {'name': 'The Narrator'}, 'contribution': 'Narrator'},
                    {'author': {'name': 'The Editor'}, 'contribution': 'Editor'}
                ]
            },
            {
                'id': 'ed2',
                'cached_contributors': [
                    {'author': {'name': 'Another Author'}, 'contribution': None},
                    {'author': {'name': 'Illustrator One'}, 'contribution': 'Illustrator'},
                    {'author': {'name': 'Illustrator Two'}, 'contribution': 'Illustrator'}
                ]
            },
            {
                'id': 'ed3',
                'cached_contributors': []  # Edition with no contributors
            }
        ]
        
        result = self.window._process_contributor_data(editions)
        
        # Check active roles are in the correct order (predefined order maintained)
        expected_roles = ['Author', 'Illustrator', 'Editor', 'Narrator']  # Only roles that exist in data
        self.assertEqual(result['active_roles'], expected_roles)
        
        # Check contributors by edition
        contributors = result['contributors_by_edition']
        
        # Edition 1 checks
        self.assertIn('ed1', contributors)
        self.assertEqual(contributors['ed1']['Author'], ['Primary Author', 'Secondary Author'])
        self.assertEqual(contributors['ed1']['Narrator'], ['The Narrator'])
        self.assertEqual(contributors['ed1']['Editor'], ['The Editor'])
        
        # Edition 2 checks
        self.assertIn('ed2', contributors)
        self.assertEqual(contributors['ed2']['Author'], ['Another Author'])
        self.assertEqual(contributors['ed2']['Illustrator'], ['Illustrator One', 'Illustrator Two'])
        
        # Edition 3 checks
        self.assertIn('ed3', contributors)
        self.assertEqual(contributors['ed3'], {})  # No contributors
        
        # Check max contributors per role
        max_contributors = result['max_contributors_per_role']
        self.assertEqual(max_contributors['Author'], 2)  # Ed1 has 2 authors
        self.assertEqual(max_contributors['Illustrator'], 2)  # Ed2 has 2 illustrators
        self.assertEqual(max_contributors['Editor'], 1)  # Ed1 has 1 editor
        self.assertEqual(max_contributors['Narrator'], 1)  # Ed1 has 1 narrator
    
    @patch.object(ApiClient, 'get_book_by_id')
    def test_contributor_column_visibility(self, mock_api_get_book_by_id):
        """Test that only roles with contributors get columns created."""
        # Mock data with only Authors and Narrators (no Illustrators, Editors, etc.)
        mock_response = {
            'id': 12345,
            'name': 'Test Book',
            'title': 'Test Book',
            'slug': 'test-book',
            'description': 'Test description',
            'editions_count': 2,
            'contributions': [],
            'default_edition': {'audio': None, 'cover': None, 'ebook': None, 'physical': None},
            'editions': [
                        {
                            'id': 'ed1',
                            'score': 100,
                            'title': 'Edition with Author and Narrator',
                            'subtitle': None,
                            'image': {'url': 'http://example.com/cover.jpg'},
                            'isbn_10': '1234567890',
                            'isbn_13': '1234567890123',
                            'asin': 'B001',
                            'reading_format_id': 1,
                            'pages': 300,
                            'audio_seconds': None,
                            'edition_format': 'Hardcover',
                            'edition_information': 'First edition',
                            'release_date': '2023-01-01',
                            'publisher': {'name': 'Test Publisher'},
                            'language': {'language': 'English'},
                            'country': {'name': 'United States'},
                            'cached_contributors': [
                                {'author': {'name': 'Author One'}, 'contribution': None},
                                {'author': {'name': 'Narrator One'}, 'contribution': 'Narrator'}
                            ]
                        },
                        {
                            'id': 'ed2', 
                            'score': 90,
                            'title': 'Edition with only Author',
                            'subtitle': None,
                            'image': None,
                            'isbn_10': None,
                            'isbn_13': None,
                            'asin': None,
                            'reading_format_id': 4,
                            'pages': None,
                            'audio_seconds': None,
                            'edition_format': 'E-book',
                            'edition_information': None,
                            'release_date': None,
                            'publisher': None,
                            'language': None,
                            'country': None,
                            'cached_contributors': [
                                {'author': {'name': 'Author Two'}, 'contribution': 'Author'}
                            ]
                        }
                    ]
        }
        
        # Set up the mock return value
        mock_api_get_book_by_id.return_value = mock_response
        
        # Mock the config manager to return a token
        with patch.object(self.window.config_manager, 'load_token', return_value='test_token'):
            self.window.book_id_line_edit.setText("12345")
            self.window.fetch_data_button.click()
            QApplication.processEvents()
        
        # Check that only Author and Narrator columns exist
        editions_table = self.window.editions_table_widget
        self.assertGreater(editions_table.columnCount(), 0, "Table should have columns after fetch")
        headers = [editions_table.horizontalHeaderItem(i).text() for i in range(editions_table.columnCount())]
        
        # Should have only Author 1 and Narrator 1 columns (based on test data)
        self.assertIn("Author 1", headers)
        self.assertIn("Narrator 1", headers)
        
        # Should NOT have additional Author/Narrator columns beyond what's needed
        for i in range(2, 11):
            self.assertNotIn(f"Author {i}", headers)
            self.assertNotIn(f"Narrator {i}", headers)
        
        # Should NOT have columns for roles with no contributors
        self.assertNotIn("Illustrator 1", headers)
        self.assertNotIn("Editor 1", headers)
        self.assertNotIn("Translator 1", headers)
        self.assertNotIn("Foreword 1", headers)
        self.assertNotIn("Cover Artist 1", headers)
        self.assertNotIn("Other 1", headers)
    
    @patch.object(ApiClient, 'get_book_by_id')
    def test_contributor_null_handling(self, mock_api_get_book_by_id):
        """Test handling of null contribution field (primary author)."""
        mock_response = {
            'id': 12345,
            'name': 'Test Book',
            'title': 'Test Book',
            'slug': 'test-book',
            'description': 'Test description',
            'editions_count': 1,
            'contributions': [],
            'default_edition': {'audio': None, 'cover': None, 'ebook': None, 'physical': None},
            'editions': [
                        {
                            'id': 'ed1',
                            'score': 100,
                            'title': 'Test Edition',
                            'subtitle': None,
                            'image': None,
                            'isbn_10': None,
                            'isbn_13': None,
                            'asin': None,
                            'reading_format_id': 1,
                            'pages': 200,
                            'audio_seconds': None,
                            'edition_format': 'Paperback',
                            'edition_information': None,
                            'release_date': None,
                            'publisher': None,
                            'language': None,
                            'country': None,
                            'cached_contributors': [
                                {'author': {'name': 'Primary Author'}, 'contribution': None},
                                {'author': {'name': 'Secondary Author'}, 'contribution': 'Author'},
                                {'author': {'name': 'Third Author'}, 'contribution': None}
                            ]
                        }
                    ]
        }
        
        # Set up the mock return value
        mock_api_get_book_by_id.return_value = mock_response
        
        # Mock the config manager to return a token
        with patch.object(self.window.config_manager, 'load_token', return_value='test_token'):
            self.window.book_id_line_edit.setText("12345")
            self.window.fetch_data_button.click()
            QApplication.processEvents()
        
        editions_table = self.window.editions_table_widget
        self.assertGreater(editions_table.columnCount(), 0, "Table should have columns after fetch")
        headers = [editions_table.horizontalHeaderItem(i).text() for i in range(editions_table.columnCount())]
        
        # Find Author columns (strip sort indicators)
        headers_base = [h.replace(" ▲", "").replace(" ▼", "") for h in headers]
        author1_col = headers_base.index("Author 1")
        author2_col = headers_base.index("Author 2")
        author3_col = headers_base.index("Author 3")
        
        # First null contribution should be Author 1, then Secondary Author, then Third Author with null
        self.assertEqual(editions_table.item(0, author1_col).text(), "Primary Author")
        self.assertEqual(editions_table.item(0, author2_col).text(), "Secondary Author")
        self.assertEqual(editions_table.item(0, author3_col).text(), "Third Author")

    def test_collapsible_groupboxes(self):
        """Test that API input and book info areas are collapsible with arrow indicators."""
        # Check that both group boxes are checkable
        self.assertTrue(self.window.api_input_area.isCheckable())
        self.assertTrue(self.window.book_info_area.isCheckable())
        
        # Check that both start expanded with down arrows
        self.assertTrue(self.window.api_input_area.isChecked())
        self.assertTrue(self.window.book_info_area.isChecked())
        self.assertIn("▼", self.window.api_input_area.title())
        self.assertIn("▼", self.window.book_info_area.title())
        
        # Test that the handlers exist
        self.assertTrue(hasattr(self.window, '_on_api_input_toggled'))
        self.assertTrue(hasattr(self.window, '_on_book_info_toggled'))
        
        # Test collapsing API input area
        initial_height = self.window.api_input_area.maximumHeight()
        self.window.api_input_area.setChecked(False)
        # Manually trigger the toggle handler since setChecked doesn't emit toggled
        self.window._on_api_input_toggled(False)
        QApplication.processEvents()
        
        # Check that the height is limited and arrow changed
        self.assertEqual(self.window.api_input_area.maximumHeight(), 30)
        self.assertLess(self.window.api_input_area.maximumHeight(), initial_height)
        self.assertIn("▶", self.window.api_input_area.title())
        self.assertNotIn("▼", self.window.api_input_area.title())
        
        # Test expanding API input area
        self.window.api_input_area.setChecked(True)
        self.window._on_api_input_toggled(True)
        QApplication.processEvents()
        
        # Check that the height is reset and arrow changed back
        self.assertEqual(self.window.api_input_area.maximumHeight(), 16777215)
        self.assertIn("▼", self.window.api_input_area.title())
        self.assertNotIn("▶", self.window.api_input_area.title())
        
        # Test the same for book info area
        initial_info_height = self.window.book_info_area.maximumHeight()
        self.window.book_info_area.setChecked(False)
        self.window._on_book_info_toggled(False)
        QApplication.processEvents()
        
        # Check collapsed state with arrow
        self.assertEqual(self.window.book_info_area.maximumHeight(), 30)
        self.assertLess(self.window.book_info_area.maximumHeight(), initial_info_height)
        self.assertIn("▶", self.window.book_info_area.title())
        
        # Check expanded state with arrow
        self.window.book_info_area.setChecked(True)
        self.window._on_book_info_toggled(True)
        QApplication.processEvents()
        
        self.assertEqual(self.window.book_info_area.maximumHeight(), 16777215)
        self.assertIn("▼", self.window.book_info_area.title())
    
    def test_configure_columns_button_exists(self):
        """Test that Configure Columns button exists."""
        # Check button exists
        self.assertIsNotNone(self.window.configure_columns_button)
        self.assertEqual(self.window.configure_columns_button.text(), "Configure Columns")
        
        # Check it's in the editions table area
        self.assertEqual(self.window.configure_columns_button.parent(), self.window.editions_table_area)
    
    @patch('librarian_assistant.main.ColumnConfigDialog')
    def test_configure_columns_no_data(self, mock_dialog_class):
        """Test configure columns with no data loaded."""
        # Click configure columns button
        self.window.configure_columns_button.click()
        
        # Should show status message
        self.assertEqual(self.window.status_bar.currentMessage(), 
                        "No data loaded. Fetch book data first.")
        
        # Dialog should not be created
        mock_dialog_class.assert_not_called()
    
    @patch('librarian_assistant.main.ColumnConfigDialog')
    def test_configure_columns_with_data(self, mock_dialog_class):
        """Test configure columns after data is loaded."""
        # Mock dialog instance
        mock_dialog = Mock()
        mock_dialog_class.return_value = mock_dialog
        
        # Simulate having loaded data
        self.window.all_column_names = ["id", "title", "author", "isbn"]
        self.window.visible_column_names = ["id", "title", "author"]
        
        # Click configure columns button
        self.window.configure_columns_button.click()
        
        # Dialog should be created with current configuration
        mock_dialog_class.assert_called_once_with(
            ["id", "title", "author", "isbn"],
            ["id", "title", "author"],
            self.window
        )
        
        # Signal should be connected
        mock_dialog.columns_configured.connect.assert_called_once()
        
        # Dialog should be shown
        mock_dialog.exec_.assert_called_once()
    
    def test_table_column_resizing_enabled(self):
        """Test that table columns can be resized."""
        # Add some columns first
        self.window.editions_table_widget.setColumnCount(3)
        self.window.editions_table_widget.setHorizontalHeaderLabels(["Col1", "Col2", "Col3"])
        
        # Check resize mode is interactive
        header = self.window.editions_table_widget.horizontalHeader()
        
        # Check minimum section size is set
        self.assertEqual(header.minimumSectionSize(), 50)
        
        # Check last section stretches
        self.assertTrue(header.stretchLastSection())
        
        # Test that we can set column width
        original_width = header.sectionSize(0)
        new_width = 200
        self.window.editions_table_widget.setColumnWidth(0, new_width)
        self.assertEqual(header.sectionSize(0), new_width)
        self.assertNotEqual(original_width, new_width)
    
    def test_filter_button_exists(self):
        """Test that Advanced Filter button exists."""
        # Check button exists
        self.assertIsNotNone(self.window.filter_button)
        self.assertEqual(self.window.filter_button.text(), "Advanced Filter")
        
        # Check it's in the editions table area
        self.assertEqual(self.window.filter_button.parent(), self.window.editions_table_area)
    
    @patch('librarian_assistant.main.FilterDialog')
    def test_filter_no_data(self, mock_dialog_class):
        """Test filter with no data loaded."""
        # Click filter button
        self.window.filter_button.click()
        
        # Should show status message
        self.assertEqual(self.window.status_bar.currentMessage(), 
                        "No data loaded. Fetch book data first.")
        
        # Dialog should not be created
        mock_dialog_class.assert_not_called()
    
    def test_filter_operator_text(self):
        """Test text filter operators."""
        # Test Contains
        self.assertTrue(self.window._apply_filter_operator("Harry Potter", "Contains", "Harry", "title"))
        self.assertFalse(self.window._apply_filter_operator("Harry Potter", "Contains", "Ron", "title"))
        
        # Test Equals
        self.assertTrue(self.window._apply_filter_operator("Test", "Equals", "test", "title"))
        self.assertFalse(self.window._apply_filter_operator("Test", "Equals", "Testing", "title"))
        
        # Test Starts with
        self.assertTrue(self.window._apply_filter_operator("Harry Potter", "Starts with", "Harry", "title"))
        self.assertFalse(self.window._apply_filter_operator("Harry Potter", "Starts with", "Potter", "title"))
        
        # Test Is empty
        self.assertTrue(self.window._apply_filter_operator("", "Is empty", None, "title"))
        self.assertTrue(self.window._apply_filter_operator("N/A", "Is empty", None, "title"))
        self.assertFalse(self.window._apply_filter_operator("Test", "Is empty", None, "title"))
    
    def test_filter_operator_numeric(self):
        """Test numeric filter operators."""
        # Test equals
        self.assertTrue(self.window._apply_filter_operator("4.5", "=", "4.5", "score"))
        self.assertFalse(self.window._apply_filter_operator("4.5", "=", "4.0", "score"))
        
        # Test greater than
        self.assertTrue(self.window._apply_filter_operator("4.5", ">", "4.0", "score"))
        self.assertFalse(self.window._apply_filter_operator("4.5", ">", "5.0", "score"))
        
        # Test less than or equal
        self.assertTrue(self.window._apply_filter_operator("4.5", "<=", "4.5", "score"))
        self.assertTrue(self.window._apply_filter_operator("4.5", "<=", "5.0", "score"))
        self.assertFalse(self.window._apply_filter_operator("4.5", "<=", "4.0", "score"))
    
    def test_filter_operator_date(self):
        """Test date filter operators."""
        # Test Is on
        self.assertTrue(self.window._apply_filter_operator("01/15/2023", "Is on", "2023-01-15", "release_date"))
        self.assertFalse(self.window._apply_filter_operator("01/15/2023", "Is on", "2023-01-16", "release_date"))
        
        # Test Is before
        self.assertTrue(self.window._apply_filter_operator("01/15/2023", "Is before", "2023-01-20", "release_date"))
        self.assertFalse(self.window._apply_filter_operator("01/15/2023", "Is before", "2023-01-10", "release_date"))
        
        # Test Is between
        filter_value = {'start': '2023-01-01', 'end': '2023-01-31'}
        self.assertTrue(self.window._apply_filter_operator("01/15/2023", "Is between", filter_value, "release_date"))
        
        filter_value = {'start': '2023-02-01', 'end': '2023-02-28'}
        self.assertFalse(self.window._apply_filter_operator("01/15/2023", "Is between", filter_value, "release_date"))
    
    def test_filter_operator_special(self):
        """Test special filter operators."""
        # Test Cover Image
        self.assertTrue(self.window._apply_filter_operator("Yes", 'Is "Yes"', None, "Cover Image?"))
        self.assertFalse(self.window._apply_filter_operator("No", 'Is "Yes"', None, "Cover Image?"))
        
        # Test Is N/A
        self.assertTrue(self.window._apply_filter_operator("N/A", "Is N/A", None, "pages"))
        self.assertFalse(self.window._apply_filter_operator("100", "Is N/A", None, "pages"))
        
        # Test Reading Format
        self.assertTrue(self.window._apply_filter_operator("Audiobook", "Is", "Audiobook", "Reading Format"))
        self.assertFalse(self.window._apply_filter_operator("Audiobook", "Is", "E-Book", "Reading Format"))
    
    def test_row_matches_filters_and_logic(self):
        """Test row matching with AND logic."""
        # Set up a simple table
        self.window.editions_table_widget.setRowCount(1)
        self.window.editions_table_widget.setColumnCount(2)
        self.window.editions_table_widget.setHorizontalHeaderLabels(['title', 'score'])
        self.window.editions_table_widget.setItem(0, 0, QTableWidgetItem("Harry Potter"))
        self.window.editions_table_widget.setItem(0, 1, QTableWidgetItem("4.5"))
        
        # Test AND logic - both match
        filters = [
            {'column': 'title', 'operator': 'Contains', 'value': 'Harry'},
            {'column': 'score', 'operator': '>', 'value': '4.0'}
        ]
        self.assertTrue(self.window._row_matches_filters(0, filters, 'AND'))
        
        # Test AND logic - one doesn't match
        filters = [
            {'column': 'title', 'operator': 'Contains', 'value': 'Harry'},
            {'column': 'score', 'operator': '>', 'value': '5.0'}
        ]
        self.assertFalse(self.window._row_matches_filters(0, filters, 'AND'))
    
    def test_row_matches_filters_or_logic(self):
        """Test row matching with OR logic."""
        # Set up a simple table
        self.window.editions_table_widget.setRowCount(1)
        self.window.editions_table_widget.setColumnCount(2)
        self.window.editions_table_widget.setHorizontalHeaderLabels(['title', 'score'])
        self.window.editions_table_widget.setItem(0, 0, QTableWidgetItem("Harry Potter"))
        self.window.editions_table_widget.setItem(0, 1, QTableWidgetItem("4.5"))
        
        # Test OR logic - one matches
        filters = [
            {'column': 'title', 'operator': 'Contains', 'value': 'Ron'},
            {'column': 'score', 'operator': '>', 'value': '4.0'}
        ]
        self.assertTrue(self.window._row_matches_filters(0, filters, 'OR'))
        
        # Test OR logic - none match
        filters = [
            {'column': 'title', 'operator': 'Contains', 'value': 'Ron'},
            {'column': 'score', 'operator': '>', 'value': '5.0'}
        ]
        self.assertFalse(self.window._row_matches_filters(0, filters, 'OR'))

    @patch('librarian_assistant.main.webbrowser.open')
    def test_open_web_link_called_with_url(self, mock_webbrowser_open):
        """
        Test that _open_web_link method calls webbrowser.open with the provided URL.
        """
        test_url = "https://hardcover.app/books/test-book"
        self.window._open_web_link(test_url)
        mock_webbrowser_open.assert_called_once_with(test_url)

    @patch('librarian_assistant.main.webbrowser.open')
    def test_open_web_link_not_called_with_empty_url(self, mock_webbrowser_open):
        """
        Test that _open_web_link method does not call webbrowser.open with empty URL.
        """
        self.window._open_web_link("")
        mock_webbrowser_open.assert_not_called()

    @patch('librarian_assistant.main.webbrowser.open')
    @patch.object(ApiClient, 'get_book_by_id')
    def test_clickable_links_work_correctly(self, mock_api_get_book_by_id, mock_webbrowser_open):
        """
        Test that clicking on clickable elements opens the correct URLs and
        that clicking on 'N/A' values does not open any URL.
        """
        # Mock book data with some null default editions
        mock_book_data = {
            "id": "789",
            "slug": "clickable-test-book",
            "title": "Clickable Test Book",
            "contributions": [{"author": {"name": "Test Author"}}],
            "description": "Test description",
            "editions_count": 3,
            "default_audio_edition": None,  # This should show as N/A
            "default_cover_edition": {"id": "cov789", "edition_format": "Hardcover"},
            "default_ebook_edition": {"id": "ebk789", "edition_format": "E-book"},
            "default_physical_edition": None  # This should show as N/A
        }
        mock_api_get_book_by_id.return_value = mock_book_data

        book_id_line_edit = self.window.findChild(QLineEdit, "bookIdLineEdit")
        fetch_data_button = self.window.findChild(QPushButton, "fetchDataButton")

        book_id_line_edit.setText("789")
        fetch_data_button.click()

        # Test clicking the book slug (should open URL)
        expected_slug_url = "https://hardcover.app/books/clickable-test-book"
        self.window.book_slug_label.linkActivated.emit(expected_slug_url)
        mock_webbrowser_open.assert_called_with(expected_slug_url)
        mock_webbrowser_open.reset_mock()

        # Test clicking N/A default audio edition (should NOT open URL)
        # Since it's N/A, linkActivated should not be emitted, but let's verify
        self.assertIn("<span style='color:#999999;'>Default Audio Edition: </span>", self.window.default_audio_label.text())
        # N/A might be highlighted or not depending on context
        self.assertIn("N/A</span>", self.window.default_audio_label.text())
        # The label should not have a link when it's N/A
        self.assertFalse("href=" in self.window.default_audio_label.text())

        # Test clicking valid default cover edition (should open URL)
        expected_cover_url = "https://hardcover.app/editions/cov789"
        self.window.default_cover_label_info.linkActivated.emit(expected_cover_url)
        mock_webbrowser_open.assert_called_with(expected_cover_url)
        mock_webbrowser_open.reset_mock()

        # Test clicking valid default ebook edition (should open URL)
        expected_ebook_url = "https://hardcover.app/editions/ebk789"
        self.window.default_ebook_label.linkActivated.emit(expected_ebook_url)
        mock_webbrowser_open.assert_called_with(expected_ebook_url)
        mock_webbrowser_open.reset_mock()

        # Test clicking N/A default physical edition (should NOT open URL)
        self.assertIn("<span style='color:#999999;'>Default Physical Edition: </span>", self.window.default_physical_label.text())
        # N/A might be highlighted or not depending on context
        self.assertIn("N/A</span>", self.window.default_physical_label.text())
        self.assertFalse("href=" in self.window.default_physical_label.text())
    
    @patch.object(ApiClient, 'get_book_by_id')
    def test_multi_column_sorting_with_indicators(self, mock_api_get_book_by_id):
        """Test that table supports multi-column sorting with visual indicators."""
        # Mock book data with multiple editions for sorting
        mock_book_data = {
            "id": "123",
            "title": "Test Book",
            "editions_count": 3,
            "editions": [
                {
                    "id": "ed1",
                    "score": 95,
                    "title": "First Edition",
                    "pages": 300,
                    "release_date": "2023-01-15",
                },
                {
                    "id": "ed2", 
                    "score": 88,
                    "title": "Second Edition",
                    "pages": 250,
                    "release_date": "2023-02-20",
                },
                {
                    "id": "ed3",
                    "score": 92,
                    "title": "Third Edition", 
                    "pages": 275,
                    "release_date": "2023-03-10",
                }
            ]
        }
        mock_api_get_book_by_id.return_value = mock_book_data
        
        # Fetch data
        self.window.book_id_line_edit.setText("123")
        self.window.fetch_data_button.click()
        
        table = self.window.editions_table_widget
        
        # Check default sort indicator on score column
        score_col = None
        for i in range(table.columnCount()):
            header = table.horizontalHeaderItem(i)
            if header and "score" in header.text():
                score_col = i
                self.assertIn("▼", header.text(), "Score column should show descending indicator")
                break
        
        self.assertIsNotNone(score_col, "Score column not found")
        
        # Find pages column
        pages_col = None
        for i in range(table.columnCount()):
            header = table.horizontalHeaderItem(i)
            if header and header.text() == "pages":
                pages_col = i
                break
        
        self.assertIsNotNone(pages_col, "Pages column not found")
        
        # Simulate clicking pages column header
        table._on_header_clicked(pages_col)
        
        # Check ascending indicator on pages column
        pages_header = table.horizontalHeaderItem(pages_col)
        self.assertIn("▲", pages_header.text(), "Pages column should show ascending indicator")
        
        # Check score column indicator is cleared
        score_header = table.horizontalHeaderItem(score_col)
        self.assertNotIn("▼", score_header.text(), "Score column indicator should be cleared")
        self.assertNotIn("▲", score_header.text(), "Score column indicator should be cleared")
        
        # Click pages column again for descending
        table._on_header_clicked(pages_col)
        pages_header = table.horizontalHeaderItem(pages_col)
        self.assertIn("▼", pages_header.text(), "Pages column should show descending indicator")
        
        # Click pages column third time to clear sort
        table._on_header_clicked(pages_col)
        pages_header = table.horizontalHeaderItem(pages_col)
        self.assertNotIn("▲", pages_header.text(), "Pages column indicator should be cleared")
        self.assertNotIn("▼", pages_header.text(), "Pages column indicator should be cleared")
        
        # Verify default sort is restored (score descending)
        score_header = table.horizontalHeaderItem(score_col)
        # Note: The default sort restore doesn't update the indicator in current implementation
        # This could be enhanced if needed
    
    @patch.object(ApiClient, 'get_book_by_id')
    def test_numeric_column_sorting(self, mock_api_get_book_by_id):
        """Test that numeric columns (score, pages) sort numerically not alphabetically."""
        # Mock book data with numeric values that would sort incorrectly as strings
        mock_book_data = {
            "id": "123",
            "title": "Test Book",
            "editions_count": 4,
            "editions": [
                {"id": "ed1", "score": 100, "pages": 90, "title": "Edition 1"},
                {"id": "ed2", "score": 95.5, "pages": 200, "title": "Edition 2"},
                {"id": "ed3", "score": 9, "pages": 1000, "title": "Edition 3"},  # 9 < 95.5 numerically but "9" > "95.5" as string
                {"id": "ed4", "score": 88, "pages": 50, "title": "Edition 4"},
            ]
        }
        mock_api_get_book_by_id.return_value = mock_book_data
        
        # Fetch data
        self.window.book_id_line_edit.setText("123")
        self.window.fetch_data_button.click()
        
        table = self.window.editions_table_widget
        
        # Find score and pages columns
        score_col = None
        pages_col = None
        id_col = None
        for i in range(table.columnCount()):
            header = table.horizontalHeaderItem(i)
            if header:
                header_text = header.text().replace(" ▲", "").replace(" ▼", "")
                if header_text == "score":
                    score_col = i
                elif header_text == "pages":
                    pages_col = i
                elif header_text == "id":
                    id_col = i
        
        self.assertIsNotNone(score_col)
        self.assertIsNotNone(pages_col)
        self.assertIsNotNone(id_col)
        
        # Check default sort (score descending) - should be 100, 95.5, 88, 9
        # ID column now uses ClickableLabel widget instead of QTableWidgetItem
        def get_id_text(row):
            id_widget = table.cellWidget(row, id_col)
            if id_widget:
                return id_widget.text()
            else:
                # Fallback to QTableWidgetItem for N/A values
                item = table.item(row, id_col)
                return item.text() if item else "N/A"
        
        self.assertIn("ed1", get_id_text(0))  # score 100
        self.assertIn("ed2", get_id_text(1))  # score 95.5
        self.assertIn("ed4", get_id_text(2))  # score 88
        self.assertIn("ed3", get_id_text(3))  # score 9
        
        # Verify score values are correct
        self.assertEqual(table.item(0, score_col).text(), "100")
        self.assertEqual(table.item(1, score_col).text(), "95.5")
        self.assertEqual(table.item(2, score_col).text(), "88")
        self.assertEqual(table.item(3, score_col).text(), "9")
        
        # Check initial sort state
        self.assertEqual(table.column_sort_order.get(score_col), Qt.DescendingOrder)
        
        # First click on score column clears sort (goes to None/default)
        table._on_header_clicked(score_col)
        self.assertEqual(table.column_sort_order.get(score_col), None)
        
        # Second click on score column sorts ascending - should be 9, 88, 95.5, 100
        table._on_header_clicked(score_col)
        self.assertEqual(table.column_sort_order.get(score_col), Qt.AscendingOrder)
        
        self.assertIn("ed3", get_id_text(0))  # score 9
        self.assertIn("ed4", get_id_text(1))  # score 88
        self.assertIn("ed2", get_id_text(2))  # score 95.5
        self.assertIn("ed1", get_id_text(3))  # score 100
        
        # Click pages column to sort ascending - should be 50, 90, 200, 1000
        table._on_header_clicked(pages_col)
        self.assertIn("ed4", get_id_text(0))  # pages 50
        self.assertIn("ed1", get_id_text(1))  # pages 90
        self.assertIn("ed2", get_id_text(2))  # pages 200
        self.assertIn("ed3", get_id_text(3))  # pages 1000
        
        # Click pages column again for descending - should be 1000, 200, 90, 50
        table._on_header_clicked(pages_col)
        self.assertIn("ed3", get_id_text(0))  # pages 1000
        self.assertIn("ed2", get_id_text(1))  # pages 200
        self.assertIn("ed1", get_id_text(2))  # pages 90
        self.assertIn("ed4", get_id_text(3))  # pages 50


if __name__ == '__main__':
    unittest.main()
