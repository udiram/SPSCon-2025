#!/bin/bash
# Pre-deployment script for SPSCon 2025
# Based on TradeGrade deployment structure

set -e  # Exit on any error

echo "🚀 SPSCon 2025 Pre-Deployment Setup"
echo "=================================="

# Check if we're in Railway environment
if [ -n "$RAILWAY_ENVIRONMENT" ]; then
    echo "✅ Railway environment detected: $RAILWAY_ENVIRONMENT"
    export FLASK_ENV=production
    export FLASK_DEBUG=False
else
    echo "⚠️  Local environment detected"
    export FLASK_ENV=development
    export FLASK_DEBUG=True
fi

# Set default PORT if not provided (Railway will set this automatically)
if [ -z "$PORT" ]; then
    export PORT=5000
fi

echo "📊 Environment Configuration:"
echo "   FLASK_ENV: $FLASK_ENV"
echo "   FLASK_DEBUG: $FLASK_DEBUG"
echo "   PORT: $PORT"
echo "   HOST: 0.0.0.0"

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  DATABASE_URL not set, using SQLite fallback"
    export DATABASE_URL="sqlite:///spscon.db"
else
    echo "✅ DATABASE_URL configured"
fi

# Check if SECRET_KEY is set
if [ -z "$SECRET_KEY" ]; then
    echo "⚠️  SECRET_KEY not set, using default (NOT RECOMMENDED FOR PRODUCTION)"
    export SECRET_KEY="dev-secret-key-change-in-production"
else
    echo "✅ SECRET_KEY configured"
fi

# Set HOST for Railway
export HOST="0.0.0.0"

# Install/upgrade dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Run database migration
echo "🗄️  Running database migration..."
python deploy.py

if [ $? -eq 0 ]; then
    echo "✅ Database migration completed successfully"
else
    echo "❌ Database migration failed"
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p instance
mkdir -p static/qrcodes
mkdir -p logs

# Set permissions
echo "🔐 Setting file permissions..."
chmod +x deploy.py
chmod +x export_data.py
chmod +x start.sh

# Final checks
echo "🔍 Running final checks..."

# Check if app.py exists
if [ ! -f "app.py" ]; then
    echo "❌ app.py not found!"
    exit 1
fi

# Check if models.py exists
if [ ! -f "models.py" ]; then
    echo "❌ models.py not found!"
    exit 1
fi

# Check if config.py exists
if [ ! -f "config.py" ]; then
    echo "❌ config.py not found!"
    exit 1
fi

echo "✅ All pre-deployment checks passed!"
echo "🌐 Ready to start Flask application..."
echo "=================================="
