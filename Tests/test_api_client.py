# ABOUTME: This file contains unit tests for the ApiClient class.
# ABOUTME: It ensures that the API client can be instantiated and its methods behave as expected.

import unittest
from unittest.mock import MagicMock, patch # Import patch
import requests
from librarian_assistant.exceptions import ApiNotFoundError, ApiAuthError, NetworkError, ApiProcessingError

# Attempt to import the class we're about to create.
# This will initially fail, which is part of TDD.
# from librarian_assistant.api_client import ApiClient
# from librarian_assistant.config_manager import ConfigManager

class TestApiClient(unittest.TestCase):

    def test_api_client_can_be_instantiated(self):
        """
        Tests that the ApiClient can be instantiated with a base URL and a token manager.
        """
        # We'll need to import these once the api_client.py file is created.
        # For now, the test will fail on the import of ApiClient itself.
        from librarian_assistant.api_client import ApiClient
        from librarian_assistant.config_manager import ConfigManager # Assuming ConfigManager is used

        mock_token_manager = MagicMock(spec=ConfigManager)
        base_url = "http://fakeapi.com"
        
        client = ApiClient(base_url=base_url, token_manager=mock_token_manager)
        self.assertIsNotNone(client, "ApiClient instance should not be None.")
        # We can add more assertions here later, e.g., checking if base_url is stored.

    @unittest.mock.patch('librarian_assistant.api_client.requests.post')
    def test_get_book_by_id_success(self, mock_post):
        """
        Tests that get_book_by_id successfully fetches and parses book data.
        """
        from librarian_assistant.api_client import ApiClient
        from librarian_assistant.config_manager import ConfigManager

        # Assume this is the base URL for the API
        # From Prompt 1.1 in todo.md, API_URL = "https://api.hardcover.app/v1/graphql"
        # The ApiClient's base_url should be this.
        # For this test, we'll ensure the ApiClient is initialized with it.
        # However, the ApiClient's __init__ already takes base_url.
        # The actual endpoint for GraphQL is usually the base_url itself.
        
        mock_token_manager = MagicMock(spec=ConfigManager)
        # The token loaded should now include "Bearer " as the user provides it
        mock_token_manager.load_token.return_value = "Bearer test_bearer_token"
        
        # The base_url for ApiClient should be the GraphQL endpoint
        client = ApiClient(base_url="https://api.hardcover.app/v1/graphql", token_manager=mock_token_manager)

        book_id_to_fetch = 123
        # This should match the structure of a single book object returned by the API,
        # corresponding to the fields in api_client.py's GraphQL query.
        expected_book_object_from_api = {
            "id": book_id_to_fetch, # Assuming API returns int for ID
            "slug": "test-book-title",
            "title": "Test Book Title",
            "subtitle": "An Amazing Subtitle",
            "description": "A fascinating description of the test book.",
            "editions_count": 2,
            "editions": [
                {
                    "id": 101,
                    "score": 4.5,
                    "title": "First Edition",
                    "subtitle": "Collector's Print",
                    "image": {"url": "http://example.com/ed1_cover.jpg"},
                    "isbn10": "1234567890",
                    "isbn13": "9781234567890",
                    "asin": "B00TESTASIN",
                    "cached_contributors": ["Writer: Author One (slug: author-one)", "Illustrator: Author Two (slug: author-two)"], # Mock as list of strings
                    "contributions": [
                        {"author": {"slug": "author-one", "name": "Author One"}},
                        {"author": {"slug": "author-two", "name": "Author Two"}}
                    ],
                    "reading_format_id": 1, # Physical
                    "pages": 300,
                    "audio_seconds": None,
                    "edition_format": "Hardcover",
                    "edition_information": "Special Edition",
                    # "release_date" moved to top level
                    "book_mappings": [{"external_id": "gr123", "platform": {"name": "Goodreads"}}],
                    "publisher": {"name": "Test Publisher"},
                    "language": {"name": "English"},
                    # "country" was removed in the new query
                }
            ],
            "release_date": "2023-01-01", # Moved to top level
            "default_audio_edition": {"book_id": book_id_to_fetch, "edition_format": "Audiobook"},
            "default_cover_edition": {"id": 101, "image": {"url": "http://example.com/default_cover.jpg"}}, # Updated mock
            "default_ebook_edition": {"book_id": book_id_to_fetch, "edition_format": "Ebook"},
            "default_physical_edition": {"book_id": book_id_to_fetch, "edition_format": "Hardcover"}
        }
        # The API returns a list for "books"
        expected_api_response_data = {
            "data": {"books": [expected_book_object_from_api]}
        }

        # Configure the mock for requests.post
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_api_response_data
        mock_post.return_value = mock_response

        # Call the method under test
        result = client.get_book_by_id(book_id_to_fetch)

        # Assertions
        self.assertEqual(result, expected_book_object_from_api, "The method should return the detailed book data.")

        # Verify requests.post was called correctly
        # This query should match the one in api_client.py
        spec_graphql_query = """
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
        """
        
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        
        # Check URL
        self.assertEqual(args[0], "https://api.hardcover.app/v1/graphql")
        
        # Check headers
        self.assertIn("Authorization", kwargs["headers"])
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test_bearer_token")
        self.assertIn("Content-Type", kwargs["headers"])
        self.assertEqual(kwargs["headers"]["Content-Type"], "application/json")
        
        # Check JSON payload (query and variables)
        sent_payload = kwargs["json"]
        self.assertIn("query", sent_payload)
        
        # More robust check for the query content.
        # Normalizing whitespace can help make the comparison more resilient.
        def normalize_whitespace(s):
            return " ".join(s.split())

        self.assertEqual(normalize_whitespace(sent_payload["query"]), normalize_whitespace(spec_graphql_query))
        
        self.assertEqual(sent_payload["variables"], {"bookId": book_id_to_fetch})
        
        mock_token_manager.load_token.assert_called_once()
    
    @unittest.mock.patch('librarian_assistant.api_client.requests.post')
    def test_get_book_by_id_not_found_http_404_error(self, mock_post):
        """
        Tests that get_book_by_id raises ApiNotFoundError for a 404 response.
        """
        from librarian_assistant.api_client import ApiClient
        from librarian_assistant.config_manager import ConfigManager

        mock_token_manager = MagicMock(spec=ConfigManager)
        # The token loaded should now include "Bearer "
        mock_token_manager.load_token.return_value = "Bearer test_bearer_token"
        
        client = ApiClient(base_url="https://api.hardcover.app/v1/graphql", token_manager=mock_token_manager)

        book_id_not_found = 404

        # Configure the mock for requests.post to simulate a 404 error
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Resource not found" # Example error text
        # Simulate raise_for_status() behavior for HTTPError
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "404 Client Error: Not Found for url", response=mock_response
        )
        mock_post.return_value = mock_response

        # Assert that ApiNotFoundError is raised
        with self.assertRaises(ApiNotFoundError) as context:
            client.get_book_by_id(book_id_not_found)
        
        self.assertEqual(context.exception.resource_id, book_id_not_found)
        self.assertIn(str(book_id_not_found), str(context.exception)) # Check if ID is in message
        
        mock_post.assert_called_once() # Ensure the API call was attempted
        mock_token_manager.load_token.assert_called_once()

    @unittest.mock.patch('librarian_assistant.api_client.requests.post')
    def test_get_book_by_id_not_found_empty_list(self, mock_post):
        """
        Tests ApiNotFoundError when API returns 200 OK with an empty 'books' list.
        """
        from librarian_assistant.api_client import ApiClient
        from librarian_assistant.config_manager import ConfigManager

        mock_token_manager = MagicMock(spec=ConfigManager)
        mock_token_manager.load_token.return_value = "Bearer test_bearer_token"
        client = ApiClient(base_url="https://api.hardcover.app/v1/graphql", token_manager=mock_token_manager)
        book_id_to_fetch = 404 # A different ID for this test case

        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"books": []}} # Empty list
        mock_post.return_value = mock_response

        with self.assertRaises(ApiNotFoundError) as context:
            client.get_book_by_id(book_id_to_fetch)
        self.assertEqual(f"Book ID {book_id_to_fetch} not found (API returned an empty 'books' list): ID {book_id_to_fetch}", str(context.exception))
        mock_post.assert_called_once()
        mock_token_manager.load_token.assert_called_once()

    @unittest.mock.patch('librarian_assistant.api_client.requests.post')
    def test_get_book_by_id_unexpected_structure_books_null(self, mock_post):
        """
        Tests ApiProcessingError when API returns 200 OK with 'books: null'.
        """
        from librarian_assistant.api_client import ApiClient
        from librarian_assistant.config_manager import ConfigManager

        mock_token_manager = MagicMock(spec=ConfigManager)
        mock_token_manager.load_token.return_value = "Bearer test_bearer_token"
        client = ApiClient(base_url="https://api.hardcover.app/v1/graphql", token_manager=mock_token_manager)
        book_id_to_fetch = 505 

        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"books": None}} # books is null
        mock_post.return_value = mock_response

        with self.assertRaises(ApiProcessingError) as context:
            client.get_book_by_id(book_id_to_fetch)
        # Updated to expect the more specific error message from the refined api_client.py logic
        self.assertIn(
            "API response contained 'data' but 'books' field was null or missing.",
            str(context.exception))
        mock_post.assert_called_once()
        mock_token_manager.load_token.assert_called_once()

    @unittest.mock.patch('librarian_assistant.api_client.requests.post')
    def test_get_book_by_id_auth_error(self, mock_post):
        """
        Tests that get_book_by_id raises ApiAuthError for a 401 response.
        """
        from librarian_assistant.api_client import ApiClient
        from librarian_assistant.config_manager import ConfigManager

        mock_token_manager = MagicMock(spec=ConfigManager)
        # Simulate an invalid token being loaded, as provided by the user
        mock_token_manager.load_token.return_value = "Bearer invalid_or_expired_token"
        
        client = ApiClient(base_url="https://api.hardcover.app/v1/graphql", token_manager=mock_token_manager)

        book_id_to_fetch = 789

        # Configure the mock for requests.post to simulate a 401 Unauthorized error
        mock_response = MagicMock()
        mock_response.status_code = 401 # Simulate Unauthorized
        mock_response.text = "Authentication required" # Example error text
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "401 Client Error: Unauthorized for url", response=mock_response
        )
        mock_post.return_value = mock_response

        # Assert that ApiAuthError is raised
        with self.assertRaises(ApiAuthError) as context:
            client.get_book_by_id(book_id_to_fetch)
        
        # Optionally, check the message of the raised exception if it's specific
        self.assertIn("API Authentication Error", str(context.exception))
        
        mock_post.assert_called_once() # Ensure the API call was attempted
        mock_token_manager.load_token.assert_called_once()

    @unittest.mock.patch('librarian_assistant.api_client.requests.post')
    def test_get_book_by_id_network_error(self, mock_post):
        """
        Tests that get_book_by_id raises NetworkError for a requests.exceptions.RequestException.
        """
        from librarian_assistant.api_client import ApiClient
        from librarian_assistant.config_manager import ConfigManager

        mock_token_manager = MagicMock(spec=ConfigManager)
        # The token loaded should now include "Bearer "
        mock_token_manager.load_token.return_value = "Bearer test_bearer_token"
        
        client = ApiClient(base_url="https://api.hardcover.app/v1/graphql", token_manager=mock_token_manager)

        book_id_to_fetch = 101

        # Configure the mock for requests.post to simulate a ConnectionError
        mock_post.side_effect = requests.exceptions.ConnectionError("Failed to connect")

        # Assert that NetworkError is raised
        with self.assertRaises(NetworkError) as context:
            client.get_book_by_id(book_id_to_fetch)
        
        # Optionally, check the message of the raised exception
        self.assertIn("Failed to connect", str(context.exception))
        self.assertIn("Request error", str(context.exception)) # From our current NetworkError message
        
        mock_post.assert_called_once() # Ensure the API call was attempted
        mock_token_manager.load_token.assert_called_once()

    @unittest.mock.patch('librarian_assistant.api_client.requests.post')
    def test_get_book_by_id_graphql_error_in_response(self, mock_post):
        """
        Tests that get_book_by_id raises ApiProcessingError if the 200 OK response
        contains a GraphQL 'errors' array.
        """
        from librarian_assistant.api_client import ApiClient
        from librarian_assistant.config_manager import ConfigManager

        mock_token_manager = MagicMock(spec=ConfigManager)
        # The token loaded should now include "Bearer "
        mock_token_manager.load_token.return_value = "Bearer test_bearer_token"
        
        client = ApiClient(base_url="https://api.hardcover.app/v1/graphql", token_manager=mock_token_manager)

        book_id_to_fetch = 202

        # Simulate a 200 OK response that includes a GraphQL error object
        graphql_error_response = {
            "errors": [
                {
                    "message": "Some GraphQL error occurred",
                    "locations": [{"line": 2, "column": 3}],
                    "path": ["book"]
                }
            ]
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = graphql_error_response
        # raise_for_status() should not be called or should not raise for 200
        mock_response.raise_for_status.return_value = None 
        mock_post.return_value = mock_response

        # Assert that ApiProcessingError is raised
        with self.assertRaises(ApiProcessingError) as context:
            client.get_book_by_id(book_id_to_fetch)
        
        # Optionally, check the message of the raised exception
        self.assertIn("graphql error in response", str(context.exception).lower())
        self.assertIn("Some GraphQL error occurred", str(context.exception))
        
        mock_post.assert_called_once()
        mock_token_manager.load_token.assert_called_once()

    @unittest.mock.patch('librarian_assistant.api_client.requests.post')
    def test_get_book_by_id_graphql_invalid_headers_error_raises_auth_error(self, mock_post):
        """
        Tests that get_book_by_id raises ApiAuthError if the 200 OK response
        contains a GraphQL 'errors' array with code 'invalid-headers'.
        """
        from librarian_assistant.api_client import ApiClient
        from librarian_assistant.config_manager import ConfigManager

        mock_token_manager = MagicMock(spec=ConfigManager)
        # Token is present but API deems it malformed. User provides the full string.
        mock_token_manager.load_token.return_value = "Malformed Bearer Token String" 
        
        client = ApiClient(base_url="https://api.hardcover.app/v1/graphql", token_manager=mock_token_manager)

        book_id_to_fetch = 25 # Using the ID from your example

        # Simulate a 200 OK response with a GraphQL 'invalid-headers' error
        graphql_invalid_header_error_response = {
            "errors": [
                {
                    "message": "Malformed Authorization header",
                    "extensions": {"path": "$", "code": "invalid-headers"}
                }
            ]
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = graphql_invalid_header_error_response
        mock_response.raise_for_status.return_value = None 
        mock_post.return_value = mock_response

        # Assert that ApiAuthError is raised
        with self.assertRaises(ApiAuthError) as context:
            client.get_book_by_id(book_id_to_fetch)
        
        # Check the message of the raised exception
        self.assertIn("Malformed Authorization header", str(context.exception))
        self.assertIn("Authentication failed", str(context.exception))
        
        mock_post.assert_called_once()
        mock_token_manager.load_token.assert_called_once()

    @patch('librarian_assistant.api_client.requests.post')
    def test_get_book_by_id_unexpected_structure_no_data_no_errors(self, mock_post):
        """
        Tests ApiProcessingError for unexpected response without data or errors keys.
        """
        from librarian_assistant.api_client import ApiClient
        from librarian_assistant.config_manager import ConfigManager

        mock_token_manager = MagicMock(spec=ConfigManager)
        mock_token_manager.load_token.return_value = "Bearer test_bearer_token"
        client = ApiClient(base_url="https://api.hardcover.app/v1/graphql", token_manager=mock_token_manager)
        book_id_to_fetch = 789

        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"unexpected_key": "unexpected_value"} # No 'data' or 'errors'
        mock_post.return_value = mock_response

        with self.assertRaises(ApiProcessingError) as context:
            client.get_book_by_id(book_id_to_fetch)
        self.assertIn("Unexpected API response structure: Missing 'data' and 'errors'.", str(context.exception))
        mock_post.assert_called_once()
        mock_token_manager.load_token.assert_called_once()

    @patch('librarian_assistant.api_client.requests.post') # Add mock_post to prevent actual calls
    def test_get_book_by_id_no_token_raises_auth_error(self, mock_post):
        """
        Tests that get_book_by_id raises ApiAuthError if no token is available
        before making an API call.
        """
        from librarian_assistant.api_client import ApiClient
        from librarian_assistant.config_manager import ConfigManager

        mock_token_manager = MagicMock(spec=ConfigManager)
        mock_token_manager.load_token.return_value = None # Simulate no token
        
        client = ApiClient(base_url="https://api.hardcover.app/v1/graphql", token_manager=mock_token_manager)

        book_id_to_fetch = 123

        with self.assertRaises(ApiAuthError) as context:
            client.get_book_by_id(book_id_to_fetch)
        
        self.assertIn("API token is not configured", str(context.exception))
        mock_token_manager.load_token.assert_called_once()
        mock_post.assert_not_called() # Ensure no API call was attempted

if __name__ == '__main__':
    unittest.main()