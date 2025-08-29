#!/bin/bash

# =============================================
# PRODUCTION Environment Startup Script
# CAUTION: This runs against LIVE data!
# =============================================

# Safety warnings
echo "=========================================="
echo "⚠️  WARNING: PRODUCTION ENVIRONMENT ⚠️"
echo "=========================================="
echo ""
echo "This will start the application in PRODUCTION mode:"
echo "  - Using LIVE database"
echo "  - Processing REAL transactions"
echo "  - Affecting ACTUAL customer data"
echo ""
echo "Are you SURE you want to continue?"
echo "Type 'yes production' to confirm: "

read confirmation

if [ "$confirmation" != "yes production" ]; then
    echo "❌ Cancelled. Not starting production."
    exit 1
fi

# Set environment
export APP_ENV=production

# Check for production env file
if [ ! -f ".env.production" ]; then
    echo "❌ ERROR: .env.production not found!"
    echo "Cannot start production without proper configuration."
    exit 1
fi

# Create logs directory if needed
mkdir -p logs

# Final confirmation
echo ""
echo "Starting PRODUCTION in 5 seconds..."
echo "Press Ctrl+C to cancel"
sleep 5

# Start the application in background
echo ""
echo "Starting production server..."
echo "  Environment: PRODUCTION"
echo "  Port: 8001"
echo "  Debug: Disabled"
echo ""

# Run with nohup for production
LOG_FILE="logs/prod_$(date +%Y%m%d_%H%M%S).log"
nohup python3 main.py > "$LOG_FILE" 2>&1 &

PID=$!
echo $PID > prod.pid

echo "✅ Production server started"
echo "  PID: $PID (saved to prod.pid)"
echo "  Log: $LOG_FILE"
echo ""
echo "Commands:"
echo "  Monitor logs:  tail -f $LOG_FILE"
echo "  Check status:  ps -p $PID"
echo "  Stop server:   kill $PID"
echo ""
echo "Testing:"
echo "  curl http://localhost:8001/health"
echo ""