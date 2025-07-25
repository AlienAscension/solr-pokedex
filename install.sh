#!/bin/bash

# Solr Pokédex Installation Script
# This script automates the setup process for the Solr Pokédex project

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    local missing_deps=()
    local container_runtime_found=false
    
    # Check Python 3
    if command_exists python3; then
        local python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
        print_success "Python 3 found: $python_version"
    else
        missing_deps+=("python3")
    fi
    
    # --- START OF IMPROVED LOGIC ---

    # Try to find a working Docker + Docker Compose combination
    if command_exists docker; then
        if command_exists docker-compose || docker compose version >/dev/null 2>&1; then
            print_success "Found working environment: Docker + Docker Compose"
            container_runtime_found=true
        fi
    fi

    # If Docker+Compose not found, try Podman + Podman Compose
    if ! $container_runtime_found && command_exists podman; then
        if command_exists podman-compose; then
            print_success "Found working environment: Podman + Podman Compose"
            container_runtime_found=true
        fi
    fi

    if ! $container_runtime_found; then
         missing_deps+=("a working container environment (Docker with docker-compose, or Podman with podman-compose)")
    fi
    
    # --- END OF IMPROVED LOGIC ---

    # Report missing dependencies
    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "Missing dependencies: ${missing_deps[*]}"
        print_error "Please install the missing dependencies and run this script again."
        exit 1
    fi
    
    print_success "All prerequisites are satisfied!"
}

# Function to create virtual environment
create_virtual_environment() {
    print_status "Creating Python virtual environment..."
    
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists. Skipping creation."
        return 0
    fi
    
    python3 -m venv venv
    
    if [ $? -eq 0 ]; then
        print_success "Virtual environment created successfully!"
    else
        print_error "Failed to create virtual environment!"
        exit 1
    fi
}

# Function to activate virtual environment and install dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Check if requirements.txt exists
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found in current directory!"
        exit 1
    fi
    
    # Activate virtual environment and install dependencies
    local os=$(detect_os)
    local activate_script=""
    
    if [[ "$os" == "windows" ]]; then
        activate_script="venv/Scripts/activate"
    else
        activate_script="venv/bin/activate"
    fi
    
    if [ ! -f "$activate_script" ]; then
        print_error "Virtual environment activation script not found: $activate_script"
        exit 1
    fi
    
    # Source the activation script and check for pip
    source "$activate_script"
    
    # Now check for pip within the activated virtual environment
    if command_exists pip; then
        print_success "pip found in virtual environment"
        pip install -r requirements.txt
    elif command_exists pip3; then
        print_success "pip3 found in virtual environment"
        pip3 install -r requirements.txt
    else
        print_error "Neither pip nor pip3 found in virtual environment!"
        print_error "The virtual environment may not have been created properly."
        exit 1
    fi
    
    if [ $? -eq 0 ]; then
        print_success "Dependencies installed successfully!"
    else
        print_error "Failed to install dependencies!"
        exit 1
    fi
}

# Function to make fetcher script executable
make_fetcher_executable() {
    print_status "Making fetcher script executable..."
    
    if [ ! -f "fetcher_v2.py" ]; then
        print_error "fetcher_v2.py not found in current directory!"
        exit 1
    fi
    
    chmod +x fetcher_v2.py
    
    if [ $? -eq 0 ]; then
        print_success "fetcher_v2.py is now executable!"
    else
        print_error "Failed to make fetcher_v2.py executable!"
        exit 1
    fi
}

# Function to start containers
start_containers() {
    print_status "Starting containers..."
    
    if [ ! -f "docker-compose.yml" ]; then
        print_error "docker-compose.yml not found in current directory!"
        exit 1
    fi
    
    # Try different compose commands
    if command_exists docker-compose; then
        docker-compose up -d
    elif docker compose version >/dev/null 2>&1; then
        docker compose up -d
    elif command_exists podman-compose; then
        podman-compose up -d
    else
        print_error "No suitable compose command found!"
        exit 1
    fi
    
    if [ $? -eq 0 ]; then
        print_success "Containers started successfully!"
    else
        print_error "Failed to start containers!"
        exit 1
    fi
}

# Function to wait for Solr to be ready
wait_for_solr() {
    print_status "Waiting for Solr to be ready..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:8983/solr/admin/cores >/dev/null 2>&1; then
            print_success "Solr is ready!"
            return 0
        fi
        
        print_status "Attempt $attempt/$max_attempts - Solr not ready yet, waiting 5 seconds..."
        sleep 5
        ((attempt++))
    done
    
    print_error "Solr failed to start within expected time!"
    return 1
}

# Function to run the fetcher
run_fetcher() {
    print_status "Running Pokémon data fetcher..."
    
    # Activate virtual environment first
    local os=$(detect_os)
    local activate_script=""
    
    if [[ "$os" == "windows" ]]; then
        activate_script="venv/Scripts/activate"
    else
        activate_script="venv/bin/activate"
    fi
    
    source "$activate_script"
    
    ./fetcher_v2.py
    
    if [ $? -eq 0 ]; then
        print_success "Pokémon data fetched and indexed successfully!"
    else
        print_error "Failed to fetch Pokémon data!"
        exit 1
    fi
}

# Function to show final status
show_final_status() {
    echo ""
    print_success "=== Installation Complete! ==="
    echo ""
    print_status "Your Solr Pokédex is now ready to use!"
    echo ""
    print_status "Access points:"
    echo "  • Web Application: http://localhost:5000"
    echo "  • Apache Solr Admin: http://localhost:8983"
    echo ""
    print_status "Useful commands:"
    echo "  • View logs: tail -f pokemon_fetcher.log"
    echo "  • Stop containers: docker-compose down (or podman-compose down)"
    echo "  • Restart containers: docker-compose restart (or podman-compose restart)"
    echo ""
    print_warning "Note: Make sure to activate the virtual environment before running the fetcher again:"
    local os=$(detect_os)
    if [[ "$os" == "windows" ]]; then
        echo "  venv\\Scripts\\Activate.ps1"
    else
        echo "  source venv/bin/activate"
    fi
}

# Main installation function
main() {
    echo ""
    print_status "=== Solr Pokédex Installation Script ==="
    echo ""
    
    # Check if we're in the right directory
    if [ ! -f "fetcher_v2.py" ] || [ ! -f "docker-compose.yml" ]; then
        print_error "This script must be run from the solr-pokedex project root directory!"
        print_error "Make sure you can see fetcher_v2.py and docker-compose.yml in the current directory."
        exit 1
    fi
    
    check_prerequisites
    create_virtual_environment
    install_dependencies
    make_fetcher_executable
    start_containers
    
    if wait_for_solr; then
        run_fetcher
        show_final_status
    else
        print_error "Installation failed due to Solr startup issues."
        print_warning "You can try running the fetcher manually once Solr is ready:"
        print_warning "  source venv/bin/activate && ./fetcher_v2.py"
    fi
}

# Run main function
main "$@"
