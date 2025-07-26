# Solr Pokédex
A Pokémon search application using Apache Solr for indexing and search functionality, with a Python Flask web interface.

## Project Structure
```
solr-pokedex/
├── docker-compose.yml          # Docker compose configuration
├── main.py                    # Main Pokemon data fetcher script
├── api_client.py              # Pokemon API client module
├── data_processor.py          # Data processing and transformation
├── solr_indexer.py            # Solr indexing and schema management
├── config.py                  # Configuration and logging setup
├── install.sh                 # Automated setup script
├── test.py                    # Comprehensive test suite
├── LICENSE                    # Project license
├── README.md                  # This file
├── requirements.txt           # Python dependencies
├── solr/                      # Solr configuration
│   └── configsets/           # Solr schema configurations
└── web/                      # Web application
    ├── Dockerfile            # Web app Docker configuration
    ├── requirements.txt      # Web app specific dependencies
    ├── templates/            # HTML templates
    ├── static/               # CSS and JavaScript files
    └── web_app.py           # Flask web application
```

## Prerequisites
- **Docker/Podman**: Container runtime
- **Docker Compose/Podman Compose**: Container orchestration
- **Python 3.x**: For running the fetcher script

## Setup Instructions

### Option 1: Automated Setup (Recommended)
Run the provided installation script to automatically set up the environment:

```bash
chmod +x install.sh
./install.sh
```

The script will handle:
- Creating the Python virtual environment
- Installing dependencies
- Making main.py executable
- Starting the Solr service
- Fetching and indexing Pokémon data

### Option 2: Manual Setup
If you prefer to set up manually or need to troubleshoot:


#### 1. Clone this Repo
```
git clone https://github.com/AlienAscension/solr-pokedex
```


#### 2. Create Python Virtual Environment
Navigate to the project root directory and create a virtual environment:
```bash
python3 -m venv venv
```

#### 3. Activate Virtual Environment
**On Linux/macOS:**
```bash
source venv/bin/activate
```
**On Windows PowerShell:** (untested)
```powershell
venv\Scripts\Activate.ps1
```

#### 4. Install Dependencies
With the virtual environment activated, install the required packages:
```bash
pip install -r requirements.txt
```

#### 5. Make Main Script Executable
```bash
chmod +x main.py
```

#### 6. Start Solr Service
Start the Solr container using Docker Compose:
```bash
docker compose up -d
```
Or with Podman:
```bash
podman compose up -d
```

#### 7. Fetch Pokémon Data
Run the main script to populate Solr with Pokémon data:
```bash
./main.py
```

## Usage
After setup (using either method), the web application should be available at:
```
http://localhost:5000
```

Apache Solr admin interface is available at:
```
http://localhost:8983
```

### API Endpoints
The web application provides several API endpoints:
- `GET /api/search` - Main search endpoint with enhanced substring matching
- `GET /api/autocomplete` - Real-time autocomplete suggestions
- `GET /api/pokemon/<id>` - Individual Pokémon details
- `GET /api/stats` - Search statistics and collection overview

## How to Use the Search Interface
The search bar provides a powerful way to find Pokémon using simple text or advanced Solr query syntax. The engine supports several types of searches with intelligent autocomplete suggestions:

### Search Capabilities

*   **Autocomplete Suggestions**: As you type, the search bar provides real-time suggestions based on Pokémon names, types, and abilities. The autocomplete supports:
    *   **Substring Matching**: Typing `saur` will suggest Bulbasaur, Ivysaur, and Venusaur
    *   **Case-Insensitive**: Works regardless of capitalization (`bulba`, `BULBA`, or `Bulba` all work)
    *   **Keyboard Navigation**: Use arrow keys to navigate suggestions, Enter to select, Escape to close
    *   **Visual Highlighting**: Matching parts of suggestions are highlighted in bold

*   **Enhanced Substring Search**: The search engine now intelligently handles partial matches anywhere in Pokémon names:
    *   **Example:** Searching for `saur` will find all Pokémon ending in "-saur" (Bulbasaur, Ivysaur, Venusaur)
    *   **Example:** Searching for `char` will find Charmander, Charmeleon, and Charizard
    *   **Example:** Searching for `pika` will find Pikachu and related Pokémon

*   **Keyword Search**: This is the default search behavior. Simply typing a term into the search bar performs a broad, case-insensitive search across key fields like Pokémon Name, Types, Abilities, and Flavor Text.
    *   **Example:** A search for `stone` will find Pokémon of the `rock` type (a synonym), Pokémon like `Onix` (described as a stone snake), and Pokémon with abilities like `Sturdy`.

*   **Phrase Search**: To search for an exact sequence of words, enclose the phrase in double quotes (`"`). The search will look for the exact phrase in the Pokémon's name and flavor text.
    *   **Example:** `"stores electricity in its cheeks"` will find Pokémon like Pikachu and Pichu, without needing a field specifier.

*   **Wildcard Search**: Use the asterisk (`*`) as a wildcard to match any sequence of characters. This is automatically used in keyword searches but can also be used in advanced field-based searches.
    *   **Example:** In an advanced query, `name:*saur` will find Bulbasaur, Ivysaur, and Venusaur.

