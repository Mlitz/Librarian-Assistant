# ABOUTME: This file defines the ConfigManager for handling application configuration.
# ABOUTME: It uses the keyring library for secure storage of the API Bearer Token.

import keyring
import logging

# Configure a logger for this module
logger = logging.getLogger(__name__)

SERVICE_NAME = "HardcoverApp"
USERNAME = "BearerToken"

class ConfigManager:
    """
    Manages configuration data for the Librarian-Assistant application,
    using the keyring library for secure token storage.
    """
    def __init__(self):
        """
        Initializes the ConfigManager.
        (No in-memory token storage needed anymore)
        """
        pass

    def save_token(self, token: str | None):
        try:
            # If token is None, keyring might store it as "None" string or empty.
            # The prompt is to call set_password with the token.
            actual_token_to_store = token 
            keyring.set_password(SERVICE_NAME, USERNAME, actual_token_to_store)
            logger.info("Token processed by keyring.set_password.")
        except Exception as e:
            logger.error(f"Error saving token to keyring: {e}")

    def load_token(self) -> str | None:
        try:
            stored_value = keyring.get_password(SERVICE_NAME, USERNAME)
            if stored_value is not None:
                logger.info(f"Value loaded from keyring: '{stored_value}'")
                # If keyring stored Python None as the string "None"
                if stored_value == "None":
                    return None
                return stored_value
            else:
                logger.info("No token found in keyring for the specified service/username.")
                return None
        except Exception as e:
            logger.error(f"Error loading token from keyring: {e}")
            return None