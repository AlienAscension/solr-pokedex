
"""
Processes data fetched from the PokeAPI.
"""

import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class DataProcessor:
    """Processes and cleans Pokemon data."""

    def clean_text(self, text: str) -> str:
        """
        Clean up text data from PokeAPI.

        Args:
            text: The raw text from PokeAPI.

        Returns:
            The cleaned text suitable for indexing.
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

    def extract_flavor_texts(self, species_data: Dict) -> str:
        """
        Extract and combine flavor texts from species data.

        Args:
            species_data: The raw species data from PokeAPI.

        Returns:
            The combined and cleaned flavor texts.
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
        Process and combine Pokemon data for Solr indexing.

        Args:
            basic_data: The basic Pokemon data from the /pokemon endpoint.
            species_data: The species data from the /pokemon-species endpoint.

        Returns:
            The processed data ready for Solr indexing.
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

        # Moves learned by leveling up
        levelup_moves = set() # Use a set to store unique move names
        for move_info in basic_data.get('moves', []):
            for version_detail in move_info.get('version_group_details', []):
                learn_method = version_detail.get('move_learn_method', {}).get('name')
                if learn_method == 'level-up':
                    move_name = move_info['move']['name'].replace('-', ' ').title()
                    levelup_moves.add(move_name)
        
        doc['levelup_moves'] = sorted(list(levelup_moves)) # Add the sorted list to the doc
        
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
