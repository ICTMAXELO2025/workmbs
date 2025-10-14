#!/usr/bin/env bash
# build.sh - Render build script

echo "Starting build process..."

# Install Python dependencies
pip install -r requirements.txt

# Run any database migrations or setup
python -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('Database tables created successfully')
"

echo "Build completed successfully!"