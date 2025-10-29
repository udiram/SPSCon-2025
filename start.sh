#!/bin/bash
# Railway startup script

echo "🚀 Starting SPSCon 2025 deployment..."

# Check if we're in Railway environment
if [ -n "$RAILWAY_ENVIRONMENT" ]; then
    echo "✅ Railway environment detected"
else
    echo "⚠️  Local environment detected"
fi

# Run database setup
echo "📊 Running database setup..."
python deploy.py

if [ $? -eq 0 ]; then
    echo "✅ Database setup completed"
else
    echo "❌ Database setup failed"
    exit 1
fi

# Run migrations (safe to run multiple times, only applies new ones)
echo "🔄 Running database migrations..."
python migrations.py

if [ $? -eq 0 ]; then
    echo "✅ Migrations completed"
else
    echo "❌ Migrations failed"
    exit 1
fi

# Start the Flask application
echo "🌐 Starting Flask application..."
python app.py
