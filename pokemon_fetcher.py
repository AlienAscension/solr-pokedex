#!/usr/bin/env python3
"""
Pokemon Data Fetcher for Solr Search Engine

This script fetches Pokemon data from the first 3 generations (Gen I-III, Pokemon #1-386)
from PokeAPI and indexes it into Apache Solr for full-text search capabilities.

Features:
- Fetches basic Pokemon data (name, types, abilities, stats)
- Fetches species data (flavor text, color, habitat, etc.)
- Cleans up text data (removes \n, \f, etc.)
- Combines multiple flavor texts for better full text search
- Indexes data into Solr with proper field mapping

Requirements:
- requests
- pysolr
- tqdm (for progress bars)

Usage:
    python pokemon_fetcher.py

Author: Linus Breitenberger
"""

import requests
import pysolr
import json
import time
import re
from typing import Dict, List, Optional, Any
from tqdm import tqdm
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pokemon_fetcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PokemonFetcher:
    """
    Fetches Pokemon data from PokeAPI and indexes it into Solr
    """
    
    def __init__(self, solr_url: str = "http://localhost:8983/solr/pokemon"):
        """
        Initialize the Pokemon fetcher
        
        Args:
            solr_url: URL to the Solr core
        """
        self.base_url = "https://pokeapi.co/api/v2"
        self.solr = pysolr.Solr(solr_url, always_commit=True, timeout=10)
        self.session = requests.Session()
        
        # Rate limiting - be respectful to PokeAPI
        self.request_delay = 0.1  # 100ms between requests
        
        # Generation limits (first 3 generations)
        self.gen_limits = {
            1: (1, 151),    # Gen I: Bulbasaur to Mew
            2: (152, 251),  # Gen II: Chikorita to Celebi  
            3: (252, 386)   # Gen III: Treecko to Deoxys
        }
    
    def clean_text(self, text: str) -> str:
        """
        Clean up text data from PokeAPI
        
        Args:
            text: Raw text from PokeAPI
            
        Returns:
            Cleaned text suitable for indexing
        """
        if not text:
            return ""
        
        # Remove form feed characters, newlines, and extra spaces
        cleaned = re.sub(r'[\n\f\r\t]+', ' ', text)
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        # Strip leading/trailing whitespace
        cleaned = cleaned.strip()
        
        return cleaned
    
    def fetch_with_retry(self, url: str, max_retries: int = 3) -> Optional[Dict]:
        """
        Fetch data from API with retry logic
        
        Args:
            url: API endpoint URL
            max_retries: Maximum number of retry attempts
            
        Returns:
            JSON response data or None if failed
        """
        for attempt in range(max_retries):
            try:
                time.sleep(self.request_delay)  # Rate limiting
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
        Fetch basic Pokemon data (stats, types, abilities, etc.)
        
        Args:
            pokemon_id: Pokemon ID number
            
        Returns:
            Basic Pokemon data or None if failed
        """
        url = f"{self.base_url}/pokemon/{pokemon_id}"
        return self.fetch_with_retry(url)
    
    def fetch_pokemon_species_data(self, pokemon_id: int) -> Optional[Dict]:
        """
        Fetch Pokemon species data (flavor text, color, habitat, etc.)
        
        Args:
            pokemon_id: Pokemon ID number
            
        Returns:
            Species data or None if failed
        """
        url = f"{self.base_url}/pokemon-species/{pokemon_id}"
        return self.fetch_with_retry(url)
    
    def extract_flavor_texts(self, species_data: Dict) -> str:
        """
        Extract and combine flavor texts from species data
        
        Args:
            species_data: Raw species data from PokeAPI
            
        Returns:
            Combined and cleaned flavor texts
        """
        flavor_texts = []
        
        if 'flavor_text_entries' in species_data:
            # Prefer English flavor texts
            english_texts = [
                entry for entry in species_data['flavor_text_entries']
                if entry.get('language', {}).get('name') == 'en'
            ]
            
            # Get unique flavor texts (avoid duplicates)
            seen_texts = set()
            for entry in english_texts:
                text = self.clean_text(entry.get('flavor_text', ''))
                if text and text not in seen_texts:
                    flavor_texts.append(text)
                    seen_texts.add(text)
        
        return ' '.join(flavor_texts)
    
    def process_pokemon_data(self, basic_data: Dict, species_data: Dict) -> Dict[str, Any]:
        """
        Process and combine Pokemon data for Solr indexing
        
        Args:
            basic_data: Basic Pokemon data from /pokemon endpoint
            species_data: Species data from /pokemon-species endpoint
            
        Returns:
            Processed data ready for Solr indexing
        """
        # Basic information
        doc = {
            'id': str(basic_data['id']),
            'pokemon_id': basic_data['id'],
            'name': basic_data['name'].title(),
            'height': basic_data.get('height', 0),
            'weight': basic_data.get('weight', 0),
            'base_experience': basic_data.get('base_experience', 0),
        }
        
        # Types
        types = [type_info['type']['name'] for type_info in basic_data.get('types', [])]
        doc['types'] = types
        doc['primary_type'] = types[0] if types else 'unknown'
        doc['secondary_type'] = types[1] if len(types) > 1 else None
        
        # Abilities
        abilities = []
        hidden_abilities = []
        for ability_info in basic_data.get('abilities', []):
            ability_name = ability_info['ability']['name'].replace('-', ' ').title()
            if ability_info.get('is_hidden', False):
                hidden_abilities.append(ability_name)
            else:
                abilities.append(ability_name)
        
        doc['abilities'] = abilities
        doc['hidden_abilities'] = hidden_abilities
        doc['all_abilities'] = abilities + hidden_abilities
        
        # Stats
        stats = {}
        total_stats = 0
        for stat_info in basic_data.get('stats', []):
            stat_name = stat_info['stat']['name'].replace('-', '_')
            stat_value = stat_info['base_stat']
            stats[f'stat_{stat_name}'] = stat_value
            total_stats += stat_value
        
        doc.update(stats)
        doc['total_stats'] = total_stats
        
        # Species information
        if species_data:
            doc['color'] = species_data.get('color', {}).get('name', '')
            doc['habitat'] = species_data.get('habitat', {}).get('name', '') if species_data.get('habitat') else ''
            doc['base_happiness'] = species_data.get('base_happiness', 0)
            doc['capture_rate'] = species_data.get('capture_rate', 0)
            doc['is_legendary'] = species_data.get('is_legendary', False)
            doc['is_mythical'] = species_data.get('is_mythical', False)
            
            # Generation (based on ID ranges)
            pokemon_id = basic_data['id']
            generation = 1
            if 152 <= pokemon_id <= 251:
                generation = 2
            elif 252 <= pokemon_id <= 386:
                generation = 3
            doc['generation'] = generation
            
            # Flavor texts for full-text search
            doc['flavor_text'] = self.extract_flavor_texts(species_data)
            
            # Evolution chain info
            evolves_from = species_data.get('evolves_from_species')
            doc['evolves_from'] = evolves_from['name'].title() if evolves_from else None
        
        return doc
    
    def fetch_generation(self, generation: int) -> List[Dict[str, Any]]:
        """
        Fetch all Pokemon data for a specific generation
        
        Args:
            generation: Generation number (1, 2, or 3)
            
        Returns:
            List of processed Pokemon documents
        """
        if generation not in self.gen_limits:
            raise ValueError(f"Generation {generation} not supported. Use 1, 2, or 3.")
        
        start_id, end_id = self.gen_limits[generation]
        documents = []
        
        logger.info(f"Fetching Generation {generation} Pokemon (#{start_id}-#{end_id})")
        
        for pokemon_id in tqdm(range(start_id, end_id + 1), desc=f"Gen {generation}"):
            try:
                # Fetch basic Pokemon data
                basic_data = self.fetch_pokemon_basic_data(pokemon_id)
                if not basic_data:
                    logger.warning(f"Skipping Pokemon #{pokemon_id} - no basic data")
                    continue
                
                # Fetch species data
                species_data = self.fetch_pokemon_species_data(pokemon_id)
                if not species_data:
                    logger.warning(f"No species data for Pokemon #{pokemon_id}")
                
                # Process and combine data
                doc = self.process_pokemon_data(basic_data, species_data)
                documents.append(doc)
                
                logger.debug(f"Processed {doc['name']} (#{pokemon_id})")
                
            except Exception as e:
                logger.error(f"Error processing Pokemon #{pokemon_id}: {e}")
                continue
        
        return documents
    
    def index_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """
        Index documents into Solr
        
        Args:
            documents: List of Pokemon documents to index
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Indexing {len(documents)} documents into Solr...")
            
            # Index in batches to avoid memory issues
            batch_size = 50
            for i in tqdm(range(0, len(documents), batch_size), desc="Indexing"):
                batch = documents[i:i + batch_size]
                self.solr.add(batch)
            
            # Optimize the index for better search performance
            logger.info("Optimizing Solr index...")
            self.solr.optimize()
            
            logger.info("Successfully indexed all documents!")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing documents: {e}")
            return False
    
    def fetch_and_index_all_generations(self) -> bool:
        """
        Fetch and index Pokemon data for all 3 generations
        
        Returns:
            True if successful, False otherwise
        """
        all_documents = []
        
        try:
            # Clear existing data
            logger.info("Clearing existing Solr data...")
            self.solr.delete(q='*:*')
            
            # Fetch each generation
            for generation in [1, 2, 3]:
                gen_docs = self.fetch_generation(generation)
                all_documents.extend(gen_docs)
                logger.info(f"Generation {generation}: {len(gen_docs)} Pokemon fetched")
            
            # Index all documents
            success = self.index_documents(all_documents)
            
            if success:
                logger.info(f"Successfully processed {len(all_documents)} Pokemon total!")
                return True
            else:
                logger.error("Failed to index documents")
                return False
                
        except Exception as e:
            logger.error(f"Error in fetch_and_index_all_generations: {e}")
            return False

def main():
    """
    Main function to run the Pokemon data fetcher
    """
    print("Pokemon Data Fetcher for Solr Search Engine")
    print("=" * 50)
    
    # Initialize fetcher
    try:
        fetcher = PokemonFetcher()
        logger.info("Initialized Pokemon fetcher")
        
        # Test Solr connection
        fetcher.solr.ping()
        logger.info("Successfully connected to Solr")
        
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        logger.error("Make sure Solr is running at http://localhost:8983/solr/pokemon")
        return False
    
    # Fetch and index all generations
    success = fetcher.fetch_and_index_all_generations()
    
    if success:
        print("\n✅ Successfully fetched and indexed all Pokemon data!")
        print("🔍 You can now search using the web interface or Solr admin panel")
        print("📊 Solr Admin: http://localhost:8983/solr/#/pokemon")
    else:
        print("\n❌ Failed to fetch and index Pokemon data")
        print("📋 Check the logs for more details")
    
    return success

if __name__ == "__main__":
    main()