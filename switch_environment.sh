#!/bin/bash

# =============================================
# Environment Switcher
# Safely switch between dev and prod configs
# =============================================

echo "=========================================="
echo "Environment Configuration Switcher"
echo "=========================================="
echo ""
echo "Current setup:"

# Check current environment
if [ -f ".env" ]; then
    CURRENT_ENV=$(grep "^ENVIRONMENT=" .env | cut -d'=' -f2)
    CURRENT_PORT=$(grep "^PORT=" .env | cut -d'=' -f2)
    echo "  Active .env file: $CURRENT_ENV on port $CURRENT_PORT"
else
    echo "  No .env file found"
fi

echo ""
echo "Available environments:"
echo "  1) Development (port 8000)"
echo "  2) Production  (port 8001)"
echo "  3) View current settings"
echo "  4) Exit"
echo ""
echo -n "Select option [1-4]: "
read choice

case $choice in
    1)
        echo ""
        echo "Switching to DEVELOPMENT..."
        
        # Backup current
        if [ -f ".env" ]; then
            cp .env .env.backup
            echo "✓ Current .env backed up to .env.backup"
        fi
        
        # Switch to dev
        if [ -f ".env.development" ]; then
            cp .env.development .env
            echo "✓ Switched to development environment"
            echo ""
            echo "Settings:"
            grep -E "^(ENVIRONMENT|PORT|DB_NAME|DEBUG)=" .env
            echo ""
            echo "To start: ./start_dev.sh or python3 main.py"
        else
            echo "❌ .env.development not found!"
            exit 1
        fi
        ;;
        
    2)
        echo ""
        echo "⚠️  WARNING: Switching to PRODUCTION!"
        echo "This will use LIVE data!"
        echo -n "Type 'confirm' to proceed: "
        read confirm
        
        if [ "$confirm" = "confirm" ]; then
            # Backup current
            if [ -f ".env" ]; then
                cp .env .env.backup
                echo "✓ Current .env backed up to .env.backup"
            fi
            
            # Switch to prod
            if [ -f ".env.production" ]; then
                cp .env.production .env
                echo "✓ Switched to production environment"
                echo ""
                echo "Settings:"
                grep -E "^(ENVIRONMENT|PORT|DB_NAME|DEBUG)=" .env
                echo ""
                echo "To start: ./start_prod.sh"
            else
                echo "❌ .env.production not found!"
                exit 1
            fi
        else
            echo "Cancelled."
        fi
        ;;
        
    3)
        echo ""
        echo "Current .env settings:"
        echo "====================="
        if [ -f ".env" ]; then
            grep -E "^(ENVIRONMENT|PORT|DB_SERVER|DB_NAME|DEBUG|IMS_BASE_URL)=" .env
        else
            echo "No .env file found"
        fi
        ;;
        
    4)
        echo "Exiting..."
        exit 0
        ;;
        
    *)
        echo "Invalid option"
        exit 1
        ;;
esac