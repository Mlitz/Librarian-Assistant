# ABOUTME: This file is the main entry point for the Librarian-Assistant application.
# ABOUTME: It defines the main window and initializes the application.
import sys
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QLineEdit, QTableWidget, QTableWidgetItem, QScrollArea,
                             QVBoxLayout, QLabel, QGroupBox, QPushButton)
from PyQt5.QtGui import QIntValidator, QValidator
from PyQt5.QtCore import Qt

# Import ConfigManager for Prompt 2.2
from librarian_assistant.config_manager import ConfigManager
# Import TokenDialog for Prompt 2.2
from librarian_assistant.token_dialog import TokenDialog
# Import ApiClient for Prompt 3.3
from librarian_assistant.api_client import ApiClient
# Import custom exceptions for Prompt 3.3
from librarian_assistant.exceptions import ApiException, ApiNotFoundError
# Import ImageDownloader for Prompt 4.1
from librarian_assistant.image_downloader import ImageDownloader

import webbrowser # For Prompt 4.3
import logging
logger = logging.getLogger(__name__)

# Constants
HARDCOVER_API_BASE_URL = "https://api.hardcover.app/v1/graphql"
MAX_DESC_CHARS = 500 # Define max characters for display

class ClickableLabel(QLabel):
    """
    A QLabel subclass that can be made clickable and emits a signal with a URL.
    """
    # No custom signal needed; QLabel.linkActivated will be used.

    def __init__(self, parent=None): # Text will be set via setContent
        super().__init__(parent)
        self._url_for_link_part = "" # Store the URL associated with the link part
        self.setTextFormat(Qt.RichText)
        self.setOpenExternalLinks(False) # Important: emit linkActivated instead of QLabel opening it
        self.setCursor(Qt.ArrowCursor) # Default cursor
        # Default style for the non-link part (taken from main stylesheet)
        self._default_text_color = "#cccccc" # Matches QWidget color in stylesheet
        self._link_text_color = "#6cb6ff"    # A common link blue

    def setContent(self, prefix: str, value_part: str, url_for_value_part: str = ""):
        """
        Sets the content of the label.
        - prefix: The static text part (e.g., "Slug: ").
        - value_part: The dynamic text part that might be a link (e.g., "my-book-slug" or "N/A").
        - url_for_value_part: The URL to associate with the value_part if it's linkable.
        """
        self._url_for_link_part = url_for_value_part
        current_value_part = value_part if value_part is not None else "N/A"

        is_value_linkable = bool(self._url_for_link_part) and current_value_part != "N/A"

        if is_value_linkable:
            # Construct HTML with styled prefix and link
            # Ensure HTML special characters in prefix and value_part are escaped if necessary,
            # but for simple text like "Slug: " and typical slugs/IDs, it's often fine.
            # For robustness, one might use Qt.escape().
            html_text = (
                f"<span style='color:{self._default_text_color};'>{prefix}</span>"
                f"<a href='{self._url_for_link_part}' style='color:{self._link_text_color}; text-decoration:underline;'>{current_value_part}</a>"
            )
            self.setText(html_text)
            self.setCursor(Qt.PointingHandCursor)
            self.setToolTip(f"Open: {self._url_for_link_part}")
        else:
            plain_text = f"{prefix}{current_value_part}"
            self.setText(plain_text) # This will display with default QLabel styling (inherited)
            self.setCursor(Qt.ArrowCursor)
            self.setToolTip("")
            self.setStyleSheet(f"color: {self._default_text_color}; text-decoration: none;") # Ensure non-link style
