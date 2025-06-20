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
