#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Convert static files
python -m pip install --upgrade pip
pip install -r requirements.txt

# Create or update database schema
python app.py