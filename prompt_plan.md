\# Librarian-Assistant: Comprehensive Project Blueprint & LLM Prompts

This document outlines the phased development approach for the Librarian-Assistant application, integrating specific prompts for a code-generation LLM at each step. The development prioritizes a stable core and iterative feature additions, with a strong emphasis on Test-Driven Development (TDD) using Python and PyQt.

\#\# Phase 0: Foundation & Setup

\*\*Narrative Overview:\*\*  
This initial phase focuses on establishing the project's groundwork. It includes setting up the Python environment, initializing version control, selecting core libraries, creating the main application window with its basic structure (tabs, placeholder areas), and applying the initial dark theme styling.

\#\#\# Chunk 1: Project Setup and Basic UI Shell (Prompts 1.1 \- 1.3)

\* \*\*Goal\*\*: Create the main application window with tabs, basic layout placeholders, and initial dark theme.  
\* \*\*Focus\*\*: UI structure.

\`\`\`text  
Prompt 1.1:  
Objective: Initialize a new Python project for the "Librarian-Assistant" application.  
Details:  
1\. Create a main application script (e.g., \`main.py\`).  
2\. Set up a basic PyQt \`QMainWindow\`.  
3\. The window title should be "Librarian-Assistant \- Hardcover.app Edition Viewer".  
4\. Implement a basic dark theme stylesheet. You can use a common dark palette (e.g., dark gray background, lighter gray text). Apply this stylesheet to the application.  
5\. Ensure the application uses system default fonts as a base.  
6\. Create a placeholder test suite (e.g., using \`unittest\` or \`pytest\`) and a simple test that checks if the main window can be created.  
File Structure:  
librarian\_assistant/  
  main.py  
  tests/  
    test\_main\_window.py

Prompt 1.2:  
Objective: Implement a tabbed interface within the main window.  
Details:  
1\. Building on \`main.py\` from Prompt 1.1, add a \`QTabWidget\`.  
2\. Create two tabs:  
    \- "Main View"  
    \- "History"  
3\. For now, each tab can contain a simple \`QLabel\` indicating its name.  
4\. Ensure the dark theme applies to the tabs.  
5\. Write unit tests to verify:  
    \- The \`QTabWidget\` is present.  
    \- The correct number of tabs exists with the correct titles.  
Files: \`main.py\`, \`tests/test\_main\_window.py\`

Prompt 1.3:  
Objective: Define the layout structure for the "Main View" tab.  
Details:  
1\. In the "Main View" tab created in Prompt 1.2, set up a vertical layout.  
2\. Add placeholder areas using \`QGroupBox\` or \`QFrame\` with \`QLabel\`s for:  
    \- "API & Book ID Input Area" (top)  
    \- "General Book Information Area" (middle-top)  
    \- "Editions Table Area" (main bottom area)  
    \- "Status Bar" (at the very bottom of the main window, not just the tab).  
3\. Ensure these placeholders are distinguishable within the dark theme.  
4\. Write unit tests to verify that these placeholder areas are present in the "Main View" tab and the status bar is part of the main window.  
Files: \`main.py\`, \`tests/test\_main\_window.py\`

## **Phase 1: API Authentication & Configuration**

Narrative Overview:  
This phase deals with user authentication. It involves creating a dialog for users to input their Hardcover.app Bearer Token, implementing secure local storage for this token, displaying it in a masked format on the UI, and allowing users to set or update it. The application will also load this token on startup.

### **Chunk 2: Bearer Token Management (Prompts 2.1 \- 2.3)**

* **Goal**: Allow users to input, store securely, and display (masked) their API Bearer Token.  
* **Focus**: Secure storage, UI for token input.

Prompt 2.1:  
Objective: Create a "Set/Update Token" dialog.  
Details:  
1\. Create a new module \`token\_dialog.py\`.  
2\. Implement a \`QDialog\` subclass named \`TokenDialog\`.  
3\. The dialog should contain:  
    \- A \`QLabel\` "Enter your Hardcover.app Bearer Token:"  
    \- A \`QLineEdit\` for token input.  
    \- "OK" and "Cancel" buttons.  
4\. The "OK" button should emit a signal with the entered token.  
5\. Apply the dark theme to this dialog.  
6\. Write unit tests for \`TokenDialog\` to:  
    \- Verify all UI elements are present.  
    \- Simulate button clicks and check for signal emission with the correct token.  
File Structure:  
librarian\_assistant/  
  main.py  
  token\_dialog.py  
  tests/  
    test\_token\_dialog.py  
    test\_main\_window.py

Prompt 2.2:  
Objective: Integrate Bearer Token input and masked display in the "Main View".  
Details:  
1\. In \`main.py\`, within the "API & Book ID Input Area" (from Prompt 1.3):  
    \- Add a \`QLabel\` to display the Bearer Token in a masked format (e.g., "Token: \*\*\*\*\*\*\*"). Initially, it can show "Token: Not Set".  
    \- Add a \`QPushButton\` "Set/Update Token".  
2\. Clicking "Set/Update Token" should open the \`TokenDialog\` (from Prompt 2.1).  
3\. When the \`TokenDialog\`'s "OK" is clicked:  
    \- Create a new module \`config\_manager.py\`.  
    \- Implement a class \`ConfigManager\` in \`config\_manager.py\`.  
    \- Add methods \`save\_token(token)\` and \`load\_token()\` to \`ConfigManager\`. For now, these methods will store/retrieve the token in a simple instance variable or a temporary file for testing purposes. Do \*\*not\*\* implement secure storage yet. This will be a separate step.  
    \- The \`main.py\` will use \`ConfigManager\` to save the token.  
    \- Update the masked token display in the main view. If a token is set (e.g., length \> 0), show "Token: \*\*\*\*\*\*\*"; otherwise, "Token: Not Set".  
4\. On application startup, attempt to load the token using \`ConfigManager\` and update the display.  
5\. Write unit tests to:  
    \- Verify the token display and button are present.  
    \- Mock \`TokenDialog\` and \`ConfigManager\`.  
    \- Test that clicking "Set/Update Token" shows the dialog.  
    \- Test that after the dialog provides a token, \`ConfigManager.save\_token\` is called and the display updates.  
    \- Test that \`ConfigManager.load\_token\` is called on startup and the display reflects the loaded token state.  
Files: \`main.py\`, \`token\_dialog.py\`, \`config\_manager.py\`, \`tests/test\_main\_window.py\`, \`tests/test\_config\_manager.py\`

Prompt 2.3:  
Objective: Implement secure Bearer Token storage using the \`keyring\` library.  
Details:  
1\. Modify the \`ConfigManager\` class in \`config\_manager.py\` (from Prompt 2.2).  
2\. Import the \`keyring\` library.  
3\. Change \`save\_token(token)\` to store the token securely using \`keyring.set\_password("HardcoverApp", "BearerToken", token)\`.  
4\. Change \`load\_token()\` to retrieve the token using \`keyring.get\_password("HardcoverApp", "BearerToken")\`. It should return the token or \`None\` if not found.  
5\. Add error handling within these methods for potential \`keyring\` exceptions (e.g., if no suitable backend is found). Log errors. If saving/loading fails, the application should still function, and an error message should be prepared for display (e.g., via status bar, to be implemented later). For now, just log it.  
6\. Update unit tests for \`ConfigManager\`:  
    \- Mock the \`keyring\` library functions (\`set\_password\`, \`get\_password\`).  
    \- Test successful token saving and loading.  
    \- Test scenarios where \`keyring\` might raise an exception or return \`None\`.  
    \- Ensure the methods handle these gracefully (e.g., return \`None\` or a specific error indicator if token retrieval fails).  
Files: \`config\_manager.py\`, \`tests/test\_config\_manager.py\`  
Requirements: Add \`keyring\` to project dependencies.

## **Phase 2: Core Data Fetching & Display (General Book Information)**

Narrative Overview:  
This phase is about enabling the core functionality of fetching and displaying book data. It involves setting up the GraphQL client, implementing the Book ID input and fetch mechanism, making the actual API call (initially mocked, then live), handling basic API errors, and populating the "General Book Information" section of the UI with the retrieved data. Clickable links for the book slug and default editions will also be implemented. A status bar will provide feedback to the user.

### **Chunk 3: Basic API Interaction & Book ID Input (Prompts 3.1 \- 3.3)**

* **Goal**: Set up GraphQL query execution and Book ID input. Initially use a mocked API response.  
* **Focus**: API client structure, input handling.

Prompt 3.1:  
Objective: Implement Book ID input and "Fetch" button in the "Main View".  
Details:  
1\. In \`main.py\`, within the "API & Book ID Input Area" (from Prompt 1.3):  
    \- Add a \`QLabel\` "Book ID:".  
    \- Add a \`QLineEdit\` for users to input the Book ID. This \`QLineEdit\` should only accept numerical input.  
    \- Add a \`QPushButton\` "Fetch Data".  
2\. Write unit tests to:  
    \- Verify these UI elements are present.  
    \- Test that the \`QLineEdit\` for Book ID accepts only numbers.  
    \- Simulate clicking "Fetch Data" (for now, it can just log or print the Book ID and token status).  
Files: \`main.py\`, \`tests/test\_main\_window.py\`

Prompt 3.2:  
Objective: Create an API client service for Hardcover.app GraphQL queries.  
Details:  
1\. Create a new module \`api\_client.py\`.  
2\. Implement a class \`ApiClient\`.  
3\. The constructor should accept the API URL (e.g., \`https://hardcover.app/graphql/beta\` \- verify correct URL if possible, otherwise use this placeholder).  
4\. Implement a method \`Workspace\_book\_data(book\_id: int, bearer\_token: str)\`:  
    \- This method will construct the GraphQL query specified in Appendix A of \`spec.md\`. The query requires a \`$bookId\` variable.  
    \- It will use the \`requests\` (or \`httpx\`) library and \`gql\` library for making the GraphQL request.  
    \- Include the Bearer Token in the "Authorization" header.  
    \- For this prompt, \*\*do not make a live API call\*\*. Instead, mock the \`requests.post\` (or \`httpx.Client.post\`) call.  
    \- If \`book\_id\` is, for example, \`123\`, return a predefined successful JSON response structure similar to Appendix A (include \`books\[0\].id\`, \`title\`, \`slug\`, \`description\`, \`editions\_count\`, \`contributions\`, \`default\_...\_edition\` fields with sample data).  
    \- If \`book\_id\` is \`404\` (for testing), return a mock error indicating "not found" (e.g., an empty \`books\` list or a specific error structure your mock returns).  
    \- If \`bearer\_token\` is "invalid\_token" (for testing), simulate an authentication error.  
    \- The method should return the parsed JSON data or raise a custom exception (e.g., \`ApiException\` with a message and type) for errors. Define \`ApiException\` and specific subclasses like \`ApiAuthError\`, \`ApiNotFoundError\`, \`NetworkError\`.  
5\. Write unit tests for \`ApiClient\`:  
    \- Test successful query construction and mock response parsing for a valid \`book\_id\`.  
    \- Test "not found" scenario (e.g., \`book\_id=404\`).  
    \- Test authentication error scenario (e.g., \`bearer\_token="invalid\_token"\`).  
    \- Test a general network error scenario (mock \`requests.post\` to raise \`requests.exceptions.ConnectionError\`).  
Files: \`api\_client.py\`, \`tests/test\_api\_client.py\`  
Requirements: Add \`requests\` (or \`httpx\`) and \`gql\` to project dependencies.  
Note: The GraphQL query from Appendix A is:  
query MyQuery($bookId: Int\!) {  
  books(where: {id: {\_eq: $bookId}}) {  
    id  
    slug  
    title  
    subtitle  
    description  
    editions\_count  
    contributions { author { name } }  
    editions { id score title subtitle image { url } isbn\_10 isbn\_13 asin cached\_contributors { author { slug name } contribution } reading\_format\_id pages audio\_seconds edition\_format edition\_information release\_date book\_mappings { external\_id platform { name } } publisher { name } language { language } country { name } }  
    default\_audio\_edition { id edition\_format }  
    default\_cover\_edition { id edition\_format }  
    default\_ebook\_edition { id edition\_format }  
    default\_physical\_edition { id edition\_format }  
  }  
}

Prompt 3.3:  
Objective: Integrate \`ApiClient\` with the "Fetch Data" button and update the status bar.  
Details:  
1\. In \`main.py\`, when the "Fetch Data" button is clicked:  
    \- Retrieve the Book ID from the input field. Validate it's a number. If not, show "Please enter a valid numerical Book ID." in the status bar and do not proceed.  
    \- Retrieve the Bearer Token using \`ConfigManager.load\_token()\`.  
    \- If the token is not set, show "API Bearer Token not set. Please set it via the 'Set/Update Token' button." in the status bar and do not proceed.  
    \- Instantiate \`ApiClient\`.  
    \- Call \`api\_client.fetch\_book\_data(book\_id, token)\`.  
    \- Update the status bar:  
        \- On start of fetch: "Loading data for Book ID {book\_id}..."  
        \- On success (for now, just log the fetched data): "Successfully fetched data for Book ID {book\_id}."  
        \- On \`ApiNotFoundError\`: "Book ID {book\_id} not found."  
        \- On \`ApiAuthError\`: "API Authentication Failed. Please check your Bearer Token."  
        \- On \`NetworkError\`: "Network error. Unable to connect to Hardcover.app API."  
        \- On other \`ApiException\` or general errors: "An unexpected error occurred fetching data."  
2\. Write unit tests in \`test\_main\_window.py\`:  
    \- Mock \`ConfigManager\` and \`ApiClient\`.  
    \- Test clicking "Fetch Data" with:  
        \- Invalid Book ID format.  
        \- Token not set.  
        \- Successful API call (mock \`Workspace\_book\_data\` to return sample data).  
        \- \`ApiClient\` raising \`ApiNotFoundError\`.  
        \- \`ApiClient\` raising \`ApiAuthError\`.  
        \- \`ApiClient\` raising \`NetworkError\`.  
    \- Verify the status bar messages are updated correctly for each scenario.  
Files: \`main.py\`, \`api\_client.py\`, \`config\_manager.py\`, \`tests/test\_main\_window.py\`

### **Chunk 4: Display General Book Information (Prompts 4.1 \- 4.3)**

* **Goal**: Fetch (mocked) data for a Book ID and display the general book information section.  
* **Focus**: Data parsing and UI population for the top section.

Prompt 4.1:  
Objective: Implement UI elements to display General Book Information.  
Details:  
1\. In \`main.py\`, within the "General Book Information Area" (from Prompt 1.3), add \`QLabel\` widgets for the following fields. Each label should have a corresponding value label next to it (e.g., \`QLabel("Title:"), QLabel("Actual Title")\`).  
    \- Book Title  
    \- Book Slug (this will be made clickable later)  
    \- Author(s)  
    \- Book Description (use a \`QTextEdit\` set to read-only, allowing for scrollable multi-line text)  
    \- Book ID (queried)  
    \- Total Editions Count  
2\. Also, add a sub-section or group box for "Default Editions" with labels for:  
    \- Default Audio Edition: (format \+ ID, to be made clickable later)  
    \- Default Cover Edition: (format \+ ID, to be made clickable later)  
    \- Default E-book Edition: (format \+ ID, to be made clickable later)  
    \- Default Physical Edition: (format \+ ID, to be made clickable later)  
3\. Initialize all value labels/TextEdit to "N/A" or empty.  
4\. Write unit tests in \`test\_main\_window.py\` to verify these UI elements are created and are initially empty or show "N/A".  
Files: \`main.py\`, \`tests/test\_main\_window.py\`

Prompt 4.2:  
Objective: Populate General Book Information UI from (mocked) API response.  
Details:  
1\. In \`main.py\`, modify the successful fetch logic from Prompt 3.3.  
2\. When \`api\_client.fetch\_book\_data\` returns successfully, parse the \`books\[0\]\` object from the response.  
3\. Populate the UI elements created in Prompt 4.1:  
    \- Book Title: from \`books\[0\].title\`.  
    \- Book Slug: from \`books\[0\].slug\`.  
    \- Author(s): from \`books\[0\].contributions\[0\].author.name\`. (Assume one top-level author for now as per query structure. If \`contributions\` is empty or path is invalid, display "N/A").  
    \- Book Description: from \`books\[0\].description\`. Set this in the \`QTextEdit\`.  
    \- Book ID: The ID used for the query.  
    \- Total Editions Count: From \`books\[0\].editions\_count\`.  
4\. For Default Editions:  
    \- For \`default\_audio\_edition\`, \`default\_cover\_edition\`, \`default\_ebook\_edition\`, \`default\_physical\_edition\`:  
        \- Display \`edition\_format\` and \`id\`. E.g., "Audiobook (ID: 12345)".  
        \- If a default edition is \`null\` in the response, display "N/A".  
5\. If any field is \`null\` or missing in the response, display "N/A" in its corresponding UI element.  
6\. Write unit tests in \`test\_main\_window.py\`:  
    \- Mock \`ApiClient\` to return a structured response (as defined in Prompt 3.2).  
    \- Trigger a fetch and verify all general book information labels and the description \`QTextEdit\` are populated correctly.  
    \- Test with a mock response where some default editions are \`null\` to ensure "N/A" is displayed.  
    \- Test with a mock response where \`contributions\` is empty/null.  
Files: \`main.py\`, \`tests/test\_main\_window.py\`

Prompt 4.3:  
Objective: Make Book Slug and Default Edition IDs clickable to open web pages.  
Details:  
1\. In \`main.py\`, modify the display of:  
    \- Book Slug: Make the \`QLabel\` displaying the slug clickable. Clicking it should open \`https://hardcover.app/books/{slug}\` in the user's default web browser. Use the \`webbrowser\` module.  
    \- Default Editions: For each default edition that is not "N/A", make its display (e.g., the "(ID: 12345)" part or the whole text) clickable. Clicking it should open \`https://hardcover.app/editions/{edition\_id}\` in the user's default web browser.  
2\. To make \`QLabel\`s clickable, you can use event filters or subclass \`QLabel\`.  
3\. Update unit tests in \`test\_main\_window.py\`:  
    \- Mock the \`webbrowser.open\` function.  
    \- After populating data, simulate clicks on the slug label and default edition labels.  
    \- Verify \`webbrowser.open\` is called with the correct URLs.  
    \- Ensure clicks on "N/A" labels or non-link parts do not trigger \`webbrowser.open\`.  
Files: \`main.py\`, \`tests/test\_main\_window.py\`  
Requirements: Add \`import webbrowser\`.

## **Phase 3: Editions Table \- Basic Implementation**

Narrative Overview:  
This phase focuses on displaying the list of book editions. A table widget will be set up, and initially, static columns (non-contributor related) will be defined. Data from the API response will be parsed and transformed for display in these columns, including handling special formats for reading format IDs, audio duration, dates, and the presence of cover images. Default sorting by score and basic table customizations like scrolling and text truncation with tooltips will also be implemented.  
*(Prompts* for Phase 3 would follow a similar structure, detailing steps for table setup, static column definition, data parsing/transformation for *core fields, default sorting, and basic table customization. Each prompt would emphasize TDD.)*

## **Phase 4: Editions Table \- Contributor Columns**

Narrative Overview:  
Here, the editions table will be enhanced to dynamically display contributor information. This involves parsing contributor data from the API, dynamically generating numbered columns based on the roles present in the queried book's editions (e.g., "Author 1", "Narrator 1-10"), and correctly populating these columns. A key feature is that columns for roles not present in any edition of a book will be hidden.  
*(Prompts for Phase 4 would detail steps for contributor data parsing, dynamic column generation logic, populating these columns including specific logic for "Author" roles, handling missing contributors with "N/A", and implementing role-level column visibility. Each prompt would emphasize TDD.)*

## **Phase 5: Editions Table \- Advanced Interactivity**

Narrative Overview:  
This phase adds advanced user interaction features to the editions table. This includes multi-column sorting (ascending/descending/clear), drag-and-drop column reordering, and column resizing. A significant feature is the implementation of a row accordion, which expands to show detailed book\_mappings for an edition, including clickable links to external platforms.  
*(Prompts* for Phase 5 would cover multi-column sorting implementation, column reordering/resizing capabilities, row accordion setup *for book\_mappings, display of platform data, and creation of clickable links with research for URL structures. Each prompt would emphasize TDD.)*

## **Phase 6: Editions Table \- Filtering**

Narrative Overview:  
To allow users to refine the displayed editions, this phase introduces an advanced filtering system. A toggleable filter panel will enable users to construct multiple filter rules based on column values and various operators (for text, numbers, dates, and custom fields like "Cover Image?" or "Reading Format"). Filters can be combined with AND/OR logic.  
*(Prompts* for Phase 6 would detail the filter panel UI creation, implementation of various filter operators, the logic for applying combined filters to the table, and filter management options like removing rules or clearing all filters. Each prompt would *emphasize TDD.)*

## **Phase 7: Search History**

Narrative Overview:  
This phase implements a search history feature. Successful searches will be stored locally and displayed in a dedicated "History" tab. Users will be able to click on history items to re-fetch data, sort the history list, search/filter within it, and clear the history. Persistence across application sessions is key.  
*(Prompts for Phase 7 would cover the History tab UI, history storage mechanisms (local JSON/CSV), populating and displaying history, interaction features like re-fetching, sorting, filtering, and clearing the history. Each prompt would emphasize TDD.)*

## **Phase 8: UI/UX Refinements & Comprehensive Error Handling**

Narrative Overview:  
With core functionality in place, this phase focuses on polishing the user interface and experience. This includes ensuring the dark theme is consistently applied, balancing information density and readability, and adding subtle visual cues for a modern look. Crucially, all specified error scenarios will be handled comprehensively with user-friendly messages and robust logging.  
*(Prompts* for Phase 8 would address consistent dark theme application, layout adjustments for visual balance, implementation of all detailed error handling scenarios from the specification with user-friendly messages and logging, and refining notification *systems. Each prompt would emphasize TDD.)*

## **Phase 9: Testing & Packaging**

Narrative Overview:  
The final phase involves thorough testing and preparation for distribution. This includes a final review of unit and integration tests, conducting User Acceptance Testing (UAT) based on predefined scenarios, ensuring cross-platform compatibility (Windows, macOS, Linux), and packaging the application into standalone executables.  
\*(Prompts for Phase 9 would focus on guiding the final review of all tests, potentially setting up UAT checklists, addressing any platform-specific bugs found during cross-platform testing, and configuring tools like PyInstaller for packaging. Each prompt would