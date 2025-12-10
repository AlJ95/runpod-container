#!/bin/bash
# Unified Python Environment Setup Script
# Sets up a single virtual environment for all services

set -e

echo ">>> Setting up unified Python environment..."

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo ">>> Creating virtual environment (.venv)..."
    uv venv .venv
else
    echo ">>> Virtual environment (.venv) already exists."
fi

# Activate environment
source .venv/bin/activate

echo ">>> Installing dependencies from requirements.txt..."
uv pip install --upgrade pip --quiet
uv pip install -r requirements.txt

echo ">>> Setup completed successfully."
echo "Environment: .venv"
