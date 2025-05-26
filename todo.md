Librarian-Assistant Project TODO List
Phase 0: Foundation & Setup
Chunk 1: Project Setup and Basic UI Shell (Prompts 1.1 - 1.3)

    [X] Prompt 1.1: Initialize Project & Main Window

        [X] Create main application script (main.py).

        [X] Set up basic PyQt QMainWindow.

        [X] Set window title: "Librarian-Assistant - Hardcover.app Edition Viewer".

        [X] Implement basic dark theme stylesheet.

        [X] Ensure system default fonts are used.

        [X] Create placeholder test suite (unittest or pytest).

        [X] Add simple test: main window creation.

    [X] Prompt 1.2: Implement Tabbed Interface

        [X] Add QTabWidget to main.py.

        [X] Create "Main View" tab.

        [X] Create "History" tab.

        [X] Add placeholder QLabel in each tab.

        [X] Ensure dark theme applies to tabs.

        [X] Unit Test: QTabWidget presence.

        [X] Unit Test: Correct number and titles of tabs.

    [X] Prompt 1.3: Define "Main View" Layout Structure

        [X] Set up vertical layout in "Main View" tab.

        [X] Add placeholder QGroupBox or QFrame for "API & Book ID Input Area".

        [X] Add placeholder for "General Book Information Area".

        [X] Add placeholder for "Editions Table Area".

        [X] Add QStatusBar to the main window.

        [X] Ensure placeholders are distinguishable in dark theme.

        [X] Unit Test: Placeholder areas present in "Main View".

        [X] Unit Test: Status bar part of main window.

Phase 1: API Authentication & Configuration
Chunk 2: Bearer Token Management (Prompts 2.1 - 2.3)

    [X] Prompt 2.1: Create "Set/Update Token" Dialog

        [X] Create token_dialog.py.

        [X] Implement TokenDialog (QDialog subclass).

        [X] Add QLabel "Enter your Hardcover.app Bearer Token:".

        [X] Add QLineEdit for token input.

        [X] Add "OK" and "Cancel" buttons.

        [X] "OK" button emits signal with token.

        [X] Apply dark theme to dialog.

        [X] Unit Test: TokenDialog UI elements present.

        [X] Unit Test: TokenDialog button clicks and signal emission.

    [X] Prompt 2.2: Integrate Token Input & Masked Display

        [X] In "API & Book ID Input Area":

            [X] Add QLabel for masked token display (e.g., "Token: *******" or "Token: Not Set").

            [X] Add QPushButton "Set/Update Token".

        [X] Clicking "Set/Update Token" opens TokenDialog.

        [X] Create config_manager.py with ConfigManager class.

        [X] Implement ConfigManager.save_token(token) (temporary storage for now).

        [X] Implement ConfigManager.load_token() (temporary storage for now).

        [X] On TokenDialog "OK", use ConfigManager to save token.

        [X] Update masked token display on main view.

        [X] On app startup, load token via ConfigManager and update display.

        [X] Unit Test: Token display and button presence.

        [X] Unit Test: Mock TokenDialog and ConfigManager.

        [X] Unit Test: "Set/Update Token" shows dialog.

        [X] Unit Test: ConfigManager.save_token called and display updates.

        [X] Unit Test: ConfigManager.load_token called on startup and display reflects state.

    [X] Prompt 2.3: Implement Secure Bearer Token Storage

        [X] Modify ConfigManager in config_manager.py.

        [X] Import keyring library.

        [X] save_token(token) uses keyring.set_password().

        [X] load_token() uses keyring.get_password().

        [X] Add error handling for keyring exceptions (log errors).

        [X] Unit Test: Mock keyring library.

        [X] Unit Test: Successful token saving and loading via mocked keyring.

        [X] Unit Test: keyring exception scenarios and graceful handling.

