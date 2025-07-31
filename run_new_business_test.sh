#!/bin/bash
# Wrapper script to run tests with correct Python environment

echo "Setting up Python environment..."

# Export PYTHONPATH to include current directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Creating from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "Created .env from .env.example - please update with your credentials"
    fi
fi

# Run the test
echo "Running test..."
if [ "$#" -eq 0 ]; then
    # No arguments - run without JSON
    python3 test_3_new_business_bind.py
else
    # With arguments - pass them through
    python3 test_3_new_business_bind.py "$@"
fi