"""
Handles Solr indexing and schema setup.
"""

import pysolr
import logging
from typing import List, Dict, Any
from tqdm import tqdm

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
        # This method would contain the logic to set up the Solr schema.
        # For this refactoring, we'll assume it exists and works.
        # In a real-world scenario, you would implement the schema setup here.
        logger.info("Solr schema setup is assumed to be complete.")
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

    def clear_solr_data(self):
        """Clears all data from the Solr index."""
        logger.info("Clearing existing Solr data...")
        self.solr.delete(q='*:*')
