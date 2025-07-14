#!/bin/bash

# Start the RSG Integration Service
# Usage: ./start_service.sh [dev|prod|background]

MODE=${1:-dev}
PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}

echo "Starting RSG Integration Service..."
echo "Mode: $MODE"
echo "Host: $HOST"
echo "Port: $PORT"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "No virtual environment found. Make sure dependencies are installed."
fi

# Load environment variables if .env exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Warning: No .env file found. Using default configuration."
fi

# Create logs directory
mkdir -p logs

case $MODE in
    dev)
        echo "Starting in development mode with auto-reload..."
        uvicorn app.main:app --reload --host $HOST --port $PORT --log-level info
        ;;
    prod)
        echo "Starting in production mode..."
        gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind $HOST:$PORT --access-logfile logs/access.log --error-logfile logs/error.log
        ;;
    background)
        echo "Starting in background mode..."
        nohup uvicorn app.main:app --host $HOST --port $PORT --log-level info > logs/service.log 2>&1 &
        echo $! > service.pid
        echo "Service started with PID: $(cat service.pid)"
        echo "Logs: tail -f logs/service.log"
        ;;
    *)
        echo "Invalid mode. Use: dev, prod, or background"
        exit 1
        ;;
esac