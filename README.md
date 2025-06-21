# Solr Pokédex
A Pokémon search application using Apache Solr for indexing and search functionality, with a Python Flask web interface.

## Project Structure
```
solr-pokedex/
├── docker-compose.yml          # Docker compose configuration
├── fetcher_v2.py              # Pokemon data fetcher script
├── install.sh                 # Automated setup script
├── LICENSE                    # Project license
├── README.md                  # This file
├── requirements.txt           # Python dependencies
├── solr/                      # Solr configuration
│   └── configsets/           # Solr schema configurations
└── web/                      # Web application
    ├── Dockerfile            # Web app Docker configuration
    ├── requirements.txt      # Web app specific dependencies
    ├── templates/            # HTML templates
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
- Making scripts executable
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

#### 5. Make Fetcher Script Executable
```bash
chmod +x fetcher_v2.py
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
Run the fetcher script to populate Solr with Pokémon data:
```bash
./fetcher_v2.py
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

## How to Use the Search Interface
The search bar provides a powerful way to find Pokémon using simple text or advanced Solr query syntax. The engine supports several types of searches:

### Search Capabilities

*   **Keyword Search**: This is the default search behavior. Simply typing a term into the search bar performs a broad, case-insensitive search across key fields like Pokémon Name, Types, Abilities, and Flavor Text.
    *   **Example:** A search for `stone` will find Pokémon of the `rock` type (a synonym), Pokémon like `Onix` (described as a stone snake), and Pokémon with abilities like `Sturdy`.

*   **Phrase Search**: To search for an exact sequence of words, enclose the phrase in double quotes (`"`). The search will look for the exact phrase in the Pokémon's name and flavor text.
    *   **Example:** `"stores electricity in its cheeks"` will  find Pokémon like Pikachu and Pichu, without needing a field specifier.

*   **Wildcard Search**: Use the asterisk (`*`) as a wildcard to match any sequence of characters. This is automatically used in keyword searches but can also be used in advanced field-based searches.
    *   **Example:** In an advanced query, `name:*saur` will find Bulbasaur, Ivysaur, and Venusaur.

*   **Faceted Search **: This feature allows you to refine and filter your search results. The UI displays available filters (like Generation, Primary Type, Legendary) along with a count of matching Pokémon for each filter. Clicking on these categories allows you to progressively narrow down your results.

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

## Features
- **Search Interface**: Web-based search for Pokémon
- **Solr Integration**: Fast, scalable search using Apache Solr
- **Data Fetching**: Automated script to populate the search index. Fetcher is rate limited to 100ms, to respect the usage guidelines of https://pokeapi.co/
- **Containerized**: Easy deployment with Docker/Podman

## Development
### Project Components
- **`install.sh`**: Automated setup script for quick deployment
- **`fetcher_v2.py`**: Fetches Pokémon data and indexes it into Solr
- **`web/web_app.py`**: Flask web application providing the search interface
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
