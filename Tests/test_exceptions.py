# ABOUTME: Tests for custom exception classes used throughout the application
# ABOUTME: Verifies exception hierarchy, constructors, and message formatting

import pytest
from librarian_assistant.exceptions import (
    ApiException, ApiAuthError, ApiNotFoundError,
    NetworkError, ApiProcessingError
)


class TestExceptions:
    """Test custom exception classes."""

    def test_api_exception_base_class(self):
        """Test the base ApiException class."""
        # Test with default message
        exc = ApiException()
        assert str(exc) == ""

        # Test with custom message
        exc = ApiException("Custom error message")
        assert str(exc) == "Custom error message"

        # Verify it's an Exception subclass
        assert isinstance(exc, Exception)

    def test_api_auth_error(self):
        """Test ApiAuthError exception."""
        # Test with default message
        exc = ApiAuthError()
        assert str(exc) == "API Authentication Error"

        # Test with custom message
        exc = ApiAuthError("Invalid token provided")
        assert str(exc) == "Invalid token provided"

        # Verify inheritance
        assert isinstance(exc, ApiException)
        assert isinstance(exc, Exception)

    def test_api_not_found_error(self):
        """Test ApiNotFoundError exception with resource ID."""
        # Test with integer resource ID
        exc = ApiNotFoundError(resource_id=123)
        assert str(exc) == "Resource not found: ID 123"
        assert exc.resource_id == 123

        # Test with string resource ID
        exc = ApiNotFoundError(resource_id="book-slug")
        assert str(exc) == "Resource not found: ID book-slug"
        assert exc.resource_id == "book-slug"

        # Test with custom message prefix
        exc = ApiNotFoundError(resource_id=456, message_prefix="Book not found")
        assert str(exc) == "Book not found: ID 456"
        assert exc.resource_id == 456

        # Verify inheritance
        assert isinstance(exc, ApiException)

    def test_network_error(self):
        """Test NetworkError exception."""
        # Test with default message
        exc = NetworkError()
        assert str(exc) == "A network error occurred"

        # Test with custom message
        exc = NetworkError("Connection timeout")
        assert str(exc) == "Connection timeout"

        # Verify inheritance
        assert isinstance(exc, ApiException)

    def test_api_processing_error(self):
        """Test ApiProcessingError exception."""
        # Test with default message
        exc = ApiProcessingError()
        assert str(exc) == "Error processing API response"

        # Test with custom message
        exc = ApiProcessingError("Invalid JSON structure")
        assert str(exc) == "Invalid JSON structure"

        # Verify inheritance
        assert isinstance(exc, ApiException)

    def test_exception_hierarchy(self):
        """Test that all custom exceptions inherit from ApiException."""
        exceptions = [
            ApiAuthError(),
            ApiNotFoundError(resource_id=1),
            NetworkError(),
            ApiProcessingError()
        ]

        for exc in exceptions:
            assert isinstance(exc, ApiException)
            assert isinstance(exc, Exception)

    def test_exception_catching(self):
        """Test that exceptions can be caught at different levels."""
        # Test catching specific exception
        with pytest.raises(ApiAuthError):
            raise ApiAuthError("Test auth error")

        # Test catching base ApiException
        with pytest.raises(ApiException):
            raise ApiAuthError("Test auth error")

        # Test catching as generic Exception
        with pytest.raises(Exception):
            raise ApiAuthError("Test auth error")

    def test_exception_attributes(self):
        """Test that exceptions preserve their attributes."""
        # ApiNotFoundError has resource_id attribute
        exc = ApiNotFoundError(resource_id=999, message_prefix="Test")
        assert hasattr(exc, 'resource_id')
        assert exc.resource_id == 999

        # Other exceptions don't have resource_id
        exc = ApiAuthError()
        assert not hasattr(exc, 'resource_id')
