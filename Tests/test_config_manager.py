# ABOUTME: This file contains unit tests for the ConfigManager.
# ABOUTME: It ensures token saving and loading functionalities work as expected using the keyring library.

import pytest
# import keyring # Not strictly needed here if patching by string and not referencing keyring.errors directly

# This line is crucial for the tests to know about ConfigManager
from librarian_assistant.config_manager import ConfigManager 

# These constants should also be defined here for use in tests,
# or imported from config_manager if you prefer (though defining here is fine for tests).
SERVICE_NAME = "HardcoverApp" 
USERNAME = "BearerToken"

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

def test_config_manager_save_none_as_token(mocker): # Name was test_config_manager_save_none_token
    """
    Tests saving None. Assumes keyring might store it as string "None",
    and load_token handles this to return Python None.
    """
    mocked_keyring_module = mocker.patch('librarian_assistant.config_manager.keyring')
    config = ConfigManager()

    # Save some token first
    config.save_token("some_token_to_clear")
    mocked_keyring_module.set_password.assert_called_with(SERVICE_NAME, USERNAME, "some_token_to_clear")

    # Now save None
    config.save_token(None)
    mocked_keyring_module.set_password.assert_called_with(SERVICE_NAME, USERNAME, None)
    
    # Simulate keyring.get_password returning the string "None" if set_password(..., None) did that
    mocked_keyring_module.get_password.return_value = "None" 
    assert config.load_token() is None, "load_token should convert string 'None' from keyring to Python None."
    mocked_keyring_module.get_password.assert_called_with(SERVICE_NAME, USERNAME)