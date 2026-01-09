#!/bin/bash
# Bank Analyzer - Easy Run Script
# This script automatically sets up Python virtual environment and runs the analyzer

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
PYTHON_CMD=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Find Python 3.9+
find_python() {
    for cmd in python3.12 python3.11 python3.10 python3.9 python3 python; do
        if command -v "$cmd" &> /dev/null; then
            version=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
            major=$(echo "$version" | cut -d. -f1)
            minor=$(echo "$version" | cut -d. -f2)
            if [ "$major" -ge 3 ] && [ "$minor" -ge 9 ]; then
                PYTHON_CMD="$cmd"
                echo_info "Found Python $version ($cmd)"
                return 0
            fi
        fi
    done
    return 1
}

# Setup virtual environment
setup_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        echo_info "Creating virtual environment..."
        "$PYTHON_CMD" -m venv "$VENV_DIR"
    fi

    # Activate venv
    source "$VENV_DIR/bin/activate"

    # Install/upgrade pip
    echo_info "Upgrading pip..."
    pip install --quiet --upgrade pip

    # Install dependencies
    if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
        echo_info "Installing dependencies..."
        pip install --quiet -r "$SCRIPT_DIR/requirements.txt"
    fi

    # Install package in development mode
    echo_info "Installing bank-analyzer..."
    pip install --quiet -e "$SCRIPT_DIR"
}

# Main
main() {
    echo ""
    echo "=========================================="
    echo "   Bank Analyzer - Easy Setup & Run"
    echo "=========================================="
    echo ""

    # Find Python
    if ! find_python; then
        echo_error "Python 3.9 or higher is required but not found!"
        echo_error "Please install Python from https://www.python.org/downloads/"
        exit 1
    fi

    # Setup venv if needed
    if [ ! -d "$VENV_DIR" ] || [ ! -f "$VENV_DIR/bin/activate" ]; then
        setup_venv
    else
        source "$VENV_DIR/bin/activate"
        # Check if package is installed
        if ! pip show bank-analyzer &> /dev/null; then
            setup_venv
        fi
    fi

    # Copy example config if needed
    if [ ! -f "$SCRIPT_DIR/config/rules.yaml" ] && [ -f "$SCRIPT_DIR/config/rules.example.yaml" ]; then
        echo_info "Copying example rules configuration..."
        cp "$SCRIPT_DIR/config/rules.example.yaml" "$SCRIPT_DIR/config/rules.yaml"
    fi

    if [ ! -f "$SCRIPT_DIR/config/categories.yaml" ] && [ -f "$SCRIPT_DIR/config/categories.example.yaml" ]; then
        echo_info "Copying example categories configuration..."
        cp "$SCRIPT_DIR/config/categories.example.yaml" "$SCRIPT_DIR/config/categories.yaml"
    fi

    # Create data directories if needed
    mkdir -p "$SCRIPT_DIR/data/input"
    mkdir -p "$SCRIPT_DIR/data/output"
    mkdir -p "$SCRIPT_DIR/data/processed"

    echo ""
    echo_info "Setup complete!"
    echo ""

    # If arguments provided, run the CLI with them
    if [ $# -gt 0 ]; then
        echo_info "Running: bank-analyzer $*"
        echo ""
        bank-analyzer "$@"
    else
        # Show help
        echo "Usage:"
        echo "  ./run.sh analyze data/input/*.csv     - Analyze CSV files"
        echo "  ./run.sh parse file.csv               - Parse single file"
        echo "  ./run.sh detect file.csv              - Detect bank format"
        echo "  ./run.sh version                      - Show version"
        echo "  ./run.sh --help                       - Show all commands"
        echo ""
        echo "Example:"
        echo "  ./run.sh analyze data/input/pko_*.csv -o output.xlsx"
        echo ""
        bank-analyzer --help
    fi
}

main "$@"
