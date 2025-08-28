#!/bin/bash

# =============================================
# RSG Integration - AWS Production Startup Script
# Simple, reliable startup for AWS deployment
# =============================================

# Configuration - ADJUST THESE FOR YOUR ENVIRONMENT
APP_DIR="/home/ubuntu/RSG_Integration_2"  # Change to your actual path
PYTHON_CMD="python3"  # or python3.9 if specific version needed
LOG_FILE="$APP_DIR/logs/app.log"
PID_FILE="$APP_DIR/app.pid"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Functions
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if app directory exists
if [ ! -d "$APP_DIR" ]; then
    print_error "Application directory not found: $APP_DIR"
    exit 1
fi

# Navigate to app directory
cd "$APP_DIR"

# Check if main.py exists
if [ ! -f "main.py" ]; then
    print_error "main.py not found in $APP_DIR"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found!"
    if [ -f ".env.example" ]; then
        print_warning "Copy .env.example to .env and configure it"
    fi
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Kill any existing process
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p $OLD_PID > /dev/null 2>&1; then
        print_warning "Stopping existing process (PID: $OLD_PID)"
        kill $OLD_PID
        sleep 2
    fi
fi

# Also check for any orphaned python main.py processes
pkill -f "python.*main.py" 2>/dev/null || true

echo "=========================================="
echo "Starting RSG Integration Service"
echo "=========================================="
echo "Directory: $APP_DIR"
echo "Python: $PYTHON_CMD"
echo "Log file: $LOG_FILE"
echo ""

# Start the application
print_status "Starting application..."
nohup $PYTHON_CMD main.py > "$LOG_FILE" 2>&1 &

# Save PID
APP_PID=$!
echo $APP_PID > "$PID_FILE"

# Wait a moment for app to start
sleep 3

# Check if process is running
if ps -p $APP_PID > /dev/null; then
    print_status "Application started successfully!"
    print_status "PID: $APP_PID"
    print_status "Log file: $LOG_FILE"
    echo ""
    echo "Commands:"
    echo "  View logs:    tail -f $LOG_FILE"
    echo "  Check status: ps -p $APP_PID"
    echo "  Stop app:     kill $APP_PID"
    echo "  Test health:  curl http://localhost:8000/health"
    echo ""
    
    # Show last few lines of log
    echo "Recent log entries:"
    echo "------------------"
    tail -n 5 "$LOG_FILE"
    
else
    print_error "Failed to start application!"
    echo "Check the log file for errors:"
    echo "  cat $LOG_FILE"
    exit 1
fi

echo ""
echo "=========================================="
print_status "Deployment complete!"
echo "=========================================="