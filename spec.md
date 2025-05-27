Librarian-Assistant - Developer Specification

Version: 1.0
Date: May 22, 2025
1. Project Overview
1.1. Purpose

The Hardcover.app Edition Viewer is a desktop application designed to allow users to fetch, view, and analyze book edition data from the Hardcover.app API. Users will input a Book ID to retrieve comprehensive information about a specific book and all its associated editions. The application will feature a detailed, sortable, and filterable table of editions, along with general book information and a persistent search history.
1.2. Target Platforms

The application must be a standalone Python program compatible with:

    Windows

    macOS

    Linux

2. Core Functional Requirements
2.1. API Interaction & Data Fetching

    The application will interact with the Hardcover.app GraphQL API.

    Data fetching will be initiated by the user providing a specific Book ID.

    The application will use the GraphQL query specified in Appendix A.

2.2. User Authentication (Bearer Token)

    The Hardcover.app API requires a Bearer Token for authentication.

    Users must be able to input and store their Bearer Token within the application.

    The token will be displayed in a masked format (e.g., *******) on the main UI.

    A "Set/Update Token" button will allow users to enter or modify their token via a dedicated dialog.

    The token must be stored securely on the user's local system to persist across sessions.

2.3. Main Data Display (Book Information & Editions Table)

Upon a successful API query for a Book ID, the application will display:
2.3.1. General Book Information

This section will appear at the top of the results view and include:

    Book Title: From books[0].title.

    Book Slug (Clickable): From books[0].slug. Clicking this should open https://hardcover.app/books/{slug} in the user's default web browser.

    Author(s): Derived from books[0].contributions[0].author.name. (Note: The provided query shows one top-level author; if multiple are possible here, the logic should accommodate).

    Book Description: From books[0].description.

    Book ID: The ID used for the query.

    Total Editions Count: From books[0].editions_count.

    Default Editions Information:

        For default_audio_edition, default_cover_edition, default_ebook_edition, and default_physical_edition:

            Display the edition_format (e.g., "Audiobook", "Hardcover").

            Provide a clickable link using the id of the default edition, opening https://hardcover.app/editions/{edition_id} in the user's default web browser.

2.3.2. Editions Table

A comprehensive, scrollable table displaying details for each edition found in books[0].editions.
2.4. Editions Table Features
2.4.1. Column Definitions

The table will include the following columns, derived from the editions array objects:

    id (Edition ID): Primary identifier for the edition.

    score: Numerical score. Default sort column (descending).

    title (Edition Title): Title specific to the edition.

    subtitle (Edition Subtitle): Subtitle specific to the edition. Display "N/A" if null.

    Cover Image?: Text: "Yes" if image.url is present and not null/empty; "No" otherwise.

    isbn_10: Display "N/A" if null.

    isbn_13: Display "N/A" if null.

    asin: Display "N/A" if null.

    reading_format_id (Displayed Name: Reading Format):

        1: Display "Physical Book"

        2: Display "Audiobook"

        4: Display "E-Book"

        Other/Null: Display "N/A" or the raw ID if mapping is unknown.

    pages: Numerical value. Display "N/A" if null or not applicable (e.g., for audiobooks).

    audio_seconds (Displayed Name: Duration):

        If a value exists, convert and display in HH:MM:SS format.

        Display "N/A" if null or not applicable (e.g., for physical books).

    edition_format: Text. Display "N/A" if null/empty.

    edition_information: Text. Display "N/A" if null/empty.

    release_date: Date. Format as MM/DD/YYYY. Display "N/A" if null.

    publisher { name } (Displayed Name: Publisher): Text. Display "N/A" if publisher or publisher.name is null.

    language { language } (Displayed Name: Language): Text. Display "N/A" if language or language.language is null.

    country { name } (Displayed Name: Country): Text. Display "N/A" if country or country.name is null.

