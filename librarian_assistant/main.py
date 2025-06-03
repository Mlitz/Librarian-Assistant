# ABOUTME: This file is the main entry point for the Librarian-Assistant application.
# ABOUTME: It defines the main window and initializes the application.
import sys
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QLineEdit, QTableWidget, QTableWidgetItem, QScrollArea,
                             QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QPushButton, QHeaderView, QComboBox, QCheckBox, QMessageBox)
from PyQt6.QtGui import QIntValidator, QValidator, QColor
from PyQt6.QtCore import Qt

# Import configuration and authentication modules
from librarian_assistant.config_manager import ConfigManager
from librarian_assistant.token_dialog import TokenDialog
# Import API client and exceptions
from librarian_assistant.api_client import ApiClient
from librarian_assistant.exceptions import (ApiException, ApiNotFoundError,
                                            ApiAuthError, NetworkError, ApiProcessingError)
# Import image handling
from librarian_assistant.image_downloader import ImageDownloader
# Import ColumnConfigDialog for column configuration
from librarian_assistant.column_config_dialog import ColumnConfigDialog
# Import FilterDialog for advanced filtering
from librarian_assistant.filter_dialog import FilterDialog
# Import HistoryManager for search history
from librarian_assistant.history_manager import HistoryManager
# Import enhanced stylesheet
from librarian_assistant.enhanced_stylesheet import ENHANCED_DARK_THEME

import webbrowser  # For opening external links
import logging
logger = logging.getLogger(__name__)

# Constants
HARDCOVER_API_BASE_URL = "https://api.hardcover.app/v1/graphql"
MAX_DESC_CHARS = 500  # Define max characters for display


class ClickableLabel(QLabel):
    """
    A QLabel subclass that can be made clickable and emits a signal with a URL.
    """
    # No custom signal needed; QLabel.linkActivated will be used.

    def __init__(self, parent=None):  # Text will be set via setContent
        super().__init__(parent)
        self._url_for_link_part = ""  # Store the URL associated with the link part
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setOpenExternalLinks(False)  # Important: emit linkActivated instead of QLabel opening it
        self.setCursor(Qt.CursorShape.ArrowCursor)  # Default cursor
        # Default style for the non-link part (taken from main stylesheet)
        self._default_text_color = "#e0e0e0"  # Matches QWidget color in stylesheet
        self._link_text_color = "#9f7aea"    # Purple accent color to match theme

    def setContent(self, prefix: str, value_part: str, url_for_value_part: str = "", field_name: str = ""):
        """
        Sets the content of the label.
        - prefix: The static text part (e.g., "Slug: ").
        - value_part: The dynamic text part that might be a link (e.g., "my-book-slug" or "N/A").
        - url_for_value_part: The URL to associate with the value_part if it's linkable.
        - field_name: Optional field identifier for N/A highlighting logic.
        """
        from librarian_assistant.ui_utils import should_highlight_general_info_na
        from librarian_assistant.styling_constants import get_na_highlight_html

        self._url_for_link_part = url_for_value_part
        current_value_part = value_part if value_part is not None else "N/A"

        # Use a dimmer color for the prefix to make values stand out
        prefix_color = "#999999"  # Medium gray for labels

        is_value_linkable = bool(self._url_for_link_part) and current_value_part != "N/A"

        # Check if N/A should be highlighted
        should_highlight_na = (current_value_part == "N/A" and
                               field_name and
                               should_highlight_general_info_na(field_name))

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
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.setToolTip(f"Open: {self._url_for_link_part}")
        else:
            # Use HTML for consistent styling even for non-links
            if should_highlight_na:
                # Use highlighted N/A styling
                value_html = get_na_highlight_html(current_value_part)
            else:
                # Use default styling
                value_html = f"<span style='color:{self._default_text_color};'>{current_value_part}</span>"

            html_text = f"<span style='color:{prefix_color};'>{prefix}</span>{value_html}"
            self.setText(html_text)
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.setToolTip("")


class NumericTableWidgetItem(QTableWidgetItem):
    """A QTableWidgetItem that sorts numerically instead of alphabetically."""

    def __init__(self, text, numeric_value=None):
        super().__init__(text)
        # Store the numeric value for sorting
        if numeric_value is not None:
            self.setData(Qt.ItemDataRole.UserRole, numeric_value)

    def __lt__(self, other):
        """Override less-than operator for proper numeric sorting."""
        my_value = self.data(Qt.ItemDataRole.UserRole)
        other_value = other.data(Qt.ItemDataRole.UserRole) if hasattr(other, 'data') else None

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

        # Connect header click to custom sort handler
        self.horizontalHeader().sectionClicked.connect(self._on_header_clicked)

        # Disable the default sorting behavior
        self.setSortingEnabled(False)

        # Enable column resizing
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.horizontalHeader().setStretchLastSection(True)  # Make last column fill remaining space
        self.horizontalHeader().setMinimumSectionSize(50)  # Minimum column width

        # Set selection behavior
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        # Track checkbox states for persistence
        self.checked_editions = set()  # Set of edition IDs that are checked

    def _toggle_all_checkboxes(self):
        """Toggle all checkboxes in the Select column."""
        # Count how many are currently checked
        checked_count = 0
        total_count = 0

        for row in range(self.rowCount()):
            widget = self.cellWidget(row, 0)  # Select column is at index 0
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox:
                    total_count += 1
                    if checkbox.isChecked():
                        checked_count += 1

        # If all or some are checked, uncheck all. If none are checked, check all.
        new_state = checked_count == 0

        # Update all checkboxes
        for row in range(self.rowCount()):
            widget = self.cellWidget(row, 0)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox:
                    checkbox.setChecked(new_state)

        # Trigger main window update
        main_window = self.window()
        if main_window and hasattr(main_window, '_update_book_mappings_tab'):
            main_window._update_book_mappings_tab()

    def _on_header_clicked(self, logical_index):
        """Handle header click to cycle through sort states."""
        # Check if this is the Select column (index 0)
        header_item = self.horizontalHeaderItem(logical_index)
        if header_item and header_item.text().replace(" ▲", "").replace(" ▼", "") == "Select":
            # Toggle all checkboxes
            self._toggle_all_checkboxes()
            return

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
            new_order = Qt.SortOrder.AscendingOrder
        elif current_order == Qt.SortOrder.AscendingOrder:
            # Ascending → Descending
            new_order = Qt.SortOrder.DescendingOrder
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
            if sort_order == Qt.SortOrder.AscendingOrder:
                header_item.setText(f"{base_text} ▲")
            elif sort_order == Qt.SortOrder.DescendingOrder:
                header_item.setText(f"{base_text} ▼")
            else:
                header_item.setText(base_text)

    def _restore_default_sort(self):
        """Restore default sort (by score descending)."""
        # Find score column
        for col in range(self.columnCount()):
            header = self.horizontalHeaderItem(col)
            if header and header.text().replace(" ▲", "").replace(" ▼", "") == "score":
                self.sortItems(col, Qt.SortOrder.DescendingOrder)
                break

    def setHorizontalHeaderLabels(self, labels):
        """Override to track original header labels."""
        super().setHorizontalHeaderLabels(labels)
        # Clear any existing sort states when headers are set
        self.column_sort_order.clear()
        self.last_sorted_column = None

    def sortItems(self, column, order):
        """Override sortItems to preserve checkbox states."""
        # Store checkbox states before sorting
        checkbox_states = {}  # edition_id -> checked state

        for row in range(self.rowCount()):
            # Get checkbox state
            widget = self.cellWidget(row, 0)  # Select column is at index 0
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox:
                    # Get edition ID for this row
                    edition_id = self._get_edition_id_for_row(row)
                    if edition_id:
                        checkbox_states[edition_id] = checkbox.isChecked()

        # Perform the sort
        super().sortItems(column, order)

        # Restore checkbox states after sorting
        for row in range(self.rowCount()):
            edition_id = self._get_edition_id_for_row(row)
            if edition_id in checkbox_states:
                widget = self.cellWidget(row, 0)
                if widget:
                    checkbox = widget.findChild(QCheckBox)
                    if checkbox:
                        checkbox.setChecked(checkbox_states[edition_id])

    def _get_edition_id_for_row(self, visual_row):
        """Get the edition ID for a visual row."""
        logger.info(f"_get_edition_id_for_row: visual_row={visual_row}, columnCount={self.columnCount()}")

        # Check if we have columns
        if self.columnCount() == 0:
            logger.error("No columns in table!")
            return None

        # First, try to find the ID column - it might not be at index 0 if columns were reordered
        id_col_index = None
        for col in range(self.columnCount()):
            header_item = self.horizontalHeaderItem(col)
            if header_item:
                header_text = header_item.text().replace(" ▲", "").replace(" ▼", "")
                if header_text == "id":
                    id_col_index = col
                    logger.info(f"Found ID column at index {col}")
                    break

        if id_col_index is None:
            logger.warning("ID column not found in table headers!")
            # Fallback: use row number as a string ID
            fallback_id = f"row_{visual_row}"
            logger.info(f"Using fallback ID: {fallback_id}")
            return fallback_id

        # Check the ID column for the edition ID
        widget = self.cellWidget(visual_row, id_col_index)
        logger.info(f"Widget at row {visual_row}, col {id_col_index}: {widget}")

        if widget:
            # For ClickableLabel, we need to extract the ID from the link text
            if hasattr(widget, 'text'):
                text = widget.text()
                logger.info(f"Widget text: {text}")
                # Extract ID from the HTML if it's a ClickableLabel
                if '<a href=' in text:
                    # Parse the ID from the link
                    import re
                    match = re.search(r'>([^<]+)</a>', text)
                    if match:
                        edition_id = match.group(1)
                        logger.info(f"Extracted edition ID from link: {edition_id}")
                        return edition_id
                return text

        # Try regular item
        item = self.item(visual_row, id_col_index)
        if item:
            edition_id = item.text()
            logger.info(f"Got edition ID from item: {edition_id}")
            return edition_id

        logger.warning(f"Could not find edition ID for row {visual_row}")
        # Fallback: use row number as ID
        fallback_id = f"row_{visual_row}"
        logger.info(f"Using fallback ID: {fallback_id}")
        return fallback_id


