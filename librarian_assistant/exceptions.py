# ABOUTME: This file defines custom exceptions for the Librarian-Assistant application.
# ABOUTME: These exceptions help in handling specific error conditions gracefully.

class ApiException(Exception):
    """Base class for exceptions raised by the ApiClient."""
    pass

class ApiAuthError(ApiException):
    """Raised when an API authentication error occurs (e.g., invalid token)."""
    def __init__(self, message="API Authentication Error"):
        super().__init__(message)

class ApiNotFoundError(ApiException):
    """Raised when a resource is not found by the API (e.g., 404 error)."""
    def __init__(self, resource_id: str | int, message_prefix: str = "Resource not found"):
        self.resource_id = resource_id
        message = f"{message_prefix}: ID {resource_id}"
        super().__init__(message)

class NetworkError(ApiException):
    """Raised when a network-related error occurs during an API call."""
    def __init__(self, message="A network error occurred"):
        super().__init__(message)

class ApiProcessingError(ApiException):
    """Raised when there's an issue processing the API response (e.g., unexpected format)."""
    def __init__(self, message="Error processing API response"):
        super().__init__(message)