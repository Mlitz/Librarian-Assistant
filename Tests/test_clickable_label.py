# ABOUTME: This file contains unit tests for the ClickableLabel widget.
# ABOUTME: It tests clickable functionality, link activation, and non-clickable state handling.
import unittest
from unittest.mock import MagicMock
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
import sys

# Import the ClickableLabel from main
from librarian_assistant.main import ClickableLabel


class TestClickableLabel(unittest.TestCase):
    """Test cases for the ClickableLabel widget."""
    
    @classmethod
    def setUpClass(cls):
        """Create QApplication instance for all tests."""
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.label = ClickableLabel()
        self.link_activated_mock = MagicMock()
        self.label.linkActivated.connect(self.link_activated_mock)
    
    def tearDown(self):
        """Clean up after each test method."""
        self.label.deleteLater()
    
    def test_initial_state(self):
        """Test the initial state of ClickableLabel."""
        self.assertEqual(self.label.textFormat(), Qt.RichText)
        self.assertFalse(self.label.openExternalLinks())
        self.assertEqual(self.label.cursor().shape(), Qt.ArrowCursor)
        self.assertEqual(self.label._url_for_link_part, "")
    
    def test_set_content_with_valid_url(self):
        """Test setContent with a valid URL creates a clickable link."""
        prefix = "Slug: "
        value = "my-book-slug"
        url = "https://hardcover.app/books/my-book-slug"
        
        self.label.setContent(prefix, value, url)
        
        # Check that HTML is set correctly with dimmed prefix
        expected_html = (
            f"<span style='color:#999999;'>{prefix}</span>"
            f"<a href='{url}' style='color:#9f7aea; text-decoration:underline;'>{value}</a>"
        )
        self.assertEqual(self.label.text(), expected_html)
        
        # Check cursor and tooltip
        self.assertEqual(self.label.cursor().shape(), Qt.PointingHandCursor)
        self.assertEqual(self.label.toolTip(), f"Open: {url}")
    
    def test_set_content_with_na_value(self):
        """Test setContent with 'N/A' value creates non-clickable text."""
        prefix = "Default Audio Edition: "
        value = "N/A"
        url = "https://hardcover.app/editions/12345"
        
        self.label.setContent(prefix, value, url)
        
        # Check that HTML is set with dimmed prefix (no link for N/A)
        expected_html = (
            f"<span style='color:#999999;'>{prefix}</span>"
            f"<span style='color:#e0e0e0;'>{value}</span>"
        )
        self.assertEqual(self.label.text(), expected_html)
        
        # Check cursor and tooltip
        self.assertEqual(self.label.cursor().shape(), Qt.ArrowCursor)
        self.assertEqual(self.label.toolTip(), "")
    
    def test_set_content_with_empty_url(self):
        """Test setContent with empty URL creates non-clickable text."""
        prefix = "Slug: "
        value = "my-book-slug"
        url = ""
        
        self.label.setContent(prefix, value, url)
        
        # Check that HTML is set with dimmed prefix
        expected_html = (
            f"<span style='color:#999999;'>{prefix}</span>"
            f"<span style='color:#e0e0e0;'>{value}</span>"
        )
        self.assertEqual(self.label.text(), expected_html)
        
        # Check cursor and tooltip
        self.assertEqual(self.label.cursor().shape(), Qt.ArrowCursor)
        self.assertEqual(self.label.toolTip(), "")
    
    def test_set_content_with_none_value(self):
        """Test setContent with None value defaults to 'N/A'."""
        prefix = "Title: "
        value = None
        url = "https://example.com"
        
        self.label.setContent(prefix, value, url)
        
        # Should be treated as N/A with HTML formatting
        expected_html = (
            f"<span style='color:#999999;'>{prefix}</span>"
            f"<span style='color:#e0e0e0;'>N/A</span>"
        )
        self.assertEqual(self.label.text(), expected_html)
        self.assertEqual(self.label.cursor().shape(), Qt.ArrowCursor)
    
    def test_clickable_label_style_preservation(self):
        """Test that non-clickable labels maintain proper styling."""
        prefix = "Test: "
        value = "Some Value"
        
        self.label.setContent(prefix, value, "")
        
        # Check that HTML formatting is applied for non-link
        expected_html = (
            f"<span style='color:#999999;'>{prefix}</span>"
            f"<span style='color:#e0e0e0;'>{value}</span>"
        )
        self.assertEqual(self.label.text(), expected_html)
    
    def test_multiple_content_updates(self):
        """Test that label can be updated multiple times correctly."""
        # First set as clickable
        self.label.setContent("Slug: ", "book-1", "https://example.com/book-1")
        self.assertEqual(self.label.cursor().shape(), Qt.PointingHandCursor)
        self.assertTrue("href=" in self.label.text())
        
        # Update to non-clickable
        self.label.setContent("Slug: ", "N/A", "https://example.com/book-2")
        self.assertEqual(self.label.cursor().shape(), Qt.ArrowCursor)
        self.assertFalse("href=" in self.label.text())
        
        # Update to clickable again with different URL
        self.label.setContent("Slug: ", "book-3", "https://example.com/book-3")
        self.assertEqual(self.label.cursor().shape(), Qt.PointingHandCursor)
        self.assertTrue("href=" in self.label.text())
        self.assertEqual(self.label.toolTip(), "Open: https://example.com/book-3")


if __name__ == '__main__':
    unittest.main()