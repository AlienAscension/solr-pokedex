"""
API client for interacting with the PokeAPI.
"""

import requests
import time
import logging
from typing import Dict, Optional

from config import BASE_URL, REQUEST_DELAY

logger = logging.getLogger(__name__)

class ApiClient:
    """A client to handle requests to the PokeAPI."""

    def __init__(self):
        """Initializes the ApiClient."""
        self.session = requests.Session()

    def fetch_with_retry(self, url: str, max_retries: int = 3) -> Optional[Dict]:
        """
        Fetch data from the API with retry logic.

        Args:
            url: The API endpoint URL.
            max_retries: The maximum number of retry attempts.

        Returns:
            The JSON response data or None if it fails.
        """
        for attempt in range(max_retries):
            try:
                time.sleep(REQUEST_DELAY)  # Rate limiting
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"Failed to fetch {url} after {max_retries} attempts")
                    return None
                time.sleep(2 ** attempt)  # Exponential backoff
        return None

    def fetch_pokemon_basic_data(self, pokemon_id: int) -> Optional[Dict]:
        """
        Fetch basic Pokemon data (stats, types, abilities, etc.).

        Args:
            pokemon_id: The Pokemon ID number.

        Returns:
            The basic Pokemon data or None if it fails.
        """
        url = f"{BASE_URL}/pokemon/{pokemon_id}"
        return self.fetch_with_retry(url)

    def fetch_pokemon_species_data(self, pokemon_id: int) -> Optional[Dict]:
        """
        Fetch Pokemon species data (flavor text, color, habitat, etc.).

        Args:
            pokemon_id: The Pokemon ID number.

        Returns:
            The species data or None if it fails.
        """
        url = f"{BASE_URL}/pokemon-species/{pokemon_id}"
        return self.fetch_with_retry(url)
