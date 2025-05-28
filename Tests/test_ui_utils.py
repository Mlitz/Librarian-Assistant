# ABOUTME: This file contains unit tests for the ui_utils module.
# ABOUTME: It tests the N/A applicability logic for various fields and contexts.
import unittest
from librarian_assistant.ui_utils import is_na_highlightable, should_highlight_general_info_na


class TestUiUtils(unittest.TestCase):
    """Test cases for UI utility functions."""
    
    def test_always_highlightable_fields(self):
        """Test fields that should always be highlighted when N/A."""
        always_highlightable = [
            'title', 'book_title', 'edition_title',
            'isbn_10', 'isbn_13', 'asin',
            'publisher', 'language', 'country',
            'release_date', 'edition_format'
        ]
        
        for field in always_highlightable:
            with self.subTest(field=field):
                self.assertTrue(is_na_highlightable(field))
                # Test case insensitivity
                self.assertTrue(is_na_highlightable(field.upper()))
    
    def test_never_highlightable_fields(self):
        """Test fields that should never be highlighted when N/A."""
        never_highlightable = [
            'subtitle', 'edition_subtitle',
            'edition_information', 'description'
        ]
        
        for field in never_highlightable:
            with self.subTest(field=field):
                self.assertFalse(is_na_highlightable(field))
    
    def test_contributor_slots_never_highlighted(self):
        """Test that numbered contributor slots are never highlighted."""
        contributor_slots = [
            'author_2', 'author_10',
            'narrator_1', 'narrator_5',
            'illustrator_3', 'editor_7',
            'translator_4', 'foreword_2',
            'cover_artist_1', 'other_9'
        ]
        
        for slot in contributor_slots:
            with self.subTest(slot=slot):
                self.assertFalse(is_na_highlightable(slot))
    
    def test_pages_field_with_context(self):
        """Test pages field highlighting based on reading format."""
        # Pages expected for physical book
        physical_context = {'reading_format_id': 1}
        self.assertTrue(is_na_highlightable('pages', physical_context))
        
        # Pages expected for e-book
        ebook_context = {'reading_format_id': 4}
        self.assertTrue(is_na_highlightable('pages', ebook_context))
        
        # Pages not applicable for audiobook
        audio_context = {'reading_format_id': 2}
        self.assertFalse(is_na_highlightable('pages', audio_context))
        
        # No context provided - default to not highlight
        self.assertFalse(is_na_highlightable('pages'))
    
    def test_duration_field_with_context(self):
        """Test duration/audio_seconds field highlighting based on reading format."""
        # Duration expected for audiobook
        audio_context = {'reading_format_id': 2}
        self.assertTrue(is_na_highlightable('duration', audio_context))
        self.assertTrue(is_na_highlightable('audio_seconds', audio_context))
        
        # Duration not applicable for physical book
        physical_context = {'reading_format_id': 1}
        self.assertFalse(is_na_highlightable('duration', physical_context))
        self.assertFalse(is_na_highlightable('audio_seconds', physical_context))
        
        # Duration not applicable for e-book
        ebook_context = {'reading_format_id': 4}
        self.assertFalse(is_na_highlightable('duration', ebook_context))
    
    def test_narrator_field_with_context(self):
        """Test narrator field highlighting based on reading format."""
        # Narrator expected for audiobook
        audio_context = {'reading_format_id': 2}
        self.assertTrue(is_na_highlightable('narrator', audio_context))
        
        # Narrator not applicable for physical book
        physical_context = {'reading_format_id': 1}
        self.assertFalse(is_na_highlightable('narrator', physical_context))
    
    def test_should_highlight_general_info_na(self):
        """Test general info area N/A highlighting logic."""
        # Should highlight
        highlightable = [
            'title', 'slug', 'author', 'authors',
            'book_id', 'total_editions',
            'default_audio', 'default_cover',
            'default_ebook', 'default_physical'
        ]
        
        for field in highlightable:
            with self.subTest(field=field):
                self.assertTrue(should_highlight_general_info_na(field))
        
        # Should not highlight
        non_highlightable = ['description', 'subtitle']
        
        for field in non_highlightable:
            with self.subTest(field=field):
                self.assertFalse(should_highlight_general_info_na(field))
        
        # Test partial matches
        self.assertTrue(should_highlight_general_info_na('book_title'))
        self.assertTrue(should_highlight_general_info_na('default_audio_edition'))


if __name__ == '__main__':
    unittest.main()