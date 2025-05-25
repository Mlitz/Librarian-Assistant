# ABOUTME: This file contains unit tests for the ConfigManager.
# ABOUTME: It ensures token saving and loading functionalities work as expected using the keyring library.

import pytest
# We might need to import specific keyring errors if ConfigManager catches them explicitly.
# For now, we'll use a generic Exception for side_effect in tests.
# e.g., from keyring.errors import NoKeyringError 

from librarian_assistant.config_manager import ConfigManager # Ensure this path is correct

SERVICE_NAME = "HardcoverApp"
USERNAME = "BearerToken"

# Test for initial load (keyring returns None)
def test_config_manager_load_token_initially_none(mocker):
    """Tests that ConfigManager loads None if no token is found by keyring."""
    # Mock keyring module as it's used in config_manager.py
    mocked_keyring_module = mocker.patch('librarian_assistant.config_manager.keyring')
    mocked_keyring_module.get_password.return_value = None
    
    config = ConfigManager()
    assert config.load_token() is None, "Should load None initially."
    mocked_keyring_module.get_password.assert_called_once_with(SERVICE_NAME, USERNAME)

# Test for saving and loading a token
def test_config_manager_save_and_load_token(mocker):
    """Tests saving a token via keyring and then loading it."""
    mocked_keyring_module = mocker.patch('librarian_assistant.config_manager.keyring')
    
    config = ConfigManager()
    test_token = "my_secret_token_123"
    
    # Test saving: save_token should call keyring.set_password
    config.save_token(test_token)
    mocked_keyring_module.set_password.assert_called_once_with(SERVICE_NAME, USERNAME, test_token)
    
    # Test loading: load_token should call keyring.get_password
    # Configure mock for this specific load call
    mocked_keyring_module.get_password.return_value = test_token 
    loaded_token = config.load_token()
    assert loaded_token == test_token
    # Ensure get_password was called (could be multiple times if tests run in certain orders,
    # so assert_called_with is better than assert_called_once here if reset_mock isn't used between phases)
    mocked_keyring_module.get_password.assert_called_with(SERVICE_NAME, USERNAME)

# Test overwriting a token
def test_config_manager_overwrite_token(mocker):
    """Tests that saving a new token overwrites an existing one via keyring."""
    mocked_keyring_module = mocker.patch('librarian_assistant.config_manager.keyring')
    
    config = ConfigManager()
    initial_token = "initial_token_xyz"
    new_token = "new_updated_token_xyz"
    
    # First save
    config.save_token(initial_token)
    mocked_keyring_module.set_password.assert_called_with(SERVICE_NAME, USERNAME, initial_token)
    
    # Simulate that keyring now has initial_token for an intermediate load
    mocked_keyring_module.get_password.return_value = initial_token
    assert config.load_token() == initial_token 

    # Second save (overwrite)
    config.save_token(new_token)
    # Assert set_password was called with the new_token. 
    # If called multiple times, the last call should be this one.
    mocked_keyring_module.set_password.assert_called_with(SERVICE_NAME, USERNAME, new_token)
    assert mocked_keyring_module.set_password.call_count == 2 # Assuming fresh mock or reset

    # Load after overwrite
    mocked_keyring_module.get_password.return_value = new_token # Keyring now returns the new token
    loaded_token = config.load_token()
    assert loaded_token == new_token
    # Check that get_password was called at least for the two load_token calls
    assert mocked_keyring_module.get_password.call_count >= 2


# Test saving an empty token
def test_config_manager_save_empty_token(mocker):
    """Tests saving an empty token string via keyring."""
    mocked_keyring_module = mocker.patch('librarian_assistant.config_manager.keyring')
    config = ConfigManager()
    
    config.save_token("")
    mocked_keyring_module.set_password.assert_called_once_with(SERVICE_NAME, USERNAME, "")
    
    mocked_keyring_module.get_password.return_value = "" # Simulate keyring storing/returning empty string
    assert config.load_token() == ""
    mocked_keyring_module.get_password.assert_called_with(SERVICE_NAME, USERNAME)

# Test saving None as token
def test_config_manager_save_none_token(mocker):
    """
    Tests saving None as a token. Expects keyring.set_password(..., None) to be called
    as per strict interpretation of Prompt 2.3.
    """
    mocked_keyring_module = mocker.patch('librarian_assistant.config_manager.keyring')
    config = ConfigManager()

    # Initial save to have something to overwrite/clear
    config.save_token("some_initial_value")
    mocked_keyring_module.set_password.assert_called_with(SERVICE_NAME, USERNAME, "some_initial_value")

    # Save None
    config.save_token(None)
    # This will call keyring.set_password(SERVICE_NAME, USERNAME, None)
    # which might be problematic for keyring, but we test the call was made.
    # The error handling test for save_token should cover if keyring itself errors.
    mocked_keyring_module.set_password.assert_called_with(SERVICE_NAME, USERNAME, None)
    
    # If save_token(None) implies deletion or keyring stores it as retrievable None
    mocked_keyring_module.get_password.return_value = None 
    assert config.load_token() is None
    mocked_keyring_module.get_password.assert_called_with(SERVICE_NAME, USERNAME)

# --- New tests for keyring error handling (as per Prompt 2.3) ---

def test_load_token_handles_keyring_exception_and_logs(mocker, caplog):
    """
    Tests that load_token handles keyring exceptions gracefully (returns None and logs error).
    """
    mocked_keyring_module = mocker.patch('librarian_assistant.config_manager.keyring')
    # Simulate a keyring error (e.g., NoKeyringError or any other Exception)
    mocked_keyring_module.get_password.side_effect = Exception("Simulated Keyring Access Failed")
    
    config = ConfigManager()
    loaded_token = config.load_token()
    
    assert loaded_token is None, "load_token should return None on keyring exception."
    mocked_keyring_module.get_password.assert_called_once_with(SERVICE_NAME, USERNAME)
    # Check for log messages (requires ConfigManager to implement logging)
    assert "Error loading token from keyring" in caplog.text
    assert "Simulated Keyring Access Failed" in caplog.text

def test_save_token_handles_keyring_exception_and_logs(mocker, caplog):
    """
    Tests that save_token handles keyring exceptions gracefully (logs error and doesn't crash).
    """
    mocked_keyring_module = mocker.patch('librarian_assistant.config_manager.keyring')
    error_message = "Simulated Keyring Set Failed"
    mocked_keyring_module.set_password.side_effect = Exception(error_message)
    
    config = ConfigManager()
    test_token = "token_that_will_fail_to_save"
    
    # The save_token method itself should not raise the exception.
    try:
        config.save_token(test_token)
    except Exception as e_raised:
        pytest.fail(f"ConfigManager.save_token raised an unexpected exception: {e_raised}")
        
    mocked_keyring_module.set_password.assert_called_once_with(SERVICE_NAME, USERNAME, test_token)
    # Check for log messages
    assert "Error saving token to keyring" in caplog.text
    assert error_message in caplog.text