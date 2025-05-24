# ABOUTME: This file defines the ConfigManager for handling application configuration.
# ABOUTME: Initially, it provides simple in-memory storage for the API Bearer Token.

class ConfigManager:
    """
    Manages configuration data for the Librarian-Assistant application.
    For Prompt 2.2, this provides basic in-memory storage for the API token.
    Secure storage will be implemented in a later prompt.
    """
    def __init__(self):
        """
        Initializes the ConfigManager.
        The token is stored in an instance variable for now.
        """
        self._token = None  # Initialize token as None

    def save_token(self, token: str | None):
        """
        Saves the API Bearer Token.

        Args:
            token: The token string to save. Can be None to clear the token.
        """
        self._token = token

    def load_token(self) -> str | None:
        """
        Loads the API Bearer Token.

        Returns:
            The saved token string, or None if no token has been saved or if it was cleared.
        """
        return self._token