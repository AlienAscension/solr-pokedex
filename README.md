# Solr Pokédex

A Pokémon search application using Apache Solr for indexing and search functionality, with a Python Flask web interface.

## Project Structure

```
solr-pokedex/
├── docker-compose.yml          # Docker compose configuration
├── fetcher_v2.py              # Pokemon data fetcher script
├── LICENSE                    # Project license
├── pokemon_fetcher.log        # Fetcher log file
├── README.md                  # This file
├── requirements.txt           # Python dependencies
├── solr/                      # Solr configuration
│   └── configsets/           # Solr schema configurations
├── venv/                     # Python virtual environment
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

### 1. Create Python Virtual Environment

Navigate to the project root directory and create a virtual environment:

```bash
python3 -m venv venv
```

### 2. Activate Virtual Environment

**On Linux/macOS:**
```bash
source venv/bin/activate
```

**On Windows PowerShell:** (untested)
```powershell
venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

With the virtual environment activated, install the required packages:

```bash
pip install -r requirements.txt
```

### 4. Make Fetcher Script Executable

```bash
chmod +x fetcher_v2.py
```

## Usage

### 1. Start Solr Service

Start the Solr container using Docker Compose:

```bash
docker-compose up -d
```

Or with Podman:

```bash
podman-compose up -d
```

### 2. Fetch Pokémon Data

Run the fetcher script to populate Solr with Pokémon data:

```bash
./fetcher_v2.py
```

This script will:
- Fetch Pokémon data from the API
- Index the data into Solr
- Log the process to `pokemon_fetcher.log`

### 3. Start Web Application

The web application should be available after the Docker containers are running. Access it at:

```
http://localhost:5000
```

Apache Solr is available at:

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

- **`fetcher_v2.py`**: Fetches Pokémon data and indexes it into Solr
- **`web/web_app.py`**: Flask web application providing the search interface
- **`solr/configsets/`**: Solr schema and configuration files
- **`docker-compose.yml`**: Defines the multi-container application setup

### Logs

Check `pokemon_fetcher.log` for data fetching logs and debugging information.

## Troubleshooting

1. **Container Issues**: Ensure Docker/Podman is running and you have sufficient permissions
2. **Port Conflicts**: Check if ports 5000 (web app) and 8983 (Solr) are available
3. **Virtual Environment**: Make sure the virtual environment is activated before running the fetcher
4. **Dependencies**: Verify all requirements are installed with `pip list`

## License

This project is licensed under the terms specified in the LICENSE file.