Phase 2: Core Data Fetching & Display (General Book Info)
Chunk 3: Basic API Interaction & Book ID Input (Prompts 3.1 - 3.3)

    [X] Prompt 3.1: Implement Book ID Input & "Fetch" Button

        [X] In "API & Book ID Input Area":

            [X] Add QLabel "Book ID:".

            [X] Add QLineEdit for Book ID (numerical input only).

            [X] Add QPushButton "Fetch Data".

        [X] Unit Test: UI elements presence.

        [X] Unit Test: Book ID QLineEdit accepts only numbers.

        [X] Unit Test: Simulate "Fetch Data" click (logging/printing for now).

    [X] Prompt 3.2: Create API Client Service

        [X] Create api_client.py with ApiClient class.

        [X] Constructor accepts API URL.

        [X] Implement fetch_book_data(book_id: int, bearer_token: str):

            [X] Construct GraphQL query from spec.md Appendix A.

            [X] Use requests/httpx and gql.

            [X] Include Bearer Token in "Authorization" header.

            [X] Mock requests.post (or httpx.Client.post).

            [X] Mock success response (e.g., book_id=123).

            [X] Mock "not found" error (e.g., book_id=404).

            [X] Mock authentication error (e.g., bearer_token="invalid_token").

            [X] Return parsed JSON or raise custom exceptions (ApiException, ApiAuthError, ApiNotFoundError, NetworkError).

        [X] Unit Test: ApiClient successful query construction & mock response parsing.

        [X] Unit Test: ApiClient "not found" scenario.

        [X] Unit Test: ApiClient authentication error scenario.

        [X] Unit Test: ApiClient general network error scenario.

    [X] Prompt 3.3: Integrate ApiClient with "Fetch Data" Button & Status Bar

        [X] On "Fetch Data" click:

            [X] Retrieve and validate Book ID (numerical). Show status bar error if invalid.

            [X] Retrieve Bearer Token via ConfigManager. Show status bar error if not set.

            [X] Instantiate ApiClient.

            [X] Call api_client.fetch_book_data(book_id, token).

            [X] Update status bar: "Loading data...", "Successfully fetched...", "Book ID not found.", "API Authentication Failed.", "Network error.", "An unexpected error occurred...".

        [X] Unit Test: Mock ConfigManager and ApiClient.

        [X] Unit Test: Click "Fetch Data" with invalid Book ID format.

        [X] Unit Test: Click "Fetch Data" with token not set.

        [X] Unit Test: Click "Fetch Data" with successful API call (mocked).

        [X] Unit Test: Click "Fetch Data" with ApiNotFoundError.

        [X] Unit Test: Click "Fetch Data" with ApiAuthError.

        [X] Unit Test: Click "Fetch Data" with NetworkError.

        [X] Unit Test: Verify status bar messages are correct for each scenario.

Chunk 4: Display General Book Information (Prompts 4.1 - 4.3)

    [x] Prompt 4.1: Implement UI Elements for General Book Information

        [x] In "General Book Information Area":

            [x] Add QLabel pairs for: Book Title, Book Slug, Author(s), Book ID (queried), Total Editions Count.

            [x] Add QTextEdit (read-only) for Book Description.

        [x] Add "Default Editions" sub-section/group box with labels for: Default Audio, Cover, E-book, Physical editions (format + ID).

        [x] Initialize all value labels/TextEdit to "N/A" or empty.

        [x] Unit Test: UI elements created and initially empty/"N/A".

    [X] Prompt 4.2: Populate General Book Information UI from API Response

        [X] On successful api_client.fetch_book_data:

            [X] Parse books[0] from response.

            [X] Populate UI: Title, Slug, Author(s) (handle empty contributions), Description, Book ID, Total Editions Count.

            [X] Populate Default Editions: edition_format and id (e.g., "Audiobook (ID: 12345)"). Display "N/A" if null.

            [X] Display "N/A" for any other null/missing fields.

        [X] Unit Test: Mock ApiClient with structured response.

        [X] Unit Test: Trigger fetch, verify all general info UI populated correctly.

        [X] Unit Test: Mock response with null default editions.

        [X] Unit Test: Mock response with empty/null contributions.

    [ ] Prompt 4.3: Make Book Slug & Default Edition IDs Clickable

        [ ] Make Book Slug QLabel clickable: opens https://hardcover.app/books/{slug}.

        [ ] Make Default Edition displays clickable (if not "N/A"): opens https://hardcover.app/editions/{edition_id}.

        [ ] Use webbrowser module.

        [ ] Use event filters or subclass QLabel for clickability.

        [ ] Unit Test: Mock webbrowser.open.

        [ ] Unit Test: Simulate clicks on slug and default edition links, verify webbrowser.open calls.

        [ ] Unit Test: Ensure clicks on "N/A" or non-link parts don't trigger webbrowser.open.

