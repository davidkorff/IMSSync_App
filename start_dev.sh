#!/bin/bash

# =============================================
# Development Environment Startup Script
# Safe for testing and development
# =============================================

echo "=========================================="
echo "Starting DEVELOPMENT Environment"
echo "=========================================="

# Set environment
export APP_ENV=development

# Safety check - make sure we're not accidentally in production
if [ -f ".env" ]; then
    if grep -q "ENVIRONMENT=production" .env; then
        echo "⚠️  WARNING: .env file contains production settings!"
        echo "Please verify you want to run in development mode."
        echo "Press Ctrl+C to cancel, Enter to continue..."
        read
    fi
fi

# Check for dev env file
if [ ! -f ".env.development" ]; then
    echo "⚠️  Warning: .env.development not found"
    echo "Using default .env file"
fi

# Start the application
echo ""
echo "Starting application..."
echo "  Environment: DEVELOPMENT"
echo "  Port: 8000"
echo "  Debug: Enabled"
echo ""

python3 main.py

# Or if you want to run in background:
# nohup python3 main.py > logs/dev_$(date +%Y%m%d_%H%M%S).log 2>&1 &
# echo "Development server started with PID: $!"
# echo "Logs: tail -f logs/dev_*.log"