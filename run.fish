#!/usr/bin/env fish
# Bank Analyzer - Easy Run Script for Fish Shell
# This script automatically sets up Python virtual environment and runs the analyzer

set SCRIPT_DIR (dirname (status filename))
set VENV_DIR "$SCRIPT_DIR/.venv"
set PYTHON_CMD ""

# Colors for output (using ANSI codes directly for consistency)
function echo_info
    printf '\033[0;32m[INFO]\033[0m %s\n' "$argv"
end

function echo_warn
    printf '\033[1;33m[WARN]\033[0m %s\n' "$argv"
end

function echo_error
    printf '\033[0;31m[ERROR]\033[0m %s\n' "$argv"
end

# Find Python 3.9+
function find_python
    for cmd in python3.12 python3.11 python3.10 python3.9 python3 python
        if command -v $cmd >/dev/null 2>&1
            set py_version ($cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
            set major (string split '.' $py_version)[1]
            set minor (string split '.' $py_version)[2]
            if test "$major" -ge 3; and test "$minor" -ge 9
                set -g PYTHON_CMD $cmd
                echo_info "Found Python $py_version ($cmd)"
                return 0
            end
        end
    end
    return 1
end

# Setup virtual environment
function setup_venv
    if not test -d "$VENV_DIR"
        echo_info "Creating virtual environment..."
        $PYTHON_CMD -m venv "$VENV_DIR"
    end

    # Activate venv
    source "$VENV_DIR/bin/activate.fish"

    # Install/upgrade pip
    echo_info "Upgrading pip..."
    pip install --quiet --upgrade pip

    # Install dependencies
    if test -f "$SCRIPT_DIR/requirements.txt"
        echo_info "Installing dependencies..."
        pip install --quiet -r "$SCRIPT_DIR/requirements.txt"
    end

    # Install package in development mode
    echo_info "Installing bank-analyzer..."
    pip install --quiet -e "$SCRIPT_DIR"
end

# Main
function main
    echo ""
    echo "=========================================="
    echo "   Bank Analyzer - Easy Setup & Run"
    echo "=========================================="
    echo ""

    # Find Python
    if not find_python
        echo_error "Python 3.9 or higher is required but not found!"
        echo_error "Please install Python from https://www.python.org/downloads/"
        exit 1
    end

    # Setup venv if needed
    if not test -d "$VENV_DIR"; or not test -f "$VENV_DIR/bin/activate.fish"
        setup_venv
    else
        source "$VENV_DIR/bin/activate.fish"
        # Check if package is installed
        if not pip show bank-analyzer >/dev/null 2>&1
            setup_venv
        end
    end

    # Copy example config if needed
    if not test -f "$SCRIPT_DIR/config/rules.yaml"; and test -f "$SCRIPT_DIR/config/rules.example.yaml"
        echo_info "Copying example rules configuration..."
        cp "$SCRIPT_DIR/config/rules.example.yaml" "$SCRIPT_DIR/config/rules.yaml"
    end

    if not test -f "$SCRIPT_DIR/config/categories.yaml"; and test -f "$SCRIPT_DIR/config/categories.example.yaml"
        echo_info "Copying example categories configuration..."
        cp "$SCRIPT_DIR/config/categories.example.yaml" "$SCRIPT_DIR/config/categories.yaml"
    end

    # Create data directories if needed
    mkdir -p "$SCRIPT_DIR/data/input"
    mkdir -p "$SCRIPT_DIR/data/output"
    mkdir -p "$SCRIPT_DIR/data/processed"

    echo ""
    echo_info "Setup complete!"
    echo ""

    # If arguments provided, run the CLI with them
    if test (count $argv) -gt 0
        echo_info "Running: bank-analyzer $argv"
        echo ""
        bank-analyzer $argv
    else
        # Show help
        echo "Usage:"
        echo "  ./run.fish analyze data/input/*.csv     - Analyze CSV files"
        echo "  ./run.fish parse file.csv               - Parse single file"
        echo "  ./run.fish detect file.csv              - Detect bank format"
        echo "  ./run.fish version                      - Show version"
        echo "  ./run.fish --help                       - Show all commands"
        echo ""
        echo "Example:"
        echo "  ./run.fish analyze data/input/pko_*.csv -o output.xlsx"
        echo ""
        bank-analyzer --help
    end
end

main $argv
