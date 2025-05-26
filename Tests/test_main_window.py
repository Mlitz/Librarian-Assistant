# In tests/test_main_window.py
import unittest
from unittest.mock import patch, MagicMock # Import patch and MagicMock
from PyQt5.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton, QGroupBox, QTextEdit, QTableWidget
from PyQt5.QtGui import QPixmap # QPixmap is in PyQt5.QtGui
from librarian_assistant.main import MainWindow # Make sure this import path is correct
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
            "title": "The Great Test Book",
            # Authors come from the 'contributions' array
            "contributions": [
                {"author": {"name": "Author One"}},
                {"author": {"name": "Author Two"}}
            ],
            "description": "A truly captivating description of testing.",
            # The cover URL for general display would likely come from default_cover_edition
            "default_cover_edition": {
                "image": {"url": "http://example.com/great_test_book_cover.jpg"}
            }
            # Add other fields from books[0] like slug, editions_count if they are
            # displayed in this specific part of the UI and tested here.
        }
        mock_api_get_book_by_id.return_value = mock_book_data

        book_id_line_edit = self.window.findChild(QLineEdit, "bookIdLineEdit")
        fetch_data_button = self.window.findChild(QPushButton, "fetchDataButton")

        book_id_line_edit.setText("123")
        fetch_data_button.click()

        # Check the instance attributes which should point to the new, populated widgets
        # Ensure these objectNames match what's set in your MainWindow's UI setup.
        self.assertIsNotNone(self.window.book_title_label, "Book title QLabel attribute not updated.")
        self.assertEqual(self.window.book_title_label.text(), "Title: The Great Test Book")
        self.assertEqual(self.window.book_title_label.parentWidget(), self.window.book_info_area, "Title label not in book info area.")

        self.assertIsNotNone(self.window.book_authors_label, "Book authors QLabel attribute not updated.")
        # Assuming authors are joined by ", " in main.py
        self.assertEqual(self.window.book_authors_label.text(), "Authors: Author One, Author Two")
        self.assertEqual(self.window.book_authors_label.parentWidget(), self.window.book_info_area, "Authors label not in book info area.")

        # Test for the new QLabel based description display
        self.assertIsNotNone(self.window.book_description_label, "Book description QLabel attribute not updated.")
        
        full_mock_description = "A truly captivating description of testing."
        MAX_DESC_CHARS = 150 # Must match the constant in main.py
        
        if len(full_mock_description) > MAX_DESC_CHARS:
            expected_display_text = f"Description: {full_mock_description[:MAX_DESC_CHARS]}..."
            expected_tooltip_text = full_mock_description
        else:
            expected_display_text = f"Description: {full_mock_description}"
            expected_tooltip_text = "" # Or full_mock_description if tooltip is always set
            
        self.assertEqual(self.window.book_description_label.text(), expected_display_text)
        self.assertEqual(self.window.book_description_label.toolTip(), expected_tooltip_text)
        self.assertEqual(self.window.book_description_label.parentWidget(), self.window.book_info_area, "Description label not in book info area.")
        
        self.assertIsNotNone(self.window.book_cover_label, "Book cover QLabel attribute not updated.")
        # This assumes book_cover_label displays the URL as text.
        self.assertEqual(self.window.book_cover_label.text(), "Cover URL: http://example.com/great_test_book_cover.jpg")
        self.assertEqual(self.window.book_cover_label.parentWidget(), self.window.book_info_area, "Cover label not in book info area.")
        
    @patch.object(ApiClient, 'get_book_by_id')
    def test_fetch_data_success_populates_editions_table(self, mock_api_get_book_by_id):
        """
        Test that a successful API call populates the Editions Table Area
        with the fetched editions data.
        """
        # Sample book data with editions
        mock_book_data = {
            "id": "123",
            "title": "The Great Test Book",
            "authors": [{"name": "Author One"}],
            "description": "A description.",
            "cover": {"url": "http://example.com/cover.jpg"},
            "editions": [
                {
                    "id": "ed1",
                    "title": "First Edition",
                    "pageCount": 300,
                    "publishedDate": "2023-01-01",
                    "isbn10": "1234567890",
                    "isbn13": "9781234567890",
                    "language": {"name": "English"},
                    "cover": {"url": "http://example.com/ed1_cover.jpg"}
                },
                {
                    "id": "ed2",
                    "title": "Second Edition",
                    "pageCount": 320,
                    "publishedDate": "2024-01-01",
                    "isbn10": "0987654321",
                    "isbn13": "9780987654321",
                    "language": {"name": "French"},
                    "cover": {"url": "http://example.com/ed2_cover.jpg"}
                }
            ]
        }
        mock_api_get_book_by_id.return_value = mock_book_data

        book_id_line_edit = self.window.findChild(QLineEdit, "bookIdLineEdit")
        fetch_data_button = self.window.findChild(QPushButton, "fetchDataButton")

        book_id_line_edit.setText("123")
        fetch_data_button.click()

        # Find the QTableWidget within the editions_table_area
        # This objectName will need to be set in main.py
        editions_table = self.window.editions_table_area.findChild(QTableWidget, "editionsTableWidget")
        self.assertIsNotNone(editions_table, "Editions QTableWidget not found.")

        # Expected column headers (order matters for indexing)
        expected_headers = ["Title", "Pages", "Published", "ISBN10", "ISBN13", "Language", "Cover URL"]
        self.assertEqual(editions_table.columnCount(), len(expected_headers))
        for i, header in enumerate(expected_headers):
            self.assertEqual(editions_table.horizontalHeaderItem(i).text(), header)
        
        self.assertEqual(editions_table.rowCount(), 2) # Two editions in mock_book_data

        # Check content of the first row
        self.assertEqual(editions_table.item(0, 0).text(), "First Edition")
        self.assertEqual(editions_table.item(0, 1).text(), "300")
        self.assertEqual(editions_table.item(0, 2).text(), "2023-01-01")
        self.assertEqual(editions_table.item(0, 3).text(), "1234567890")
        self.assertEqual(editions_table.item(0, 4).text(), "9781234567890")
        self.assertEqual(editions_table.item(0, 5).text(), "English")
        self.assertEqual(editions_table.item(0, 6).text(), "http://example.com/ed1_cover.jpg")
        
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
        self.assertIsNotNone(self.window.book_title_label, "Book Title QLabel not found.")
        self.assertEqual(self.window.book_title_label.text(), "Title: Not Fetched")

        self.assertIsNotNone(self.window.book_slug_label, "Book Slug QLabel not found.")
        self.assertEqual(self.window.book_slug_label.text(), "Slug: Not Fetched")

        self.assertIsNotNone(self.window.book_authors_label, "Book Authors QLabel not found.")
        self.assertEqual(self.window.book_authors_label.text(), "Authors: Not Fetched")

        self.assertIsNotNone(self.window.book_id_queried_label, "Book ID (Queried) QLabel not found.")
        self.assertEqual(self.window.book_id_queried_label.text(), "Book ID (Queried): Not Fetched")

        self.assertIsNotNone(self.window.book_total_editions_label, "Total Editions QLabel not found.")
        self.assertEqual(self.window.book_total_editions_label.text(), "Total Editions: Not Fetched")

        # Check for the new QLabel for description
        self.assertIsNotNone(self.window.book_description_label, "Book Description QLabel not found.")
        self.assertEqual(self.window.book_description_label.text(), "Description: Not Fetched")
        self.assertEqual(self.window.book_description_label.toolTip(), "", "Initial tooltip for description should be empty.")

        # Check for Default Editions GroupBox
        default_editions_gb = self.window.findChild(QGroupBox, "defaultEditionsGroupBox")
        self.assertIsNotNone(default_editions_gb, "Default Editions QGroupBox not found.")
        self.assertEqual(default_editions_gb.title(), "Default Editions")
        self.assertIs(default_editions_gb.parentWidget(), book_info_area, "Default Editions GroupBox should be in Book Info Area.")

        # Check labels within Default Editions GroupBox
        self.assertIsNotNone(self.window.default_audio_label, "Default Audio Label not found.")
        self.assertEqual(self.window.default_audio_label.text(), "Default Audio Edition: N/A")
        self.assertIs(self.window.default_audio_label.parentWidget(), default_editions_gb, "Default Audio Label not in correct group box.")

        self.assertIsNotNone(self.window.default_cover_label_info, "Default Cover Label Info not found.")
        self.assertEqual(self.window.default_cover_label_info.text(), "Default Cover Edition: N/A")
        self.assertIs(self.window.default_cover_label_info.parentWidget(), default_editions_gb, "Default Cover Label Info not in correct group box.")

        self.assertIsNotNone(self.window.default_ebook_label, "Default E-book Label not found.")
        self.assertEqual(self.window.default_ebook_label.text(), "Default E-book Edition: N/A")
        self.assertIs(self.window.default_ebook_label.parentWidget(), default_editions_gb, "Default E-book Label not in correct group box.")

        self.assertIsNotNone(self.window.default_physical_label, "Default Physical Label not found.")
        self.assertEqual(self.window.default_physical_label.text(), "Default Physical Edition: N/A")
        self.assertIs(self.window.default_physical_label.parentWidget(), default_editions_gb, "Default Physical Label not in correct group box.")

        # Check the main book cover URL label (which is separate from default editions info)
        self.assertIsNotNone(self.window.book_cover_label, "Book Cover URL QLabel not found.")
        self.assertEqual(self.window.book_cover_label.text(), "Cover URL: Not Fetched")

if __name__ == '__main__':
    unittest.main()
