#!/bin/bash
# Railway startup script

echo "🚀 Starting SPSCon 2025 deployment..."

# Check if we're in Railway environment
if [ -n "$RAILWAY_ENVIRONMENT" ]; then
    echo "✅ Railway environment detected"
else
    echo "⚠️  Local environment detected"
fi

# Run database setup with timeout
echo "📊 Running database setup..."
timeout 60 python3 deploy.py &
DEPLOY_PID=$!

# Wait for deploy or timeout
wait $DEPLOY_PID 2>/dev/null
DEPLOY_EXIT=$?

if [ $DEPLOY_EXIT -eq 0 ]; then
    echo "✅ Database setup completed"
elif [ $DEPLOY_EXIT -eq 124 ]; then
    echo "⚠️  Database setup timed out after 60s"
    echo "   Continuing with app startup..."
else
    echo "⚠️  Database setup had issues (exit code: $DEPLOY_EXIT)"
    echo "   Continuing with app startup..."
fi

# Run migrations with timeout (safe to run multiple times, only applies new ones)
echo "🔄 Running database migrations..."
timeout 30 python3 migrations.py &
MIGRATE_PID=$!

wait $MIGRATE_PID 2>/dev/null
MIGRATE_EXIT=$?

if [ $MIGRATE_EXIT -eq 0 ]; then
    echo "✅ Migrations completed"
elif [ $MIGRATE_EXIT -eq 124 ]; then
    echo "⚠️  Migrations timed out after 30s"
    echo "   Continuing with app startup..."
else
    echo "⚠️  Migrations had issues"
    echo "   Continuing with app startup..."
fi

# Give database a moment to settle
echo "⏱️  Waiting 2 seconds for database..."
sleep 2

# Start the Flask application
echo "🌐 Starting Flask application..."
echo "🔗 Health check will be available at /health"
python3 app.py
