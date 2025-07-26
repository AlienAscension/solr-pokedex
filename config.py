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
# Gen IV: Turtwig to Arceus
# Gen V: Victini to Genesect
# Gen VI: Chespin to Volcanion
# Gen VII: Rowlet to Marshadow (plus Meltan/Melmetal optional)
# Gen VIII: Grookey to Enamorus
# Gen IX: Sprigatito to Pecharunt (as of July 2025)
GEN_LIMITS = {
    1: (1, 151),
    2: (152, 251),
    3: (252, 386),
    4: (387, 493),
    5: (494, 649),
    6: (650, 721),
    7: (722, 809),
    8: (810, 905),
    9: (906, 1025)  # Pecharunt is currently the last known Pokémon
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

