# Librarian-Assistant.py
"""
A Tkinter-based desktop application to fetch and display book and edition details
from the Hardcover.app API.

Allows users to input a bearer token and a book ID to retrieve comprehensive
information, including titles, authors, descriptions, editions, publishers,
and various metadata flags indicating data completeness or potential issues.
The application features a dark theme, configurable font sizes (via an external
JSON file), and clickable links to relevant Hardcover.app pages and external
book platforms (Goodreads, Google Books, OpenLibrary).
"""

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import requests
import json
import os
import webbrowser
import tkinter.font as tkFont
from tkinter import scrolledtext
import traceback
import base64

# --- Constants for UI Theming and Configuration ---
COLOR_BACKGROUND = "#2E2E2E"
COLOR_FOREGROUND = "#EAEAEA"
COLOR_WIDGET_BG = "#3C3C3C"
COLOR_WIDGET_FG = "#EAEAEA"
COLOR_ACCENT_FG = "#569CD6"
COLOR_LABEL_FG = "#CCCCCC"
COLOR_HEADER_FG = "#4EC9B0"
COLOR_ERROR_FG = "#F44747"
COLOR_SEPARATOR_FG = "#6A6A6A"
COLOR_WARNING_FG = "#FF8C00"
COLOR_INFO_FG = "#FFCC66"

PRIMARY_OUTPUT_FONT_FAMILY = "Consolas"  # Font for primary text output areas
LINK_LABEL_FONT_FAMILY = "Segoe UI"     # Font for UI labels and links

# Default font sizes. These can be overridden by 'config.json'.
# Users can modify 'config.json' to adjust these sizes.
DEFAULT_FONT_SIZES = {
    "ui_label": 10,
    "button": 11,
    "entry": 10,
    "status_label": 10,
    "link_label": 10,
    "notebook_tab": 10,
    "output_default": 12,
    "output_header": 13,
    "output_data_label": 11,
    "output_data_value": 12,
    "output_hyperlink": 12,
    "output_flag": 12
}
# Active font configuration, initialized with defaults and updated from config.json.
FONT_CONFIG = DEFAULT_FONT_SIZES.copy()

# Global list to store information about clickable regions in the output text area.
clickable_regions = []

# Configuration file constants
CONFIG_DIR_NAME = "HardcoverFetcher"
CONFIG_FILE_NAME = "config.json"

def get_config_path():
    """
    Determines the appropriate platform-specific path for the configuration file.
    Creates the configuration directory if it doesn't exist.

    Returns:
        str: The full path to the configuration file.
    """
    app_data_path = os.getenv('APPDATA')  # Windows
    if not app_data_path:
        # Linux/macOS common paths
        app_data_path = os.path.expanduser("~/.config")
        if not os.path.isdir(app_data_path):
             app_data_path = os.path.expanduser("~/.local/share")
             if not os.path.isdir(app_data_path):
                  # macOS alternative
                  app_data_path = os.path.expanduser("~/Library/Application Support")
                  if not os.path.isdir(app_data_path):
                       app_data_path = os.path.expanduser("~") # Fallback to home directory

    config_dir = os.path.join(app_data_path, CONFIG_DIR_NAME)
    try:
        os.makedirs(config_dir, exist_ok=True)
    except OSError as e:
        # Non-critical error, app can still run with default config or local config file
        print(f"Warning: Could not create config directory {config_dir}: {e}")
        # Fallback to using a config file in the current working directory
        return os.path.abspath(CONFIG_FILE_NAME)
    return os.path.join(config_dir, CONFIG_FILE_NAME)

def save_config(config_data):
    """
    Saves the given configuration data to the config file.

    Args:
        config_data (dict): The configuration dictionary to save.
    """
    config_file = get_config_path()
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4)
    except IOError as e:
        print(f"Error saving config file to {config_file}: {e}")
        messagebox.showwarning("Config Error", f"Could not save configuration file:\n{e}")

def load_config():
    """
    Loads configuration data from the config file.
    Returns an empty dictionary if the file doesn't exist or an error occurs.

    Returns:
        dict: The loaded configuration data.
    """
    config_file = get_config_path()
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content: return {} # Handle empty file
                return json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading/parsing config file from {config_file}: {e}")
            return {} # Return default/empty config on error
    else:
        print(f"Config file not found at {config_file}. Using defaults.")
        return {}

# --- Link Handling Functions ---
def open_book_link(book_slug):
    """
    Opens the Hardcover.app book page in a web browser.

    Args:
        book_slug (str): The slug of the book.
    """
    if book_slug:
        url = f"https://hardcover.app/books/{book_slug}"
        try:
            webbrowser.open_new_tab(url)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open link:\n{e}")
    else:
        messagebox.showwarning("Link Error", "Could not create link (missing book slug).")

def get_platform_url(platform_name, external_id):
    """
    Constructs a URL for a given book platform and its external ID.

    Args:
        platform_name (str): The name of the platform (e.g., "goodreads", "google").
        external_id (str): The external ID for the book on that platform.

    Returns:
        str or None: The formatted URL, or None if the platform is unknown or ID is invalid.
    """
    if not platform_name or not external_id:
        return None
    name = platform_name.lower()

    # If external_id is already a full URL, return it directly (basic validation)
    if isinstance(external_id, str) and external_id.startswith(('http://', 'https://')):
        # Basic check to see if it looks like a valid domain in the URL
        parts = external_id.split('/')
        domain_part_index = 2 if external_id.startswith('https') else 1
        if len(parts) > domain_part_index and '.' in parts[domain_part_index]:
            return external_id
        else:
            return None # Looks like a scheme but not a valid URL structure

    ext_id_str = str(external_id)
    if name == 'goodreads':
        return f"https://www.goodreads.com/book/show/{ext_id_str}"
    if name == 'google':
        return f"https://books.google.com/books?id={ext_id_str}"
    if name == 'openlibrary':
        if ext_id_str.startswith(('/books/', '/works/')): # Handle full paths
            return f"https://openlibrary.org{ext_id_str}"
        else: # Assume it's an ID that needs to be searched
            return f"https://openlibrary.org/search?q={ext_id_str}"
    return None

def on_link_enter(event):
    """Changes cursor to hand2 when mouse enters a hyperlink region."""
    event.widget.config(cursor="hand2")

def on_link_leave(event):
    """Changes cursor back to default when mouse leaves a hyperlink region."""
    event.widget.config(cursor="")