Phase 3: Editions Table - Basic Implementation

    [ ] Table Widget Setup

        [ ] Add QTableWidget to "Editions Table Area" in main.py.

    [ ] Static Column Definition (Non-Contributor Columns from spec.md 2.4.1)

        [ ] Define headers: id, score, title, subtitle, Cover Image?, isbn_10, isbn_13, asin, Reading Format, pages, Duration, edition_format, edition_information, release_date, Publisher, Language, Country.

        [ ] Set initial column headers in the QTableWidget.

    [ ] Data Parsing & Transformation (Core Fields for Table)

        [ ] When API data is fetched, iterate through books[0].editions.

        [ ] For each edition, populate a new row in the table.

        [ ] Transform reading_format_id: 1 -> "Physical Book", 2 -> "Audiobook", 4 -> "E-Book", Other/Null -> "N/A".

        [ ] Handle null values in any field by displaying "N/A".

        [ ] "Cover Image?": "Yes" if image.url is present, "No" otherwise.

        [ ] audio_seconds to HH:MM:SS format; "N/A" if null/not applicable.

        [ ] release_date to MM/DD/YYYY format; "N/A" if null.

        [ ] Populate publisher.name, language.language, country.name, handling nulls.

    [ ] Default Sorting

        [ ] Implement default sort by score column, descending, after data population.

        [ ] (May require making table items sortable, e.g. by subclassing QTableWidgetItem for numerical sort).

    [ ] Basic Table Customization

        [ ] Ensure horizontal and vertical scrolling is enabled and functional.

        [ ] Implement text truncation with ellipsis for overflowing cell content.

        [ ] Add tooltips to display full text on hover for truncated cells.

    [ ] Unit Tests for Basic Table

        [ ] Test table creation and header setup.

        [ ] Test population of table rows from mock API data.

        [ ] Test data transformations (reading format, dates, audio seconds, cover image).

        [ ] Test "N/A" display for null/missing values.

        [ ] Test default sorting by score (descending).

        [ ] Test text truncation and tooltip functionality (may require UI interaction testing or specific mocks).

Phase 4: Editions Table - Contributor Columns

    [ ] Contributor Data Parsing Logic

        [ ] Create a helper function/method to process cached_contributors for an edition.

        [ ] This function should categorize contributors by role (Author, Illustrator, etc., from spec.md Appendix B) and handle the contribution: null case for primary authors.

    [ ] Dynamic Contributor Column Header Management

        [ ] Before populating the table with new book data, clear existing contributor columns.

        [ ] Analyze all editions of the fetched book to find all unique contributor roles present.

        [ ] For each unique role found, dynamically add up to 10 numbered columns to the QTableWidget (e.g., "Author 1", "Author 2", ..., "Illustrator 1", ...).

    [ ] Populating Contributor Columns in Table

        [ ] For each edition row:

            [ ] Get its processed contributor data.

            [ ] Populate "Author" columns: first contribution: null as "Author 1", then explicit "Author" contributions.

            [ ] Populate other role columns (e.g., "Narrator 1", "Narrator 2") based on their contribution value.

            [ ] Display "N/A" in cells for which an edition has no contributor (e.g., if an edition has 1 narrator, "Narrator 2" to "Narrator 10" for that row show "N/A").

    [ ] Column Visibility (Role-Level)

        [ ] After determining unique roles for a book, if a predefined role (e.g., "Illustrator") has no contributors across any edition of that book, do not create/show the "Illustrator 1-10" columns for that specific book's results.

    [ ] Unit Tests for Contributor Columns

        [ ] Test contributor data parsing logic.

        [ ] Test dynamic column header generation based on mock data with various contributor roles.

        [ ] Test correct population of contributor cells, including "Author" logic and "N/A" for missing ones.

        [ ] Test role-level column visibility (e.g., "Illustrator" columns hidden if no illustrators).

