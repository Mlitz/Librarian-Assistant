# ABOUTME: This file defines the ImageDownloader class for fetching images from URLs.
# ABOUTME: It will handle downloading image data and potentially caching.

import logging
import requests # Import the requests library
from PyQt5.QtGui import QPixmap # Import QPixmap

logger = logging.getLogger(__name__)

class ImageDownloader:
    """A utility class for downloading images."""
    
    def download_image(self, url: str) -> QPixmap | None:
        """
        Downloads an image from the given URL and returns it as a QPixmap.
        Returns None if the download fails or the data is not a valid image.
        """
        if not url:
            logger.warning("Image download requested with no URL.")
            return None
        
        try:
            logger.info(f"Attempting to download image from: {url}")
            response = requests.get(url, stream=True) # stream=True is good for binary files
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
            
            pixmap = QPixmap()
            if pixmap.loadFromData(response.content):
                logger.info(f"Successfully loaded image into QPixmap from: {url}")
                return pixmap
            else:
                logger.error(f"Failed to load image data into QPixmap from: {url}. Data might be corrupt or not an image.")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading image from {url}: {e}")
            return None