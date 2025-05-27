# ABOUTME: This file is the main entry point for the Librarian-Assistant application.
# ABOUTME: It defines the main window and initializes the application.
import sys
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QLineEdit, QTableWidget, QTableWidgetItem, QScrollArea,
                             QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QPushButton, QHeaderView, QFrame)
from PyQt5.QtGui import QIntValidator, QValidator
from PyQt5.QtCore import Qt, pyqtSignal

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
# Import ColumnConfigDialog for column configuration
from librarian_assistant.column_config_dialog import ColumnConfigDialog

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
        self._default_text_color = "#e0e0e0" # Matches QWidget color in stylesheet
        self._link_text_color = "#9f7aea"    # Purple accent color to match theme

    def setContent(self, prefix: str, value_part: str, url_for_value_part: str = ""):
        """
        Sets the content of the label.
        - prefix: The static text part (e.g., "Slug: ").
        - value_part: The dynamic text part that might be a link (e.g., "my-book-slug" or "N/A").
        - url_for_value_part: The URL to associate with the value_part if it's linkable.
        """
        self._url_for_link_part = url_for_value_part
        current_value_part = value_part if value_part is not None else "N/A"
        
        # Use a dimmer color for the prefix to make values stand out
        prefix_color = "#999999"  # Medium gray for labels

        is_value_linkable = bool(self._url_for_link_part) and current_value_part != "N/A"

        if is_value_linkable:
            # Construct HTML with styled prefix and link
            # Ensure HTML special characters in prefix and value_part are escaped if necessary,
            # but for simple text like "Slug: " and typical slugs/IDs, it's often fine.
            # For robustness, one might use Qt.escape().
            html_text = (
                f"<span style='color:{prefix_color};'>{prefix}</span>"
                f"<a href='{self._url_for_link_part}' style='color:{self._link_text_color}; text-decoration:underline;'>{current_value_part}</a>"
            )
            self.setText(html_text)
            self.setCursor(Qt.PointingHandCursor)
            self.setToolTip(f"Open: {self._url_for_link_part}")
        else:
            # Use HTML for consistent styling even for non-links
            html_text = (
                f"<span style='color:{prefix_color};'>{prefix}</span>"
                f"<span style='color:{self._default_text_color};'>{current_value_part}</span>"
            )
            self.setText(html_text)
            self.setCursor(Qt.ArrowCursor)
            self.setToolTip("")


class NumericTableWidgetItem(QTableWidgetItem):
    """A QTableWidgetItem that sorts numerically instead of alphabetically."""
    
    def __init__(self, text, numeric_value=None):
        super().__init__(text)
        # Store the numeric value for sorting
        if numeric_value is not None:
            self.setData(Qt.UserRole, numeric_value)
    
    def __lt__(self, other):
        """Override less-than operator for proper numeric sorting."""
        my_value = self.data(Qt.UserRole)
        other_value = other.data(Qt.UserRole) if hasattr(other, 'data') else None
        
        # Handle None/N/A values
        if my_value is None:
            return True  # None values sort to beginning
        if other_value is None:
            return False
            
        # Compare numeric values
        try:
            return float(my_value) < float(other_value)
        except (ValueError, TypeError):
            # Fall back to string comparison
            return self.text() < other.text()


