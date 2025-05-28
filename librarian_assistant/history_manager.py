# ABOUTME: This file manages the search history functionality for the Librarian-Assistant.
# ABOUTME: It handles storing, loading, and managing book search history with local persistence.
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class HistoryManager:
    """
    Manages search history for the Librarian-Assistant application.
    Stores book search history locally in JSON format.
    """
    
    def __init__(self, storage_dir: str = None):
        """
        Initialize the HistoryManager.
        
        Args:
            storage_dir: Directory to store history file. If None, uses user's app data directory.
        """
        if storage_dir is None:
            # Use platform-appropriate app data directory
            if os.name == 'nt':  # Windows
                app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
                storage_dir = os.path.join(app_data, 'LibrarianAssistant')
            else:  # Unix-like systems
                app_data = os.environ.get('XDG_DATA_HOME', os.path.expanduser('~/.local/share'))
                storage_dir = os.path.join(app_data, 'LibrarianAssistant')
        
        self.storage_dir = storage_dir
        self.history_file = os.path.join(storage_dir, 'search_history.json')
        
        # Ensure storage directory exists
        try:
            os.makedirs(storage_dir, exist_ok=True)
        except (PermissionError, OSError) as e:
            logger.error(f"Failed to create storage directory: {e}")
            # Continue anyway - save/load operations will also fail but won't crash
        
        # In-memory cache
        self._history = []
        
        # Load existing history
        self.load_history()
    
    def add_search(self, book_id: int, book_title: str) -> None:
        """
        Add a search to the history.
        
        Args:
            book_id: The ID of the book that was searched
            book_title: The title of the book
        """
        search_time = datetime.now().isoformat()
        
        # Check if this book is already in history
        existing_index = None
        for i, entry in enumerate(self._history):
            if entry['book_id'] == book_id:
                existing_index = i
                break
        
        # If exists, update the timestamp and move to front
        if existing_index is not None:
            self._history.pop(existing_index)
        
        # Add new entry at the beginning
        new_entry = {
            'book_id': book_id,
            'book_title': book_title,
            'search_time': search_time
        }
        self._history.insert(0, new_entry)
        
        # Save to file
        self.save_history()
        
        logger.info(f"Added book to search history: ID {book_id}, Title: {book_title}")
    
    def get_history(self) -> List[Dict]:
        """
        Get the current search history.
        
        Returns:
            List of history entries, each containing book_id, book_title, and search_time
        """
        return self._history.copy()
    
    def clear_history(self) -> None:
        """Clear all search history."""
        self._history = []
        self.save_history()
        logger.info("Search history cleared")
    
    def save_history(self) -> None:
        """Save the current history to file."""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self._history, f, indent=2, ensure_ascii=False)
            logger.debug(f"History saved to {self.history_file}")
        except Exception as e:
            logger.error(f"Failed to save history: {e}")
    
    def load_history(self) -> None:
        """Load history from file."""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self._history = json.load(f)
                logger.debug(f"History loaded from {self.history_file}, {len(self._history)} entries")
            else:
                self._history = []
                logger.debug("No existing history file found, starting with empty history")
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            self._history = []
    
    def search_history(self, query: str) -> List[Dict]:
        """
        Search through history entries.
        
        Args:
            query: Search query to match against book ID or title
            
        Returns:
            List of matching history entries
        """
        if not query:
            return self._history.copy()
        
        query_lower = query.lower()
        matches = []
        
        for entry in self._history:
            # Search in book ID (as string) and title
            if (query_lower in str(entry['book_id']) or 
                query_lower in entry['book_title'].lower()):
                matches.append(entry)
        
        return matches
    
    def sort_history(self, sort_by: str) -> List[Dict]:
        """
        Sort history entries.
        
        Args:
            sort_by: Sort criteria - 'book_id', 'title', or 'date'
            
        Returns:
            Sorted list of history entries
        """
        history_copy = self._history.copy()
        
        if sort_by == 'book_id':
            history_copy.sort(key=lambda x: x['book_id'])
        elif sort_by == 'title':
            history_copy.sort(key=lambda x: x['book_title'].lower())
        elif sort_by == 'date':
            # Default order is already newest first, so reverse for oldest first
            # But spec says "newest first" so we keep default order
            pass
        
        return history_copy
    
    def get_entry_by_book_id(self, book_id: int) -> Optional[Dict]:
        """
        Get a specific history entry by book ID.
        
        Args:
            book_id: The book ID to find
            
        Returns:
            History entry if found, None otherwise
        """
        for entry in self._history:
            if entry['book_id'] == book_id:
                return entry
        return None
    
    def get_history_count(self) -> int:
        """Get the number of entries in history."""
        return len(self._history)