class EditionsTableWidget(SortableTableWidget):
    """
    Custom table widget for editions that provides book_mappings data.
    """

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window

    def get_row_book_mappings(self, row):
        """Get book_mappings data for a specific row."""
        logger.info(f"get_row_book_mappings called with row={row}, editions_data length={len(self.main_window.editions_data)}")
        if 0 <= row < len(self.main_window.editions_data):
            edition_data = self.main_window.editions_data[row]
            book_mappings = edition_data.get('book_mappings', [])
            logger.info(f"Found {len(book_mappings)} book mappings for data row {row}")
            return book_mappings
        logger.warning(f"Row {row} out of range for editions_data")
        return []

    def get_book_mappings_by_edition_id(self, edition_id):
        """Get book_mappings data for a specific edition ID."""
        logger.info(f"get_book_mappings_by_edition_id called with edition_id={edition_id}")

        # Handle fallback row IDs
        if edition_id and edition_id.startswith("row_"):
            try:
                row_index = int(edition_id.split("_")[1])
                logger.info(f"Using fallback row index: {row_index}")

                # When using fallback, we need to get the data from the actual row
                # First try to get the stored data index from the score column

                # Find the score column
                score_col = None
                for col in range(self.columnCount()):
                    header = self.horizontalHeaderItem(col)
                    if header and header.text().replace(" ▲", "").replace(" ▼", "") == "score":
                        score_col = col
                        break

                if score_col is not None:
                    score_item = self.item(row_index, score_col)
                    if score_item:
                        # Get the stored data index
                        stored_data_index = score_item.data(Qt.ItemDataRole.UserRole + 1)
                        if stored_data_index is not None:
                            logger.info(f"Found stored data index {stored_data_index} for row {row_index}")
                            if 0 <= stored_data_index < len(self.main_window.editions_data):
                                edition_data = self.main_window.editions_data[stored_data_index]
                                book_mappings = edition_data.get('book_mappings', [])
                                logger.info(f"Found {len(book_mappings)} book mappings for stored data index {stored_data_index}")
                                return book_mappings

                        # Fallback to score matching if no stored index
                        score_text = score_item.text()
                        logger.info(f"No stored index, trying score match: {score_text}")

                        for idx, edition_data in enumerate(self.main_window.editions_data):
                            if str(edition_data.get('score', '')) == score_text:
                                book_mappings = edition_data.get('book_mappings', [])
                                logger.info(f"Found edition by score match at index {idx}: {len(book_mappings)} book mappings")
                                return book_mappings

                logger.warning(f"Could not find book mappings for row {row_index}")
            except (ValueError, IndexError) as e:
                logger.error(f"Error parsing fallback row ID: {e}")

        # Try normal ID lookup
        for edition_data in self.main_window.editions_data:
            if str(edition_data.get('id', '')) == str(edition_id):
                book_mappings = edition_data.get('book_mappings', [])
                logger.info(f"Found {len(book_mappings)} book mappings for edition ID {edition_id}")
                return book_mappings

        logger.warning(f"Edition ID {edition_id} not found in editions_data")
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

        # Edition data storage
        self.editions_data = []  # Store full edition data for each row

        # Filter tracking
        self.active_filters = []  # Currently applied filters
        self.filter_logic_mode = 'AND'  # AND or OR

        # Create status bar early so it can be used for error messages
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Initializing...")

        # Initialize managers with error handling
        try:
            self.config_manager = ConfigManager()
        except Exception as e:
            logger.error(f"Failed to initialize ConfigManager: {e}")
            QMessageBox.critical(self, "Initialization Error",
                                 "Failed to initialize configuration manager.\n"
                                 "The application may not function properly.")
            self.config_manager = None

        self.api_client = ApiClient(
            base_url=HARDCOVER_API_BASE_URL,
            token_manager=self.config_manager
        ) if self.config_manager else None

        self.image_downloader = ImageDownloader()

        try:
            self.history_manager = HistoryManager()
        except Exception as e:
            logger.error(f"Failed to initialize HistoryManager: {e}")
            self.status_bar.showMessage("Error loading search history. History features may be unavailable.")
            self.history_manager = None

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
        self.token_display_label.setTextFormat(Qt.TextFormat.RichText)
        self.token_display_label.setText(self._format_label_text("Token: ", "Not Set"))
        self.token_display_label.setObjectName("tokenDisplayLabel")
        api_layout.addWidget(self.token_display_label)

        self.set_token_button = QPushButton("Set/Update Token")
        self.set_token_button.setObjectName("setUpdateTokenButton")
        self.set_token_button.clicked.connect(self._open_set_token_dialog)
        api_layout.addWidget(self.set_token_button)

        # Add Book ID input elements as per Prompt 3.1
        self.book_id_label = QLabel()
        self.book_id_label.setTextFormat(Qt.TextFormat.RichText)
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
        self.fetch_data_button.clicked.connect(self._on_fetch_data_clicked)  # Connect signal
        api_layout.addWidget(self.fetch_data_button)

        main_view_layout.addWidget(self.api_input_area)

        self.book_info_area = QGroupBox("▼ General Book Information Area")
        self.book_info_area.setObjectName("bookInfoArea")
        self.book_info_area.setCheckable(True)
        self.book_info_area.setChecked(True)  # Start expanded
        self.info_layout = QVBoxLayout(self.book_info_area)  # Store layout for easy access

        # Add specific widgets for book information - these will be populated later
        self.book_title_label = QLabel()
        self.book_title_label.setTextFormat(Qt.TextFormat.RichText)
        self.book_title_label.setText(self._format_label_text("Title: ", "Not Fetched"))
        self.book_title_label.setObjectName("bookTitleLabel")
        self.info_layout.addWidget(self.book_title_label)

        self.book_slug_label = ClickableLabel(self)  # Pass parent
        self.book_slug_label.setObjectName("bookSlugLabel")
        self.book_slug_label.setContent("Slug: ", "Not Fetched", "", field_name='slug')
        self.info_layout.addWidget(self.book_slug_label)
        self.book_slug_label.linkActivated.connect(self._open_web_link)

        self.book_authors_label = QLabel()
        self.book_authors_label.setTextFormat(Qt.TextFormat.RichText)
        self.book_authors_label.setText(self._format_label_text("Authors: ", "Not Fetched"))
        self.book_authors_label.setObjectName("bookAuthorsLabel")
        self.info_layout.addWidget(self.book_authors_label)

        self.book_id_queried_label = QLabel()
        self.book_id_queried_label.setTextFormat(Qt.TextFormat.RichText)
        self.book_id_queried_label.setText(self._format_label_text("Book ID (Queried): ", "Not Fetched"))
        self.book_id_queried_label.setObjectName("bookIdQueriedLabel")
        self.info_layout.addWidget(self.book_id_queried_label)

        self.book_total_editions_label = QLabel()
        self.book_total_editions_label.setTextFormat(Qt.TextFormat.RichText)
        self.book_total_editions_label.setText(self._format_label_text("Total Editions: ", "Not Fetched"))
        self.book_total_editions_label.setObjectName("bookTotalEditionsLabel")
        self.info_layout.addWidget(self.book_total_editions_label)

        self.book_description_label = QLabel()
        self.book_description_label.setTextFormat(Qt.TextFormat.RichText)
        self.book_description_label.setText(self._format_label_text("Description: ", "Not Fetched"))
        self.book_description_label.setObjectName("bookDescriptionLabel")
        self.book_description_label.setWordWrap(True)  # Allow text to wrap
        # Tooltip will be set dynamically if text is truncated
        self.info_layout.addWidget(self.book_description_label)

        # Default Editions GroupBox and Labels (as per Prompt 4.1)
        self.default_editions_group_box = QGroupBox("Default Editions")
        self.default_editions_group_box.setObjectName("defaultEditionsGroupBox")
        default_editions_layout_init = QVBoxLayout(self.default_editions_group_box)  # Layout for init

        self.default_audio_label = ClickableLabel(self)
        self.default_audio_label.setObjectName("defaultAudioLabel")
        self.default_audio_label.setContent("Default Audio Edition: ", "N/A", "", field_name='default_audio_edition')
        default_editions_layout_init.addWidget(self.default_audio_label)
        self.default_audio_label.linkActivated.connect(self._open_web_link)

        self.default_cover_label_info = ClickableLabel(self)
        self.default_cover_label_info.setObjectName("defaultCoverLabelInfo")
        self.default_cover_label_info.setContent("Default Cover Edition: ", "N/A", "", field_name='default_cover_edition')
        default_editions_layout_init.addWidget(self.default_cover_label_info)
        self.default_cover_label_info.linkActivated.connect(self._open_web_link)

        self.default_ebook_label = ClickableLabel(self)
        self.default_ebook_label.setObjectName("defaultEbookLabel")
        self.default_ebook_label.setContent("Default E-book Edition: ", "N/A", "", field_name='default_ebook_edition')
        default_editions_layout_init.addWidget(self.default_ebook_label)
        self.default_ebook_label.linkActivated.connect(self._open_web_link)

        self.default_physical_label = ClickableLabel(self)
        self.default_physical_label.setObjectName("defaultPhysicalLabel")
        self.default_physical_label.setContent("Default Physical Edition: ", "N/A", "", field_name='default_physical_edition')
        default_editions_layout_init.addWidget(self.default_physical_label)
        self.default_physical_label.linkActivated.connect(self._open_web_link)
        self.info_layout.addWidget(self.default_editions_group_box)

        self.book_cover_label = QLabel()
        self.book_cover_label.setTextFormat(Qt.TextFormat.RichText)
        self.book_cover_label.setText(self._format_label_text("Cover URL: ", "Not Fetched"))
        self.book_cover_label.setObjectName("bookCoverLabel")
        self.info_layout.addWidget(self.book_cover_label)

        main_view_layout.addWidget(self.book_info_area)

        self.editions_table_area = QGroupBox("Editions Table Area")
        self.editions_table_area.setObjectName("editionsTableArea")
        self.editions_layout = QVBoxLayout(self.editions_table_area)  # Store layout

        # Add button bar for table controls
        table_controls_layout = QHBoxLayout()
        self.configure_columns_button = QPushButton("Configure Columns")
        self.configure_columns_button.setObjectName("configureColumnsButton")
        self.configure_columns_button.clicked.connect(self._on_configure_columns)
        table_controls_layout.addWidget(self.configure_columns_button)

        self.filter_button = QPushButton("Advanced Filter")
        self.filter_button.setObjectName("filterButton")
        self.filter_button.clicked.connect(self._on_filter)
        table_controls_layout.addWidget(self.filter_button)

        table_controls_layout.addStretch()  # Push buttons to the left
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
        self.main_view_scroll_area.setWidgetResizable(True)  # Important for the inner widget to resize correctly
        self.main_view_scroll_area.setWidget(self.main_view_content_widget)  # Put the content widget inside the scroll area

        self.tab_widget.addTab(self.main_view_scroll_area, "Main View")  # Add the scroll area to the tab

        self.history_tab_content = QWidget()
        history_layout = QVBoxLayout(self.history_tab_content)

        # History controls
        history_controls_layout = QHBoxLayout()

        # Search/filter box
        self.history_search_box = QLineEdit()
        self.history_search_box.setPlaceholderText("Search history...")
        self.history_search_box.textChanged.connect(self._filter_history)
        history_controls_layout.addWidget(QLabel("Search:"))
        history_controls_layout.addWidget(self.history_search_box)

        # Sort dropdown
        self.history_sort_combo = QComboBox()
        self.history_sort_combo.addItems(["Sort by Book ID", "Sort by Title", "Sort by Date (Newest First)"])
        self.history_sort_combo.currentTextChanged.connect(self._sort_history)
        history_controls_layout.addWidget(self.history_sort_combo)

        # Clear history button
        self.clear_history_button = QPushButton("Clear History")
        self.clear_history_button.clicked.connect(self._clear_history)
        history_controls_layout.addWidget(self.clear_history_button)

        history_controls_layout.addStretch()
        history_layout.addLayout(history_controls_layout)

        # History list
        self.history_list = QTableWidget()
        self.history_list.setColumnCount(3)
        self.history_list.setHorizontalHeaderLabels(["Book ID", "Title", "Date Searched"])
        self.history_list.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history_list.horizontalHeader().setStretchLastSection(True)
        self.history_list.itemDoubleClicked.connect(self._on_history_item_double_clicked)
        history_layout.addWidget(self.history_list)

        # Instructions
        history_instructions = QLabel("Double-click a book to search it again.")
        history_instructions.setStyleSheet("color: #888; font-style: italic;")
        history_layout.addWidget(history_instructions)

        self.tab_widget.addTab(self.history_tab_content, "History")

        # Book Mappings Tab
        self.book_mappings_scroll = QScrollArea()
        self.book_mappings_scroll.setWidgetResizable(True)
        self.book_mappings_content = QWidget()
        self.book_mappings_layout = QVBoxLayout(self.book_mappings_content)
        self.book_mappings_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.book_mappings_scroll.setWidget(self.book_mappings_content)

        # Add placeholder text
        self.book_mappings_placeholder = QLabel("Select editions from the Main View tab to display their book mappings here.")
        self.book_mappings_placeholder.setStyleSheet("color: #888; font-style: italic; margin: 20px;")
        self.book_mappings_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.book_mappings_layout.addWidget(self.book_mappings_placeholder)

        self.tab_widget.addTab(self.book_mappings_scroll, "Book Mappings")

        # Status bar already created at the beginning of __init__
        self.status_bar.showMessage("Ready")

        self._update_token_display()

        # Load and display history
        self._populate_history_list()

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
        dialog.exec()  # Show the dialog modally

    def _handle_token_accepted(self, token: str):
        """
        Handles the token received from TokenDialog.
        Saves the token and updates the display.
        """
        if self.config_manager:
            try:
                self.config_manager.save_token(token)
                self._update_token_display()
                self.status_bar.showMessage("Token saved successfully.", 3000)
            except Exception as e:
                logger.error(f"Failed to save token: {e}")
                self.status_bar.showMessage("Error saving API token. Please try setting it again.")
        else:
            self.status_bar.showMessage("Configuration manager not available.", 3000)

    def _update_token_display(self):
        """
        Updates the token display label based on the token in ConfigManager.
        """
        if self.config_manager:
            try:
                current_token = self.config_manager.load_token()
                if current_token:  # Checks if token is not None and not an empty string
                    self.token_display_label.setText(self._format_label_text("Token: ", "*******"))
                else:
                    self.token_display_label.setText(self._format_label_text("Token: ", "Not Set"))
            except Exception as e:
                logger.error(f"Failed to load token: {e}")
                self.token_display_label.setText(self._format_label_text("Token: ", "Error Loading"))
                self.status_bar.showMessage("Error loading API token. Please try setting it again.", 3000)
        else:
            self.token_display_label.setText(self._format_label_text("Token: ", "Config Error"))

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
            if state == QValidator.State.Invalid:
                self.book_id_line_edit.blockSignals(True)  # Prevent recursion
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

        # Check if token is set
        if self.config_manager:
            try:
                token = self.config_manager.load_token()
                if not token:
                    self.status_bar.showMessage("API Bearer Token not set. Please set it via the 'Set/Update Token' button.")
                    logger.warning("Fetch Data clicked without API token set.")
                    return
            except Exception as e:
                logger.error(f"Failed to check token status: {e}")
                self.status_bar.showMessage("Error checking API token. Please try setting it again.")
                return
        else:
            self.status_bar.showMessage("Configuration error. Cannot proceed with fetch.")
            return

        # The QIntValidator ensures book_id_str is numerical if not empty.
        # We still need to convert it to an int for the ApiClient.
        try:
            book_id_int = int(book_id_str)
        except ValueError:
            # This case should ideally not be reached if QIntValidator and _on_book_id_text_changed work perfectly,
            # but as a safeguard:
            self.status_bar.showMessage("Please enter a valid numerical Book ID.")
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
                self._clear_layout(self.info_layout)  # Clear general info area
                # Don't clear editions_layout - just clear the table data
                self.editions_table_widget.setRowCount(0)  # Clear existing rows
                self.editions_table_widget.setColumnCount(0)  # Clear existing columns
                self.editions_table_widget.checked_editions.clear()  # Clear checkbox state tracking
                self.editions_data = []  # Clear edition data
                self._clear_filters()  # Clear any active filters
                self.status_bar.showMessage(f"Book data fetched successfully for ID {book_id_str}.")
                logger.info(f"Successfully fetched data for Book ID {book_id_int}: {book_data.get('title', 'N/A')}")
                logger.info(f"Complete book_data received by main.py for Book ID {book_id_int}: {book_data}")

                # Add to search history with error handling
                book_title = book_data.get('title', 'Unknown Title')
                if self.history_manager:
                    try:
                        self.history_manager.add_search(book_id_int, book_title)
                        self._populate_history_list()  # Refresh history display
                    except Exception as e:
                        logger.error(f"Failed to save search history: {e}")
                        # Non-critical error - continue with displaying the book data
                        self.status_bar.showMessage("Error saving search history.", 3000)  # Show for 3 seconds

                # Re-create and populate the General Book Information Area widgets
                # Title
                self.book_title_label = QLabel()
                self.book_title_label.setTextFormat(Qt.TextFormat.RichText)
                title_value = book_data.get('title', 'N/A')
                self.book_title_label.setText(self._format_label_text_with_na_highlight("Title: ", title_value, 'title'))
                self.book_title_label.setObjectName("bookTitleLabel")
                self.info_layout.addWidget(self.book_title_label)

                # Populate Slug
                slug_text = book_data.get('slug')
                slug_url_val = f"https://hardcover.app/books/{slug_text}" if slug_text else ""
                self.book_slug_label = ClickableLabel(self)  # Re-create after clear
                self.book_slug_label.setObjectName("bookSlugLabel")
                self.book_slug_label.setContent("Slug: ", slug_text if slug_text else "N/A", slug_url_val, field_name='slug')
                self.book_slug_label.linkActivated.connect(self._open_web_link)
                self.info_layout.addWidget(self.book_slug_label)

                # Book ID
                self.book_id_queried_label = QLabel()
                self.book_id_queried_label.setTextFormat(Qt.TextFormat.RichText)
                self.book_id_queried_label.setText(self._format_label_text_with_na_highlight("Book ID (Queried): ", str(book_id_int), 'book_id'))
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
                self.book_authors_label.setTextFormat(Qt.TextFormat.RichText)
                self.book_authors_label.setText(self._format_label_text_with_na_highlight("Authors: ", authors_display_text, 'authors'))
                self.book_authors_label.setObjectName("bookAuthorsLabel")  # Keep object name for consistency/testing
                self.info_layout.addWidget(self.book_authors_label)

                # Total Editions Count
                editions_count_raw = book_data.get('editions_count')
                editions_count_val = str(editions_count_raw) if editions_count_raw is not None else 'N/A'
                self.book_total_editions_label = QLabel()
                self.book_total_editions_label.setTextFormat(Qt.TextFormat.RichText)
                self.book_total_editions_label.setText(self._format_label_text_with_na_highlight("Total Editions: ", editions_count_val, 'total_editions'))
                self.book_total_editions_label.setObjectName("bookTotalEditionsLabel")
                self.info_layout.addWidget(self.book_total_editions_label)

                # Description with truncation and tooltip
                # Ensure full_description is a string, defaulting to "N/A" if None or missing.
                full_description_raw = book_data.get('description')
                full_description = full_description_raw if full_description_raw is not None else "N/A"
                MAX_DESC_CHARS = 500  # Define max characters for display

                if full_description != "N/A" and len(full_description) > MAX_DESC_CHARS:
                    display_desc_text = full_description[:MAX_DESC_CHARS] + "..."
                    tooltip_desc_text = full_description
                else:
                    display_desc_text = full_description
                    tooltip_desc_text = ""  # No tooltip needed if not truncated, or set full_description

                self.book_description_label = QLabel()
                self.book_description_label.setTextFormat(Qt.TextFormat.RichText)
                self.book_description_label.setText(self._format_label_text_with_na_highlight("Description: ", display_desc_text, 'description'))
                self.book_description_label.setObjectName("bookDescriptionLabel")
                self.book_description_label.setWordWrap(True)
                if tooltip_desc_text:  # Only set tooltip if it was truncated
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
                self.default_audio_label.setContent(audio_prefix, audio_value_part, audio_url, field_name='default_audio_edition')
                self.default_audio_label.linkActivated.connect(self._open_web_link)
                default_editions_layout_dyn.addWidget(self.default_audio_label)

                cover_prefix, cover_value_part, cover_url_link = get_default_edition_parts(book_data.get('default_cover_edition'), "Default Cover Edition")
                self.default_cover_label_info = ClickableLabel(self)
                self.default_cover_label_info.setObjectName("defaultCoverLabelInfo")
                self.default_cover_label_info.setContent(cover_prefix, cover_value_part, cover_url_link, field_name='default_cover_edition')
                self.default_cover_label_info.linkActivated.connect(self._open_web_link)
                default_editions_layout_dyn.addWidget(self.default_cover_label_info)

                ebook_prefix, ebook_value_part, ebook_url = get_default_edition_parts(book_data.get('default_ebook_edition'), "Default E-book Edition")
                self.default_ebook_label = ClickableLabel(self)
                self.default_ebook_label.setObjectName("defaultEbookLabel")
                self.default_ebook_label.setContent(ebook_prefix, ebook_value_part, ebook_url, field_name='default_ebook_edition')
                self.default_ebook_label.linkActivated.connect(self._open_web_link)
                default_editions_layout_dyn.addWidget(self.default_ebook_label)

                physical_prefix, physical_value_part, physical_url = get_default_edition_parts(book_data.get('default_physical_edition'), "Default Physical Edition")
                self.default_physical_label = ClickableLabel(self)
                self.default_physical_label.setObjectName("defaultPhysicalLabel")
                self.default_physical_label.setContent(physical_prefix, physical_value_part, physical_url, field_name='default_physical_edition')
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
                self.book_cover_label.setTextFormat(Qt.TextFormat.RichText)
                self.book_cover_label.setText(self._format_label_text_with_na_highlight("Cover URL: ", cover_url, 'cover_url'))
                self.book_cover_label.setObjectName("bookCoverLabel")  # Keep object name
                self.info_layout.addWidget(self.book_cover_label)

                if cover_url != "N/A" and hasattr(self, 'image_downloader') and hasattr(self, 'actual_cover_display_label'):
                    pixmap = self.image_downloader.download_image(cover_url)
                    if pixmap and not pixmap.isNull():
                        self.actual_cover_display_label.setPixmap(pixmap.scaled(  # Optional scaling
                            self.actual_cover_display_label.size(),
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        ))
                    else:
                        self.actual_cover_display_label.setText("Cover not available")  # Or clear it
                else:
                    if hasattr(self, 'actual_cover_display_label'):
                        self.actual_cover_display_label.setText("Cover URL not found")  # Or clear it

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
                        "Select", "id", "score", "title", "subtitle", "Cover Image?",
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

                    # Sort editions by score (descending) before creating widgets
                    editions_sorted = sorted(editions, key=lambda x: x.get('score', 0), reverse=True)

                    # Store edition data for accordion
                    self.editions_data = editions_sorted

                    for row, edition_data in enumerate(editions_sorted):
                        col = 0

                        # Select checkbox
                        checkbox = QCheckBox()
                        checkbox.setStyleSheet("QCheckBox { margin-left: 8px; }")

                        # Block signals during setup to prevent premature firing
                        checkbox.blockSignals(True)

                        checkbox_widget = QWidget()
                        checkbox_layout = QHBoxLayout(checkbox_widget)
                        checkbox_layout.addWidget(checkbox)
                        checkbox_layout.setContentsMargins(0, 0, 0, 0)
                        checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

                        # Add widget to table first
                        self.editions_table_widget.setCellWidget(row, col, checkbox_widget)

                        # Connect checkbox to handler
                        edition_id_for_connection = edition_data.get('id', f'row_{row}')
                        print(f"DEBUG: Connecting checkbox for edition_id: {edition_id_for_connection}")
                        logger.info(f"Connecting checkbox for edition_id: {edition_id_for_connection}")

                        # Connect the signal
                        def debug_state_change(state, ed_id=edition_id_for_connection):
                            print(f"DEBUG: Raw signal fired - Edition: {ed_id}, State: {state}")
                            logger.info(f"Raw signal fired - Edition: {ed_id}, State: {state}")
                            self._on_edition_checkbox_changed(ed_id, state)

                        checkbox.stateChanged.connect(debug_state_change)

                        # Re-enable signals after setup is complete
                        checkbox.blockSignals(False)
                        col += 1

                        # id (make clickable to edition edit page)
                        edition_id = edition_data.get('id', 'N/A')
                        if edition_id != 'N/A':
                            edition_url = f"https://hardcover.app/editions/{edition_id}/edit"
                            id_label = ClickableLabel()
                            id_label.setContent("", str(edition_id), edition_url)
                            id_label.linkActivated.connect(self._open_web_link)
                            self.editions_table_widget.setCellWidget(row, col, id_label)
                        else:
                            self.editions_table_widget.setItem(row, col, QTableWidgetItem(str(edition_id)))

                        col += 1

                        # score
                        score_value = edition_data.get('score')
                        if score_value is not None:
                            score_item = NumericTableWidgetItem(str(score_value), score_value)
                        else:
                            score_item = self._create_table_item_with_na_highlight('N/A', 'score', edition_data)
                        # Store the original data index AND the book_mappings with this item
                        score_item.setData(Qt.ItemDataRole.UserRole + 1, row)  # row is the index in editions_data
                        score_item.setData(Qt.ItemDataRole.UserRole + 2, edition_data.get('book_mappings', []))  # Store mappings directly
                        self.editions_table_widget.setItem(row, col, score_item)
                        col += 1

                        # title (may be long, use truncation)
                        title_item = self._create_table_item_with_tooltip(edition_data.get('title', 'N/A'))
                        self.editions_table_widget.setItem(row, col, title_item)
                        col += 1

                        # subtitle (may be long, use truncation)
                        subtitle = edition_data.get('subtitle')
                        if subtitle:
                            subtitle_item = self._create_table_item_with_tooltip(subtitle)
                        else:
                            subtitle_item = self._create_table_item_with_na_highlight('N/A', 'subtitle', edition_data)
                            # For long fields, preserve tooltip functionality
                            if len('N/A') > 50:  # Won't happen but keep pattern
                                subtitle_item.setToolTip('N/A')
                        self.editions_table_widget.setItem(row, col, subtitle_item)
                        col += 1

                        # Cover Image?
                        image_data = edition_data.get('image')
                        has_cover = bool(image_data and image_data.get('url'))
                        self.editions_table_widget.setItem(row, col, QTableWidgetItem("Yes" if has_cover else "No"))
                        col += 1

                        # isbn_10
                        isbn_10 = edition_data.get('isbn_10')
                        if isbn_10:
                            isbn_10_item = QTableWidgetItem(isbn_10)
                        else:
                            isbn_10_item = self._create_table_item_with_na_highlight('N/A', 'isbn_10', edition_data)
                        self.editions_table_widget.setItem(row, col, isbn_10_item)
                        col += 1

                        # isbn_13
                        isbn_13 = edition_data.get('isbn_13')
                        if isbn_13:
                            isbn_13_item = QTableWidgetItem(isbn_13)
                        else:
                            isbn_13_item = self._create_table_item_with_na_highlight('N/A', 'isbn_13', edition_data)
                        self.editions_table_widget.setItem(row, col, isbn_13_item)
                        col += 1

                        # asin
                        asin = edition_data.get('asin')
                        if asin:
                            asin_item = QTableWidgetItem(asin)
                        else:
                            asin_item = self._create_table_item_with_na_highlight('N/A', 'asin', edition_data)
                        self.editions_table_widget.setItem(row, col, asin_item)
                        col += 1

                        # Reading Format (transform reading_format_id)
                        reading_format_id = edition_data.get('reading_format_id')
                        reading_format_map = {1: "Physical Book", 2: "Audiobook", 4: "E-Book"}
                        reading_format = reading_format_map.get(reading_format_id, "N/A" if reading_format_id is None else str(reading_format_id))
                        self.editions_table_widget.setItem(row, col, QTableWidgetItem(reading_format))
                        col += 1

                        # pages
                        pages_value = edition_data.get('pages')
                        if pages_value is not None:
                            pages_item = NumericTableWidgetItem(str(pages_value), pages_value)
                        else:
                            pages_item = self._create_table_item_with_na_highlight('N/A', 'pages', edition_data)
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
                            duration_item = self._create_table_item_with_na_highlight("N/A", 'duration', edition_data)
                        self.editions_table_widget.setItem(row, col, duration_item)
                        col += 1

                        # edition_format
                        edition_format = edition_data.get('edition_format')
                        if edition_format:
                            edition_format_item = QTableWidgetItem(edition_format)
                        else:
                            edition_format_item = self._create_table_item_with_na_highlight('N/A', 'edition_format', edition_data)
                        self.editions_table_widget.setItem(row, col, edition_format_item)
                        col += 1

                        # edition_information (may be long, use truncation)
                        edition_info = edition_data.get('edition_information')
                        if edition_info:
                            edition_info_item = self._create_table_item_with_tooltip(edition_info)
                        else:
                            edition_info_item = self._create_table_item_with_na_highlight('N/A', 'edition_information', edition_data)
                            # For long fields, preserve tooltip functionality
                            if len('N/A') > 50:  # Won't happen but keep pattern
                                edition_info_item.setToolTip('N/A')
                        self.editions_table_widget.setItem(row, col, edition_info_item)
                        col += 1

                        # release_date (format as MM/DD/YYYY)
                        release_date = edition_data.get('release_date')
                        if release_date:
                            try:
                                # Assuming format is YYYY-MM-DD from API
                                date_obj = datetime.strptime(release_date, '%Y-%m-%d')
                                formatted_date = date_obj.strftime('%m/%d/%Y')
                            except (ValueError, TypeError):
                                formatted_date = release_date  # Use as-is if parsing fails
                            release_date_item = QTableWidgetItem(formatted_date)
                        else:
                            release_date_item = self._create_table_item_with_na_highlight("N/A", 'release_date', edition_data)
                        self.editions_table_widget.setItem(row, col, release_date_item)
                        col += 1

                        # Publisher
                        publisher_name = edition_data.get('publisher', {}).get('name', 'N/A') if edition_data.get('publisher') else 'N/A'
                        if publisher_name != 'N/A':
                            publisher_item = QTableWidgetItem(publisher_name)
                        else:
                            publisher_item = self._create_table_item_with_na_highlight('N/A', 'publisher', edition_data)
                        self.editions_table_widget.setItem(row, col, publisher_item)
                        col += 1

                        # Language
                        language_name = edition_data.get('language', {}).get('language', 'N/A') if edition_data.get('language') else 'N/A'
                        if language_name != 'N/A':
                            language_item = QTableWidgetItem(language_name)
                        else:
                            language_item = self._create_table_item_with_na_highlight('N/A', 'language', edition_data)
                        self.editions_table_widget.setItem(row, col, language_item)
                        col += 1

                        # Country
                        country_name = edition_data.get('country', {}).get('name', 'N/A') if edition_data.get('country') else 'N/A'
                        if country_name != 'N/A':
                            country_item = QTableWidgetItem(country_name)
                        else:
                            country_item = self._create_table_item_with_na_highlight('N/A', 'country', edition_data)
                        self.editions_table_widget.setItem(row, col, country_item)
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

                    # Set initial sort indicator (data is already sorted by score descending)
                    score_column = all_headers.index("score")
                    self.editions_table_widget.column_sort_order[score_column] = Qt.SortOrder.DescendingOrder
                    self.editions_table_widget._update_header_text(score_column)

                    # Enable scrolling (should be enabled by default, but let's be explicit)
                    self.editions_table_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
                    self.editions_table_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

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
            self.status_bar.showMessage(f"Book ID {book_id_int} not found.")
            logger.warning(f"API_CLIENT_ERROR - ApiNotFoundError for Book ID {book_id_int}: {e}")
        except ApiAuthError as e:
            self.status_bar.showMessage("API Authentication Failed. Please check your Bearer Token.")
            logger.error(f"API_CLIENT_ERROR - Authentication error for Book ID {book_id_int}: {e}")
        except NetworkError as e:
            # Check if it's a rate limit error
            if hasattr(e, 'response') and e.response and e.response.status_code == 429:
                self.status_bar.showMessage("API rate limit exceeded. Please try again later.")
                logger.warning(f"API_CLIENT_ERROR - Rate limit exceeded for Book ID {book_id_int}")
            else:
                self.status_bar.showMessage("Network error. Unable to connect to Hardcover.app API. Please check your internet connection.")
                logger.error(f"API_CLIENT_ERROR - Network error for Book ID {book_id_int}: {e}")
        except ApiProcessingError as e:
            # Show detailed error dialog for unexpected API responses
            error_details = f"ApiProcessingError: {str(e)}\n\nBook ID: {book_id_int}"
            QMessageBox.critical(self, "API Error",
                                 f"An unexpected error occurred. Please copy the details below and report this issue:\n\n{error_details}")
            self.status_bar.showMessage("An unexpected API error occurred. See dialog for details.")
            logger.error(f"API_CLIENT_ERROR - Processing error for Book ID {book_id_int}: {e}")
        except ApiException as e:
            # Generic API exception
            self.status_bar.showMessage(f"API error: {e}")
            logger.error(f"API_CLIENT_ERROR - Generic API exception for Book ID {book_id_int}: {e}")
        except Exception as e:
            # Catch any other unexpected errors
            error_details = f"{type(e).__name__}: {str(e)}\n\nBook ID: {book_id_int}"
            QMessageBox.critical(self, "Unexpected Error",
                                 f"An unexpected error occurred. Please copy the details below and report this issue:\n\n{error_details}")
            self.status_bar.showMessage("An unexpected error occurred. See dialog for details.")
            logger.exception(f"Unexpected error while fetching Book ID {book_id_int}: {e}")

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

    def _format_label_text_with_na_highlight(self, label: str, value: str, field_name: str) -> str:
        """
        Format label text with N/A highlighting when appropriate.

        Args:
            label: The label text (e.g., "Title: ")
            value: The value to display
            field_name: The field identifier for N/A applicability checking

        Returns:
            HTML-formatted string with appropriate styling
        """
        from librarian_assistant.ui_utils import should_highlight_general_info_na
        from librarian_assistant.styling_constants import get_na_highlight_html

        # Check if this is an N/A value that should be highlighted
        if value == "N/A" and should_highlight_general_info_na(field_name):
            # Use highlighted N/A
            value_html = get_na_highlight_html(value)
        else:
            # Use normal styling
            value_html = f"<span style='color:#e0e0e0;'>{value}</span>"

        return f"<span style='color:#999999;'>{label}</span>{value_html}"

    def _create_table_item_with_na_highlight(self, text: str, field_name: str, edition_context: dict = None) -> QTableWidgetItem:
        """
        Create a QTableWidgetItem with N/A highlighting when appropriate.

        Args:
            text: The text to display in the cell
            field_name: The field identifier for N/A applicability checking
            edition_context: The edition data for context-aware decisions (optional)

        Returns:
            QTableWidgetItem with appropriate styling
        """
        from librarian_assistant.ui_utils import is_na_highlightable
        from librarian_assistant.styling_constants import N_A_HIGHLIGHT_TEXT_COLOR_HEX, N_A_HIGHLIGHT_BG_COLOR_HEX

        item = QTableWidgetItem(text)

        # Apply N/A highlighting if appropriate
        if text == "N/A" and is_na_highlightable(field_name, edition_context):
            # Set text color and background color for highlighting
            item.setForeground(QColor(N_A_HIGHLIGHT_TEXT_COLOR_HEX))
            item.setBackground(QColor(N_A_HIGHLIGHT_BG_COLOR_HEX))

            # Set italic font
            font = item.font()
            font.setItalic(True)
            item.setFont(font)

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
        dialog.exec()

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

        # Store all current data including checkbox states
        table_data = []
        checkbox_states = {}  # row -> checked state

        for row in range(row_count):
            row_data = {}
            # Check if this row has a checkbox
            select_widget = self.editions_table_widget.cellWidget(row, 0)  # Select column is at index 0
            if select_widget:
                checkbox = select_widget.findChild(QCheckBox)
                if checkbox:
                    checkbox_states[row] = checkbox.isChecked()

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
                if col_name == "Select":
                    # Recreate checkbox widget
                    checkbox = QCheckBox()
                    checkbox.setStyleSheet("QCheckBox { margin-left: 8px; }")
                    checkbox_widget = QWidget()
                    checkbox_layout = QHBoxLayout(checkbox_widget)
                    checkbox_layout.addWidget(checkbox)
                    checkbox_layout.setContentsMargins(0, 0, 0, 0)
                    checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

                    # Restore checkbox state
                    if row in checkbox_states:
                        checkbox.setChecked(checkbox_states[row])

                    # Get edition ID for this row
                    edition_id = None
                    if row < len(self.editions_data):
                        edition_id = self.editions_data[row].get('id', f'row_{row}')

                    # Connect checkbox to handler
                    if edition_id:
                        print(f"DEBUG: Connecting checkbox for edition_id (method 2): {edition_id}")
                        logger.info(f"Connecting checkbox for edition_id (method 2): {edition_id}")

                        # Test signal connection with a simple lambda first
                        def debug_state_change_2(state, ed_id=edition_id):
                            print(f"DEBUG: Raw signal fired (method 2) - Edition: {ed_id}, State: {state}")
                            logger.info(f"Raw signal fired (method 2) - Edition: {ed_id}, State: {state}")
                            self._on_edition_checkbox_changed(ed_id, state)

                        checkbox.stateChanged.connect(debug_state_change_2)

                    self.editions_table_widget.setCellWidget(row, col, checkbox_widget)
                else:
                    value = row_data.get(col_name, "N/A")
                    # Check if this was a numeric column
                    if col_name == "score" or col_name == "pages":
                        try:
                            numeric_value = float(value) if value != "N/A" else None
                            item = NumericTableWidgetItem(value, numeric_value)
                        except (ValueError, TypeError):
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
                        except (ValueError, IndexError, TypeError):
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

    def _on_filter(self):
        """Show the filter dialog and apply filters."""
        # Only allow filtering if we have data
        if not self.all_column_names:
            self.status_bar.showMessage("No data loaded. Fetch book data first.", 3000)
            return

        # Create dialog with visible columns
        dialog = FilterDialog(self.visible_column_names, self)

        # Connect to filter signal
        dialog.filters_applied.connect(self._apply_filters)

        # Show dialog
        dialog.exec()

    def _apply_filters(self, filters, logic_mode):
        """
        Apply filters to the table.

        Args:
            filters: List of filter dictionaries
            logic_mode: 'AND' or 'OR'
        """
        # Store active filters
        self.active_filters = filters
        self.filter_logic_mode = logic_mode

        # Apply filters to table
        hidden_count = 0
        total_rows = self.editions_table_widget.rowCount()

        for row in range(total_rows):
            # Check if row matches filters
            row_visible = self._row_matches_filters(row, filters, logic_mode)

            # Show/hide row
            self.editions_table_widget.setRowHidden(row, not row_visible)

            if not row_visible:
                hidden_count += 1

        # Update status
        visible_count = total_rows - hidden_count
        if hidden_count > 0:
            self.status_bar.showMessage(
                f"Filter applied: {visible_count} editions shown, {hidden_count} hidden.",
                5000
            )
        else:
            self.status_bar.showMessage("Filter applied: All editions match.", 3000)

    def _row_matches_filters(self, row, filters, logic_mode):
        """
        Check if a row matches the given filters.

        Args:
            row: Row index
            filters: List of filter dictionaries
            logic_mode: 'AND' or 'OR'

        Returns:
            bool: True if row matches filters
        """
        if not filters:
            return True

        results = []

        for filter_data in filters:
            column_name = filter_data['column']
            operator = filter_data['operator']
            filter_value = filter_data['value']

            # Find column index
            col_index = None
            for col in range(self.editions_table_widget.columnCount()):
                header = self.editions_table_widget.horizontalHeaderItem(col)
                if header and header.text().replace(" ▲", "").replace(" ▼", "") == column_name:
                    col_index = col
                    break

            if col_index is None:
                continue

            # Get cell value
            item = self.editions_table_widget.item(row, col_index)
            cell_value = item.text() if item else ""

            # Apply operator
            match = self._apply_filter_operator(cell_value, operator, filter_value, column_name)
            results.append(match)

        # Combine results based on logic mode
        if logic_mode == 'AND':
            return all(results) if results else True
        else:  # OR
            return any(results) if results else False

    def _apply_filter_operator(self, cell_value, operator, filter_value, column_name):  # pylint: disable=unused-argument
        """
        Apply a filter operator to a cell value.

        Args:
            cell_value: The value in the cell
            operator: The filter operator
            filter_value: The filter value to compare against
            column_name: The column name for type-specific handling

        Returns:
            bool: True if the filter matches
        """
        # Handle N/A values
        if cell_value == "N/A":
            return operator in ['Is N/A', 'Is empty', 'Is not empty']

        # Text operators
        if operator == 'Contains':
            return filter_value.lower() in cell_value.lower()
        elif operator == 'Does not contain':
            return filter_value.lower() not in cell_value.lower()
        elif operator == 'Equals':
            return cell_value.lower() == filter_value.lower()
        elif operator == 'Does not equal':
            return cell_value.lower() != filter_value.lower()
        elif operator == 'Starts with':
            return cell_value.lower().startswith(filter_value.lower())
        elif operator == 'Ends with':
            return cell_value.lower().endswith(filter_value.lower())
        elif operator == 'Is empty':
            return cell_value == "" or cell_value == "N/A"
        elif operator == 'Is not empty':
            return cell_value != "" and cell_value != "N/A"

        # Numeric operators
        elif operator in ['=', '≠', '>', '>=', '<', '<=']:
            try:
                cell_num = float(cell_value)
                filter_num = float(filter_value)

                if operator == '=':
                    return cell_num == filter_num
                elif operator == '≠':
                    return cell_num != filter_num
                elif operator == '>':
                    return cell_num > filter_num
                elif operator == '>=':
                    return cell_num >= filter_num
                elif operator == '<':
                    return cell_num < filter_num
                elif operator == '<=':
                    return cell_num <= filter_num
            except ValueError:
                return False

        # Date operators
        elif operator in ['Is on', 'Is before', 'Is after', 'Is between']:
            try:
                # Convert MM/DD/YYYY to comparable format
                from datetime import datetime
                cell_date = datetime.strptime(cell_value, '%m/%d/%Y')

                if operator == 'Is between' and isinstance(filter_value, dict):
                    start_date = datetime.strptime(filter_value['start'], '%Y-%m-%d')
                    end_date = datetime.strptime(filter_value['end'], '%Y-%m-%d')
                    return start_date <= cell_date <= end_date
                else:
                    filter_date = datetime.strptime(filter_value, '%Y-%m-%d')

                    if operator == 'Is on':
                        return cell_date.date() == filter_date.date()
                    elif operator == 'Is before':
                        return cell_date < filter_date
                    elif operator == 'Is after':
                        return cell_date > filter_date
            except ValueError:
                return False

        # Special operators
        elif operator == 'Is "Yes"':
            return cell_value == "Yes"
        elif operator == 'Is "No"':
            return cell_value == "No"
        elif operator == 'Is N/A':
            return cell_value == "N/A"
        elif operator == 'Is not N/A':
            return cell_value != "N/A"
        elif operator == 'Is':
            return cell_value == filter_value
        elif operator == 'Is not':
            return cell_value != filter_value

        return False

    def _clear_filters(self):
        """Clear all active filters."""
        self.active_filters = []
        self.filter_logic_mode = 'AND'

        # Show all rows
        for row in range(self.editions_table_widget.rowCount()):
            self.editions_table_widget.setRowHidden(row, False)

        self.status_bar.showMessage("Filters cleared.", 3000)

    def _filter_history(self, search_text: str):  # pylint: disable=unused-argument
        """Filter history items based on search text."""
        if self.history_manager:
            try:
                filtered_entries = self.history_manager.search_history(search_text)
                self._display_history_entries(filtered_entries)
            except Exception as e:
                logger.error(f"Failed to filter history: {e}")
                self.status_bar.showMessage("Error filtering search history.", 3000)

    def _sort_history(self, sort_by: str):  # pylint: disable=unused-argument
        """Sort history items by the specified field."""
        # Map combo box text to sort criteria
        if "Book ID" in sort_by:
            sorted_entries = self.history_manager.sort_history('book_id')
        elif "Title" in sort_by:
            sorted_entries = self.history_manager.sort_history('title')
        else:  # Date (Newest First)
            sorted_entries = self.history_manager.sort_history('date')

        # Apply current search filter if any
        search_text = self.history_search_box.text()
        if search_text:
            sorted_entries = [entry for entry in sorted_entries
                              if search_text.lower() in str(entry['book_id']) or
                              search_text.lower() in entry['book_title'].lower()]

        self._display_history_entries(sorted_entries)

    def _populate_history_list(self):
        """Populate the history list widget with saved searches."""
        if self.history_manager:
            try:
                history_entries = self.history_manager.get_history()
                self._display_history_entries(history_entries)
            except Exception as e:
                logger.error(f"Failed to load history: {e}")
                self.status_bar.showMessage("Error loading search history.", 3000)
                # Display empty list on error
                self._display_history_entries([])

    def _clear_history(self):
        """Clear all search history."""
        if self.history_manager:
            try:
                self.history_manager.clear_history()
                self._populate_history_list()
                self.status_bar.showMessage("Search history cleared.", 3000)
            except Exception as e:
                logger.error(f"Failed to clear history: {e}")
                self.status_bar.showMessage("Error clearing search history.", 3000)

    def _on_history_item_clicked(self, item):  # pylint: disable=unused-argument
        """Handle clicking on a history item to re-fetch that book."""
        # Implementation placeholder for history item clicks
        pass

    def _on_history_item_double_clicked(self, item):  # pylint: disable=unused-argument
        """Handle double-clicking on a history item to re-fetch that book."""
        row = item.row()
        book_id_item = self.history_list.item(row, 0)
        if book_id_item:
            book_id = book_id_item.text()
            # Switch to main tab
            self.tab_widget.setCurrentIndex(0)
            # Set the book ID in the input field
            self.book_id_line_edit.setText(book_id)
            # Trigger the fetch
            self._on_fetch_data_clicked()

    def _display_history_entries(self, entries: list):
        """Display the given history entries in the history table."""
        self.history_list.setRowCount(len(entries))

        for row, entry in enumerate(entries):
            # Book ID
            book_id_item = QTableWidgetItem(str(entry['book_id']))
            book_id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.history_list.setItem(row, 0, book_id_item)

            # Title
            title_item = QTableWidgetItem(entry['book_title'])
            self.history_list.setItem(row, 1, title_item)

            # Date
            try:
                # Parse ISO format and display in readable format
                search_time = datetime.fromisoformat(entry['search_time'])
                date_str = search_time.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, KeyError):
                date_str = "Unknown"
            date_item = QTableWidgetItem(date_str)
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.history_list.setItem(row, 2, date_item)

    def _on_edition_checkbox_changed(self, edition_id, state):
        """Handle checkbox state change for an edition."""
        print(f"DEBUG: Checkbox changed - Edition ID: {edition_id}, State: {state}")
        logger.info(f"Checkbox changed - Edition ID: {edition_id}, State: {state}")

        if state == Qt.CheckState.Checked or state == 2:  # Handle both enum and int values
            self.editions_table_widget.checked_editions.add(edition_id)
            print(f"DEBUG: Added {edition_id} to checked_editions")
            logger.info(f"Added {edition_id} to checked_editions")
        else:
            self.editions_table_widget.checked_editions.discard(edition_id)
            print(f"DEBUG: Removed {edition_id} from checked_editions")
            logger.info(f"Removed {edition_id} from checked_editions")

        print(f"DEBUG: Current checked_editions: {self.editions_table_widget.checked_editions}")
        logger.info(f"Current checked_editions: {self.editions_table_widget.checked_editions}")

        # Update the Book Mappings tab
        self._update_book_mappings_tab()

    def _update_book_mappings_tab(self):
        """Update the Book Mappings tab based on checked editions."""
        print("DEBUG: _update_book_mappings_tab called")
        logger.info("_update_book_mappings_tab called")

        # Clear existing content
        while self.book_mappings_layout.count():
            child = self.book_mappings_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Get checked edition IDs
        checked_ids = getattr(self.editions_table_widget, 'checked_editions', set())
        print(f"DEBUG: Retrieved checked_ids: {checked_ids}")
        print(f"DEBUG: editions_data length: {len(getattr(self, 'editions_data', []))}")
        logger.info(f"Retrieved checked_ids: {checked_ids}")
        logger.info(f"editions_data length: {len(getattr(self, 'editions_data', []))}")

        if not checked_ids:
            # Show placeholder
            self.book_mappings_placeholder = QLabel("Select editions from the Main View tab to display their book mappings here.")
            self.book_mappings_placeholder.setStyleSheet("color: #888; font-style: italic; margin: 20px;")
            self.book_mappings_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.book_mappings_layout.addWidget(self.book_mappings_placeholder)
            return

        # Create cards for each checked edition
        for edition_id in checked_ids:
            # Find the edition data
            edition_data = None
            for ed in self.editions_data:
                if str(ed.get('id', '')) == str(edition_id) or edition_id == f"row_{self.editions_data.index(ed)}":
                    edition_data = ed
                    break

            if not edition_data:
                continue

            # Create card widget
            card = QGroupBox()
            card.setStyleSheet("""
                QGroupBox {
                    background-color: #242424;
                    border: 1px solid #3d3d3d;
                    border-radius: 8px;
                    margin: 10px;
                    padding: 15px;
                }
            """)
            card_layout = QVBoxLayout(card)

            # Create title with edition info
            book_id = edition_data.get('id', 'N/A')
            isbn_10 = edition_data.get('isbn_10', 'N/A')
            isbn_13 = edition_data.get('isbn_13', 'N/A')
            asin = edition_data.get('asin', 'N/A')

            # Get reading format
            reading_format_id = edition_data.get('reading_format_id')
            reading_format_map = {1: "Physical", 2: "Audiobook", 4: "E-Book"}
            reading_format = reading_format_map.get(reading_format_id, "Unknown")

            title_text = f"Book ID: {book_id} | ISBN-10: {isbn_10} | ISBN-13: {isbn_13} | ASIN: {asin} | Format: {reading_format}"
            title_label = QLabel(title_text)
            title_label.setStyleSheet("""
                font-weight: bold;
                font-size: 14px;
                color: #ffffff;
                margin-bottom: 10px;
            """)
            title_label.setWordWrap(True)
            card_layout.addWidget(title_label)

            # Add book mappings
            book_mappings = edition_data.get('book_mappings', [])
            if book_mappings:
                mappings_label = QLabel("Book Mappings:")
                mappings_label.setStyleSheet("font-weight: bold; margin-top: 5px;")
                card_layout.addWidget(mappings_label)

                for mapping in book_mappings:
                    platform_data = mapping.get('platform')
                    external_id = mapping.get('external_id')

                    if platform_data and external_id:
                        # Extract platform name from dict
                        platform_name = platform_data.get('name', 'Unknown') if isinstance(platform_data, dict) else str(platform_data)

                        # Create clickable link
                        link_label = ClickableLabel()
                        url = self._get_external_url(platform_name, external_id)
                        link_label.setContent("", f"{platform_name}: {external_id}", url)
                        link_label.linkActivated.connect(self._open_web_link)
                        card_layout.addWidget(link_label)
            else:
                no_mappings_label = QLabel("No book mappings available")
                no_mappings_label.setStyleSheet("color: #888; font-style: italic;")
                card_layout.addWidget(no_mappings_label)

            self.book_mappings_layout.addWidget(card)

        # Add stretch to push cards to top
        self.book_mappings_layout.addStretch()

        # Ensure the scroll area properly refreshes the content
        self.book_mappings_scroll.setWidget(self.book_mappings_content)

    def _get_external_url(self, platform, external_id):
        """Get the external URL for a given platform and ID."""
        # Platform URL mappings from the accordion implementation
        platform_urls = {
            'goodreads': f'https://www.goodreads.com/book/show/{external_id}',
            'openlibrary': f'https://openlibrary.org{external_id}' if external_id.startswith('/') else f'https://openlibrary.org/books/{external_id}',
            'googlebooks': f'https://books.google.com/books?id={external_id}',
            'bookshop': f'https://bookshop.org/books/{external_id}',
            'amazon': f'https://www.amazon.com/dp/{external_id}',
            'bookdepository': f'https://www.bookdepository.com/book/{external_id}',
            'indiebound': f'https://www.indiebound.org/book/{external_id}',
            'audible': f'https://www.audible.com/pd/{external_id}',
            'kobo': f'https://www.kobo.com/ebook/{external_id}',
            'scribd': f'https://www.scribd.com/book/{external_id}',
            'librarything': f'https://www.librarything.com/work/{external_id}',
            'storygraph': f'https://app.thestorygraph.com/books/{external_id}',
            'bookwyrm': f'https://bookwyrm.social/book/{external_id}',
            'wikidata': f'https://www.wikidata.org/wiki/{external_id}',
            'wikipedia': f'https://en.wikipedia.org/wiki/{external_id}',
            'isfdb': f'https://www.isfdb.org/cgi-bin/title.cgi?{external_id}',
            'lccn': f'https://lccn.loc.gov/{external_id}',
            'oclc': f'https://www.worldcat.org/oclc/{external_id}',
            'dnb': f'https://portal.dnb.de/opac/showFullRecord?currentResultId={external_id}',
            'trove': f'https://trove.nla.gov.au/work/{external_id}',
            'jisc': f'https://discover.jisc.ac.uk/search?q={external_id}',
            'k10plus': f'https://k10plus.de/DB=2.1/PPNSET?PPN={external_id}',
        }

        platform_lower = platform.lower()
        if platform_lower in platform_urls:
            return platform_urls[platform_lower]
        else:
            # Default fallback - just search for the ID
            return f'https://www.google.com/search?q={platform}+{external_id}'


def main():
    """
    Main function to initialize and run the application.
    """
    # Configure comprehensive logging
    import os
    from datetime import datetime

    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.expanduser('~'), '.librarian-assistant', 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # Log file with timestamp
    log_file = os.path.join(log_dir, f'librarian-assistant-{datetime.now().strftime("%Y%m%d")}.log')

    # Configure logging with both file and console handlers
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # Console output
        ]
    )

    # Set console handler to INFO level to reduce noise
    console_handler = logging.getLogger().handlers[1]  # Second handler is console
    console_handler.setLevel(logging.INFO)

    logger.info("Starting Librarian-Assistant application")
    logger.info(f"Log file: {log_file}")
    app = QApplication(sys.argv)

    app.setStyleSheet(ENHANCED_DARK_THEME)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