def on_link_click(event):
    """Opens the URL associated with a clicked hyperlink region in the output_viewer."""
    widget = event.widget
    # Get the character index under the mouse click
    index = widget.index(f"@{event.x},{event.y}")
    global clickable_regions
    for region in clickable_regions:
        # Check if the click was within the start and end indices of a stored clickable region
        if widget.compare(index, '>=', region['start']) and widget.compare(index, '<', region['end']):
            try:
                webbrowser.open_new_tab(region['url'])
            except Exception as e:
                messagebox.showerror("Link Error", f"Could not open URL:\n{region['url']}\nError: {e}")
            break

# --- Data Display Function ---
def display_formatted_data(widget, book_data):
    """
    Formats and displays the fetched book data in the provided ScrolledText widget.
    Uses font sizes from FONT_CONFIG and sets up clickable hyperlinks.

    Args:
        widget (tk.scrolledtext.ScrolledText): The widget to display data in.
        book_data (dict): The dictionary containing book and edition information.
    """
    global clickable_regions
    clickable_regions = [] # Reset for new data

    # Define fonts based on current FONT_CONFIG
    header_font = tkFont.Font(weight='bold', size=FONT_CONFIG["output_header"])
    flag_font_size = FONT_CONFIG["output_flag"]
    warning_font = tkFont.Font(weight='bold', size=flag_font_size)
    info_font = tkFont.Font(weight='bold', size=flag_font_size)
    error_font = tkFont.Font(weight='bold', size=flag_font_size)
    output_data_label_font = tkFont.Font(size=FONT_CONFIG["output_data_label"])
    output_data_value_font = tkFont.Font(size=FONT_CONFIG["output_data_value"])
    output_hyperlink_font = tkFont.Font(size=FONT_CONFIG["output_hyperlink"], underline=True)

    # Configure text tags for styling
    widget.tag_configure("header", foreground=COLOR_HEADER_FG, font=header_font)
    widget.tag_configure("label", foreground=COLOR_LABEL_FG, font=output_data_label_font)
    widget.tag_configure("value", foreground=COLOR_FOREGROUND, font=output_data_value_font)
    widget.tag_configure("hyperlink", foreground=COLOR_ACCENT_FG, font=output_hyperlink_font)
    widget.tag_configure("separator", foreground=COLOR_SEPARATOR_FG)
    widget.tag_configure("error_flag", foreground=COLOR_ERROR_FG, font=error_font)
    widget.tag_configure("warning_flag", foreground=COLOR_WARNING_FG, font=warning_font)
    widget.tag_configure("info_flag", foreground=COLOR_INFO_FG, font=info_font)

    def insert_pair(label_text, value_text, is_link=False, url=None, flag_text=None, flag_tag=None):
        """Helper function to insert a label-value pair, optionally as a link or with a flag."""
        widget.insert(tk.END, label_text, ("label",))
        value_str = str(value_text if value_text is not None else 'N/A')

        if is_link and url and value_str != 'N/A':
            start_index = widget.index(f"{tk.END}-1c") # Get index before inserting value
            widget.insert(tk.END, value_str, ("hyperlink",))
            end_index = widget.index(tk.END)
            clickable_regions.append({'start': start_index, 'end': end_index, 'url': url})
        else:
            widget.insert(tk.END, value_str, ("value",))

        if flag_text and flag_tag:
            widget.insert(tk.END, " ", ("value",)) # Space before the flag
            widget.insert(tk.END, flag_text, (flag_tag,))

        widget.insert(tk.END, "\n")

    # This function was defined but not used. Keeping it for potential future use or removal.
    # def insert_list_data(label_text, data_list):
    #     widget.insert(tk.END, label_text, ("label",))
    #     if data_list and isinstance(data_list, list):
    #         widget.insert(tk.END, "\n")
    #         for item in data_list:
    #             if isinstance(item, dict):
    #                 name = item.get('name', 'N/A')
    #                 role = item.get('role', 'Unknown Role')
    #                 item_display = [f"      - {name} ({role})"]
    #                 widget.insert(tk.END, "\n".join(item_display) + "\n", ("value",))
    #             else:
    #                 widget.insert(tk.END, f"      - {str(item)}\n", ("value",))
    #     elif data_list:
    #          widget.insert(tk.END, str(data_list) + "\n", ("value",))
    #     else:
    #         widget.insert(tk.END, "N/A\n", ("value",))

    widget.config(state=tk.NORMAL) # Enable editing
    widget.delete('1.0', tk.END)    # Clear previous content

    # --- Display Book Details ---
    widget.insert(tk.END, "Book Details:\n", ("header",))
    widget.insert(tk.END, "-" * 50 + "\n", ("separator",))

    # Initialize flags; they will be set if corresponding data is missing or noteworthy
    desc_flag, cover_flag, ebook_flag, audio_flag, physical_flag = [None]*5 # Removed book_contrib_flag

    if not book_data.get('description'): desc_flag = ("[NO DESCRIPTION]", "warning_flag")
    if not book_data.get('default_cover_edition'): cover_flag = ("[NO DEFAULT COVER]", "info_flag")
    if not book_data.get('default_ebook_edition'): ebook_flag = ("[NO DEFAULT EBOOK]", "info_flag")
    if not book_data.get('default_audio_edition'): audio_flag = ("[NO DEFAULT AUDIO]", "info_flag")
    if not book_data.get('default_physical_edition'): physical_flag = ("[NO DEFAULT PHYSICAL]", "info_flag")

    insert_pair("Title: ", book_data.get('title', 'N/A'))
    insert_pair("Subtitle: ", book_data.get('subtitle', 'N/A'))

    # Extract primary author name from contributions
    author_name = "N/A"
    contributions = book_data.get('contributions', [])
    if contributions and isinstance(contributions, list) and len(contributions) > 0:
        first_contribution = contributions[0]
        if isinstance(first_contribution, dict):
            author_info = first_contribution.get('author')
            if author_info and isinstance(author_info, dict):
                 author_name = author_info.get('name', 'N/A')
    insert_pair("Primary Author: ", author_name)

    book_slug = book_data.get('slug')
    slug_url = f"https://hardcover.app/books/{book_slug}" if book_slug else None
    insert_pair("Slug: ", book_slug, is_link=bool(slug_url), url=slug_url)

    insert_pair("Book ID: ", str(book_data.get('id', 'N/A')))
    insert_pair("Editions Count: ", str(book_data.get('editions_count', 'N/A')))

    description = book_data.get('description')
    if description:
         widget.insert(tk.END, "Description:\n", ("label",))
         # Display first 500 chars of description with ellipsis if longer
         widget.insert(tk.END, description[:500] + ("..." if len(description) > 500 else "") + "\n", ("value",))
    else:
        insert_pair("Description: ", "N/A", flag_text=desc_flag[0] if desc_flag else None, flag_tag=desc_flag[1] if desc_flag else None)

    # Display general book status flags if any are set
    general_book_flags = [f for f in [cover_flag, ebook_flag, audio_flag, physical_flag] if f]
    if general_book_flags:
        widget.insert(tk.END, "Book Status Flags: ", ("label",))
        for flag_text, flag_tag in general_book_flags:
            widget.insert(tk.END, flag_text + " ", (flag_tag,))
        widget.insert(tk.END, "\n")

    widget.insert(tk.END, "\n" + "=" * 50 + "\n\n", ("separator",))

    # --- Display Editions Details ---
    editions = book_data.get('editions', [])
    if editions:
        try:
            # Sort editions by score (ascending). Editions without a score are treated as having negative infinity.
            if isinstance(editions, list) and all(isinstance(e, dict) for e in editions):
                 editions.sort(key=lambda e: e.get('score') if e.get('score') is not None else -float('inf'))
        except Exception as sort_e:
            print(f"Error sorting editions: {sort_e}")
            widget.insert(tk.END, f"(Could not sort editions: {sort_e})\n", ("error_flag",))

    if not editions:
        widget.insert(tk.END,"No editions found in the data.\n", ("value",))
    else:
        widget.insert(tk.END, f"Editions Found ({len(editions)}) - Sorted by Score (Lowest First):\n", ("header",))
        widget.insert(tk.END, "-" * 50 + "\n", ("separator",))

        LOW_SCORE_THRESHOLD = 500 # Threshold for flagging editions with low scores
        # Mapping for reading_format_id to human-readable string
        READING_FORMAT_MAP = {
            1: "Physical", 2: "Audiobook", 4: "Ebook"
        }

        for i, edition in enumerate(editions):
            if not isinstance(edition, dict): continue # Skip if edition data is not a dictionary

            widget.insert(tk.END, f"\n--- Edition {i+1} --- \n", ("header",))

            # Initialize flags for each edition to None. They are set based on data validation.
            edition_id_flag, score_flag, low_score_flag, edition_title_flag, edition_subtitle_flag, \
            image_url_flag, isbn10_flag, isbn13_flag, all_isbn_flag, asin_flag, \
            edition_contrib_flag, reading_format_id_flag, unknown_reading_format_flag, \
            pages_flag, invalid_pages_flag, audio_duration_missing_flag, \
            invalid_audio_seconds_flag, audio_duration_zero_flag, has_audio_not_audiobook_flag, \
            edition_format_flag, edition_info_flag, release_date_flag, no_mappings_flag, \
            invalid_mappings_flag, empty_mappings_flag, publisher_flag, language_flag, \
            narrator_missing_flag = [None] * 28 # Adjusted count after removing one flag


            # Extract data for the current edition
            edition_id = edition.get('id')
            edition_score = edition.get('score')
            edition_title = edition.get('title')
            edition_subtitle = edition.get('subtitle')
            image_info = edition.get('image')
            image_url = image_info.get('url') if image_info and isinstance(image_info, dict) else None
            isbn_10 = edition.get('isbn_10')
            isbn_13 = edition.get('isbn_13')
            asin = edition.get('asin')
            edition_cached_contributors_raw = edition.get('cached_contributors')
            reading_format_id = edition.get('reading_format_id')
            pages = edition.get('pages')
            audio_seconds = edition.get('audio_seconds')
            edition_format_val = edition.get('edition_format')
            edition_info_text = edition.get('edition_information')
            release_date = edition.get('release_date')
            mappings = edition.get('book_mappings', []) # Default to empty list
            publisher_info = edition.get('publisher')
            publisher_name = publisher_info.get('name') if publisher_info and isinstance(publisher_info, dict) else None
            language_info = edition.get('language')
            language_name_val = language_info.get('language') if language_info and isinstance(language_info, dict) else None

            # --- Set Flags based on data validation ---
            if not edition_id: edition_id_flag = ("[MISSING EDITION ID]", "error_flag")
            if edition_score is None: score_flag = ("[MISSING SCORE]", "info_flag")
            elif edition_score < LOW_SCORE_THRESHOLD: low_score_flag = (f"[LOW SCORE:{edition_score}]", "warning_flag")

            if not edition_title: edition_title_flag = ("[MISSING EDITION TITLE]", "warning_flag")
            # A colon in the title might indicate the subtitle was mistakenly included in the title.
            elif ":" in edition_title: edition_title_flag = ("[EDITION TITLE HAS COLON - VERIFY SUBTITLE]", "info_flag")
            if not edition_subtitle: edition_subtitle_flag = ("[MISSING EDITION SUBTITLE]", "info_flag")

            if not image_url: image_url_flag = ("[NO IMAGE URL]", "warning_flag")
            if not isbn_10: isbn10_flag = ("[MISSING ISBN-10]", "info_flag")
            if not isbn_13: isbn13_flag = ("[MISSING ISBN-13]", "info_flag")
            if not isbn_10 and not isbn_13: all_isbn_flag = ("[MISSING ALL ISBNs]", "warning_flag") # More severe if both are missing
            if not asin: asin_flag = ("[MISSING ASIN]", "info_flag")
            if not edition_cached_contributors_raw: edition_contrib_flag = ("[NO EDITION CONTRIBUTORS DATA]", "info_flag")

            mapped_reading_format = "N/A"
            if reading_format_id is None:
                reading_format_id_flag = ("[MISSING READING FORMAT ID]", "warning_flag")
            elif reading_format_id in READING_FORMAT_MAP:
                mapped_reading_format = READING_FORMAT_MAP[reading_format_id]
            else:
                unknown_reading_format_flag = (f"[UNKNOWN READING FORMAT ID: {reading_format_id}]", "warning_flag")
                mapped_reading_format = f"Unknown ({reading_format_id})"

            # Determine if the format is likely an audiobook for further checks
            is_audiobook_format = (reading_format_id == 2)

            if pages is None or pages == '': # Check for empty string as well as None
                if reading_format_id != 2: # Page count is not expected for audiobooks
                    pages_flag = ("[NO PAGES DATA]", "info_flag")
            elif not isinstance(pages, int) or pages < 0:
                invalid_pages_flag = ("[INVALID PAGES DATA]", "warning_flag")

            if audio_seconds is None:
                if is_audiobook_format:
                    audio_duration_missing_flag = ("[AUDIOBOOK - DURATION FIELD MISSING]", "info_flag")
            elif not isinstance(audio_seconds, (int, float)) or audio_seconds < 0:
                invalid_audio_seconds_flag = ("[INVALID AUDIO SECONDS DATA]", "warning_flag")
            else:
                if is_audiobook_format and audio_seconds == 0:
                    audio_duration_zero_flag = ("[AUDIOBOOK - DURATION IS ZERO]", "info_flag")
                elif not is_audiobook_format and audio_seconds > 0:
                    # This flags if a non-audiobook format has an audio duration
                    has_audio_not_audiobook_flag = ("[HAS AUDIO DURATION BUT NOT AUDIOBOOK FORMAT?]", "info_flag")

            if not edition_format_val: edition_format_flag = ("[MISSING EDITION FORMAT]", "info_flag")
            if not edition_info_text: edition_info_flag = ("[NO EDITION INFORMATION]", "info_flag")
            if not release_date: release_date_flag = ("[NO RELEASE DATE]", "info_flag")

            # --- Book Mappings Flags ---
            mapping_flags = [] # Store individual mapping item flags
            if not mappings: # If 'book_mappings' key is missing or None
                no_mappings_flag = ("[NO BOOK MAPPINGS DATA]", "info_flag")
            elif not isinstance(mappings, list):
                invalid_mappings_flag = ("[INVALID BOOK MAPPINGS FORMAT]", "warning_flag")
            else:
                if not mappings: # If 'book_mappings' is an empty list
                    empty_mappings_flag = ("[BOOK MAPPINGS LIST EMPTY]", "info_flag")
                for idx, mapping_item in enumerate(mappings):
                    if not isinstance(mapping_item, dict):
                        mapping_flags.append((f"[MAPPING ITEM {idx+1} INVALID FORMAT]", "warning_flag")); continue
                    if not mapping_item.get('external_id'):
                        mapping_flags.append((f"[MAPPING {idx+1} MISSING EXTERNAL ID]", "info_flag"))
                    platform_item_info = mapping_item.get('platform')
                    if not platform_item_info or not isinstance(platform_item_info, dict) or not platform_item_info.get('name'):
                        mapping_flags.append((f"[MAPPING {idx+1} MISSING PLATFORM NAME]", "info_flag"))

                # Check for duplicate platform entries in mappings
                platform_counts = {}
                for mapping_item in mappings:
                     if isinstance(mapping_item, dict):
                          platform = mapping_item.get('platform')
                          p_name = platform.get('name', 'N/A') if platform and isinstance(platform, dict) else "N/A"
                          if p_name != "N/A":
                              platform_counts[p_name] = platform_counts.get(p_name, 0) + 1
                dupe_platforms = [p for p, c in platform_counts.items() if c > 1]
                if dupe_platforms:
                    mapping_flags.append((f"[DUPE PLATFORMS: {', '.join(dupe_platforms)}]", "info_flag"))

            if not publisher_name: publisher_flag = ("[NO PUBLISHER NAME]", "info_flag")
            if not language_name_val: language_flag = ("[NO LANGUAGE SPECIFIED]", "info_flag")

            # Check for narrator if it's an audiobook and contributors data is present
            if edition_cached_contributors_raw and is_audiobook_format :
                contrib_str = str(edition_cached_contributors_raw).lower() # Simple string check
                if "narrator" not in contrib_str:
                    narrator_missing_flag = ("[AUDIOBOOK - NARRATOR INFO MISSING IN CONTRIBUTORS?]", "warning_flag")

            # --- Displaying Edition Fields with Inline Flags ---
            edit_url = f"https://hardcover.app/books/{book_slug}/editions/{edition_id}/edit" if book_slug and edition_id else None
            insert_pair("  ID: ", edition_id, is_link=bool(edit_url), url=edit_url, flag_text=edition_id_flag[0] if edition_id_flag else None, flag_tag=edition_id_flag[1] if edition_id_flag else None)
            insert_pair("  Edition Title: ", edition_title or 'N/A', flag_text=edition_title_flag[0] if edition_title_flag else None, flag_tag=edition_title_flag[1] if edition_title_flag else None)
            insert_pair("  Edition Subtitle: ", edition_subtitle or 'N/A', flag_text=edition_subtitle_flag[0] if edition_subtitle_flag else None, flag_tag=edition_subtitle_flag[1] if edition_subtitle_flag else None)

            score_display_val = str(edition_score if edition_score is not None else 'N/A')
            current_score_flag = low_score_flag or score_flag # Prioritize low score warning
            insert_pair("  Score: ", score_display_val, flag_text=current_score_flag[0] if current_score_flag else None, flag_tag=current_score_flag[1] if current_score_flag else None)

            current_reading_format_flag = unknown_reading_format_flag or reading_format_id_flag # Prioritize unknown format warning
            insert_pair("  Reading Format: ", mapped_reading_format, flag_text=current_reading_format_flag[0] if current_reading_format_flag else None, flag_tag=current_reading_format_flag[1] if current_reading_format_flag else None)
            insert_pair("  Edition Format: ", edition_format_val or 'N/A', flag_text=edition_format_flag[0] if edition_format_flag else None, flag_tag=edition_format_flag[1] if edition_format_flag else None)
            insert_pair("  ASIN: ", asin or 'N/A', flag_text=asin_flag[0] if asin_flag else None, flag_tag=asin_flag[1] if asin_flag else None)

            isbn10_flag_to_show = all_isbn_flag or isbn10_flag # Show 'all missing' if specific not present
            insert_pair("  ISBN-10: ", isbn_10 or 'N/A', flag_text=isbn10_flag_to_show[0] if isbn10_flag_to_show else None, flag_tag=isbn10_flag_to_show[1] if isbn10_flag_to_show else None)
            # If all_isbn_flag was shown with ISBN-10, don't repeat it for ISBN-13. Only show specific isbn13_flag.
            isbn13_flag_to_show = isbn13_flag if not all_isbn_flag else None
            insert_pair("  ISBN-13: ", isbn_13 or 'N/A', flag_text=isbn13_flag_to_show[0] if isbn13_flag_to_show else None, flag_tag=isbn13_flag_to_show[1] if isbn13_flag_to_show else None)


            current_pages_flag = invalid_pages_flag or pages_flag # Prioritize invalid data warning
            insert_pair("  Pages: ", str(pages if pages is not None else 'N/A'), flag_text=current_pages_flag[0] if current_pages_flag else None, flag_tag=current_pages_flag[1] if current_pages_flag else None)

            # Combine all audio related flags, prioritizing more specific warnings
            current_audio_flag = invalid_audio_seconds_flag or audio_duration_zero_flag or audio_duration_missing_flag or has_audio_not_audiobook_flag
            insert_pair("  Audio Seconds: ", str(audio_seconds if audio_seconds is not None else 'N/A'), flag_text=current_audio_flag[0] if current_audio_flag else None, flag_tag=current_audio_flag[1] if current_audio_flag else None)

            insert_pair("  Release Date: ", release_date or 'N/A', flag_text=release_date_flag[0] if release_date_flag else None, flag_tag=release_date_flag[1] if release_date_flag else None)
            insert_pair("  Edition Information: ", edition_info_text or 'N/A', flag_text=edition_info_flag[0] if edition_info_flag else None, flag_tag=edition_info_flag[1] if edition_info_flag else None)

            # --- Format and Display Edition Cached Contributors ---
            widget.insert(tk.END, "  Edition Cached Contributors: ", ("label",))
            if edition_contrib_flag: # General flag for missing contributor data
                widget.insert(tk.END, "N/A ", ("value",))
                widget.insert(tk.END, edition_contrib_flag[0] + " ", (edition_contrib_flag[1],))
                widget.insert(tk.END, "\n")
            elif edition_cached_contributors_raw:
                try:
                    actual_contributors_list = []
                    # Attempt to parse if it's a JSON string representation of a list
                    if isinstance(edition_cached_contributors_raw, str):
                        # Heuristic: if it looks like a list string
                        if edition_cached_contributors_raw.startswith('[') and edition_cached_contributors_raw.endswith(']'):
                            try:
                                # Replace Python literals for eval; for true JSON, json.loads is better
                                # but API might return Python-like string list.
                                processed_str = edition_cached_contributors_raw.replace('null', 'None') \
                                                                           .replace('true', 'True') \
                                                                           .replace('false', 'False')
                                parsed_object = eval(processed_str) # CAUTION: eval can be risky with untrusted input
                                if isinstance(parsed_object, list):
                                    actual_contributors_list = parsed_object
                                else:
                                    actual_contributors_list = [parsed_object] # Wrap if eval didn't yield a list
                            except Exception as parse_eval_error:
                                print(f"Eval parsing error for contributors string: {parse_eval_error}")
                                # Fallback: treat the raw string as a single non-structured contributor
                                actual_contributors_list = [{"unknown_role": {"name": edition_cached_contributors_raw}, "contribution": "Raw data (parse failed)"}]
                        else:
                            # It's a string, but not obviously a list structure
                            actual_contributors_list = [{"unknown_role": {"name": edition_cached_contributors_raw}, "contribution": "Raw data (string)"}]
                    elif isinstance(edition_cached_contributors_raw, list):
                        actual_contributors_list = edition_cached_contributors_raw
                    else:
                        # Some other data type, convert to string
                         actual_contributors_list = [{"unknown_role": {"name": str(edition_cached_contributors_raw)}, "contribution": "Raw data (other type)"}]

                    if not actual_contributors_list:
                        widget.insert(tk.END, " N/A (No contributor data found or list empty)\n", ("value",))
                    else:
                        widget.insert(tk.END, "\n")  # Start list on a new line
                        contributor_found_in_list = False
                        for item in actual_contributors_list:
                            item_processed = False
                            if isinstance(item, dict):
                                # Handles structures like: {'author': {'name': 'Name', ...}, 'contribution': 'Role'}
                                # Or: {'narrator': {'name': 'Name', ...}, 'contribution': None}
                                for role_key, details_dict in item.items():
                                    if role_key == 'contribution': continue # Skip the 'contribution' field itself as a role

                                    if isinstance(details_dict, dict) and 'name' in details_dict:
                                        name = details_dict.get('name', 'N/A')
                                        # Use role_key (e.g., 'author', 'narrator') or item's 'contribution' field if more descriptive
                                        display_role = item.get('contribution') if item.get('contribution') else role_key.capitalize()
                                        widget.insert(tk.END, f"    - {name} - {display_role}\n", ("value",))
                                        item_processed = True; contributor_found_in_list = True
                                        break # Processed this item's main role/name pair

                                # Handles simpler flat structure: {'name': 'Artist Name', 'contribution': 'Cover Artist'}
                                if not item_processed and 'name' in item and 'contribution' in item:
                                    name = item.get('name', 'N/A')
                                    display_role = item.get('contribution', 'Contributor')
                                    widget.insert(tk.END, f"    - {name} - {display_role}\n", ("value",))
                                    item_processed = True; contributor_found_in_list = True
                            else: # If item is not a dict (e.g., simple string from failed parse)
                                widget.insert(tk.END, f"    - {str(item)}\n", ("value",))
                                item_processed = True; contributor_found_in_list = True

                            if not item_processed and isinstance(item, dict): # Fallback for unhandled dict structures
                                widget.insert(tk.END, f"    - {str(item)} (Unrecognized structure)\n", ("value",))
                                item_processed = True; contributor_found_in_list = True


                        if not contributor_found_in_list:
                             widget.insert(tk.END, "    Data found, but content format unclear or empty.\n", ("value",))

                    # Display narrator missing flag if applicable, after processing contributors
                    if actual_contributors_list and narrator_missing_flag:
                        widget.insert(tk.END, "    ", ("value",)) # Indentation
                        widget.insert(tk.END, narrator_missing_flag[0] + " ", (narrator_missing_flag[1],))
                        widget.insert(tk.END, "\n")

                except Exception as e:
                    widget.insert(tk.END, " Error formatting contributors\n", ("error_flag",))
                    print(f"Error processing edition_cached_contributors: {e}")
                    traceback.print_exc() # For debugging
            else: # No raw contributor data
                widget.insert(tk.END, " N/A\n", ("value",))

            insert_pair("  Publisher: ", publisher_name or 'N/A', flag_text=publisher_flag[0] if publisher_flag else None, flag_tag=publisher_flag[1] if publisher_flag else None)
            insert_pair("  Language: ", language_name_val or 'N/A', flag_text=language_flag[0] if language_flag else None, flag_tag=language_flag[1] if language_flag else None)

            widget.insert(tk.END, "  Image: ", ("label",)) # Label for image URL
            # The image_url itself is the value, potentially a link. The flag is for its absence.
            insert_pair("", image_url, is_link=bool(image_url), url=image_url, flag_text=image_url_flag[0] if image_url_flag else None, flag_tag=image_url_flag[1] if image_url_flag else None)


            # --- Display Mapping Information and General Mapping Flags ---
            widget.insert(tk.END, "  Platform Mappings:", ("label",))
            # Show one general flag for mappings if any apply (e.g. no data, invalid format, or empty list)
            current_mapping_header_flag = no_mappings_flag or invalid_mappings_flag or empty_mappings_flag
            if current_mapping_header_flag:
                 widget.insert(tk.END, " ", ("value",)) # Space before the flag
                 widget.insert(tk.END, current_mapping_header_flag[0], (current_mapping_header_flag[1],))
            widget.insert(tk.END, "\n")

            # Iterate and display individual mappings if data is valid
            if mappings and isinstance(mappings, list) and any(isinstance(m, dict) for m in mappings):
                valid_mapping_found_for_display = False
                for mapping_idx, mapping_item in enumerate(mappings):
                     if not isinstance(mapping_item, dict): continue # Skip non-dict items in the list
                     valid_mapping_found_for_display = True # At least one dict mapping found

                     platform_item = mapping_item.get('platform')
                     p_name = platform_item.get('name', 'N/A') if platform_item and isinstance(platform_item, dict) else "N/A"
                     ext_id = mapping_item.get('external_id', 'N/A')

                     # Find item-specific flags from the 'mapping_flags' list
                     item_specific_flags_texts = []
                     for flag_tuple in mapping_flags:
                         # Check if the flag text mentions this specific mapping index or platform name (heuristic)
                         if f"MAPPING {mapping_idx+1}" in flag_tuple[0] or \
                            (p_name != 'N/A' and p_name in flag_tuple[0] and "DUPE PLATFORMS" in flag_tuple[0]): # Include dupe if it matches current platform
                             item_specific_flags_texts.append(flag_tuple)

                     widget.insert(tk.END, f"    - Mapping {mapping_idx+1}:", ("label",))
                     if item_specific_flags_texts:
                         for flg_txt, flg_tag in item_specific_flags_texts:
                             widget.insert(tk.END, " " + flg_txt, (flg_tag,)) # Prepend space for readability
                     widget.insert(tk.END, "\n")

                     widget.insert(tk.END, "      Platform Name: ", ("label",)); widget.insert(tk.END, f"{p_name}\n", ("value",))
                     platform_url = get_platform_url(p_name, ext_id)
                     # External ID can be a link, no specific flag here unless ID itself is problematic (covered by item_specific_flags_texts)
                     insert_pair("      External ID: ", ext_id, is_link=bool(platform_url), url=platform_url)

                if not valid_mapping_found_for_display and isinstance(mappings, list) and len(mappings)>0 :
                     # This case handles if 'mappings' is a list but contains no dicts (e.g., list of strings)
                     widget.insert(tk.END, "    - Mapping data present but in unexpected item format.\n", ("value",))
            elif not current_mapping_header_flag :
                 # This message shows if no header-level mapping flag was displayed,
                 # meaning data was expected but not found in a usable way.
                 widget.insert(tk.END, "    - None found or unrecognized format for this edition.\n", ("value",))

    widget.config(state=tk.DISABLED) # Make output read-only

