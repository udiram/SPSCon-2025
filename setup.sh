#!/bin/bash

# SPSCon Dashboard Setup Script
# This script sets up the database and imports data

echo "🚀 Setting up SPSCon Dashboard..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run: python3 -m venv venv"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Initialize database
echo "🗄️ Initializing database..."
python init_db.py

# Check if Excel file exists
if [ ! -f "2025 SPSCon Poster Assignments_Student View.xlsx" ]; then
    echo "❌ Excel file not found. Please ensure '2025 SPSCon Poster Assignments_Student View.xlsx' is in the current directory."
    exit 1
fi

# Import data
echo "📊 Importing poster data..."
python seed_data.py

# Check database status
echo "✅ Checking database status..."
python -c "
from init_db import check_db_status
check_db_status()
"

echo "🎉 Setup complete! You can now run: python app.py"
echo "📱 The dashboard will be available at http://localhost:5000"

