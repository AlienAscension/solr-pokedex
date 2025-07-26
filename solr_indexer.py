"""
Handles Solr indexing and schema setup.
"""

import pysolr
import logging
from typing import List, Dict, Any
from tqdm import tqdm
import requests
import json

from config import SOLR_URL

logger = logging.getLogger(__name__)

class SolrIndexer:
    """Manages indexing documents into Solr."""

    def __init__(self):
        """Initializes the SolrIndexer."""
        self.solr = pysolr.Solr(SOLR_URL, always_commit=True, timeout=10)
        self.schema_url = f"{SOLR_URL.rstrip('/')}/schema"

    def setup_solr_schema(self) -> bool:
        """
        Configures the Solr schema with the required fields.

        Returns:
            True if the schema setup is successful, False otherwise.
        """
        logger.info("Setting up Solr schema...")
        
        fields_to_configure = [
        # Field that caused the original error
        {'name': 'pokemon_id', 'type': 'pint', 'multiValued': False, 'docValues': True, 'indexed': False, 'stored': True},
        
        # Other fields good for sorting/faceting
        {'name': 'name', 'type': 'string', 'docValues': True, 'indexed': True, 'stored': True},
        {'name': 'height', 'type': 'pint', 'docValues': True, 'indexed': False, 'stored': True},
        {'name': 'weight', 'type': 'pint', 'docValues': True, 'indexed': False, 'stored': True},
        {'name': 'base_experience', 'type': 'pint', 'docValues': True, 'indexed': False, 'stored': True},
        {'name': 'primary_type', 'type': 'string', 'docValues': True, 'indexed': True, 'stored': True},
        {'name': 'total_stats', 'type': 'pint', 'docValues': True, 'indexed': False, 'stored': True},
        {'name': 'generation', 'type': 'pint', 'docValues': True, 'indexed': True, 'stored': True},
        {'name': 'color', 'type': 'string', 'docValues': True, 'indexed': False, 'stored': True},
        {'name': 'habitat', 'type': 'string', 'docValues': True, 'indexed': False, 'stored': True},
        {'name': 'capture_rate', 'type': 'pint', 'docValues': True, 'indexed': False, 'stored': True},
        {'name': 'is_legendary', 'type': 'boolean', 'docValues': True, 'indexed': True, 'stored': True},
        {'name': 'is_mythical', 'type': 'boolean', 'docValues': True, 'indexed': True, 'stored': True},
        
        # All individual stats - used only for sorting/display
        {'name': 'stat_hp', 'type': 'pint', 'docValues': True, 'indexed': False, 'stored': True},
        {'name': 'stat_attack', 'type': 'pint', 'docValues': True, 'indexed': False, 'stored': True},
        {'name': 'stat_defense', 'type': 'pint', 'docValues': True, 'indexed': False, 'stored': True},
        {'name': 'stat_special_attack', 'type': 'pint', 'docValues': True, 'indexed': False, 'stored': True},
        {'name': 'stat_special_defense', 'type': 'pint', 'docValues': True, 'indexed': False, 'stored': True},
        {'name': 'stat_speed', 'type': 'pint', 'docValues': True, 'indexed': False, 'stored': True},

        # Add definitions for other fields created by the script
        {'name': 'id', 'type': 'string', 'required': True, 'indexed': True, 'stored': True},
        {'name': 'flavor_text', 'type': 'text_general', 'indexed': True, 'stored': True},
        {'name': 'types', 'type': 'strings', 'indexed': True, 'stored': True},
        {'name': 'secondary_type', 'type': 'string', 'indexed': True, 'stored': True},
        {'name': 'abilities', 'type': 'strings', 'indexed': True, 'stored': True},
        {'name': 'hidden_abilities', 'type': 'strings', 'indexed': True, 'stored': True},
        {'name': 'all_abilities', 'type': 'strings', 'indexed': True, 'stored': True},
        {'name': 'evolves_from', 'type': 'string', 'indexed': True, 'stored': True},
        {'name': 'name_spell', 'type': 'text_general', 'indexed': True, 'stored': True, 'multiValued': True, 'termVectors': True},
        {'name': 'spellcheck_base', 'type': 'text_general', 'indexed': True, 'stored': True, 'multiValued': True},
        {'name': 'levelup_moves', 'type': 'strings', 'multiValued': True, 'indexed': True, 'stored': True},
    ]
        
        copy_fields_to_configure = [
            {'source': 'name', 'dest': 'name_spell'},
        ]

        headers = {'Content-type': 'application/json'}
        
        for field_config in fields_to_configure:
            field_name = field_config['name']
            try:
                # Check if field already exists
                response = requests.get(f"{self.schema_url}/fields/{field_name}")
                if response.status_code == 200:
                    logger.info(f"Field '{field_name}' already exists. Skipping.")
                    continue
                
                # Add field
                payload = {"add-field": field_config}
                response = requests.post(f"{self.schema_url}", headers=headers, data=json.dumps(payload))
                response.raise_for_status()
                logger.info(f"Successfully added field '{field_name}'.")
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 400 and "already exists" in e.response.text:
                    logger.info(f"Field '{field_name}' already exists. Skipping.")
                else:
                    logger.error(f"Error adding field '{field_name}': {e}")
                    return False
            except Exception as e:
                logger.error(f"An unexpected error occurred while adding field '{field_name}': {e}")
                return False

        for copy_field_config in copy_fields_to_configure:
            source_field = copy_field_config['source']
            dest_field = copy_field_config['dest']
            try:
                # Check if copy field already exists (this is a bit trickier, often easier to just try adding)
                # Solr will return 400 if it already exists, which we can catch
                payload = {"add-copy-field": copy_field_config}
                response = requests.post(f"{self.schema_url}", headers=headers, data=json.dumps(payload))
                response.raise_for_status()
                logger.info(f"Successfully added copy field from '{source_field}' to '{dest_field}'.")
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 400 and "already exists" in e.response.text:
                    logger.info(f"Copy field from '{source_field}' to '{dest_field}' already exists. Skipping.")
                else:
                    logger.error(f"Error adding copy field from '{source_field}' to '{dest_field}': {e}")
                    return False
            except Exception as e:
                logger.error(f"An unexpected error occurred while adding copy field from '{source_field}' to '{dest_field}': {e}")
                return False
        
        logger.info("Solr schema setup complete.")
        return True

    def index_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """
        Index documents into Solr.

        Args:
            documents: A list of Pokemon documents to index.

        Returns:
            True if successful, False otherwise.
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

    def build_spellcheck_dictionary(self):
        """
        Explicitly builds the spellcheck dictionary in Solr.
        """
        logger.info("Building Solr spellcheck dictionary...")
        try:
            # Reload the Solr core to ensure schema changes are picked up
            reload_url = f"{self.solr.url.rsplit('/', 1)[0]}/admin/cores?action=RELOAD&core={self.solr.url.rsplit('/', 1)[1].split('/')[0]}"
            reload_response = requests.get(reload_url)
            reload_response.raise_for_status()
            logger.info(f"Solr core reloaded: {reload_response.text}")

            # Use the Solr SpellCheckComponent's build command
            response = requests.get(f"{self.solr.url}/spell?spellcheck.build=true&spellcheck.dictionary=default")
            response.raise_for_status()
            logger.info(f"Solr spellcheck dictionary build response: {response.text}")
            logger.info("Solr spellcheck dictionary built successfully.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error building spellcheck dictionary: {e}")

    def clear_solr_data(self):
        """Clears all data from the Solr index."""
        logger.info("Clearing existing Solr data...")
        self.solr.delete(q='*:*')
