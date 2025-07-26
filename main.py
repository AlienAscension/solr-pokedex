
"""
Main script to fetch Pokemon data and index it into Solr.
"""


import logging
from tqdm import tqdm

from config import setup_logging, GEN_LIMITS
from api_client import ApiClient
from data_processor import DataProcessor
from solr_indexer import SolrIndexer

logger = setup_logging()

def main():
    """Main function to run the Pokemon data fetcher."""
    print("Pokemon Data Fetcher for Solr Search Engine")
    print("=" * 50)

    try:
        api_client = ApiClient()
        data_processor = DataProcessor()
        solr_indexer = SolrIndexer()

        logger.info("Initialized all components.")

        # Test Solr connection
        solr_indexer.solr.ping()
        logger.info("Successfully connected to Solr")

    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        logger.error("Make sure Solr is running.")
        return

    if not solr_indexer.setup_solr_schema():
        logger.error("Halting script due to schema setup failure.")
        print("\n❌ Failed to configure the Solr schema. Please check the logs.")
        return

    all_documents = []
    solr_indexer.clear_solr_data()

    for gen, (start_id, end_id) in GEN_LIMITS.items():
        logger.info(f"Fetching Generation {gen} Pokemon (#{start_id}-#{end_id})")
        for pokemon_id in tqdm(range(start_id, end_id + 1), desc=f"Gen {gen}"):
            try:
                basic_data = api_client.fetch_pokemon_basic_data(pokemon_id)
                if not basic_data:
                    logger.warning(f"Skipping Pokemon #{pokemon_id} - no basic data")
                    continue

                species_data = api_client.fetch_pokemon_species_data(pokemon_id)
                if not species_data:
                    logger.warning(f"No species data for Pokemon #{pokemon_id}")

                doc = data_processor.process_pokemon_data(basic_data, species_data)
                all_documents.append(doc)

                logger.debug(f"Processed {doc['name']} (#{pokemon_id})")

            except Exception as e:
                logger.error(f"Error processing Pokemon #{pokemon_id}: {e}")
                continue

    success = solr_indexer.index_documents(all_documents)

    if success:
        print("\n✅ Successfully fetched and indexed all Pokemon data!")
        print("🔍 You can now search using the web interface or Solr admin panel")
    else:
        print("\n❌ Failed to fetch and index Pokemon data")
        print("📋 Check the logs for more details")

if __name__ == "__main__":
    main()