class MainWindow(QMainWindow):
    """
    Main application window for Librarian-Assistant.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Librarian-Assistant - Hardcover.app Edition Viewer")
        self.resize(800, 600)
        
        # Constants for table display
        self.MAX_CELL_TEXT_LENGTH = 50  # Maximum characters before truncation

        self.config_manager = ConfigManager()
        self.api_client = ApiClient(
            base_url=HARDCOVER_API_BASE_URL,
            token_manager=self.config_manager
        )
        self.image_downloader = ImageDownloader()

        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # This widget will contain all the content for the "Main View" tab and will be placed inside the scroll area.
        self.main_view_content_widget = QWidget()
        # The layout is applied to this content widget.
        main_view_layout = QVBoxLayout(self.main_view_content_widget)

        self.api_input_area = QGroupBox("API & Book ID Input Area")
        self.api_input_area.setObjectName("apiInputArea")
        api_layout = QVBoxLayout(self.api_input_area)
        self.token_display_label = QLabel("Token: Not Set")
        self.token_display_label.setObjectName("tokenDisplayLabel")
        api_layout.addWidget(self.token_display_label)

        self.set_token_button = QPushButton("Set/Update Token")
        self.set_token_button.setObjectName("setTokenButton")
        self.set_token_button.clicked.connect(self._open_set_token_dialog)
        api_layout.addWidget(self.set_token_button)

        # Add Book ID input elements as per Prompt 3.1
        self.book_id_label = QLabel("Book ID:")
        self.book_id_label.setObjectName("bookIdLabel")
        api_layout.addWidget(self.book_id_label)

        self.book_id_line_edit = QLineEdit()
        self.book_id_line_edit.setObjectName("bookIdLineEdit")
        # Placeholder text can be useful for users
        # Add QIntValidator to allow only numbers
        self.book_id_line_edit.setValidator(QIntValidator())
        self.book_id_line_edit.textChanged.connect(self._on_book_id_text_changed)
        self.book_id_line_edit.setPlaceholderText("Enter numerical Book ID")
        api_layout.addWidget(self.book_id_line_edit)

        self.fetch_data_button = QPushButton("Fetch Data")
        self.fetch_data_button.setObjectName("fetchDataButton")
        self.fetch_data_button.clicked.connect(self._on_fetch_data_clicked) # Connect signal
        api_layout.addWidget(self.fetch_data_button)

        main_view_layout.addWidget(self.api_input_area)

        self.book_info_area = QGroupBox("General Book Information Area")
        self.book_info_area.setObjectName("bookInfoArea")
        self.info_layout = QVBoxLayout(self.book_info_area) # Store layout for easy access

        # Add specific widgets for book information - these will be populated later
        self.book_title_label = QLabel("Title: Not Fetched")
        self.book_title_label.setObjectName("bookTitleLabel")
        self.info_layout.addWidget(self.book_title_label)

        self.book_slug_label = ClickableLabel(self) # Pass parent
        self.book_slug_label.setObjectName("bookSlugLabel")
        self.book_slug_label.setContent("Slug: ", "Not Fetched", "")
        self.info_layout.addWidget(self.book_slug_label)
        self.book_slug_label.linkActivated.connect(self._open_web_link)

        self.book_authors_label = QLabel("Authors: Not Fetched")
        self.book_authors_label.setObjectName("bookAuthorsLabel")
        self.info_layout.addWidget(self.book_authors_label)

        self.book_id_queried_label = QLabel("Book ID (Queried): Not Fetched")
        self.book_id_queried_label.setObjectName("bookIdQueriedLabel")
        self.info_layout.addWidget(self.book_id_queried_label)

        self.book_total_editions_label = QLabel("Total Editions: Not Fetched")
        self.book_total_editions_label.setObjectName("bookTotalEditionsLabel")
        self.info_layout.addWidget(self.book_total_editions_label)

        self.book_description_label = QLabel("Description: Not Fetched")
        self.book_description_label.setObjectName("bookDescriptionLabel")
        self.book_description_label.setWordWrap(True) # Allow text to wrap
        # Tooltip will be set dynamically if text is truncated
        self.info_layout.addWidget(self.book_description_label)

        # Default Editions GroupBox and Labels (as per Prompt 4.1)
        self.default_editions_group_box = QGroupBox("Default Editions")
        self.default_editions_group_box.setObjectName("defaultEditionsGroupBox")
        default_editions_layout_init = QVBoxLayout(self.default_editions_group_box) # Layout for init

        self.default_audio_label = ClickableLabel(self)
        self.default_audio_label.setObjectName("defaultAudioLabel")
        self.default_audio_label.setContent("Default Audio Edition: ", "N/A", "")
        default_editions_layout_init.addWidget(self.default_audio_label)
        self.default_audio_label.linkActivated.connect(self._open_web_link)

        self.default_cover_label_info = ClickableLabel(self)
        self.default_cover_label_info.setObjectName("defaultCoverLabelInfo")
        self.default_cover_label_info.setContent("Default Cover Edition: ", "N/A", "")
        default_editions_layout_init.addWidget(self.default_cover_label_info)
        self.default_cover_label_info.linkActivated.connect(self._open_web_link)

        self.default_ebook_label = ClickableLabel(self)
        self.default_ebook_label.setObjectName("defaultEbookLabel")
        self.default_ebook_label.setContent("Default E-book Edition: ", "N/A", "")
        default_editions_layout_init.addWidget(self.default_ebook_label)
        self.default_ebook_label.linkActivated.connect(self._open_web_link)

        self.default_physical_label = ClickableLabel(self)
        self.default_physical_label.setObjectName("defaultPhysicalLabel")
        self.default_physical_label.setContent("Default Physical Edition: ", "N/A", "")
        default_editions_layout_init.addWidget(self.default_physical_label)
        self.default_physical_label.linkActivated.connect(self._open_web_link)
        self.info_layout.addWidget(self.default_editions_group_box)

        self.book_cover_label = QLabel("Cover URL: Not Fetched")
        self.book_cover_label.setObjectName("bookCoverLabel")
        self.info_layout.addWidget(self.book_cover_label)

        main_view_layout.addWidget(self.book_info_area)

        self.editions_table_area = QGroupBox("Editions Table Area")
        self.editions_table_area.setObjectName("editionsTableArea")
        self.editions_layout = QVBoxLayout(self.editions_table_area) # Store layout
        
        self.editions_table_widget = QTableWidget()
        self.editions_table_widget.setObjectName("editionsTableWidget")
        self.editions_layout.addWidget(self.editions_table_widget)
        main_view_layout.addWidget(self.editions_table_area)

        main_view_layout.setStretchFactor(self.api_input_area, 0)
        main_view_layout.setStretchFactor(self.book_info_area, 1)
        main_view_layout.setStretchFactor(self.editions_table_area, 3)

        # Create a QScrollArea to make the main view content scrollable
        self.main_view_scroll_area = QScrollArea()
        self.main_view_scroll_area.setWidgetResizable(True) # Important for the inner widget to resize correctly
        self.main_view_scroll_area.setWidget(self.main_view_content_widget) # Put the content widget inside the scroll area

        self.tab_widget.addTab(self.main_view_scroll_area, "Main View") # Add the scroll area to the tab

        self.history_tab_content = QWidget()
        history_layout = QVBoxLayout(self.history_tab_content)
        history_label = QLabel("History")
        history_layout.addWidget(history_label)
        self.tab_widget.addTab(self.history_tab_content, "History")

        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

        self._update_token_display()


    def _open_set_token_dialog(self):
        """
        Opens the dialog for setting or updating the API token.
        If the dialog is accepted, the token is processed.
        """
        dialog = TokenDialog(self)
        # Connect the dialog's signal to the handler method
        dialog.token_accepted.connect(self._handle_token_accepted)
        dialog.exec_() # Show the dialog modally

    def _handle_token_accepted(self, token: str):
        """
        Handles the token received from TokenDialog.
        Saves the token and updates the display.
        """
        self.config_manager.save_token(token)
        self._update_token_display()

    def _update_token_display(self):
        """
        Updates the token display label based on the token in ConfigManager.
        """
        current_token = self.config_manager.load_token()
        if current_token: # Checks if token is not None and not an empty string
            self.token_display_label.setText("Token: *******")
        else:
            self.token_display_label.setText("Token: Not Set")

    def _on_book_id_text_changed(self, text: str):
        """
        If the text in book_id_line_edit changes to something
        that QIntValidator deems Invalid, clear the line edit.
        This ensures programmatic setText("abc") results in an empty field,
        aligning with test expectations. QIntValidator itself handles direct 
        user input prevention by not allowing invalid characters to be typed.
        """
        validator = self.book_id_line_edit.validator()
        if validator is not None:
            # 'text' is the new content of the QLineEdit after the change.
            state, _, _ = validator.validate(text, 0) 
            if state == QValidator.Invalid:
                self.book_id_line_edit.blockSignals(True) # Prevent recursion
                self.book_id_line_edit.setText("")
                self.book_id_line_edit.blockSignals(False)

    def _on_fetch_data_clicked(self):
        """
        Handles the "Fetch Data" button click.
        Logs the current Book ID and token status.
        """
        book_id_str = self.book_id_line_edit.text()
        if not book_id_str:
            self.status_bar.showMessage("Book ID cannot be empty. Please enter a valid numerical Book ID.")
            logger.warning("Fetch Data clicked with empty Book ID.")
            return

        # The QIntValidator ensures book_id_str is numerical if not empty.
        # We still need to convert it to an int for the ApiClient.
        try:
            book_id_int = int(book_id_str)
        except ValueError:
            # This case should ideally not be reached if QIntValidator and _on_book_id_text_changed work perfectly,
            # but as a safeguard:
            self.status_bar.showMessage("Invalid Book ID format. Please enter a numerical Book ID.")
            logger.error(f"Fetch Data clicked with non-integer Book ID that bypassed validation: {book_id_str}")
            return

        # For now, we'll just clear. The population step will add new widgets.
        # If we want placeholders when no data is present, that logic would go elsewhere or be part of error handling.

        logger.info(f"Attempting to fetch data for Book ID: {book_id_int}")
        # Call the ApiClient (actual API call will happen here)
        try:
            book_data = self.api_client.get_book_by_id(book_id_int)

            if book_data:
                # Clear previous data from info_layout before fetching new data
                # This ensures old data is removed even if the new fetch fails or returns no data.
                # We will re-add widgets as needed.
                self._clear_layout(self.info_layout) # Clear general info area
                # Don't clear editions_layout - just clear the table data
                self.editions_table_widget.setRowCount(0)  # Clear existing rows
                self.editions_table_widget.setColumnCount(0)  # Clear existing columns
                self.status_bar.showMessage(f"Book data fetched successfully for ID {book_id_str}.")
                logger.info(f"Successfully fetched data for Book ID {book_id_int}: {book_data.get('title', 'N/A')}")
                logger.info(f"Complete book_data received by main.py for Book ID {book_id_int}: {book_data}")

                # Re-create and populate the General Book Information Area widgets
                # Title
                self.book_title_label = QLabel(f"Title: {book_data.get('title', 'N/A')}")
                self.book_title_label.setObjectName("bookTitleLabel")
                self.info_layout.addWidget(self.book_title_label)

                # Populate Slug
                slug_text = book_data.get('slug')
                slug_url_val = f"https://hardcover.app/books/{slug_text}" if slug_text else ""
                self.book_slug_label = ClickableLabel(self) # Re-create after clear
                self.book_slug_label.setObjectName("bookSlugLabel")
                self.book_slug_label.setContent("Slug: ", slug_text if slug_text else "N/A", slug_url_val)
                self.book_slug_label.linkActivated.connect(self._open_web_link)
                self.info_layout.addWidget(self.book_slug_label)

                # Book ID
                self.book_id_queried_label = QLabel(f"Book ID (Queried): {book_id_int}")
                self.book_id_queried_label.setObjectName("bookIdQueriedLabel")
                self.info_layout.addWidget(self.book_id_queried_label)

                # Authors
                authors_list = []
                # Get the contributions data once to log it and use it
                book_contributions_data = book_data.get('contributions')
                logger.info(f"Book ID {book_id_int} - Raw contributions data from API: {book_contributions_data}")

                if isinstance(book_contributions_data, list):
                    for contribution in book_contributions_data:
                        if isinstance(contribution, dict) and 'author' in contribution and \
                            isinstance(contribution['author'], dict) and 'name' in contribution['author']:
                                authors_list.append(contribution['author']['name'])

                authors_display_text = "N/A"
                if authors_list:
                    authors_display_text = ", ".join(authors_list)

                self.book_authors_label = QLabel(f"Authors: {authors_display_text}") # Changed "Author:" to "Authors:"
                self.book_authors_label.setObjectName("bookAuthorsLabel") # Keep object name for consistency/testing
                self.info_layout.addWidget(self.book_authors_label)
                
                # Total Editions Count
                editions_count_raw = book_data.get('editions_count')
                editions_count_val = editions_count_raw if editions_count_raw is not None else 'N/A'
                self.book_total_editions_label = QLabel(f"Total Editions: {editions_count_val}")
                self.book_total_editions_label.setObjectName("bookTotalEditionsLabel")
                self.info_layout.addWidget(self.book_total_editions_label)

                # Description with truncation and tooltip
                # Ensure full_description is a string, defaulting to "N/A" if None or missing.
                full_description_raw = book_data.get('description')
                full_description = full_description_raw if full_description_raw is not None else "N/A"
                MAX_DESC_CHARS = 500 # Define max characters for display
                
                if full_description != "N/A" and len(full_description) > MAX_DESC_CHARS:
                    display_desc_text = full_description[:MAX_DESC_CHARS] + "..."
                    tooltip_desc_text = full_description
                else:
                    display_desc_text = full_description
                    tooltip_desc_text = "" # No tooltip needed if not truncated, or set full_description
                
                self.book_description_label = QLabel(f"Description: {display_desc_text}")
                self.book_description_label.setObjectName("bookDescriptionLabel")
                self.book_description_label.setWordWrap(True)
                if tooltip_desc_text: # Only set tooltip if it was truncated
                    self.book_description_label.setToolTip(tooltip_desc_text)
                self.info_layout.addWidget(self.book_description_label)

                # Default Editions GroupBox and Labels (re-create or update)
                self.default_editions_group_box = QGroupBox("Default Editions")
                self.default_editions_group_box.setObjectName("defaultEditionsGroupBox")
                default_editions_layout_dyn = QVBoxLayout(self.default_editions_group_box)

                # Helper to format default edition info
                def get_default_edition_parts(edition_data, edition_name_prefix_str):
                    prefix = f"{edition_name_prefix_str}: "
                    if isinstance(edition_data, dict):
                        fmt = edition_data.get('edition_format')
                        ed_id = edition_data.get('id')
                        value_part_text = f"{fmt if fmt else 'N/A'} (ID: {ed_id if ed_id else 'N/A'})"
                        url = f"https://hardcover.app/editions/{ed_id}" if ed_id else ""
                        return prefix, value_part_text, url
                    return prefix, "N/A", ""

                audio_prefix, audio_value_part, audio_url = get_default_edition_parts(book_data.get('default_audio_edition'), "Default Audio Edition")
                self.default_audio_label = ClickableLabel(self)
                self.default_audio_label.setObjectName("defaultAudioLabel")
                self.default_audio_label.setContent(audio_prefix, audio_value_part, audio_url)
                self.default_audio_label.linkActivated.connect(self._open_web_link)
                default_editions_layout_dyn.addWidget(self.default_audio_label)

                cover_prefix, cover_value_part, cover_url_link = get_default_edition_parts(book_data.get('default_cover_edition'), "Default Cover Edition")
                self.default_cover_label_info = ClickableLabel(self)
                self.default_cover_label_info.setObjectName("defaultCoverLabelInfo")
                self.default_cover_label_info.setContent(cover_prefix, cover_value_part, cover_url_link)
                self.default_cover_label_info.linkActivated.connect(self._open_web_link)
                default_editions_layout_dyn.addWidget(self.default_cover_label_info)

                ebook_prefix, ebook_value_part, ebook_url = get_default_edition_parts(book_data.get('default_ebook_edition'), "Default E-book Edition")
                self.default_ebook_label = ClickableLabel(self)
                self.default_ebook_label.setObjectName("defaultEbookLabel")
                self.default_ebook_label.setContent(ebook_prefix, ebook_value_part, ebook_url)
                self.default_ebook_label.linkActivated.connect(self._open_web_link)
                default_editions_layout_dyn.addWidget(self.default_ebook_label)

                physical_prefix, physical_value_part, physical_url = get_default_edition_parts(book_data.get('default_physical_edition'), "Default Physical Edition")
                self.default_physical_label = ClickableLabel(self)
                self.default_physical_label.setObjectName("defaultPhysicalLabel")
                self.default_physical_label.setContent(physical_prefix, physical_value_part, physical_url)
                self.default_physical_label.linkActivated.connect(self._open_web_link)
                default_editions_layout_dyn.addWidget(self.default_physical_label)

                self.info_layout.addWidget(self.default_editions_group_box)

                # Cover URL (this is for the main image display, not clickable itself,
                # the clickable part is default_cover_label_info)
                cover_url = "N/A"
                if isinstance(book_data.get('default_cover_edition'), dict) and \
                    isinstance(book_data['default_cover_edition'].get('image'), dict) and \
                    book_data['default_cover_edition']['image'].get('url'):
                        cover_url = book_data['default_cover_edition']['image']['url']

                self.book_cover_label = QLabel(f"Cover URL: {cover_url}")
                self.book_cover_label.setObjectName("bookCoverLabel") # Keep object name
                self.info_layout.addWidget(self.book_cover_label)

                if cover_url != "N/A" and hasattr(self, 'image_downloader') and hasattr(self, 'actual_cover_display_label'):
                    pixmap = self.image_downloader.download_image(cover_url)
                    if pixmap and not pixmap.isNull():
                        self.actual_cover_display_label.setPixmap(pixmap.scaled( # Optional scaling
                            self.actual_cover_display_label.size(), 
                            Qt.KeepAspectRatio, 
                            Qt.SmoothTransformation
                        ))
                    else:
                        self.actual_cover_display_label.setText("Cover not available") # Or clear it
                else:
                    if hasattr(self, 'actual_cover_display_label'):
                        self.actual_cover_display_label.setText("Cover URL not found") # Or clear it

                # Populate the Editions Table
                editions = book_data.get('editions', [])
                if editions:
                    # Define headers according to spec.md section 2.4.1 (static columns only for now)
                    headers = [
                        "id", "score", "title", "subtitle", "Cover Image?", 
                        "isbn_10", "isbn_13", "asin", "Reading Format", "pages", 
                        "Duration", "edition_format", "edition_information", 
                        "release_date", "Publisher", "Language", "Country"
                    ]
                    self.editions_table_widget.setColumnCount(len(headers))
                    self.editions_table_widget.setHorizontalHeaderLabels(headers)
                    self.editions_table_widget.setRowCount(len(editions))

                    for row, edition_data in enumerate(editions):
                        col = 0
                        
                        # id
                        self.editions_table_widget.setItem(row, col, QTableWidgetItem(str(edition_data.get('id', 'N/A'))))
                        col += 1
                        
                        # score
                        score_value = edition_data.get('score')
                        score_item = QTableWidgetItem(str(score_value) if score_value is not None else 'N/A')
                        # Store numeric value for sorting
                        if score_value is not None:
                            score_item.setData(Qt.UserRole, score_value)
                        self.editions_table_widget.setItem(row, col, score_item)
                        col += 1
                        
                        # title (may be long, use truncation)
                        title_item = self._create_table_item_with_tooltip(edition_data.get('title', 'N/A'))
                        self.editions_table_widget.setItem(row, col, title_item)
                        col += 1
                        
                        # subtitle (may be long, use truncation)
                        subtitle = edition_data.get('subtitle')
                        subtitle_item = self._create_table_item_with_tooltip(subtitle if subtitle else 'N/A')
                        self.editions_table_widget.setItem(row, col, subtitle_item)
                        col += 1
                        
                        # Cover Image?
                        image_data = edition_data.get('image')
                        has_cover = bool(image_data and image_data.get('url'))
                        self.editions_table_widget.setItem(row, col, QTableWidgetItem("Yes" if has_cover else "No"))
                        col += 1
                        
                        # isbn_10
                        isbn_10 = edition_data.get('isbn_10')
                        self.editions_table_widget.setItem(row, col, QTableWidgetItem(isbn_10 if isbn_10 else 'N/A'))
                        col += 1
                        
                        # isbn_13
                        isbn_13 = edition_data.get('isbn_13')
                        self.editions_table_widget.setItem(row, col, QTableWidgetItem(isbn_13 if isbn_13 else 'N/A'))
                        col += 1
                        
                        # asin
                        asin = edition_data.get('asin')
                        self.editions_table_widget.setItem(row, col, QTableWidgetItem(asin if asin else 'N/A'))
                        col += 1
                        
                        # Reading Format (transform reading_format_id)
                        reading_format_id = edition_data.get('reading_format_id')
                        reading_format_map = {1: "Physical Book", 2: "Audiobook", 4: "E-Book"}
                        reading_format = reading_format_map.get(reading_format_id, f"N/A" if reading_format_id is None else str(reading_format_id))
                        self.editions_table_widget.setItem(row, col, QTableWidgetItem(reading_format))
                        col += 1
                        
                        # pages
                        pages_value = edition_data.get('pages')
                        self.editions_table_widget.setItem(row, col, QTableWidgetItem(str(pages_value) if pages_value is not None else 'N/A'))
                        col += 1
                        
                        # Duration (audio_seconds converted to HH:MM:SS)
                        audio_seconds = edition_data.get('audio_seconds')
                        if audio_seconds is not None and audio_seconds > 0:
                            hours = audio_seconds // 3600
                            minutes = (audio_seconds % 3600) // 60
                            seconds = audio_seconds % 60
                            duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                        else:
                            duration_str = "N/A"
                        self.editions_table_widget.setItem(row, col, QTableWidgetItem(duration_str))
                        col += 1
                        
                        # edition_format
                        edition_format = edition_data.get('edition_format')
                        self.editions_table_widget.setItem(row, col, QTableWidgetItem(edition_format if edition_format else 'N/A'))
                        col += 1
                        
                        # edition_information (may be long, use truncation)
                        edition_info_item = self._create_table_item_with_tooltip(edition_data.get('edition_information', 'N/A'))
                        self.editions_table_widget.setItem(row, col, edition_info_item)
                        col += 1
                        
                        # release_date (format as MM/DD/YYYY)
                        release_date = edition_data.get('release_date')
                        if release_date:
                            try:
                                # Assuming format is YYYY-MM-DD from API
                                date_obj = datetime.strptime(release_date, '%Y-%m-%d')
                                formatted_date = date_obj.strftime('%m/%d/%Y')
                            except:
                                formatted_date = release_date  # Use as-is if parsing fails
                        else:
                            formatted_date = "N/A"
                        self.editions_table_widget.setItem(row, col, QTableWidgetItem(formatted_date))
                        col += 1
                        
                        # Publisher
                        publisher_name = edition_data.get('publisher', {}).get('name', 'N/A') if edition_data.get('publisher') else 'N/A'
                        self.editions_table_widget.setItem(row, col, QTableWidgetItem(publisher_name))
                        col += 1
                        
                        # Language
                        language_name = edition_data.get('language', {}).get('language', 'N/A') if edition_data.get('language') else 'N/A'
                        self.editions_table_widget.setItem(row, col, QTableWidgetItem(language_name))
                        col += 1
                        
                        # Country
                        country_name = edition_data.get('country', {}).get('name', 'N/A') if edition_data.get('country') else 'N/A'
                        self.editions_table_widget.setItem(row, col, QTableWidgetItem(country_name))
                    
                    # Enable sorting
                    self.editions_table_widget.setSortingEnabled(True)
                    
                    # Default sort by score column (descending)
                    score_column = headers.index("score")
                    self.editions_table_widget.sortItems(score_column, Qt.DescendingOrder)
                    
                    # Enable scrolling (should be enabled by default, but let's be explicit)
                    self.editions_table_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
                    self.editions_table_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
                    
                    # Adjust column widths
                    self.editions_table_widget.resizeColumnsToContents()
                else:
                    # Clear table if no editions data
                    self.editions_table_widget.setRowCount(0)
                    self.editions_table_widget.setColumnCount(0)
            else:
                # This case might occur if ApiClient returns None for reasons other than exceptions
                # (e.g., no token, which is handled inside ApiClient for now)
                self.status_bar.showMessage(f"No data returned for Book ID {book_id_str}.")
                logger.warning(f"No data returned by ApiClient for Book ID {book_id_int}, but no exception was raised.")
        except ApiNotFoundError as e:
            self.status_bar.showMessage(f"Error fetching data: {e}")
            logger.warning(f"API_CLIENT_ERROR - ApiNotFoundError for Book ID {book_id_int}: {e}")
        except ApiException as e: # Catch other ApiClient specific exceptions
            self.status_bar.showMessage(f"Error fetching data: {e}")
            logger.error(f"API_CLIENT_ERROR - An API exception occurred for Book ID {book_id_int}: {e}")

    def _open_web_link(self, url: str):
        """Opens the given URL in the default web browser."""
        if url:
            logger.info(f"Opening URL: {url}")
            webbrowser.open(url)
        else:
            logger.warning("Attempted to open an empty URL.")
    
    def _create_table_item_with_tooltip(self, text: str, max_length: int = None) -> QTableWidgetItem:
        """
        Creates a QTableWidgetItem with text truncation and tooltip for long content.
        
        Args:
            text: The text to display
            max_length: Maximum length before truncation (uses self.MAX_CELL_TEXT_LENGTH if None)
            
        Returns:
            QTableWidgetItem with truncated text and full text in tooltip if needed
        """
        if max_length is None:
            max_length = self.MAX_CELL_TEXT_LENGTH
            
        text = str(text) if text is not None else "N/A"
        item = QTableWidgetItem(text)
        
        # Add tooltip for long text
        if len(text) > max_length:
            truncated_text = text[:max_length] + "..."
            item.setText(truncated_text)
            item.setToolTip(text)  # Full text in tooltip
        
        return item

    def _clear_layout(self, layout: QVBoxLayout | None):
        """
        Removes all widgets from the given layout.
        """
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

def main():
    """
    Main function to initialize and run the application.
    """
    # Configure logging to show INFO level messages
    # This should be done before any loggers are used extensively if you want
    # to capture early messages, or at least before the parts you're interested in.
    logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
    app = QApplication(sys.argv)

    app.setStyleSheet("""
        QWidget {
            background-color: #3c3c3c; 
            color: #cccccc; 
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
            font-size: 12pt; /* <<< Added to increase default font size */
        }
        QMainWindow {
            background-color: #2b2b2b;
        }
        QTabWidget::pane {
            border-top: 2px solid #555555;
        }
        QTabBar::tab {
            background: #4a4a4a;
            color: #cccccc;
            padding: 8px; /* May need adjustment if font becomes much larger */
            border: 1px solid #555555;
            border-bottom-color: #555555; 
        }
        QTabBar::tab:selected {
            background: #3c3c3c; 
            color: #ffffff;
            margin-bottom: -1px; 
            border-bottom-color: #3c3c3c;
        }
        QTabBar::tab:hover {
            background: #5a5a5a;
        }
        QGroupBox {
            font-weight: bold; /* This will remain bold */
            border: 1px solid #555555;
            border-radius: 4px;
            margin-top: 20px; /* Increased to accommodate larger font title */
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left; 
            padding: 0 3px; /* May need minor adjustment if font is very large */
            left: 10px; 
        }
        QStatusBar {
            color: #cccccc;
        }
        QLabel {
            color: #cccccc;
        }
        QPushButton { 
            background-color: #555555; 
            color: #cccccc;
            border: 1px solid #666666; 
            padding: 4px 8px; /* May need adjustment */
            min-height: 20px; 
        }
        QPushButton:hover { 
            background-color: #6a6a6a; 
        }
        QPushButton:pressed { 
            background-color: #454545; 
        }
        QLineEdit { 
            border: 1px solid #555555; 
            background-color: #454545; 
            color: #cccccc;
            padding: 2px; 
        }
    """)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()