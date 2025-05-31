# Librarian-Assistant

A PyQt5-based desktop application for viewing and analyzing book edition data from the Hardcover.app API.

## Features

- **GraphQL API Integration**: Fetches comprehensive book and edition data from Hardcover.app
- **Bearer Token Authentication**: Secure token storage with masked display
- **Dynamic Editions Table**: 
  - Sortable columns with visual indicators
  - Advanced filtering with multiple criteria
  - Dynamic contributor columns based on book data
  - Clickable links to external platforms
- **Search History**: Persistent history with search/filter capabilities
- **Dark Theme UI**: Modern, user-friendly interface
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Installation

### From Source

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Librarian-Assistant.git
cd Librarian-Assistant
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python -m librarian_assistant.main
```

### From Executable

Download the pre-built executable for your platform from the Releases page.

## Usage

### First Time Setup

1. Launch the application
2. Click the "Set Token" button
3. Enter your Hardcover.app Bearer token
4. The token will be stored securely and displayed as masked (*******)

### Fetching Book Data

1. Enter a Book ID in the input field
2. Click "Fetch Data"
3. View the book information and editions table

### Table Features

- **Sorting**: Click column headers to cycle through ascending → descending → no sort
- **Filtering**: Click "Filter" to open the advanced filter dialog
- **Column Management**: Click "Columns" to show/hide and reorder columns
- **External Links**: Click on IDs, slugs, and platform links to open in browser

### Search History

- Switch to the "History" tab to view previous searches
- Double-click any history item to reload that book
- Use the search box to filter history
- Sort by Book ID or Title

## Building from Source

To create a standalone executable:

```bash
python build_executable.py
```

This will create platform-specific executables in the `dist` directory.

## Development

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest Tests/test_api_client.py

# Run with coverage
python -m pytest --cov=librarian_assistant
```

### Project Structure

```
Librarian-Assistant/
├── librarian_assistant/     # Main application package
│   ├── main.py             # Main window and entry point
│   ├── api_client.py       # GraphQL API client
│   ├── config_manager.py   # Token storage
│   ├── filter_dialog.py    # Advanced filtering UI
│   └── ...                 # Other modules
├── Tests/                  # Test files
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Requirements

- Python 3.8 or higher
- Internet connection for API access
- Valid Hardcover.app Bearer token

## API Token

To obtain a Bearer token:
1. Log in to your Hardcover.app account
2. Go to Settings → API
3. Generate or copy your API token

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow the TDD process outlined in CLAUDE.md
4. Ensure all tests pass
5. Commit your changes
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Acknowledgments

- Built with PyQt5
- Uses the Hardcover.app GraphQL API
- Developed using Test-Driven Development principles