*   **Faceted Search**: This feature allows you to refine and filter your search results. The UI displays available filters (like Generation, Primary Type, Legendary) along with a count of matching Pokémon for each filter. Clicking on these categories allows you to progressively narrow down your results.

### Advanced (Field-Based) Search
For more specific queries, you can still use the `field:value` syntax in the search bar.

**Syntax:** `fieldName:searchTerm`

**Commonly Used Fields:**
- `pokemon_id`: The official Pokédex number (e.g., `pokemon_id:25`)
- `name`: The Pokémon's name. Supports wildcards (e.g., `name:*saur`)
- `primary_type`: The primary type (e.g., `primary_type:fire`)
- `generation`: The game generation (e.g., `generation:1`)
- `all_abilities`: Searches both regular and hidden abilities (e.g., `all_abilities:intimidate`)
- `is_legendary`: `true` or `false`
- `base_attack`, `base_defense`, `base_hp`: Base stat values. Supports range queries (e.g., `base_attack:[121 TO *]`)

### Combining Queries
You can combine multiple queries using boolean operators `AND`, `OR`, and `NOT`. You can use parentheses `()` to group conditions.

**Examples:**
- Find Fire or Water type Pokémon: `primary_type:fire OR primary_type:water`
- Find Generation 1 Pokémon that are also Legendary: `generation:1 AND is_legendary:true`
- Find Generation 1 Ghost type Pokémon or Generation 2 Fairy type Pokémon: `(generation:1 AND primary_type:ghost) OR (generation:1 AND primary_type:fairy)`

## Testing
The project includes a comprehensive test suite (`test.py`) for evaluating the search engine's functionality, performance, and the relevance of its search results.

### Running the Tests
To run the test suite, execute the following command from the project root directory:
```bash
python3 test.py
```
You can also specify the URL of the running web application and an output file for the results:
```bash
python3 test.py --url http://localhost:5000 --output results.json
```

### Test Coverage
The test suite evaluates various search scenarios, including:
- **Exact and partial name searches**
- **Type and ability-based searches**
- **Autocomplete and spellcheck suggestions**
- **Filter combinations and edge cases**
- **Ranking quality and performance**

### Information Retrieval Metrics
To ensure search relevance, the test suite calculates and reports on key Information Retrieval (IR) metrics:
- **Precision, Recall, and F-Measure**: Overall effectiveness of the search.
- **Top-K Analysis (P@k, R@k)**: Precision and recall within the top K results.
- **Mean Reciprocal Rank (MRR)**: How high the first relevant result is ranked.
- **Normalized Discounted Cumulative Gain (NDCG)**: The quality of the ranking, rewarding higher placement for more relevant items.
- **Average Precision (AP)**: A summary measure of ranking quality.

The script uses a predefined "ground truth" set to compare search results against expected outcomes, allowing for robust and objective evaluation of the search engine's quality.

## Features
- **Enhanced Search Interface**: Web-based search for Pokémon with intelligent autocomplete
- **Real-time Autocomplete**: Instant suggestions as you type, supporting substring matching anywhere in Pokémon names
- **Smart Search**: Case-insensitive search with enhanced substring matching (e.g., "saur" finds all "-saur" Pokémon)
- **Solr Integration**: Fast, scalable search using Apache Solr
- **Data Fetching**: Automated script to populate the search index. Fetcher is rate limited to 100ms, to respect the usage guidelines of https://pokeapi.co/
- **Containerized**: Easy deployment with Docker/Podman
- **Comprehensive Testing**: Includes a test suite with IR metrics for quality assurance.

## Development
### Project Components
- **`install.sh`**: Automated setup script for quick deployment
- **`main.py`**: Main script that orchestrates the data fetching and indexing process
- **`api_client.py`**: Handles communication with the Pokemon API
- **`data_processor.py`**: Processes and transforms Pokemon data for indexing
- **`solr_indexer.py`**: Manages Solr schema setup and document indexing
- **`config.py`**: Configuration settings and logging setup
- **`test.py`**: Comprehensive test suite with performance and IR metric evaluation.
- **`web/web_app.py`**: Flask web application providing the search interface with autocomplete
- **`web/static/`**: Frontend assets (CSS, JavaScript) for the search interface
- **`solr/configsets/`**: Solr schema and configuration files
- **`docker-compose.yml`**: Defines the multi-container application setup

### Logs
Check `pokemon_fetcher.log` for data fetching logs and debugging information.

## Troubleshooting
1. **Installation Script Issues**: If `install.sh` fails, try the manual setup method
2. **Container Issues**: Ensure Docker/Podman is running and you have sufficient permissions
3. **Port Conflicts**: Check if ports 5000 (web app) and 8983 (Solr) are available
4. **Virtual Environment**: Make sure the virtual environment is activated before running the fetcher
5. **Dependencies**: Verify all requirements are installed with `pip list`

## License
This project is licensed under the terms specified in the LICENSE file.