2.4.2. Contributor Column Handling

    The application will dynamically manage columns for contributors based on roles present in the queried book's editions.

    Predefined Roles: Author, Illustrator, Editor, Translator, Narrator, Foreword, Cover Artist, Other (as per Appendix B).

    Column Generation: For each role, the system will prepare for up to 10 numbered columns (e.g., "Author 1", "Author 2", ..., "Author 10"; "Translator 1", ..., "Translator 10").

    Populating "Author" Columns:

        The first contributor in cached_contributors with contribution: null will populate "Author 1".

        Subsequent contributors with contribution: "Author" will populate "Author 2", "Author 3", etc.

    Populating Other Role Columns: Contributors with explicit contribution values (e.g., "Narrator", "Translator") will populate the corresponding numbered columns for that role (e.g., if an edition has three narrators, their names will appear in "Narrator 1", "Narrator 2", and "Narrator 3" for that edition's row).

    Column Visibility (Role-Level): If, for a specific queried book, none of its editions have any contributors for a particular role (e.g., no edition lists an "Illustrator"), then all 10 potential columns for that role (e.g., "Illustrator 1" through "Illustrator 10") will be hidden from the table display for that specific book's results.

    Cell Value for Missing Contributors: If a role's columns are visible, but a specific edition has fewer contributors for that role than the maximum (10), or no contributors for that role, the corresponding cells will display "N/A". (e.g., if an edition has two translators, "Translator 1" and "Translator 2" will have names, and "Translator 3" through "Translator 10" will show "N/A" for that row).

2.4.3. Row Accordion for book_mappings

    When a user clicks on any row in the editions table, an accordion-style dropdown will expand directly within or beneath that row.

    This accordion will display the book_mappings data for that specific edition.

    Presentation: List each mapping as Platform Name: External ID.

    Clickable Links: For platforms listed in Appendix C (Goodreads, LibraryThing, Openlibrary, Google Books, Storygraph, Inventaire, ABEBooks), the platform name or the entire entry should be a clickable hyperlink.

        The link destination will depend on the platform's URL structure (e.g., https://www.goodreads.com/book/show/{external_id}). This may require research for each platform. For "google", the ID is often a Google Books ID. For "AbeBooks", the external_id is often an image URL; the link should ideally go to a search page or the book page if possible.

    Handling Other Platforms: If book_mappings contains a platform not in Appendix C, it should be ignored for display in the accordion, and a warning should be logged (not shown to the user).

2.4.4. Sorting

    Users can sort the table by clicking on column headers.

    First click: Sorts ascending.

    Second click: Sorts descending.

    Third click: Clears sort for that column (or cycles back to ascending).

    A visual indicator (e.g., an arrow icon) in the column header will show the current sort column and direction.

    Default sort: by score column, descending.

2.4.5. Filtering

    An "Advanced Filter Panel" (toggleable visibility) will allow users to construct filter criteria.

    Users can add multiple filter rules. Each rule consists of:

        Column: Dropdown list of all available/visible columns.

        Operator: Dropdown list of relevant operators based on column data type.

        Value: Input field for the filter value.

    Supported Operators:

        Text Columns: Contains, Does not contain, Equals, Does not equal, Starts with, Ends with, Is empty, Is not empty.

        Numerical Columns: =, ≠, >, >=, <, <=, Is N/A, Is not N/A.

        Date Columns (release_date): Is on, Is before, Is after, Is between (requires two date inputs), Is N/A, Is not N/A.

        "Cover Image?" Column: Is "Yes", Is "No".

        "Reading Format" Column: Is (with dropdown: "Physical Book", "Audiobook", "E-Book"), Is not (with same dropdown).

    Combining Rules: Users can combine rules using "AND" or "OR" logic.

    Management: Options to remove individual filter rules or clear all filters.

2.4.6. Table Customization

    Scrolling: Horizontal and vertical scrolling for the table.

    Column Reordering: Users can drag and drop column headers to reorder columns.

    Column Resizing: Users can resize column widths.

    Text Truncation: Text within cells that exceeds the cell width should be truncated (e.g., with an ellipsis "..."). A tooltip should display the full text on hover.

    Column Visibility (User Choice): (Consideration for future enhancement, not explicitly requested for V1 but good for managing many columns).

2.5. Search History

    A dedicated "History" tab will display a list of previously searched books.

    Each entry will show: "Book ID: [ID] - Title: [Book Title]".

    Search history must persist across application sessions (stored locally).

    Clicking a history item will re-fetch and display that book's details in the "Output/Display" area.

    The history list is unlimited in size.

    An option to "Clear Search History" must be provided.

    The history list must be sortable by "Book ID" or "Book Title".

    The history list must be searchable/filterable by text contained in the ID or Title.

2.6. User Interface Navigation

    The application will use a tabbed interface for different sections:

        Main View (containing input, token management, and query results/table).

        "History" Tab.

    A "Settings" or "API Configuration" area (implicitly, the main page for token input).

3. Data Handling & Storage
3.1. API Query

    The application will use the GraphQL query provided in Appendix A.

    The query requires a $bookId variable.

3.2. Data Parsing & Transformation

    The JSON response from the API must be parsed.

    Specific transformations are required for display:

        reading_format_id to display names.

        audio_seconds to HH:MM:SS format.

        release_date to MM/DD/YYYY format.

        image.url presence to "Yes"/"No" for "Cover Image?".

        cached_contributors into multiple numbered columns per role.

        Handling of null or missing fields to display "N/A".

3.3. Local Storage

Secure local storage mechanisms appropriate for the chosen Python UI framework and OS should be used.
3.3.1. Bearer Token Storage

    The user's Bearer Token must be stored securely and encrypted if possible.

    It should persist across application sessions.

3.3.2. Search History Storage

    A list of (Book ID, Book Title) pairs.

    Must persist across sessions.

    Consider a simple format like JSON or CSV in a user-application-data directory.

4. User Interface (UI) & User Experience (UX) Design
4.1. General Layout

    Main View:

        Top area for Book ID input, "Fetch" button, masked Bearer Token display, and "Set/Update Token" button.

        Below this, the General Book Information section.

        The largest area dedicated to the Editions Table.

    Tabs: Clearly delineated tabs for "Output/Display" (or this is the main view itself) and "History".

    Filter Panel: A toggleable panel or dialog for constructing advanced filters.

    Status Bar (Recommended): A bar at the bottom of the window for transient messages like "Loading data...", "X editions found", "Filter applied".

4.2. Visual Aesthetics

    Theme: Dark theme.

    Information Density: Balanced – "a little bit of breathing room but not a lot." Avoid overly cramped or excessively spacious layouts.

    General Style: Modern, but not strictly flat. Incorporate subtle depth cues or visual hierarchy (e.g., slight shadows, borders, varying background shades for sections).

    Font: System default fonts for cross-platform consistency and readability.

4.3. Key UI Components & Behavior

    Input Fields: Standard text input.

    Buttons: Clear, clickable buttons with appropriate labels.

    Table: Highly interactive as specified (sorting, filtering, resizing, reordering, row accordion).

    Dialogs: For token input, potentially for filter panel if not an inline panel.

    Notifications/Warnings: Non-modal where possible (e.g., in status bar or inline message areas), modal only for critical errors preventing continuation.

5. Error Handling & User Feedback
5.1. General Principles

    Provide clear, user-friendly messages.

    Avoid technical jargon in user-facing errors where possible.

    Log detailed technical errors for debugging.

5.2. Specific Error Scenarios

    Invalid Book ID Format: Inline validation or message on fetch attempt: "Please enter a valid numerical Book ID."

    Book ID Not Found (API 404 or empty result): Message: "Book ID [ID] not found."

    Bearer Token Not Set: On fetch attempt: "API Bearer Token not set. Please set it via the 'Set/Update Token' button."

    Invalid/Expired/Unauthorized Token (API Auth Error): Message: "API Authentication Failed. Please check your Bearer Token and network connection."

    Network Issues (No Connection, API Unreachable): Message: "Network error. Unable to connect to Hardcover.app API. Please check your internet connection."

    API Rate Limiting: If detectable, inform the user: "API rate limit exceeded. Please try again later."

    Unexpected API Response/Internal Program Error: Message: "An unexpected error occurred. Please copy the details below and report this issue: [Detailed error message/stack trace for copying]."

    Failed Token Storage/Retrieval: Message: "Error saving/loading API token. Please try setting it again."

    Failed History Storage/Retrieval: Message: "Error saving/loading search history." (Non-critical, allow app to continue).

6. Technical Stack Considerations
6.1. Language & Core Libraries

    Language: Python (version 3.x).

    API Communication: requests or httpx library for HTTP requests. gql library or similar for GraphQL query construction and execution.

    Data Handling: Standard Python data structures, json library.

6.2. UI Framework

A cross-platform Python GUI framework is required. Options include:

    Tkinter (with ttk for modern widgets): Built-in, good for simpler UIs.

    PyQt or PySide: Powerful, feature-rich, uses Qt. Good for complex tables and custom styling. (Recommended for the table features).

    Kivy: Modern, good for touch-friendly UIs, might be overkill.

    CustomTkinter: Provides more modern-looking widgets for Tkinter.

The choice should prioritize good table widget support and styling capabilities to meet the aesthetic requirements.
7. Testing Plan
7.1. Unit Testing

    Test individual functions/methods:

        Data transformation logic (date formatting, seconds to HH:MM:SS, reading_format_id mapping).

        Contributor data parsing and column assignment logic.

        API query construction.

        Filter condition evaluation.

        Secure token storage/retrieval utilities (mocked).

        History management functions (add, clear, sort, search).

7.2. Integration Testing

    Test interactions between components:

        API call and response parsing.

        Token input, storage, and use in API calls.

        Fetching data and populating the UI (general info and table).

        Filter panel interaction with table display.

        History tab interaction with main data fetching.

        Accordion expansion and book_mappings display.

7.3. User Acceptance Testing (UAT) Scenarios

    Scenario 1: First Time Use

        Open app.

        Attempt fetch without token -> Expect error.

        Set Bearer Token.

        Enter valid Book ID -> Fetch data.

        Verify general book info and editions table populate correctly.

        Verify default sort by score.

    Scenario 2: Table Interaction

        Fetch a book with many editions and diverse data.

        Sort various columns (text, numeric, date) ascending/descending.

        Resize and reorder columns.

        Apply single and multiple filters using the filter panel (text, numeric, date, custom mapped fields).

        Verify "AND"/"OR" logic in filters.

        Clear filters.

        Expand accordion for an edition with book mappings -> Verify links and data.

        Expand accordion for an edition without book mappings.

    Scenario 3: Contributor Column Dynamics

        Fetch a book where some editions have many contributors in one role (e.g., 4 Narrators). Verify "Narrator 1-4" columns appear with data, and "Narrator 5-10" show N/A.

        Fetch a book where NO edition has an "Illustrator". Verify "Illustrator 1-10" columns are NOT shown at all.

        Fetch a book where one edition has an "Author" (contribution: null) and another explicit "Author". Verify "Author 1" and "Author 2" are populated correctly.

    Scenario 4: History Functionality

        Perform several searches.

        Go to History tab -> Verify searches are listed.

        Sort history by ID and Title.

        Search/filter history list.

        Click a history item -> Verify it re-fetches.

        Clear history.

        Close and reopen app -> Verify history persistence (before clearing) and token persistence.

    Scenario 5: Error Handling

        Enter an invalid Book ID format.

        Enter a non-existent Book ID.

        Temporarily use an invalid Bearer Token.

        Simulate network disconnection.

        (If possible) Test with an API response that has missing fields not normally null.

    Scenario 6: UI Aesthetics & Usability

        Verify dark theme is applied consistently.

        Assess readability and information density.

        Check for responsiveness of UI elements.

        Verify text truncation and tooltips.

        Verify clickable links (slug, default editions, book mappings) open in browser.

8. Future Considerations (Optional Post-V1)

    User-configurable column visibility in the editions table.

    Saving/loading table layout configurations (column order, widths, sort state).

    Export table data (CSV, Excel).

    Light/System theme option.

    Direct editing of some data fields (if Hardcover.app API supports mutations and it's a desired feature).

    Caching API responses locally for a short period to reduce API calls for recent Book IDs.

Appendix A: API GraphQL Query

query MyQuery($bookId: Int = 10) {
    books(where: {id: {_eq: $bookId}}) {
        id
        slug
        title
        subtitle
        description
        editions_count
        contributions {author {name slug}}
        editions {
            id
            score
            title
            subtitle
            image {url}
            isbn_10
            isbn_13
            asin
            cached_contributors
            reading_format_id
            pages
            audio_seconds
            edition_format
            edition_information
            release_date
            book_mappings {external_id platform {name}}
            publisher {name}
            language {language}}
        default_audio_edition {id edition_format}
        default_cover_edition {id edition_format image {url}}
        default_ebook_edition {id edition_format}
        default_physical_edition {id edition_format}}}


(Note: cached_contributors.author.cachedImage fields are not required for V1 display logic but are present in the query. The books[0].contributions field is used for the top-level book author).
Appendix B: Contributor Roles

The application should be prepared to create dynamic columns for the following roles (derived from cached_contributors.contribution or implied if contribution is null):

    Author (primary, often contribution: null)

    Illustrator

    Editor

    Translator

    Narrator

    Foreword (contributor of)

    Cover Artist

    Other

Appendix C: Book Mapping Platforms (for Accordion Links)

The accordion for book_mappings should prioritize creating clickable links for these platforms (case-insensitive matching on platform.name from API):

    Goodreads

    LibraryThing

    Openlibrary

    Google Books (API platform.name is often "google")

    Storygraph

    Inventaire

    ABEBooks (API platform.name is often "AbeBooks")

Mappings to other platforms should be logged and ignored for display. Link structures for these platforms will need to be determined.
Example:

    Goodreads: https://www.goodreads.com/book/show/{external_id}

    OpenLibrary: https://openlibrary.org{external_id} (if external_id starts with /books/)

    Google Books: https://books.google.com/books?id={external_id}

    AbeBooks: The external_id is often an image URL. A generic search might be https://www.abebooks.com/servlet/SearchResults?kn={isbn_if_available_or_title} or link to the image if direct book linking is hard.