Phase 5: Editions Table - Advanced Interactivity

    [ ] Multi-Column Sorting

        [ ] Enable sorting on all table columns by clicking headers.

        [ ] Implement cycle: ascending -> descending -> clear/default (or back to ascending).

        [ ] Add visual indicators (e.g., arrow icons) in column headers for sort state.

    [ ] Column Reordering

        [ ] Allow users to drag and drop column headers to reorder columns.

    [ ] Column Resizing

        [ ] Allow users to resize column widths.

    [ ] Row Accordion for book_mappings

        [ ] Implement accordion-style expansion on row click/selection. (This might involve inserting a new widget or expanding row height and showing details within the table structure).

        [ ] On expansion, display book_mappings data for that edition (Platform Name: External ID).

        [ ] Implement clickable links for platforms in spec.md Appendix C:

            [ ] Goodreads: https://www.goodreads.com/book/show/{external_id}

            [ ] OpenLibrary: https://openlibrary.org{external_id} (if external_id starts with /books/)

            [ ] Google Books: https://books.google.com/books?id={external_id}

            [ ] LibraryThing: (Research URL structure)

            [ ] Storygraph: (Research URL structure)

            [ ] Inventaire: (Research URL structure)

            [ ] ABEBooks: (Research URL structure - e.g., https://www.abebooks.com/servlet/SearchResults?kn={isbn_or_title} or link to image external_id)

        [ ] Log warnings for platforms not in Appendix C; ignore for display in accordion.

    [ ] Unit/Integration Tests for Advanced Interactivity

        [ ] Test multi-column sorting logic (ascending, descending, different data types).

        [ ] (Manual testing for column reordering/resizing, or complex UI tests if feasible).

        [ ] Test row accordion expansion.

        [ ] Test book_mappings display and link generation (mock webbrowser.open).

        [ ] Test handling of unknown platforms in book_mappings.

Phase 6: Editions Table - Filtering

    [ ] Filter Panel UI

        [ ] Design and implement a toggleable "Advanced Filter Panel" (e.g., a QDockWidget or a separate dialog).

        [ ] Allow adding multiple filter rules. Each rule UI:

            [ ] QComboBox for Column (populated dynamically with current table columns).

            [ ] QComboBox for Operator (populated based on selected column's data type).

            [ ] QLineEdit (or QDateEdit, etc.) for Value.

        [ ] Buttons: "Add Rule", "Remove Rule", "Clear All Filters", "Apply Filters".

        [ ] QComboBox or Radio Buttons for "Match: AND / OR".

    [ ] Operator Implementation & Filter Logic

        [ ] Implement filter logic for Text Columns: Contains, Does not contain, Equals, Does not equal, Starts with, Ends with, Is empty, Is not empty.

        [ ] Implement filter logic for Numerical Columns: =, ≠, >, >=, <, <=, Is N/A, Is not N/A.

        [ ] Implement filter logic for Date Columns (release_date): Is on, Is before, Is after, Is between (two date inputs), Is N/A, Is not N/A.

        [ ] Implement filter logic for "Cover Image?": Is "Yes", Is "No".

        [ ] Implement filter logic for "Reading Format": Is ("Physical Book", "Audiobook", "E-Book"), Is not.

        [ ] Apply combined filter rules (AND/OR) to the editions table (hide/show rows).

    [ ] Filter Management & Status

        [ ] Implement functionality for "Remove Rule" and "Clear All Filters".

        [ ] Update status bar with filter status (e.g., "Filter applied: X editions shown").

    [ ] Unit/Integration Tests for Filtering

        [ ] Test filter panel UI creation and dynamic population of column/operator dropdowns.

        [ ] Test individual filter operator logic for each data type.

        [ ] Test combining filter rules with AND/OR logic.

        [ ] Test filter application to table (mock table data and verify row visibility).

        [ ] Test filter management (remove, clear).

Phase 7: Search History

    [ ] History Tab UI

        [ ] Design layout for "History" tab:

            [ ] QListWidget or QTableWidget to display history items ("Book ID: [ID] - Title: [Book Title]").

            [ ] QLineEdit for searching/filtering history.

            [ ] Buttons/options for sorting history (by Book ID, by Title).

            [ ] QPushButton "Clear Search History".

    [ ] History Storage (history_manager.py)

        [ ] Create history_manager.py with HistoryManager class.

        [ ] Methods: add_search(book_id, book_title), get_history(), clear_history().

        [ ] Store history locally (e.g., JSON or CSV file in user-application-data directory).

        [ ] Ensure history persists across application sessions.

        [ ] Load history on application startup.

    [ ] Populating & Displaying History

        [ ] After a successful book data fetch, add (Book ID, Book Title) to history via HistoryManager.

        [ ] Display loaded/updated history in the "History" tab's list/table.

    [ ] Interacting with History

        [ ] Clicking a history item re-fetches and displays that book's details in the "Main View".

        [ ] Implement sorting of the history display by "Book ID" or "Book Title".

        [ ] Implement search/filter functionality for the history list based on text in ID or Title.

    [ ] Clear History Functionality

        [ ] Implement "Clear Search History" button action (call HistoryManager.clear_history() and update UI).

    [ ] Unit/Integration Tests for History

        [ ] Test HistoryManager methods (add, get, clear, persistence with mock file I/O).

        [ ] Test history population after successful fetch.

        [ ] Test history display and updates.

        [ ] Test clicking history item triggers re-fetch (mock main view's fetch logic).

        [ ] Test history sorting and filtering.

        [ ] Test "Clear History" functionality.

Phase 8: UI/UX Refinements & Comprehensive Error Handling

    [ ] Visual Aesthetics Review

        [ ] Ensure consistent dark theme application across all dialogs and components.

        [ ] Review information density and spacing for balance ("a little bit of breathing room but not a lot").

        [ ] Add subtle depth cues (slight shadows, borders, varying background shades) if appropriate for a "modern, but not strictly flat" look.

    [ ] Detailed Error Handling (as per spec.md 5.2)

        [ ] Invalid Book ID Format: Inline validation or message on fetch: "Please enter a valid numerical Book ID." (already partially done, review).

        [ ] Book ID Not Found (API 404 or empty result): "Book ID [ID] not found." (already partially done, review).

        [ ] Bearer Token Not Set: On fetch: "API Bearer Token not set..." (already partially done, review).

        [ ] Invalid/Expired/Unauthorized Token (API Auth Error): "API Authentication Failed..." (already partially done, review).

        [ ] Network Issues: "Network error. Unable to connect..." (already partially done, review).

        [ ] API Rate Limiting: If detectable, inform: "API rate limit exceeded. Please try again later." (Requires API to signal this).

        [ ] Unexpected API Response/Internal Program Error: "An unexpected error occurred. Please copy the details below... [Detailed error/stack trace]".

        [ ] Failed Token Storage/Retrieval (keyring issues): "Error saving/loading API token. Please try setting it again." (Log and status bar).

        [ ] Failed History Storage/Retrieval: "Error saving/loading search history." (Non-critical, allow app to continue, log and status bar).

    [ ] Notifications & User Feedback

        [ ] Ensure all user feedback (errors, status updates) is clear and user-friendly.

        [ ] Prefer non-modal notifications (status bar) where possible. Use modal dialogs only for critical errors preventing continuation.

    [ ] Logging

        [ ] Implement comprehensive logging throughout the application for debugging purposes (e.g., API requests/responses, errors, significant state changes).

Phase 9: Testing & Packaging

    [ ] Final Unit Testing Review

        [ ] Ensure all critical functions/methods have unit tests as per spec.md 7.1.

        [ ] Check test coverage if tools are available.

    [ ] Integration Testing Review

        [ ] Test interactions between major components (API-UI, filter-table, history-main view, token management) as per spec.md 7.2.

    [ ] User Acceptance Testing (UAT)

        [ ] Perform UAT based on all scenarios in spec.md 7.3.

            [ ] Scenario 1: First Time Use.

            [ ] Scenario 2: Table Interaction.

            [ ] Scenario 3: Contributor Column Dynamics.

            [ ] Scenario 4: History Functionality.

            [ ] Scenario 5: Error Handling.

            [ ] Scenario 6: UI Aesthetics & Usability.

    [ ] Cross-Platform Compatibility Testing

        [ ] Test application on Windows.

        [ ] Test application on macOS.

        [ ] Test application on Linux.

        [ ] Address any platform-specific issues.

    [ ] Packaging for Distribution

        [ ] Set up PyInstaller (or similar) for creating standalone executables.

        [ ] Configure build scripts for Windows.

        [ ] Configure build scripts for macOS.

        [ ] Configure build scripts for Linux.

        [ ] Test the packaged applications on each platform.

    [ ] Documentation

        [ ] Create a README.md with setup and usage instructions.

        [ ] (Optional) User manual or brief guide.