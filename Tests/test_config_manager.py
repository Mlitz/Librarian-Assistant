# ABOUTME: This file contains unit tests for the ConfigManager.
# ABOUTME: It ensures token saving and loading functionalities work as expected.

import pytest

# Assuming ConfigManager will be in librarian_assistant.config_manager
# from librarian_assistant.config_manager import ConfigManager # This will be created

def test_config_manager_load_token_initially_none():
    """Tests that a new ConfigManager loads None if no token has been saved."""
    from librarian_assistant.config_manager import ConfigManager # Import for TDD
    config = ConfigManager()
    assert config.load_token() is None, "Should load None initially."

def test_config_manager_save_and_load_token():
    """Tests saving a token and then loading it."""
    from librarian_assistant.config_manager import ConfigManager # Import for TDD
    config = ConfigManager()
    test_token = "my_secret_token_123"
    config.save_token(test_token)
    loaded_token = config.load_token()
    assert loaded_token == test_token, f"Loaded token '{loaded_token}' did not match saved token '{test_token}'."

def test_config_manager_overwrite_token():
    """Tests that saving a new token overwrites an existing one."""
    from librarian_assistant.config_manager import ConfigManager # Import for TDD
    config = ConfigManager()
    initial_token = "initial_token"
    new_token = "new_updated_token"
    
    config.save_token(initial_token)
    assert config.load_token() == initial_token, "Initial token not saved correctly."
    
    config.save_token(new_token)
    loaded_token = config.load_token()
    assert loaded_token == new_token, f"Loaded token '{loaded_token}' should be the new token '{new_token}'."

def test_config_manager_save_empty_token():
    """Tests saving an empty token."""
    from librarian_assistant.config_manager import ConfigManager # Import for TDD
    config = ConfigManager()
    config.save_token("")
    assert config.load_token() == "", "Should be able to save and load an empty token."

def test_config_manager_save_none_as_token():
    """Tests saving None as a token (e.g., to clear it)."""
    from librarian_assistant.config_manager import ConfigManager # Import for TDD
    config = ConfigManager()
    config.save_token("some_token_to_clear")
    config.save_token(None) # Clearing the token
    assert config.load_token() is None, "Saving None should result in load_token returning None."