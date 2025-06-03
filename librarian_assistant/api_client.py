# ABOUTME: This file defines the ApiClient for interacting with external APIs.
# ABOUTME: It handles making requests and processing responses.

import logging
# Import custom exceptions
from .exceptions import ApiNotFoundError, ApiAuthError, NetworkError, ApiProcessingError

from .config_manager import ConfigManager  # Assuming ConfigManager will be used as token_manager
import requests  # Import the requests library

logger = logging.getLogger(__name__)


class ApiClient:
    """
    A client for interacting with an API.
    """

    def __init__(self, base_url: str, token_manager: ConfigManager):
        self.base_url = base_url
        self.token_manager = token_manager
        logger.info(f"ApiClient initialized with base_url: {self.base_url}")

    def get_book_by_id(self, book_id: int) -> dict | None:  # Changed book_id type to int
        """
        Fetches book data by ID using a GraphQL query.
        """
        token = self.token_manager.load_token()
        if not token:
            logger.error("API token is not available. Cannot fetch book data.")
            raise ApiAuthError("API token is not configured. Please set the token.")

        # GraphQL query from spec.md Appendix A
        # GraphQL query to fetch detailed book information by ID.
        graphql_query = """
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
        variables = {"bookId": book_id}
        payload = {"query": graphql_query, "variables": variables}

        headers = {
            "Authorization": token,  # Use the token directly as provided
            "Content-Type": "application/json"
        }

        logger.info(f"Fetching book ID {book_id} from {self.base_url}")

        try:
            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()  # Raises HTTPError for 4xx/5xx responses

            response_data = response.json()
            logger.info(f"Full raw API JSON response received by ApiClient for Book ID {book_id}: {response_data}")

            if "data" in response_data:
                books_list = response_data["data"].get("books")  # .get for safety
                if books_list and isinstance(books_list, list) and len(books_list) > 0:
                    # Successfully found the book, return the first item
                    return books_list[0]
                elif books_list is not None:  # books_list is an empty list
                    logger.info(f"Book ID {book_id} not found (API returned an empty 'books' list).")
                    # Use resource_id correctly and provide a descriptive prefix
                    raise ApiNotFoundError(resource_id=book_id,
                                           message_prefix=f"Book ID {book_id} not found (API returned an empty 'books' list)")
                else:  # books_list is None (key "books" was explicitly null or missing within "data")
                    logger.warning(
                        f"API response for Book ID {book_id} had 'data' field but 'books' was null or missing. "
                        f"Response data: {response_data.get('data')}"
                    )
                    raise ApiProcessingError(
                        "API response contained 'data' but 'books' field was null or missing.")

            if "errors" in response_data:  # Check for GraphQL errors if data is not in the expected structure or missing
                graphql_errors = response_data.get("errors")
                if graphql_errors and isinstance(graphql_errors, list):
                    for err in graphql_errors:
                        # Check for specific auth-related error codes or messages
                        err_extensions = err.get("extensions", {})
                        err_code = err_extensions.get("code")
                        err_message = err.get("message", "").lower()
                        if err_code == 'invalid-headers' or 'token' in err_message or 'auth' in err_message:
                            logger.error(f"Authentication error in GraphQL response for book ID {book_id}: {graphql_errors}")
                            raise ApiAuthError(f"Authentication failed: {err.get('message', 'Invalid token or headers')}")
                    # If no specific auth error identified, raise as processing error
                    first_error_message = graphql_errors[0].get("message", "Unknown GraphQL error")
                    logger.warning(f"GraphQL errors received for book ID {book_id} (raising based on first error: '{first_error_message}'): {graphql_errors}")
                    raise ApiProcessingError(f"GraphQL error in response: {first_error_message}")
                # Fallback for unexpected structure without a clear 'errors' list
                logger.error(
                    f"Unexpected API response structure for Book ID {book_id}. "
                    f"No 'data.books' or 'errors' field. Response: {response_data}"
                )
                raise ApiProcessingError("Unexpected API response structure.")

            # Fallback if "data" is not in response_data at all, and no "errors" field either.
            logger.error(f"API response for Book ID {book_id} did not contain 'data' or 'errors' field. Response: {response_data}")
            raise ApiProcessingError("Unexpected API response structure: Missing 'data' and 'errors'.")
        except requests.exceptions.HTTPError as http_err:
            # Check if the response object and status_code exist
            if http_err.response is not None and http_err.response.status_code == 404:
                logger.warning(f"Resource not found (404) for book ID {book_id}.")
                raise ApiNotFoundError(resource_id=book_id)
            elif http_err.response is not None and http_err.response.status_code in [401, 403]:
                logger.error(f"Authentication error ({http_err.response.status_code}) occurred while fetching book ID {book_id}.")
                raise ApiAuthError(f"API Authentication Error ({http_err.response.status_code})")
            else:
                logger.error(f"HTTP error occurred while fetching book ID {book_id}: {http_err} - Response: {http_err.response.text if http_err.response else 'No response text'}")
                raise NetworkError(f"HTTP error: {http_err}")  # Or a more generic ApiException
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Request exception occurred while fetching book ID {book_id}: {req_err}")
            raise NetworkError(f"Request error: {req_err}")
