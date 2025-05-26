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
    
    # Helper for mocking keyring state for relevant tests
def mock_keyring_state_fixture(mocker_fixture):
        _keyring_storage = {} # Simulate keyring storage
    
        def set_password_mock(service, username, password):
            _keyring_storage[(service, username)] = password
    
        def get_password_mock(service, username):
            return _keyring_storage.get((service, username))
    
        mocker_fixture.patch('librarian_assistant.config_manager.keyring.set_password', side_effect=set_password_mock)
        mocker_fixture.patch('librarian_assistant.config_manager.keyring.get_password', side_effect=get_password_mock)

def test_config_manager_load_token_initially_none(mocker): # Add mocker fixture
    """Tests that a new ConfigManager loads None if no token has been saved."""
    # Mock keyring.get_password to simulate no token being found
    # This ensures the test is isolated from the actual keyring state.
    mocked_keyring_get_password = mocker.patch('librarian_assistant.config_manager.keyring.get_password')
    mocked_keyring_get_password.return_value = None

    from librarian_assistant.config_manager import ConfigManager # Import for TDD
    config = ConfigManager()
    assert config.load_token() is None, "Should load None initially."
    # Verify that keyring.get_password was called as expected
    mocked_keyring_get_password.assert_called_once_with(SERVICE_NAME, USERNAME)

def test_config_manager_save_and_load_token(mocker): # Add mocker
    """Tests saving a token and then loading it."""
    mock_keyring_state_fixture(mocker)

    from librarian_assistant.config_manager import ConfigManager # Import for TDD
    config = ConfigManager()
    test_token = "my_secret_token_123"
    config.save_token(test_token)
    loaded_token = config.load_token()
    assert loaded_token == test_token, f"Loaded token '{loaded_token}' did not match saved token '{test_token}'."
    
def test_config_manager_overwrite_token(mocker): # Add mocker
    """Tests that saving a new token overwrites an existing one."""
    mock_keyring_state_fixture(mocker)

    from librarian_assistant.config_manager import ConfigManager # Import for TDD
    config = ConfigManager()
    initial_token = "initial_token"
    new_token = "new_updated_token"

    config.save_token(initial_token)
    assert config.load_token() == initial_token, "Initial token not saved correctly."

    config.save_token(new_token)
    loaded_token = config.load_token()
    assert loaded_token == new_token, f"Loaded token '{loaded_token}' should be the new token '{new_token}'."
    
def test_config_manager_save_empty_token(mocker): # Add mocker
    """Tests saving an empty token."""
    mock_keyring_state_fixture(mocker)

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