# --- Function to Display Error Message in Output Widget ---
def display_error_message(widget, error_message):
    """
    Displays a generic error message in the provided ScrolledText widget.

    Args:
        widget (tk.scrolledtext.ScrolledText): The widget to display the error in.
        error_message (str): The error message string.
    """
    try:
        widget.config(state=tk.NORMAL)
        widget.delete('1.0', tk.END)
        # Use a default font from FONT_CONFIG for error messages if specific one isn't set
        error_display_font = tkFont.Font(family=PRIMARY_OUTPUT_FONT_FAMILY, size=FONT_CONFIG.get("output_default", 12))
        widget.tag_configure("general_error", foreground=COLOR_ERROR_FG, font=error_display_font)
        widget.insert(tk.END, "Error:\n", ("general_error",))
        widget.insert(tk.END, str(error_message), ("general_error",))
        widget.config(state=tk.DISABLED)
    except tk.TclError as e:
        # This might happen if the widget is destroyed while trying to update
        print(f"Error displaying error message in widget: {e}")


# --- Core Logic to Fetch and Process Data from API ---
def fetch_and_process_data():
    """
    Handles the entire process of fetching data from the Hardcover API,
    processing it, and updating the GUI.
    """
    link_label.grid_remove() # Hide previous book link
    status_var.set("Processing...")
    output_viewer.config(state=tk.NORMAL) # Enable output for clearing
    output_viewer.delete('1.0', tk.END)
    output_viewer.config(state=tk.DISABLED) # Disable again before potential early return
    window.update_idletasks() # Ensure UI updates immediately

    bearer_token = token_entry.get().strip()
    book_id_str = book_id_entry.get().strip()

    # --- Input Validation ---
    if not bearer_token:
        msg = "Bearer Token cannot be empty."
        messagebox.showerror("Error", msg)
        status_var.set("Error: Missing Bearer Token.")
        display_error_message(output_viewer, msg)
        return
    if not book_id_str:
        msg = "Book ID cannot be empty."
        messagebox.showerror("Input Error", msg)
        status_var.set("Error: Missing Book ID.")
        display_error_message(output_viewer, msg)
        return
    if not book_id_str.isdigit():
        msg = "Book ID must be a number."
        messagebox.showerror("Input Error", msg) # Corrected title from "InputError"
        status_var.set("Error: Invalid Book ID.")
        display_error_message(output_viewer, msg)
        return
    try:
        book_id_int = int(book_id_str)
    except ValueError:
        msg = "Book ID is not a valid integer."
        messagebox.showerror("Input Error", msg)
        status_var.set("Error: Invalid Book ID format.")
        display_error_message(output_viewer, msg)
        return

    # --- Save Configuration (including token and font settings) ---
    try:
        # Encode token for saving, use empty string if token is somehow not encodable
        encoded_token = base64.b64encode(bearer_token.encode('utf-8')).decode('utf-8') if bearer_token else ""
    except Exception as e:
        messagebox.showerror("Token Error", f"Could not encode token for saving:\n{e}")
        encoded_token = "" # Fallback

    current_config = load_config()
    current_config['bearer_token_b64'] = encoded_token # Store new/updated encoded token
    current_config.pop('bearer_token', None) # Remove old plain text token if it exists
    # FONT_CONFIG holds the active font settings (defaults or from user's JSON).
    # This ensures any user-defined font sizes from a previous session that were loaded
    # into FONT_CONFIG, or the defaults if no config existed, are saved back.
    current_config['font_sizes'] = FONT_CONFIG
    save_config(current_config)

    status_var.set(f"Fetching data for ID: {book_id_int}...")
    window.update_idletasks()

    # --- API Request ---
    api_url = "https://api.hardcover.app/v1/graphql"
    # GraphQL query to fetch book and edition details
    graphql_query = """
    query MyQuery($bookId: Int!) {
      books(where: {id: {_eq: $bookId}}) {
        id slug title subtitle description editions_count
        contributions { author { name } } # For primary author
        editions {
          id score title subtitle image { url } isbn_10 isbn_13 asin cached_contributors
          reading_format_id pages audio_seconds edition_format edition_information release_date
          book_mappings { external_id platform { name } }
          publisher { name } language { language }
        }
        # Default edition types to check for existence flags
        default_audio_edition { id edition_format }
        default_cover_edition { id edition_format }
        default_ebook_edition { id edition_format }
        default_physical_edition { id edition_format }
        # cached_contributors at book level (removed from display, but kept in query if API uses it)
        # If not used by API or display, this can be removed from query.
        cached_contributors
      }
    }"""
    payload = { "query": graphql_query, "variables": { "bookId": book_id_int }, "operationName": "MyQuery" }
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {bearer_token}",
        "content-type": "application/json",
        "user-agent": "Python Hardcover Librarian Tool V1.3" # User agent for the request
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30) # 30-second timeout
        response.raise_for_status() # Raise HTTPError for bad responses (4XX or 5XX)
        raw_data = response.json()

        status_var.set("Data received. Formatting output...")
        window.update_idletasks()

        if 'errors' in raw_data: # Check for GraphQL API errors
             error_detail = raw_data['errors'][0] if raw_data['errors'] and isinstance(raw_data['errors'], list) and raw_data['errors'][0] else {"message": "Unknown API error"}
             error_message = error_detail.get('message', str(error_detail)) # Extract message
             status_var.set(f"API Error: {error_message[:100]}...") # Show truncated error in status
             messagebox.showerror("API Error", f"The API returned an error:\n{error_message}")
             display_error_message(output_viewer, f"API Error:\n{error_message}")
             return

        books_data = raw_data.get('data', {}).get('books', [])
        if not books_data: # If no book data is returned for the ID
             no_book_message = f"No book found for ID {book_id_int}."
             status_var.set(no_book_message)
             messagebox.showinfo("Info", no_book_message)
             display_error_message(output_viewer, no_book_message)
             return

        book = books_data[0] # Assume first book in list is the one we want
        book_title = book.get('title', 'N/A')
        actual_book_slug = book.get('slug') # Slug for generating Hardcover link

        display_formatted_data(output_viewer, book) # Populate the output viewer
        status_var.set(f"Success! Displaying data for '{book_title}'.")

        # Display a direct link to the book on Hardcover.app if slug is available
        if actual_book_slug:
            link_text_val = f"View '{book_title}' on Hardcover"
            link_label.config(text=link_text_val, foreground=COLOR_ACCENT_FG)
            link_label.unbind("<Button-1>") # Remove previous binding
            link_label.bind("<Button-1>", lambda e, s=actual_book_slug: open_book_link(s)) # Bind new link
            link_label.grid() # Make label visible
        else:
            link_label.grid_remove() # Hide if no slug

    except requests.exceptions.Timeout:
        error_msg = "Network Error: The request timed out."
        status_var.set("Network Error: Timeout.")
        link_label.grid_remove()
        messagebox.showerror("Network Error", error_msg)
        display_error_message(output_viewer, error_msg)
    except requests.exceptions.RequestException as e: # Catches other requests errors
        error_msg = f"Network/API Error:\n{e}"
        status_var.set("Network/API Error.")
        link_label.grid_remove()
        messagebox.showerror("API Error", f"Failed to connect or get data from the API.\nCheck connection and token.\nError: {e}")
        display_error_message(output_viewer, error_msg)
    except json.JSONDecodeError:
        error_msg = "Invalid JSON received from API."
        status_var.set("Error: Invalid JSON received.")
        link_label.grid_remove()
        try:
            # Attempt to include part of the response text for debugging, if available
            if response is not None and hasattr(response, 'text'):
                 error_msg += f"\n\nResponse Text (first 500 chars):\n{response.text[:500]}..."
        except Exception:
            pass # Silently ignore if response text cannot be accessed
        messagebox.showerror("Data Error", "The response from the API was not valid JSON.")
        display_error_message(output_viewer, error_msg)
    except Exception as e: # General catch-all for other unexpected errors
        error_msg = f"An unexpected error occurred:\n{type(e).__name__}: {e}"
        status_var.set("An unexpected error occurred.")
        link_label.grid_remove()
        messagebox.showerror("Error", error_msg)
        print(f"Traceback for unexpected error:\n", flush=True); traceback.print_exc() # Print traceback for dev
        display_error_message(output_viewer, error_msg)

