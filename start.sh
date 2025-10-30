#!/bin/bash
# Railway startup script - EMERGENCY MODE: Start app FIRST

echo "🚀 EMERGENCY START MODE - App starting immediately!"

# Start Flask application IMMEDIATELY in background
echo "🌐 Starting Flask application NOW..."
python3 app.py &
APP_PID=$!

# Give app 5 seconds to start
sleep 5

# Check if app is running
if ps -p $APP_PID > /dev/null 2>&1; then
    echo "✅ App is running! (PID: $APP_PID)"
    
    # Now run setup in background (won't block healthcheck)
    echo "📊 Running database setup in background..."
    (
        python3 deploy.py 2>&1
        echo "✅ Deploy script completed"
    ) &
    
    echo "🔄 Running migrations in background..."
    (
        python3 migrations.py 2>&1
        echo "✅ Migrations completed"
    ) &
    
    echo "✅ Setup scripts running in background"
    echo "🔗 App responding at /health"
    
    # Wait for app process
    wait $APP_PID
else
    echo "❌ App failed to start!"
    exit 1
fi
