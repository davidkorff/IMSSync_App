#!/bin/bash

# =============================================
# QUICK START SCRIPT - Simplified Deployment
# For developers who just want to run python main.py
# =============================================

echo "=========================================="
echo "RSG Integration - Quick Start"
echo "=========================================="

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_DIR="$(dirname "$SCRIPT_DIR")"  # Parent directory (RSG_Integration_2)

echo "App Directory: $APP_DIR"

# Check if we're in the right directory
if [ ! -f "$APP_DIR/main.py" ]; then
    echo "Error: main.py not found in $APP_DIR"
    echo "Please run this script from the Final_Deployment folder"
    exit 1
fi

cd "$APP_DIR"

# Check for .env file
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found!"
    echo "Creating from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "Created .env from .env.example"
        echo "Please edit .env with your actual configuration values!"
    else
        echo "Error: No .env.example found either!"
        exit 1
    fi
fi

# Check for virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements if needed
echo "Checking Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Create logs directory if it doesn't exist
mkdir -p logs

echo ""
echo "=========================================="
echo "Starting Application"
echo "=========================================="
echo ""

# Method 1: Direct python execution (your preferred method)
echo "Starting with: python main.py"
echo "Press Ctrl+C to stop"
echo ""

python main.py

# Method 2: Using nohup (uncomment to use)
# echo "Starting in background with nohup..."
# nohup python main.py > logs/app.log 2>&1 &
# echo "PID: $!"
# echo "Check logs: tail -f logs/app.log"

# Method 3: Using uvicorn directly (uncomment to use)
# echo "Starting with uvicorn..."
# uvicorn main:app --host 0.0.0.0 --port 8000 --reload