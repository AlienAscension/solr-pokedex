"""
Configuration for the Pokemon Data Fetcher
"""

import logging

# --- API and Solr Configuration ---
SOLR_URL = "http://localhost:8983/solr/pokemon"
BASE_URL = "https://pokeapi.co/api/v2"
REQUEST_DELAY = 0.1  # 100ms between requests

# --- Generation Limits ---
# Gen I: Bulbasaur to Mew
# Gen II: Chikorita to Celebi
# Gen III: Treecko to Deoxys
GEN_LIMITS = {
    1: (1, 15),
    2: (152, 161),
    3: (252, 266)
}

# --- Logging Configuration ---
def setup_logging():
    """Sets up the logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('pokemon_fetcher.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