# --- GUI Setup ---
if __name__ == "__main__":
    # Load application configuration (includes font sizes and potentially saved token)
    app_config = load_config()
    user_font_sizes = app_config.get("font_sizes", {})
    # Update the global FONT_CONFIG: user settings from JSON override in-script defaults.
    FONT_CONFIG.update(user_font_sizes)

    # If "font_sizes" was not in config.json, FONT_CONFIG (initially DEFAULT_FONT_SIZES)
    # will be saved back to config.json during the next data fetch.
    # This ensures the user can discover and modify the font_sizes section.

    window = tk.Tk()
    window.title("Hardcover Librarian Tool")
    window.geometry("850x700") # Default window size
    window.config(bg=COLOR_BACKGROUND)

    # --- Theming for ttk Widgets ---
    style = ttk.Style()
    available_themes = style.theme_names()
    # Attempt to use a more modern theme if available, falling back otherwise
    preferred_themes = ['clam', 'alt', 'default', 'vista', 'xpnative']
    selected_theme = None
    for theme in preferred_themes:
        if theme in available_themes:
            try:
                style.theme_use(theme)
                selected_theme = theme
                print(f"Using ttk theme: {theme}")
                break
            except tk.TclError:
                continue # Theme might exist but fail to apply on some systems
    if not selected_theme:
        print("No preferred ttk theme found, using system default.")

    # Configure base style for ttk widgets
    style.configure('.', background=COLOR_BACKGROUND, foreground=COLOR_FOREGROUND)
    style.configure('TFrame', background=COLOR_BACKGROUND)

    # Configure specific ttk widget styles using FONT_CONFIG for font sizes
    style.configure('TLabel', background=COLOR_BACKGROUND, foreground=COLOR_LABEL_FG, anchor=tk.W, font=(LINK_LABEL_FONT_FAMILY, FONT_CONFIG["ui_label"]))
    style.configure('TNotebook', background=COLOR_BACKGROUND, borderwidth=0, tabposition='nw') # Place tabs at top-west
    style.configure('TNotebook.Tab', background=COLOR_WIDGET_BG, foreground=COLOR_LABEL_FG, padding=[10, 5], borderwidth=1, font=(LINK_LABEL_FONT_FAMILY, FONT_CONFIG["notebook_tab"]))
    style.map('TNotebook.Tab',
              background=[('selected', COLOR_BACKGROUND), ('!selected', COLOR_WIDGET_BG)],
              foreground=[('selected', COLOR_HEADER_FG), ('!selected', COLOR_LABEL_FG)],
              expand=[('selected', [1, 1, 1, 0])]) # Slight expansion for selected tab

    style.configure('TButton', background=COLOR_WIDGET_BG, foreground=COLOR_FOREGROUND, padding=8,
                    font=tkFont.Font(family=LINK_LABEL_FONT_FAMILY, weight='bold', size=FONT_CONFIG["button"]),
                    borderwidth=1, relief=tk.RAISED)
    style.map('TButton',
              background=[('active', COLOR_ACCENT_FG), ('pressed', COLOR_ACCENT_FG)],
              foreground=[('active', COLOR_BACKGROUND), ('pressed', COLOR_BACKGROUND)],
              relief=[('pressed', tk.SUNKEN), ('!pressed', tk.RAISED)])

    style.configure('TEntry', foreground=COLOR_WIDGET_FG, fieldbackground=COLOR_WIDGET_BG,
                    insertcolor=COLOR_FOREGROUND, borderwidth=1, relief=tk.FLAT,
                    font=(PRIMARY_OUTPUT_FONT_FAMILY, FONT_CONFIG["entry"]))
    style.map('TEntry', relief=[('focus', tk.SOLID)], bordercolor=[('focus', COLOR_ACCENT_FG)]) # Highlight border on focus

    # --- Main UI Structure: Notebook for Tabs ---
    notebook = ttk.Notebook(window, style='TNotebook')
    notebook.pack(pady=10, padx=10, fill="both", expand=True)

    # --- Input Tab ---
    input_frame = ttk.Frame(notebook, padding="20", style='TFrame')
    notebook.add(input_frame, text='Fetch Data')
    input_frame.columnconfigure(1, weight=1) # Make entry column expandable

    token_label = ttk.Label(input_frame, text="Bearer Token:")
    token_label.grid(row=0, column=0, sticky=tk.W, pady=5, padx=(0, 10))
    token_entry = ttk.Entry(input_frame, width=60, show="*", style='TEntry') # show="*" hides token
    token_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)

    book_id_label = ttk.Label(input_frame, text="Book ID:")
    book_id_label.grid(row=1, column=0, sticky=tk.W, pady=5, padx=(0, 10))
    book_id_entry = ttk.Entry(input_frame, width=20, style='TEntry')
    book_id_entry.grid(row=1, column=1, sticky=tk.W, pady=5) # Align left

    fetch_button = ttk.Button(input_frame, text="Fetch Data", command=fetch_and_process_data, style='TButton', width=15)
    fetch_button.grid(row=2, column=0, columnspan=2, pady=(25, 15)) # Centered with padding

    status_var = tk.StringVar()
    status_label = ttk.Label(input_frame, textvariable=status_var, wraplength=750,
                             font=(LINK_LABEL_FONT_FAMILY, FONT_CONFIG["status_label"]))
    status_label.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

    link_font_obj = tkFont.Font(family=LINK_LABEL_FONT_FAMILY, size=FONT_CONFIG["link_label"], underline=True)
    link_label = ttk.Label(input_frame, text="", style='TLabel', cursor="hand2", font=link_font_obj) # For book link
    link_label.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(5, 10))
    link_label.grid_remove() # Initially hidden

    # --- Output Tab ---
    output_frame = ttk.Frame(notebook, padding="5", style='TFrame')
    notebook.add(output_frame, text='Output')
    output_frame.rowconfigure(0, weight=1)    # Make output viewer row expandable
    output_frame.columnconfigure(0, weight=1) # Make output viewer column expandable

    output_viewer = scrolledtext.ScrolledText(
        output_frame, wrap=tk.WORD, state=tk.DISABLED, bg=COLOR_WIDGET_BG, fg=COLOR_FOREGROUND,
        insertbackground=COLOR_FOREGROUND,      # Cursor color when editable
        selectbackground=COLOR_ACCENT_FG,       # Background of selected text
        selectforeground=COLOR_BACKGROUND,      # Foreground of selected text
        borderwidth=0, highlightthickness=1,
        highlightbackground=COLOR_BACKGROUND,   # Border color when not focused
        highlightcolor=COLOR_ACCENT_FG,         # Border color when focused
        padx=8, pady=8, font=(PRIMARY_OUTPUT_FONT_FAMILY, FONT_CONFIG["output_default"])
    )
    output_viewer.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W)) # Fill the frame
    # Bind events for hyperlink functionality in the output viewer
    output_viewer.tag_bind("hyperlink", "<Enter>", on_link_enter)
    output_viewer.tag_bind("hyperlink", "<Leave>", on_link_leave)
    output_viewer.bind("<Button-1>", on_link_click) # General click for link detection

    # --- Load Saved Token on Startup ---
    # Prioritize 'bearer_token_b64' (encoded), then 'bearer_token' (plain text, for backward compatibility)
    saved_token_b64 = app_config.get('bearer_token_b64', '')
    saved_token_plain = app_config.get('bearer_token', '') # Legacy key
    final_token = ""

    if saved_token_b64:
        try:
            final_token = base64.b64decode(saved_token_b64).decode('utf-8')
            print("Decoded token from 'bearer_token_b64' in config.")
        except Exception as e:
            print(f"Error decoding saved base64 token: {e}. Checking for plain text token.")
            # If b64 decoding fails, it might be due to corruption or old format.
            # Proceed to check plain text as a fallback.
            final_token = "" # Ensure it's reset if b64 decode failed badly

    if not final_token and saved_token_plain: # If no b64 token, or it failed to decode
        print("Using plain text token 'bearer_token' from config (will be encoded on next save).")
        final_token = saved_token_plain

    if final_token:
        token_entry.insert(0, final_token)
        status_var.set("Loaded saved token. Enter Book ID.")
    else:
        status_var.set("Enter token and Book ID, then press 'Fetch Data'.")

    window.mainloop()