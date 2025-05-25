# ABOUTME: This file defines the ApiClient for interacting with external APIs.
# ABOUTME: It handles making requests and processing responses.

import logging
# Import custom exceptions
from .exceptions import ApiNotFoundError, ApiAuthError, NetworkError, ApiProcessingError

from .config_manager import ConfigManager # Assuming ConfigManager will be used as token_manager
import requests # Import the requests library

logger = logging.getLogger(__name__)

class ApiClient:
    """
    A client for interacting with an API.
    """
    def __init__(self, base_url: str, token_manager: ConfigManager):
        self.base_url = base_url
        self.token_manager = token_manager
        logger.info(f"ApiClient initialized with base_url: {self.base_url}")
    
    def get_book_by_id(self, book_id: int) -> dict | None: # Changed book_id type to int
        """
        Fetches book data by ID using a GraphQL query.
        """
        token = self.token_manager.load_token()
        if not token:
            logger.error("API token is not available. Cannot fetch book data.")
            # Consider raising a custom exception here in a future step
            return None

        # GraphQL query from spec.md Appendix A
        graphql_query = """
            query GetBookById($bookId: Int!) {
              book(id: $bookId) {
                id
                title
                description
                authors {
                  name
                }
                cover {
                  url
                }
                editions {
                  id
                  title
                  pageCount
                  publishedDate
                  isbn10
                  isbn13
                  language {
                    name
                  }
                  cover {
                    url
                  }
                }
                # Any other fields you might need from the 'Book' type
              }
            }
        """
        variables = {"bookId": book_id}
        payload = {"query": graphql_query, "variables": variables}
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        logger.info(f"Fetching book ID {book_id} from {self.base_url}")
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()  # Raises HTTPError for 4xx/5xx responses
            
            response_data = response.json()
            # The test expects the direct "book" dictionary.
            if "data" in response_data and "book" in response_data["data"]:
                return response_data["data"]["book"]
            else:
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
                    raise ApiProcessingError(f"GraphQL error in response: {first_error_message}")
                # Fallback for unexpected structure without a clear 'errors' list
                logger.warning(
                    f"Unexpected response structure for book ID {book_id}: {response_data}"
                )
                raise ApiProcessingError("Unexpected API response structure.")
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
                raise NetworkError(f"HTTP error: {http_err}") # Or a more generic ApiException
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Request exception occurred while fetching book ID {book_id}: {req_err}")
            raise NetworkError(f"Request error: {req_err}")