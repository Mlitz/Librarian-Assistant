# ABOUTME: This file contains UI utility functions for data display logic.
# ABOUTME: It includes N/A applicability checking and other UI helper functions.
"""
UI utility functions for Librarian-Assistant.

This module provides utility functions for UI-related logic, including
determining when "N/A" values should be highlighted based on context.
"""


def is_na_highlightable(field_identifier: str, edition_context: dict = None) -> bool:
    """
    Determine if an "N/A" value should be highlighted for a given field.
    
    N/A is highlighted when it represents data that could/should reasonably exist
    but is currently missing. N/A is NOT highlighted when the field is simply
    not applicable to the item type or context.
    
    Args:
        field_identifier: The field name/identifier (e.g., 'pages', 'duration', 'narrator_3')
        edition_context: Optional dict containing edition data for context-aware decisions.
                        Should include 'reading_format_id' when available.
    
    Returns:
        bool: True if N/A should be highlighted, False otherwise
    """
    # Normalize field identifier to lowercase for consistent checking
    field_lower = field_identifier.lower()
    
    # Fields that are always highlightable when N/A (expected data that's missing)
    always_highlightable = {
        'title', 'book_title', 'edition_title',
        'isbn_10', 'isbn_13', 'asin',
        'publisher', 'language', 'country',
        'release_date', 'edition_format'
    }
    
    if field_lower in always_highlightable:
        return True
    
    # Fields that are never highlightable (N/A means not applicable)
    never_highlightable = {
        'subtitle', 'edition_subtitle',  # Subtitles are optional
        'edition_information',  # Additional info is optional
        'description'  # Descriptions are optional
    }
    
    if field_lower in never_highlightable:
        return False
    
    # Contributor slot fields (e.g., "narrator_2", "author_3") are never highlightable
    # These represent empty slots when an edition has fewer contributors than the max
    import re
    contributor_pattern = re.compile(r'^(author|narrator|illustrator|editor|translator|foreword|cover_artist|other)_\d+$')
    if contributor_pattern.match(field_lower):
        # Higher-numbered contributor slots are never highlightable
        # They're just empty slots, not missing data
        return False
    
    # Context-dependent fields require edition_context
    if edition_context:
        reading_format_id = edition_context.get('reading_format_id')
        
        # Pages field
        if field_lower == 'pages':
            # Pages are expected for physical books (1) and e-books (4)
            # Not applicable for audiobooks (2)
            return reading_format_id in [1, 4]
        
        # Duration/audio_seconds field
        if field_lower in ['duration', 'audio_seconds']:
            # Duration is expected for audiobooks (2)
            # Not applicable for physical books (1) or e-books (4)
            return reading_format_id == 2
        
        # Narrator fields (without number suffix)
        if field_lower == 'narrator':
            # Narrators are expected for audiobooks only
            return reading_format_id == 2
    
    # Default: don't highlight if we're not sure
    return False


def should_highlight_general_info_na(field_name: str) -> bool:
    """
    Simplified check for General Book Information area fields.
    
    Args:
        field_name: The field name in the general book info section
        
    Returns:
        bool: True if N/A should be highlighted in general info area
    """
    # In general book info, most N/A values represent missing expected data
    highlightable_general_fields = {
        'title', 'slug', 'author', 'authors',
        'book_id', 'total_editions',
        'default_audio', 'default_cover', 
        'default_ebook', 'default_physical'
    }
    
    # Description is optional, so N/A is not highlighted
    non_highlightable_general_fields = {
        'description', 'subtitle'
    }
    
    field_lower = field_name.lower()
    
    if field_lower in non_highlightable_general_fields:
        return False
    
    # Check if field contains any of the highlightable keywords
    for keyword in highlightable_general_fields:
        if keyword in field_lower:
            return True
    
    return False