# ABOUTME: Tests for styling constants and helper functions
# ABOUTME: Verifies color values, text formatting, and HTML/CSS generation

from librarian_assistant.styling_constants import (
    N_A_HIGHLIGHT_TEXT_COLOR_HEX,
    N_A_HIGHLIGHT_BG_COLOR_HEX,
    N_A_HIGHLIGHT_USE_ITALIC,
    DUPLICATE_MAPPING_WARNING_TEXT,
    get_na_highlight_stylesheet,
    get_na_highlight_html
)


class TestStylingConstants:
    """Test styling constants and helper functions."""

    def test_color_constants(self):
        """Test that color constants are valid hex colors."""
        # Test text color
        assert N_A_HIGHLIGHT_TEXT_COLOR_HEX.startswith("#")
        assert len(N_A_HIGHLIGHT_TEXT_COLOR_HEX) == 7  # #RRGGBB format
        assert all(c in "0123456789ABCDEFabcdef" for c in N_A_HIGHLIGHT_TEXT_COLOR_HEX[1:])

        # Test background color
        assert N_A_HIGHLIGHT_BG_COLOR_HEX.startswith("#")
        assert len(N_A_HIGHLIGHT_BG_COLOR_HEX) == 7
        assert all(c in "0123456789ABCDEFabcdef" for c in N_A_HIGHLIGHT_BG_COLOR_HEX[1:])

    def test_italic_constant(self):
        """Test that italic setting is a boolean."""
        assert isinstance(N_A_HIGHLIGHT_USE_ITALIC, bool)

    def test_warning_text_constant(self):
        """Test the duplicate mapping warning text."""
        assert isinstance(DUPLICATE_MAPPING_WARNING_TEXT, str)
        assert len(DUPLICATE_MAPPING_WARNING_TEXT) > 0
        assert "Duplicate" in DUPLICATE_MAPPING_WARNING_TEXT

    def test_get_na_highlight_stylesheet_with_italic(self):
        """Test stylesheet generation with italic enabled."""
        # Temporarily ensure italic is True for this test
        original_italic = N_A_HIGHLIGHT_USE_ITALIC
        import librarian_assistant.styling_constants as sc
        sc.N_A_HIGHLIGHT_USE_ITALIC = True

        try:
            stylesheet = get_na_highlight_stylesheet()

            # Check that all components are present
            assert f"color: {N_A_HIGHLIGHT_TEXT_COLOR_HEX}" in stylesheet
            assert f"background-color: {N_A_HIGHLIGHT_BG_COLOR_HEX}" in stylesheet
            assert "font-style: italic;" in stylesheet

            # Check format
            assert stylesheet.endswith(";")
        finally:
            # Restore original value
            sc.N_A_HIGHLIGHT_USE_ITALIC = original_italic

    def test_get_na_highlight_stylesheet_without_italic(self):
        """Test stylesheet generation with italic disabled."""
        # Temporarily set italic to False
        original_italic = N_A_HIGHLIGHT_USE_ITALIC
        import librarian_assistant.styling_constants as sc
        sc.N_A_HIGHLIGHT_USE_ITALIC = False

        try:
            stylesheet = get_na_highlight_stylesheet()

            # Check that color components are present
            assert f"color: {N_A_HIGHLIGHT_TEXT_COLOR_HEX}" in stylesheet
            assert f"background-color: {N_A_HIGHLIGHT_BG_COLOR_HEX}" in stylesheet

            # Check that italic is NOT present
            assert "font-style: italic" not in stylesheet
        finally:
            # Restore original value
            sc.N_A_HIGHLIGHT_USE_ITALIC = original_italic

    def test_get_na_highlight_html_with_italic(self):
        """Test HTML generation with italic enabled."""
        original_italic = N_A_HIGHLIGHT_USE_ITALIC
        import librarian_assistant.styling_constants as sc
        sc.N_A_HIGHLIGHT_USE_ITALIC = True

        try:
            test_text = "N/A"
            html = get_na_highlight_html(test_text)

            # Check structure
            assert html.startswith('<span style="')
            assert html.endswith('</span>')
            assert test_text in html

            # Check style attributes
            assert f"color: {N_A_HIGHLIGHT_TEXT_COLOR_HEX}" in html
            assert f"background-color: {N_A_HIGHLIGHT_BG_COLOR_HEX}" in html
            assert "font-style: italic;" in html
        finally:
            sc.N_A_HIGHLIGHT_USE_ITALIC = original_italic

    def test_get_na_highlight_html_without_italic(self):
        """Test HTML generation with italic disabled."""
        original_italic = N_A_HIGHLIGHT_USE_ITALIC
        import librarian_assistant.styling_constants as sc
        sc.N_A_HIGHLIGHT_USE_ITALIC = False

        try:
            test_text = "N/A"
            html = get_na_highlight_html(test_text)

            # Check structure
            assert html.startswith('<span style="')
            assert html.endswith('</span>')
            assert test_text in html

            # Check style attributes
            assert f"color: {N_A_HIGHLIGHT_TEXT_COLOR_HEX}" in html
            assert f"background-color: {N_A_HIGHLIGHT_BG_COLOR_HEX}" in html
            assert "font-style: italic" not in html
        finally:
            sc.N_A_HIGHLIGHT_USE_ITALIC = original_italic

    def test_get_na_highlight_html_special_characters(self):
        """Test HTML generation with special characters."""
        # Test with HTML special characters
        test_cases = [
            ("N/A", "N/A"),  # Normal case
            ("<N/A>", "<N/A>"),  # Angle brackets should be preserved
            ("N/A & more", "N/A & more"),  # Ampersand
            ('"N/A"', '"N/A"'),  # Quotes
        ]

        for input_text, expected_content in test_cases:
            html = get_na_highlight_html(input_text)
            assert expected_content in html
            assert html.startswith('<span style="')
            assert html.endswith('</span>')

    def test_constants_are_immutable_strings(self):
        """Test that string constants are actually strings."""
        assert isinstance(N_A_HIGHLIGHT_TEXT_COLOR_HEX, str)
        assert isinstance(N_A_HIGHLIGHT_BG_COLOR_HEX, str)
        assert isinstance(DUPLICATE_MAPPING_WARNING_TEXT, str)

    def test_color_constants_are_uppercase_hex(self):
        """Test that color constants follow uppercase hex convention."""
        # While the current implementation uses mixed case, test that they're valid
        assert N_A_HIGHLIGHT_TEXT_COLOR_HEX == "#E1C584"
        assert N_A_HIGHLIGHT_BG_COLOR_HEX == "#3C3C3C"
