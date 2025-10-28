#!/bin/bash
# Railway startup script

echo "🚀 Starting SPSCon 2025 deployment..."

# Check if we're in Railway environment
if [ -n "$RAILWAY_ENVIRONMENT" ]; then
    echo "✅ Railway environment detected"
else
    echo "⚠️  Local environment detected"
fi

# Run database migration
echo "📊 Running database migration..."
python deploy.py

if [ $? -eq 0 ]; then
    echo "✅ Database migration completed"
else
    echo "❌ Database migration failed"
    exit 1
fi

# Start the Flask application
echo "🌐 Starting Flask application..."
python app.py
