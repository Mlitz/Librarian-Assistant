# In tests/test_main_window.py
import unittest
from unittest.mock import patch # Import patch
from PyQt5.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton, QGroupBox, QTableWidget
from PyQt5.QtCore import Qt # Import Qt for Qt.LeftButton
from PyQt5.QtTest import QTest # For simulating clicks
from librarian_assistant.main import MainWindow, ClickableLabel # Make sure this import path is correct
from librarian_assistant.api_client import ApiClient
from librarian_assistant.image_downloader import ImageDownloader # Import ImageDownloader
from librarian_assistant.exceptions import ApiNotFoundError, ApiAuthError, NetworkError, ApiProcessingError

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
        self.assertEqual(self.window.book_title_label.text(), "Title: The Great Test Book")
        # Parent widget check might be tricky if layout is cleared and widgets re-added.
        # Let's ensure it's a child of the main content widget of the scroll area.

        self.assertIsNotNone(self.window.book_slug_label, "Book slug QLabel attribute not updated.")
        # Check that the slug is displayed with HTML formatting
        self.assertIn("the-great-test-book-slug", self.window.book_slug_label.text())
        self.assertIn("href=", self.window.book_slug_label.text())  # Verify it's a link
        self.assertEqual(self.window.book_slug_label.parentWidget(), self.window.book_info_area, "Slug label not in book info area.")

        self.assertIsNotNone(self.window.book_authors_label, "Book authors QLabel attribute not updated.")
        # Assuming authors are joined by ", " in main.py
        self.assertEqual(self.window.book_authors_label.text(), "Authors: Author One, Author Two")

        self.assertIsNotNone(self.window.book_id_queried_label, "Book ID (queried) QLabel attribute not updated.")
        self.assertEqual(self.window.book_id_queried_label.text(), "Book ID (Queried): 123") # From input

        self.assertIsNotNone(self.window.book_total_editions_label, "Total editions QLabel attribute not updated.")
        self.assertEqual(self.window.book_total_editions_label.text(), "Total Editions: 5")


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
            
        self.assertEqual(self.window.book_description_label.text(), expected_display_text)
        self.assertEqual(self.window.book_description_label.toolTip(), expected_tooltip_text)
        
        self.assertIsNotNone(self.window.book_cover_label, "Book cover QLabel attribute not updated.")
        # This assumes book_cover_label displays the URL as text.
        self.assertEqual(self.window.book_cover_label.text(), "Cover URL: http://example.com/great_test_book_cover.jpg")

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

        # Expected column headers per spec
        expected_headers = [
            "id", "score", "title", "subtitle", "Cover Image?", 
            "isbn_10", "isbn_13", "asin", "Reading Format", "pages", 
            "Duration", "edition_format", "edition_information", 
            "release_date", "Publisher", "Language", "Country"
        ]
        self.assertEqual(editions_table.columnCount(), len(expected_headers))
        for i, header in enumerate(expected_headers):
            self.assertEqual(editions_table.horizontalHeaderItem(i).text(), header)
        
        self.assertEqual(editions_table.rowCount(), 2)

        # Check first row (should be sorted by score desc, so ed1 first)
        self.assertEqual(editions_table.item(0, 0).text(), "ed1")  # id
        self.assertEqual(editions_table.item(0, 1).text(), "95.5")  # score
        # Title should be truncated
        self.assertIn("First Edition with", editions_table.item(0, 2).text())
        self.assertIn("...", editions_table.item(0, 2).text())  # Check truncation
        self.assertEqual(editions_table.item(0, 3).text(), "Premium Hardcover")  # subtitle
        self.assertEqual(editions_table.item(0, 4).text(), "Yes")  # Cover Image?
        self.assertEqual(editions_table.item(0, 5).text(), "1234567890")  # isbn_10
        self.assertEqual(editions_table.item(0, 6).text(), "9781234567890")  # isbn_13
        self.assertEqual(editions_table.item(0, 7).text(), "B001234567")  # asin
        self.assertEqual(editions_table.item(0, 8).text(), "Physical Book")  # Reading Format
        self.assertEqual(editions_table.item(0, 9).text(), "300")  # pages
        self.assertEqual(editions_table.item(0, 10).text(), "N/A")  # Duration
        self.assertEqual(editions_table.item(0, 11).text(), "Hardcover")  # edition_format
        self.assertEqual(editions_table.item(0, 12).text(), "First printing with author signature")  # edition_information
        self.assertEqual(editions_table.item(0, 13).text(), "01/15/2023")  # release_date
        self.assertEqual(editions_table.item(0, 14).text(), "Test Publishers Inc.")  # Publisher
        self.assertEqual(editions_table.item(0, 15).text(), "English")  # Language
        self.assertEqual(editions_table.item(0, 16).text(), "United States")  # Country

        # Check second row
        self.assertEqual(editions_table.item(1, 0).text(), "ed2")  # id
        self.assertEqual(editions_table.item(1, 1).text(), "88.0")  # score
        self.assertEqual(editions_table.item(1, 2).text(), "Second Edition")  # title
        self.assertEqual(editions_table.item(1, 3).text(), "N/A")  # subtitle
        self.assertEqual(editions_table.item(1, 4).text(), "No")  # Cover Image?
        self.assertEqual(editions_table.item(1, 5).text(), "N/A")  # isbn_10
        self.assertEqual(editions_table.item(1, 6).text(), "9780987654321")  # isbn_13
        self.assertEqual(editions_table.item(1, 7).text(), "N/A")  # asin
        self.assertEqual(editions_table.item(1, 8).text(), "Audiobook")  # Reading Format
        self.assertEqual(editions_table.item(1, 9).text(), "N/A")  # pages
        self.assertEqual(editions_table.item(1, 10).text(), "09:00:00")  # Duration (9 hours)
        self.assertEqual(editions_table.item(1, 11).text(), "Audiobook")  # edition_format
        self.assertEqual(editions_table.item(1, 12).text(), "N/A")  # edition_information
        self.assertEqual(editions_table.item(1, 13).text(), "06/30/2024")  # release_date
        self.assertEqual(editions_table.item(1, 14).text(), "Audio House")  # Publisher
        self.assertEqual(editions_table.item(1, 15).text(), "French")  # Language
        self.assertEqual(editions_table.item(1, 16).text(), "Canada")  # Country

        # Check sorting is enabled
        self.assertTrue(editions_table.isSortingEnabled())
        
        # Check tooltip for truncated text
        self.assertEqual(editions_table.item(0, 2).toolTip(), 
                         "First Edition with a very long title that should be truncated")
        
        mock_api_get_book_by_id.assert_called_once_with(123)

    def test_initial_general_book_information_ui_elements_present_and_default(self):
        """
        Test that all UI elements for General Book Information are present after
        MainWindow instantiation and display their default "Not Fetched" or "N/A" text.
        Corresponds to todo.md Prompt 4.1.
        """
        # Find the "General Book Information Area" QGroupBox
        book_info_area = self.window.findChild(QGroupBox, "bookInfoArea")
        self.assertIsNotNone(book_info_area, "General Book Information Area QGroupBox not found.")

        # Check labels directly attached to MainWindow instance
        # Ensure they are ClickableLabels where appropriate
        self.assertIsNotNone(self.window.book_title_label, "Book Title QLabel not found.")
        self.assertEqual(self.window.book_title_label.text(), "Title: Not Fetched")

        self.assertIsNotNone(self.window.book_slug_label, "Book Slug QLabel not found.")
        self.assertIsInstance(self.window.book_slug_label, ClickableLabel)
        self.assertEqual(self.window.book_slug_label.text(), "Slug: Not Fetched")
        self.assertEqual(self.window.book_slug_label.toolTip(), "") # No link initially

        self.assertIsNotNone(self.window.book_authors_label, "Book Authors QLabel not found.")
        self.assertEqual(self.window.book_authors_label.text(), "Authors: Not Fetched")

        self.assertIsNotNone(self.window.book_id_queried_label, "Book ID (Queried) QLabel not found.")
        self.assertEqual(self.window.book_id_queried_label.text(), "Book ID (Queried): Not Fetched")
        # self.assertNotIsInstance(self.window.book_id_queried_label, ClickableLabel) # Should not be clickable

        self.assertIsNotNone(self.window.book_total_editions_label, "Total Editions QLabel not found.")
        self.assertEqual(self.window.book_total_editions_label.text(), "Total Editions: Not Fetched")
        # self.assertNotIsInstance(self.window.book_total_editions_label, ClickableLabel)

        # Check for the new QLabel for description
        self.assertIsNotNone(self.window.book_description_label, "Book Description QLabel not found.")
        self.assertEqual(self.window.book_description_label.text(), "Description: Not Fetched")
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
        self.assertEqual(self.window.default_audio_label.text(), "Default Audio Edition: N/A")
        self.assertIs(self.window.default_audio_label.parentWidget(), default_editions_gb, "Default Audio Label not in correct group box.")
        self.assertEqual(self.window.default_audio_label.toolTip(), "")

        self.assertIsNotNone(self.window.default_cover_label_info, "Default Cover Label Info not found.")
        self.assertIsInstance(self.window.default_cover_label_info, ClickableLabel)
        self.assertEqual(self.window.default_cover_label_info.text(), "Default Cover Edition: N/A")
        self.assertIs(self.window.default_cover_label_info.parentWidget(), default_editions_gb, "Default Cover Label Info not in correct group box.")
        self.assertEqual(self.window.default_cover_label_info.toolTip(), "")

        self.assertIsNotNone(self.window.default_ebook_label, "Default E-book Label not found.")
        self.assertIsInstance(self.window.default_ebook_label, ClickableLabel)
        self.assertEqual(self.window.default_ebook_label.text(), "Default E-book Edition: N/A")
        self.assertIs(self.window.default_ebook_label.parentWidget(), default_editions_gb, "Default E-book Label not in correct group box.")
        self.assertEqual(self.window.default_ebook_label.toolTip(), "")

        self.assertIsNotNone(self.window.default_physical_label, "Default Physical Label not found.")
        self.assertIsInstance(self.window.default_physical_label, ClickableLabel)
        self.assertEqual(self.window.default_physical_label.text(), "Default Physical Edition: N/A")
        self.assertIs(self.window.default_physical_label.parentWidget(), default_editions_gb, "Default Physical Label not in correct group box.")
        self.assertEqual(self.window.default_physical_label.toolTip(), "")

        # Check the main book cover URL label (which is separate from default editions info)
        self.assertIsNotNone(self.window.book_cover_label, "Book Cover URL QLabel not found.")
        self.assertEqual(self.window.book_cover_label.text(), "Cover URL: Not Fetched")

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
        self.assertEqual(self.window.book_title_label.text(), "Title: Book With Missing Info") # Title is present

        self.assertEqual(self.window.book_slug_label.text(), "Slug: N/A")
        self.assertEqual(self.window.book_authors_label.text(), "Authors: N/A")
        self.assertEqual(self.window.book_id_queried_label.text(), "Book ID (Queried): 456") # From input
        self.assertEqual(self.window.book_total_editions_label.text(), "Total Editions: N/A")
        
        # Description label
        self.assertEqual(self.window.book_description_label.text(), "Description: N/A")
        self.assertEqual(self.window.book_description_label.toolTip(), "", "Tooltip should be empty for N/A description")

        # Default Editions
        self.assertEqual(self.window.default_audio_label.text(), "Default Audio Edition: N/A")
        self.assertEqual(self.window.default_cover_label_info.text(), "Default Cover Edition: N/A")
        self.assertEqual(self.window.default_ebook_label.text(), "Default E-book Edition: N/A")
        self.assertEqual(self.window.default_physical_label.text(), "Default Physical Edition: N/A")

        # Main Cover URL Label (derived from default_cover_edition)
        self.assertEqual(self.window.book_cover_label.text(), "Cover URL: N/A")

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
        
        # Check E-Book format
        self.assertEqual(editions_table.item(0, 8).text(), "E-Book")
        self.assertEqual(editions_table.item(0, 10).text(), "N/A")  # No audio duration
        self.assertEqual(editions_table.item(0, 13).text(), "N/A")  # Null date
        
        # Check unknown reading format (should show raw ID)
        self.assertEqual(editions_table.item(1, 8).text(), "99")
        self.assertEqual(editions_table.item(1, 9).text(), "N/A")  # Null pages
        self.assertEqual(editions_table.item(1, 13).text(), "invalid-date")  # Invalid date kept as-is
        
        # Check audiobook duration conversion
        self.assertEqual(editions_table.item(2, 8).text(), "Audiobook")
        self.assertEqual(editions_table.item(2, 10).text(), "12:41:18")  # 45678 seconds
        self.assertEqual(editions_table.item(2, 13).text(), "12/25/2025")  # Formatted date

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
        self.assertEqual(self.window.default_audio_label.text(), "Default Audio Edition: N/A")
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
        self.assertEqual(self.window.default_physical_label.text(), "Default Physical Edition: N/A")
        self.assertFalse("href=" in self.window.default_physical_label.text())


if __name__ == '__main__':
    unittest.main()