class SortableTableWidget(QTableWidget):
    """
    A QTableWidget with enhanced sorting capabilities:
    - Cycles through ascending → descending → no sort
    - Shows visual indicators in headers
    - Row accordion for displaying additional data
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Track sort state for each column
        self.column_sort_order = {}  # column_index: Qt.SortOrder or None
        self.last_sorted_column = None
        
        # Track expanded rows and their accordion widgets
        self.expanded_rows = {}  # row_index: accordion_widget
        
        # Connect header click to custom sort handler
        self.horizontalHeader().sectionClicked.connect(self._on_header_clicked)
        
        # Disable the default sorting behavior
        self.setSortingEnabled(False)
        
        # Enable column resizing
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.horizontalHeader().setStretchLastSection(True)  # Make last column fill remaining space
        self.horizontalHeader().setMinimumSectionSize(50)  # Minimum column width
        
        # Connect row click for accordion
        self.itemClicked.connect(self._on_item_clicked)
        
    def _on_header_clicked(self, logical_index):
        """Handle header click to cycle through sort states."""
        # Get current sort order for this column
        current_order = self.column_sort_order.get(logical_index)
        
        # Clear sort indicators from all other columns
        for col in list(self.column_sort_order.keys()):
            if col != logical_index:
                del self.column_sort_order[col]
                self._update_header_text(col)
        
        # Cycle through sort states
        if current_order is None:
            # No sort → Ascending
            new_order = Qt.AscendingOrder
        elif current_order == Qt.AscendingOrder:
            # Ascending → Descending
            new_order = Qt.DescendingOrder
        else:
            # Descending → No sort (clear)
            new_order = None
            
        # Update sort state
        self.column_sort_order[logical_index] = new_order
        self.last_sorted_column = logical_index if new_order is not None else None
        
        # Update header to show sort indicator
        self._update_header_text(logical_index)
        
        # Perform the sort
        if new_order is not None:
            self.sortItems(logical_index, new_order)
        else:
            # Clear sort - restore original order or default sort
            self._restore_default_sort()
    
    def _update_header_text(self, column_index):
        """Update header text with sort indicator."""
        header_item = self.horizontalHeaderItem(column_index)
        if header_item:
            base_text = header_item.text()
            # Remove any existing indicators
            base_text = base_text.replace(" ▲", "").replace(" ▼", "")
            
            # Add new indicator if sorted
            sort_order = self.column_sort_order.get(column_index)
            if sort_order == Qt.AscendingOrder:
                header_item.setText(f"{base_text} ▲")
            elif sort_order == Qt.DescendingOrder:
                header_item.setText(f"{base_text} ▼")
            else:
                header_item.setText(base_text)
    
    def _restore_default_sort(self):
        """Restore default sort (by score descending)."""
        # Find score column
        for col in range(self.columnCount()):
            header = self.horizontalHeaderItem(col)
            if header and header.text().replace(" ▲", "").replace(" ▼", "") == "score":
                self.sortItems(col, Qt.DescendingOrder)
                break
    
    def setHorizontalHeaderLabels(self, labels):
        """Override to track original header labels."""
        super().setHorizontalHeaderLabels(labels)
        # Clear any existing sort states when headers are set
        self.column_sort_order.clear()
        self.last_sorted_column = None
    
    def _on_item_clicked(self, item):
        """Handle item click to toggle row accordion."""
        if not item:
            return
            
        row = item.row()
        self.toggle_row_accordion(row)
    
    def toggle_row_accordion(self, row):
        """Toggle the accordion for a specific row."""
        if row in self.expanded_rows:
            # Collapse the row
            self._collapse_row(row)
        else:
            # Expand the row
            self._expand_row(row)
    
    def _expand_row(self, row):
        """Expand a row to show accordion content."""
        # Get the book_mappings data for this row
        book_mappings = self.get_row_book_mappings(row)
        if not book_mappings:
            return
            
        # Create accordion widget
        accordion_widget = self._create_accordion_widget(book_mappings)
        
        # Insert the accordion below the row
        self.insertRow(row + 1)
        self.setSpan(row + 1, 0, 1, self.columnCount())
        self.setCellWidget(row + 1, 0, accordion_widget)
        
        # Track the expanded row
        self.expanded_rows[row] = row + 1  # Store the accordion row index
        
        # Adjust row heights
        self.resizeRowToContents(row + 1)
    
    def _collapse_row(self, row):
        """Collapse an expanded row."""
        if row not in self.expanded_rows:
            return
            
        accordion_row = self.expanded_rows[row]
        
        # Remove the accordion row
        self.removeRow(accordion_row)
        
        # Update tracking for rows that shifted
        del self.expanded_rows[row]
        
        # Update indices for expanded rows below this one
        updated_expanded = {}
        for exp_row, acc_row in self.expanded_rows.items():
            if exp_row > row:
                updated_expanded[exp_row - 1] = acc_row - 1
            else:
                updated_expanded[exp_row] = acc_row if acc_row < accordion_row else acc_row - 1
        self.expanded_rows = updated_expanded
    
    def _create_accordion_widget(self, book_mappings):
        """Create the accordion widget displaying book mappings."""
        from PyQt5.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout
        
        frame = QFrame()
        frame.setFrameStyle(QFrame.Box)
        frame.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                padding: 10px;
                margin: 5px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        
        # Title
        title_label = QLabel("<b>Book Mappings:</b>")
        layout.addWidget(title_label)
        
        # Platform mappings
        for mapping in book_mappings:
            platform_name = mapping.get('platform', {}).get('name', 'Unknown')
            external_id = mapping.get('external_id', '')
            
            # Create clickable link based on platform
            link_url = self._get_platform_url(platform_name, external_id)
            
            if link_url:
                # Create clickable label
                mapping_label = ClickableLabel()
                mapping_label.setContent(f"{platform_name}: ", external_id, link_url)
                mapping_label.linkActivated.connect(lambda url: webbrowser.open(url))
            else:
                # Non-clickable label for unsupported platforms
                mapping_label = QLabel(f"{platform_name}: {external_id}")
                logger.warning(f"Unsupported platform in book_mappings: {platform_name}")
            
            layout.addWidget(mapping_label)
        
        return frame
    
    def _get_platform_url(self, platform_name, external_id):
        """Get the URL for a platform based on its name and external ID."""
        platform_lower = platform_name.lower()
        
        # URL patterns for supported platforms
        platform_urls = {
            'goodreads': f'https://www.goodreads.com/book/show/{external_id}',
            'librarything': f'https://www.librarything.com/work/{external_id}',  # May need adjustment
            'openlibrary': f'https://openlibrary.org{external_id}' if external_id.startswith('/books/') else f'https://openlibrary.org/books/{external_id}',
            'google': f'https://books.google.com/books?id={external_id}',
            'google books': f'https://books.google.com/books?id={external_id}',
            'storygraph': f'https://app.thestorygraph.com/books/{external_id}',  # May need adjustment
            'inventaire': f'https://inventaire.io/entity/{external_id}',  # May need adjustment
            'abebooks': external_id if external_id.startswith('http') else None,  # Often an image URL
        }
        
        return platform_urls.get(platform_lower)
    
    def get_row_book_mappings(self, row):
        """Get book_mappings data for a specific row. This should be overridden by the main window."""
        # This will be overridden in MainWindow to provide actual data
        return []
    
    def setRowCount(self, rows):
        """Override to clear expanded rows when resetting table."""
        super().setRowCount(rows)
        self.expanded_rows.clear()


class EditionsTableWidget(SortableTableWidget):
    """
    Custom table widget for editions that provides book_mappings data.
    """
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
    
    def get_row_book_mappings(self, row):
        """Get book_mappings data for a specific row."""
        if 0 <= row < len(self.main_window.editions_data):
            edition_data = self.main_window.editions_data[row]
            return edition_data.get('book_mappings', [])
        return []


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
        
        # Column configuration tracking
        self.all_column_names = []  # All columns in current table
        self.visible_column_names = []  # Currently visible columns
        self.column_order_map = {}  # Maps display position to actual column index
        
        # Edition data storage for accordion
        self.editions_data = []  # Store full edition data for each row

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

        self.api_input_area = QGroupBox("▼ API & Book ID Input Area")
        self.api_input_area.setObjectName("apiInputArea")
        self.api_input_area.setCheckable(True)
        self.api_input_area.setChecked(True)  # Start expanded
        api_layout = QVBoxLayout(self.api_input_area)
        self.token_display_label = QLabel()
        self.token_display_label.setTextFormat(Qt.RichText)
        self.token_display_label.setText(self._format_label_text("Token: ", "Not Set"))
        self.token_display_label.setObjectName("tokenDisplayLabel")
        api_layout.addWidget(self.token_display_label)

        self.set_token_button = QPushButton("Set/Update Token")
        self.set_token_button.setObjectName("setTokenButton")
        self.set_token_button.clicked.connect(self._open_set_token_dialog)
        api_layout.addWidget(self.set_token_button)

        # Add Book ID input elements as per Prompt 3.1
        self.book_id_label = QLabel()
        self.book_id_label.setTextFormat(Qt.RichText)
        self.book_id_label.setText("<span style='color:#999999;'>Book ID:</span>")
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

        self.book_info_area = QGroupBox("▼ General Book Information Area")
        self.book_info_area.setObjectName("bookInfoArea")
        self.book_info_area.setCheckable(True)
        self.book_info_area.setChecked(True)  # Start expanded
        self.info_layout = QVBoxLayout(self.book_info_area) # Store layout for easy access

        # Add specific widgets for book information - these will be populated later
        self.book_title_label = QLabel()
        self.book_title_label.setTextFormat(Qt.RichText)
        self.book_title_label.setText(self._format_label_text("Title: ", "Not Fetched"))
        self.book_title_label.setObjectName("bookTitleLabel")
        self.info_layout.addWidget(self.book_title_label)

        self.book_slug_label = ClickableLabel(self) # Pass parent
        self.book_slug_label.setObjectName("bookSlugLabel")
        self.book_slug_label.setContent("Slug: ", "Not Fetched", "")
        self.info_layout.addWidget(self.book_slug_label)
        self.book_slug_label.linkActivated.connect(self._open_web_link)

        self.book_authors_label = QLabel()
        self.book_authors_label.setTextFormat(Qt.RichText)
        self.book_authors_label.setText(self._format_label_text("Authors: ", "Not Fetched"))
        self.book_authors_label.setObjectName("bookAuthorsLabel")
        self.info_layout.addWidget(self.book_authors_label)

        self.book_id_queried_label = QLabel()
        self.book_id_queried_label.setTextFormat(Qt.RichText)
        self.book_id_queried_label.setText(self._format_label_text("Book ID (Queried): ", "Not Fetched"))
        self.book_id_queried_label.setObjectName("bookIdQueriedLabel")
        self.info_layout.addWidget(self.book_id_queried_label)

        self.book_total_editions_label = QLabel()
        self.book_total_editions_label.setTextFormat(Qt.RichText)
        self.book_total_editions_label.setText(self._format_label_text("Total Editions: ", "Not Fetched"))
        self.book_total_editions_label.setObjectName("bookTotalEditionsLabel")
        self.info_layout.addWidget(self.book_total_editions_label)

        self.book_description_label = QLabel()
        self.book_description_label.setTextFormat(Qt.RichText)
        self.book_description_label.setText(self._format_label_text("Description: ", "Not Fetched"))
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

        self.book_cover_label = QLabel()
        self.book_cover_label.setTextFormat(Qt.RichText)
        self.book_cover_label.setText(self._format_label_text("Cover URL: ", "Not Fetched"))
        self.book_cover_label.setObjectName("bookCoverLabel")
        self.info_layout.addWidget(self.book_cover_label)

        main_view_layout.addWidget(self.book_info_area)

        self.editions_table_area = QGroupBox("Editions Table Area")
        self.editions_table_area.setObjectName("editionsTableArea")
        self.editions_layout = QVBoxLayout(self.editions_table_area) # Store layout
        
        # Add button bar for table controls
        table_controls_layout = QHBoxLayout()
        self.configure_columns_button = QPushButton("Configure Columns")
        self.configure_columns_button.setObjectName("configureColumnsButton")
        self.configure_columns_button.clicked.connect(self._on_configure_columns)
        table_controls_layout.addWidget(self.configure_columns_button)
        table_controls_layout.addStretch()  # Push button to the left
        self.editions_layout.addLayout(table_controls_layout)
        
        self.editions_table_widget = EditionsTableWidget(self)
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
        
        # Connect toggled signals for collapsible behavior
        self.api_input_area.toggled.connect(self._on_api_input_toggled)
        self.book_info_area.toggled.connect(self._on_book_info_toggled)


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
            self.token_display_label.setText(self._format_label_text("Token: ", "*******"))
        else:
            self.token_display_label.setText(self._format_label_text("Token: ", "Not Set"))

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
                self.editions_data = []  # Clear edition data
                self.status_bar.showMessage(f"Book data fetched successfully for ID {book_id_str}.")
                logger.info(f"Successfully fetched data for Book ID {book_id_int}: {book_data.get('title', 'N/A')}")
                logger.info(f"Complete book_data received by main.py for Book ID {book_id_int}: {book_data}")

                # Re-create and populate the General Book Information Area widgets
                # Title
                self.book_title_label = QLabel()
                self.book_title_label.setTextFormat(Qt.RichText)
                self.book_title_label.setText(self._format_label_text("Title: ", book_data.get('title', 'N/A')))
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
                self.book_id_queried_label = QLabel()
                self.book_id_queried_label.setTextFormat(Qt.RichText)
                self.book_id_queried_label.setText(self._format_label_text("Book ID (Queried): ", str(book_id_int)))
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

                self.book_authors_label = QLabel()
                self.book_authors_label.setTextFormat(Qt.RichText)
                self.book_authors_label.setText(self._format_label_text("Authors: ", authors_display_text))
                self.book_authors_label.setObjectName("bookAuthorsLabel") # Keep object name for consistency/testing
                self.info_layout.addWidget(self.book_authors_label)
                
                # Total Editions Count
                editions_count_raw = book_data.get('editions_count')
                editions_count_val = str(editions_count_raw) if editions_count_raw is not None else 'N/A'
                self.book_total_editions_label = QLabel()
                self.book_total_editions_label.setTextFormat(Qt.RichText)
                self.book_total_editions_label.setText(self._format_label_text("Total Editions: ", editions_count_val))
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
                
                self.book_description_label = QLabel()
                self.book_description_label.setTextFormat(Qt.RichText)
                self.book_description_label.setText(self._format_label_text("Description: ", display_desc_text))
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

                self.book_cover_label = QLabel()
                self.book_cover_label.setTextFormat(Qt.RichText)
                self.book_cover_label.setText(self._format_label_text("Cover URL: ", cover_url))
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
                    # Process contributor data to determine which columns to show
                    contributor_data = self._process_contributor_data(editions)
                    active_roles = contributor_data['active_roles']
                    contributors_by_edition = contributor_data['contributors_by_edition']
                    max_contributors_per_role = contributor_data['max_contributors_per_role']
                    
                    # Define static headers according to spec.md section 2.4.1
                    static_headers = [
                        "id", "score", "title", "subtitle", "Cover Image?", 
                        "isbn_10", "isbn_13", "asin", "Reading Format", "pages", 
                        "Duration", "edition_format", "edition_information", 
                        "release_date", "Publisher", "Language", "Country"
                    ]
                    
                    # Build dynamic contributor headers (only for actual number needed)
                    contributor_headers = []
                    contributor_role_map = {}  # Maps column index to (role, number)
                    
                    for role in active_roles:
                        max_for_role = max_contributors_per_role.get(role, 0)
                        for i in range(1, max_for_role + 1):  # Only create columns for actual contributors
                            header = f"{role} {i}"
                            col_index = len(static_headers) + len(contributor_headers)
                            contributor_role_map[col_index] = (role, i - 1)  # 0-based index
                            contributor_headers.append(header)
                    
                    # Combine all headers
                    all_headers = static_headers + contributor_headers
                    
                    # Store column configuration
                    self.all_column_names = all_headers.copy()
                    self.visible_column_names = all_headers.copy()  # Initially all visible
                    
                    self.editions_table_widget.setColumnCount(len(all_headers))
                    self.editions_table_widget.setHorizontalHeaderLabels(all_headers)
                    self.editions_table_widget.setRowCount(len(editions))
                    
                    # Store edition data for accordion
                    self.editions_data = editions

                    for row, edition_data in enumerate(editions):
                        col = 0
                        
                        # id
                        self.editions_table_widget.setItem(row, col, QTableWidgetItem(str(edition_data.get('id', 'N/A'))))
                        col += 1
                        
                        # score
                        score_value = edition_data.get('score')
                        if score_value is not None:
                            score_item = NumericTableWidgetItem(str(score_value), score_value)
                        else:
                            score_item = QTableWidgetItem('N/A')
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
                        if pages_value is not None:
                            pages_item = NumericTableWidgetItem(str(pages_value), pages_value)
                        else:
                            pages_item = QTableWidgetItem('N/A')
                        self.editions_table_widget.setItem(row, col, pages_item)
                        col += 1
                        
                        # Duration (audio_seconds converted to HH:MM:SS)
                        audio_seconds = edition_data.get('audio_seconds')
                        if audio_seconds is not None and audio_seconds > 0:
                            hours = audio_seconds // 3600
                            minutes = (audio_seconds % 3600) // 60
                            seconds = audio_seconds % 60
                            duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                            duration_item = NumericTableWidgetItem(duration_str, audio_seconds)
                        else:
                            duration_item = QTableWidgetItem("N/A")
                        self.editions_table_widget.setItem(row, col, duration_item)
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
                        col += 1
                        
                        # Populate contributor columns
                        edition_id = edition_data.get('id')
                        edition_contributors = contributors_by_edition.get(edition_id, {})
                        
                        # For each contributor column
                        for col_idx in range(len(static_headers), len(all_headers)):
                            if col_idx in contributor_role_map:
                                role, contributor_index = contributor_role_map[col_idx]
                                contributors_for_role = edition_contributors.get(role, [])
                                
                                if contributor_index < len(contributors_for_role):
                                    contributor_name = contributors_for_role[contributor_index]
                                    self.editions_table_widget.setItem(row, col_idx, QTableWidgetItem(contributor_name))
                                else:
                                    self.editions_table_widget.setItem(row, col_idx, QTableWidgetItem("N/A"))
                    
                    # Default sort by score column (descending)
                    score_column = all_headers.index("score")
                    self.editions_table_widget.sortItems(score_column, Qt.DescendingOrder)
                    # Set initial sort indicator
                    self.editions_table_widget.column_sort_order[score_column] = Qt.DescendingOrder
                    self.editions_table_widget._update_header_text(score_column)
                    
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
    
    def _on_api_input_toggled(self, checked: bool):
        """Handle the toggling of the API input area."""
        # Update the arrow in the title
        current_title = self.api_input_area.title()
        if checked:
            # Replace right arrow with down arrow
            new_title = current_title.replace("▶", "▼")
        else:
            # Replace down arrow with right arrow
            new_title = current_title.replace("▼", "▶")
        self.api_input_area.setTitle(new_title)
        
        # Find all widgets inside the group box except the title
        for i in range(self.api_input_area.layout().count()):
            widget = self.api_input_area.layout().itemAt(i).widget()
            if widget:
                widget.setVisible(checked)
        
        # Adjust the group box size and add visual property
        if not checked:
            self.api_input_area.setMaximumHeight(30)  # Just enough for the title
            self.api_input_area.setProperty("collapsed", "true")
        else:
            self.api_input_area.setMaximumHeight(16777215)  # Reset to default max
            self.api_input_area.setProperty("collapsed", "false")
        
        # Force style update
        self.api_input_area.style().unpolish(self.api_input_area)
        self.api_input_area.style().polish(self.api_input_area)
    
    def _on_book_info_toggled(self, checked: bool):
        """Handle the toggling of the book info area."""
        # Update the arrow in the title
        current_title = self.book_info_area.title()
        if checked:
            # Replace right arrow with down arrow
            new_title = current_title.replace("▶", "▼")
        else:
            # Replace down arrow with right arrow
            new_title = current_title.replace("▼", "▶")
        self.book_info_area.setTitle(new_title)
        
        # Find all widgets inside the group box except the title
        for i in range(self.book_info_area.layout().count()):
            widget = self.book_info_area.layout().itemAt(i).widget()
            if widget:
                widget.setVisible(checked)
        
        # Adjust the group box size and add visual property
        if not checked:
            self.book_info_area.setMaximumHeight(30)  # Just enough for the title
            self.book_info_area.setProperty("collapsed", "true")
        else:
            self.book_info_area.setMaximumHeight(16777215)  # Reset to default max
            self.book_info_area.setProperty("collapsed", "false")
        
        # Force style update
        self.book_info_area.style().unpolish(self.book_info_area)
        self.book_info_area.style().polish(self.book_info_area)
    
    def _process_contributor_data(self, editions: list) -> dict:
        """
        Process contributor data from all editions to determine roles and contributors.
        
        Returns:
            dict: Structure with roles as keys and lists of contributor names per edition
        """
        # Predefined roles from spec Appendix B
        predefined_roles = [
            "Author", "Illustrator", "Editor", "Translator", 
            "Narrator", "Foreword", "Cover Artist", "Other"
        ]
        
        # Dictionary to track all unique roles found across all editions
        all_roles = set()
        
        # Dictionary to store contributors by edition and role
        contributors_by_edition = {}
        
        # Track maximum contributors per role
        max_contributors_per_role = {}
        
        for edition in editions:
            edition_id = edition.get('id')
            contributors_by_edition[edition_id] = {}
            
            cached_contributors = edition.get('cached_contributors', [])
            
            # Process each contributor
            for contributor in cached_contributors:
                if not isinstance(contributor, dict):
                    continue
                    
                author_info = contributor.get('author', {})
                if not isinstance(author_info, dict):
                    continue
                    
                name = author_info.get('name', 'N/A')
                contribution = contributor.get('contribution')
                
                # Handle null contribution as primary Author
                if contribution is None:
                    role = "Author"
                else:
                    role = contribution
                    
                # Add role to all_roles set
                all_roles.add(role)
                
                # Initialize role list if needed
                if role not in contributors_by_edition[edition_id]:
                    contributors_by_edition[edition_id][role] = []
                
                contributors_by_edition[edition_id][role].append(name)
        
        # Calculate max contributors per role
        for edition_id, roles_dict in contributors_by_edition.items():
            for role, contributors in roles_dict.items():
                current_count = len(contributors)
                if role not in max_contributors_per_role:
                    max_contributors_per_role[role] = current_count
                else:
                    max_contributors_per_role[role] = max(max_contributors_per_role[role], current_count)
        
        # Filter to only include predefined roles that actually exist
        active_roles = [role for role in predefined_roles if role in all_roles]
        
        return {
            'active_roles': active_roles,
            'contributors_by_edition': contributors_by_edition,
            'max_contributors_per_role': max_contributors_per_role
        }
    
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

    def _format_label_text(self, label: str, value: str) -> str:
        """Format label text with dimmed label and prominent value."""
        return f"<span style='color:#999999;'>{label}</span><span style='color:#e0e0e0;'>{value}</span>"
    
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
    
    def _on_configure_columns(self):
        """
        Show the column configuration dialog and apply changes.
        """
        # Only allow configuration if we have data
        if not self.all_column_names:
            self.status_bar.showMessage("No data loaded. Fetch book data first.", 3000)
            return
        
        # Create dialog with current configuration
        dialog = ColumnConfigDialog(
            self.all_column_names,
            self.visible_column_names,
            self
        )
        
        # Connect to configuration signal
        dialog.columns_configured.connect(self._apply_column_configuration)
        
        # Show dialog
        dialog.exec_()
    
    def _apply_column_configuration(self, new_column_order, new_visible_columns):
        """
        Apply the new column configuration to the table.
        
        Args:
            new_column_order: List of all columns in new order
            new_visible_columns: List of visible columns in order
        """
        # Store the new configuration
        self.all_column_names = new_column_order
        self.visible_column_names = new_visible_columns
        
        # Get current table data
        row_count = self.editions_table_widget.rowCount()
        col_count = self.editions_table_widget.columnCount()
        
        # Store column widths
        column_widths = {}
        for col in range(col_count):
            header = self.editions_table_widget.horizontalHeaderItem(col)
            if header:
                col_name = header.text().replace(" ▲", "").replace(" ▼", "")
                column_widths[col_name] = self.editions_table_widget.columnWidth(col)
        
        # Store all current data
        table_data = []
        for row in range(row_count):
            row_data = {}
            for col in range(col_count):
                header = self.editions_table_widget.horizontalHeaderItem(col)
                if header:
                    col_name = header.text().replace(" ▲", "").replace(" ▼", "")
                    item = self.editions_table_widget.item(row, col)
                    if item:
                        row_data[col_name] = item.text()
            table_data.append(row_data)
        
        # Clear and reconfigure table
        self.editions_table_widget.setColumnCount(len(new_visible_columns))
        self.editions_table_widget.setHorizontalHeaderLabels(new_visible_columns)
        
        # Repopulate with reordered data
        for row, row_data in enumerate(table_data):
            for col, col_name in enumerate(new_visible_columns):
                value = row_data.get(col_name, "N/A")
                # Check if this was a numeric column
                if col_name == "score" or col_name == "pages":
                    try:
                        numeric_value = float(value) if value != "N/A" else None
                        item = NumericTableWidgetItem(value, numeric_value)
                    except:
                        item = QTableWidgetItem(value)
                elif col_name == "Duration" and value != "N/A":
                    # Preserve numeric sorting for duration
                    # Extract seconds from HH:MM:SS format
                    try:
                        parts = value.split(":")
                        if len(parts) == 3:
                            seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                            item = NumericTableWidgetItem(value, seconds)
                        else:
                            item = QTableWidgetItem(value)
                    except:
                        item = QTableWidgetItem(value)
                else:
                    item = QTableWidgetItem(value)
                
                self.editions_table_widget.setItem(row, col, item)
        
        # Restore column widths where possible
        for col, col_name in enumerate(new_visible_columns):
            if col_name in column_widths:
                self.editions_table_widget.setColumnWidth(col, column_widths[col_name])
        
        # Update status
        hidden_count = len(self.all_column_names) - len(self.visible_column_names)
        if hidden_count > 0:
            self.status_bar.showMessage(f"Column configuration applied. {hidden_count} columns hidden.", 3000)
        else:
            self.status_bar.showMessage("Column configuration applied.", 3000)

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
            background-color: #1a1a1a; 
            color: #e0e0e0; 
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, "Open Sans", "Helvetica Neue", sans-serif;
            font-size: 12pt;
        }
        QMainWindow {
            background-color: #0d0d0d;
        }
        QTabWidget::pane {
            border-top: 2px solid #2d2d2d;
            background-color: #1a1a1a;
        }
        QTabBar::tab {
            background: #242424;
            color: #b0b0b0;
            padding: 8px 16px;
            border: 1px solid #2d2d2d;
            border-bottom-color: #2d2d2d; 
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        QTabBar::tab:selected {
            background: #1a1a1a; 
            color: #ffffff;
            margin-bottom: -1px; 
            border-bottom-color: #1a1a1a;
        }
        QTabBar::tab:hover {
            background: #2d2d2d;
            color: #ffffff;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #2d2d2d;
            border-radius: 6px;
            margin-top: 20px;
            background-color: #1a1a1a;
        }
        QGroupBox:checkable {
            subcontrol-origin: margin;
            subcontrol-position: left top;
            padding-left: 0px;
            margin-left: 0px;
        }
        QGroupBox::indicator {
            width: 0px;
            height: 0px;
            margin: 0px;
            padding: 0px;
        }
        QGroupBox[collapsed="true"] {
            border-bottom: none;
            padding-bottom: 0px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left; 
            padding: 0 8px;
            left: 10px;
            color: #ffffff;
        }
        QStatusBar {
            background-color: #0d0d0d;
            color: #b0b0b0;
            border-top: 1px solid #2d2d2d;
        }
        QLabel {
            color: #e0e0e0;
        }
        QPushButton { 
            background-color: #6b46c1; 
            color: #ffffff;
            border: none;
            border-radius: 4px;
            padding: 6px 16px;
            min-height: 24px;
            font-weight: 500;
        }
        QPushButton:hover { 
            background-color: #7c52d9;
        }
        QPushButton:pressed { 
            background-color: #553899;
        }
        QLineEdit { 
            border: 1px solid #2d2d2d;
            border-radius: 4px;
            background-color: #242424;
            color: #e0e0e0;
            padding: 6px 8px;
            selection-background-color: #6b46c1;
        }
        QLineEdit:focus {
            border: 1px solid #6b46c1;
        }
        QTableWidget {
            background-color: #1a1a1a;
            alternate-background-color: #242424;
            gridline-color: #2d2d2d;
            color: #e0e0e0;
            selection-background-color: #6b46c1;
            selection-color: #ffffff;
        }
        QTableWidget::item {
            padding: 4px;
        }
        QHeaderView::section {
            background-color: #242424;
            color: #ffffff;
            padding: 6px;
            border: none;
            border-right: 1px solid #2d2d2d;
            border-bottom: 1px solid #2d2d2d;
            font-weight: 600;
        }
        QHeaderView::section:hover {
            background-color: #2d2d2d;
        }
        QScrollBar:vertical {
            background-color: #1a1a1a;
            width: 12px;
            border: none;
        }
        QScrollBar::handle:vertical {
            background-color: #3d3d3d;
            min-height: 30px;
            border-radius: 6px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #4d4d4d;
        }
        QScrollBar:horizontal {
            background-color: #1a1a1a;
            height: 12px;
            border: none;
        }
        QScrollBar::handle:horizontal {
            background-color: #3d3d3d;
            min-width: 30px;
            border-radius: 6px;
        }
        QScrollBar::handle:horizontal:hover {
            background-color: #4d4d4d;
        }
        QScrollBar::add-line, QScrollBar::sub-line {
            border: none;
            background: none;
        }
    """)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()