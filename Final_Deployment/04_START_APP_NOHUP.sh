#!/bin/bash

# =============================================
# Simple Nohup Deployment Script
# For quick deployment using nohup and uvicorn
# =============================================

# Configuration
APP_DIR="/opt/rsg-integration"  # Change to your app directory
LOG_DIR="$APP_DIR/logs"
PID_FILE="$APP_DIR/rsg-integration.pid"

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Function to check if app is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

# Function to start the application
start_app() {
    echo "Starting RSG Integration Service..."
    
    if is_running; then
        print_warning "Application is already running with PID $(cat $PID_FILE)"
        return 1
    fi
    
    # Create log directory if it doesn't exist
    mkdir -p "$LOG_DIR"
    
    # Change to app directory
    cd "$APP_DIR"
    
    # Activate virtual environment and start with nohup
    echo "Starting application with nohup..."
    
    # Method 1: Using python main.py directly (as you mentioned)
    nohup $APP_DIR/venv/bin/python main.py \
        > "$LOG_DIR/app.log" 2>&1 &
    
    # Method 2: Using uvicorn directly (alternative)
    # nohup $APP_DIR/venv/bin/uvicorn main:app \
    #     --host 0.0.0.0 \
    #     --port 8000 \
    #     --workers 4 \
    #     --loop uvloop \
    #     --log-level info \
    #     > "$LOG_DIR/app.log" 2>&1 &
    
    # Save PID
    echo $! > "$PID_FILE"
    
    sleep 2
    
    if is_running; then
        print_status "Application started successfully with PID $(cat $PID_FILE)"
        print_status "Logs: tail -f $LOG_DIR/app.log"
    else
        print_error "Failed to start application"
        return 1
    fi
}

# Function to stop the application
stop_app() {
    echo "Stopping RSG Integration Service..."
    
    if ! is_running; then
        print_warning "Application is not running"
        return 1
    fi
    
    PID=$(cat "$PID_FILE")
    print_status "Stopping process with PID $PID"
    
    # Try graceful shutdown first
    kill $PID
    
    # Wait for process to stop
    for i in {1..10}; do
        if ! is_running; then
            rm -f "$PID_FILE"
            print_status "Application stopped successfully"
            return 0
        fi
        sleep 1
    done
    
    # Force kill if still running
    print_warning "Forcing shutdown..."
    kill -9 $PID 2>/dev/null
    rm -f "$PID_FILE"
    print_status "Application forcefully stopped"
}

# Function to restart the application
restart_app() {
    echo "Restarting RSG Integration Service..."
    stop_app
    sleep 2
    start_app
}

# Function to check status
status_app() {
    if is_running; then
        PID=$(cat "$PID_FILE")
        print_status "Application is running with PID $PID"
        echo ""
        echo "Process details:"
        ps -fp $PID
        echo ""
        echo "Recent logs:"
        tail -n 10 "$LOG_DIR/app.log"
    else
        print_error "Application is not running"
    fi
}

# Function to tail logs
tail_logs() {
    if [ -f "$LOG_DIR/app.log" ]; then
        echo "Tailing application logs (Ctrl+C to stop)..."
        tail -f "$LOG_DIR/app.log"
    else
        print_error "Log file not found: $LOG_DIR/app.log"
    fi
}

# Main script logic
case "$1" in
    start)
        start_app
        ;;
    stop)
        stop_app
        ;;
    restart)
        restart_app
        ;;
    status)
        status_app
        ;;
    logs)
        tail_logs
        ;;
    *)
        echo "RSG Integration Service Manager"
        echo "================================"
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the application using nohup"
        echo "  stop    - Stop the application"
        echo "  restart - Restart the application"
        echo "  status  - Check if application is running"
        echo "  logs    - Tail the application logs"
        echo ""
        echo "Configuration:"
        echo "  App Directory: $APP_DIR"
        echo "  Log Directory: $LOG_DIR"
        echo "  PID File: $PID_FILE"
        exit 1
        ;;
esac

exit 0