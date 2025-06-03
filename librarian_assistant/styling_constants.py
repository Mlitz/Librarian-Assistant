# ABOUTME: This file contains styling constants for UI highlighting and warnings.
# ABOUTME: It defines colors and styles for N/A highlighting and duplicate warnings.
"""
Styling constants for conditional data highlighting in Librarian-Assistant.

These constants define the visual parameters for highlighting "N/A" values
that represent missing but expected data, as well as styling for warnings
like duplicate platform entries.
"""

# N/A Highlighting Style Constants
# Used when "N/A" represents data that could/should reasonably exist but is missing
N_A_HIGHLIGHT_TEXT_COLOR_HEX = "#E1C584"  # Warm amber/gold color for visibility
N_A_HIGHLIGHT_BG_COLOR_HEX = "#3C3C3C"    # Darker gray background for contrast
N_A_HIGHLIGHT_USE_ITALIC = True           # Italic text for additional emphasis

# Duplicate Warning Constants
# Used for duplicate platform entries in book mappings
DUPLICATE_MAPPING_WARNING_TEXT = " (Duplicate platform entry)"

# Helper function to generate Qt stylesheet for N/A highlighting


def get_na_highlight_stylesheet():
    """
    Generate a Qt stylesheet string for N/A highlighting.

    Returns:
        str: CSS-style string for Qt widgets
    """
    style = f"color: {N_A_HIGHLIGHT_TEXT_COLOR_HEX}; background-color: {N_A_HIGHLIGHT_BG_COLOR_HEX};"
    if N_A_HIGHLIGHT_USE_ITALIC:
        style += " font-style: italic;"
    return style

# Helper function to generate HTML for rich text N/A highlighting


def get_na_highlight_html(text):
    """
    Wrap text in HTML with N/A highlight styling.

    Args:
        text: The text to highlight

    Returns:
        str: HTML-formatted text with styling
    """
    style = f"color: {N_A_HIGHLIGHT_TEXT_COLOR_HEX}; background-color: {N_A_HIGHLIGHT_BG_COLOR_HEX};"
    if N_A_HIGHLIGHT_USE_ITALIC:
        style += " font-style: italic;"
    return f'<span style="{style}">{text}</span>'
