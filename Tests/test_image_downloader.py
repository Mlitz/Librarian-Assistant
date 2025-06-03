# ABOUTME: This file contains unit tests for the ImageDownloader class.
# ABOUTME: It ensures that images can be fetched from URLs correctly.

import unittest
from unittest.mock import patch, MagicMock
from PyQt6.QtGui import QPixmap
import requests  # For mocking requests.exceptions
from librarian_assistant.image_downloader import ImageDownloader


class TestImageDownloader(unittest.TestCase):

    def test_image_downloader_can_be_instantiated(self):
        """Tests that the ImageDownloader can be instantiated."""
        # ImageDownloader is already imported at the top of the file.
        downloader = ImageDownloader()
        self.assertIsNotNone(downloader, "ImageDownloader instance should not be None.")

    @patch('librarian_assistant.image_downloader.requests.get')
    def test_download_image_success(self, mock_requests_get):
        """
        Tests that download_image successfully fetches image data and returns a QPixmap.
        """
        downloader = ImageDownloader()
        test_url = "http://example.com/test_image.png"
        # Minimal valid PNG (1x1 transparent pixel)
        fake_image_bytes = bytes.fromhex(
            "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
            "0000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = fake_image_bytes
        mock_requests_get.return_value = mock_response

        pixmap = downloader.download_image(test_url)

        self.assertIsNotNone(pixmap, "download_image should return a QPixmap on success, not None.")
        self.assertIsInstance(pixmap, QPixmap, "download_image should return an instance of QPixmap.")
        self.assertFalse(pixmap.isNull(), "The returned QPixmap should not be null for valid image data.")
        mock_requests_get.assert_called_once_with(test_url, stream=True)

    @patch('librarian_assistant.image_downloader.requests.get')
    def test_download_image_http_error(self, mock_requests_get):
        """
        Tests that download_image returns None if an HTTP error occurs.
        """
        downloader = ImageDownloader()
        test_url = "http://example.com/not_found_image.png"

        mock_response = MagicMock()
        mock_response.status_code = 404
        # Simulate raise_for_status() behavior for HTTPError
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "404 Client Error: Not Found for url", response=mock_response
        )
        mock_requests_get.return_value = mock_response

        pixmap = downloader.download_image(test_url)

        self.assertIsNone(pixmap, "download_image should return None on HTTP error.")
        mock_requests_get.assert_called_once_with(test_url, stream=True)

    @patch('librarian_assistant.image_downloader.requests.get')
    def test_download_image_network_error(self, mock_requests_get):
        """
        Tests that download_image returns None if a network error occurs.
        """
        downloader = ImageDownloader()
        test_url = "http://example.com/network_error_image.png"

        mock_requests_get.side_effect = requests.exceptions.ConnectionError("Failed to connect")

        pixmap = downloader.download_image(test_url)

        self.assertIsNone(pixmap, "download_image should return None on network error.")
        mock_requests_get.assert_called_once_with(test_url, stream=True)

    @patch('librarian_assistant.image_downloader.requests.get')
    def test_download_image_invalid_data(self, mock_requests_get):
        """
        Tests that download_image returns None if the downloaded data is not a valid image.
        """
        downloader = ImageDownloader()
        test_url = "http://example.com/invalid_image_data.txt"

        # Simulate successful download of non-image data
        fake_non_image_bytes = b"This is not an image."
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = fake_non_image_bytes
        mock_requests_get.return_value = mock_response

        pixmap = downloader.download_image(test_url)

        self.assertIsNone(pixmap, "download_image should return None for invalid image data.")
        mock_requests_get.assert_called_once_with(test_url, stream=True)

    def test_download_image_no_url(self):
        """Tests that download_image returns None if no URL is provided."""
        downloader = ImageDownloader()
        pixmap = downloader.download_image("")
        self.assertIsNone(pixmap, "download_image should return None if URL is empty.")


if __name__ == '__main__':
    unittest.main()
