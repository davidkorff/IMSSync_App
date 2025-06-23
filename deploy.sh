#!/bin/bash
# Deployment script for IMS Integration Service
# Works on both AWS EC2 and Azure VMs

set -e

# Configuration
SERVICE_NAME="ims-integration"
DEPLOY_DIR="/opt/ims-integration"
SERVICE_FILE="/etc/systemd/system/ims-integration.service"

echo "=== IMS Integration Service Deployment ==="

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
   echo "Please run with sudo"
   exit 1
fi

# Create deployment directory
echo "Creating deployment directory..."
mkdir -p $DEPLOY_DIR

# Copy files
echo "Copying application files..."
cp -r app/ $DEPLOY_DIR/
cp requirements.txt $DEPLOY_DIR/
cp Dockerfile $DEPLOY_DIR/
cp docker-compose.prod.yml $DEPLOY_DIR/
cp -r monitoring/ $DEPLOY_DIR/
cp .env.example $DEPLOY_DIR/.env.example

# Copy .env file if it exists
if [ -f .env ]; then
    cp .env $DEPLOY_DIR/
else
    echo "WARNING: .env file not found. Please create one from .env.example"
fi

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    usermod -aG docker ubuntu
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Build Docker image
echo "Building Docker image..."
cd $DEPLOY_DIR
docker-compose -f docker-compose.prod.yml build

# Install systemd service
echo "Installing systemd service..."
cp $DEPLOY_DIR/../ims-integration.service $SERVICE_FILE
systemctl daemon-reload
systemctl enable ims-integration.service

# Start service
echo "Starting service..."
systemctl start ims-integration.service

# Check status
echo "Checking service status..."
systemctl status ims-integration.service --no-pager

echo ""
echo "=== Deployment Complete ==="
echo "Service is running at: http://$(hostname -I | awk '{print $1}'):8000"
echo "Health check: http://$(hostname -I | awk '{print $1}'):8000/api/health"
echo "Metrics: http://$(hostname -I | awk '{print $1}'):8000/api/metrics"
echo ""
echo "To view logs: sudo journalctl -u ims-integration -f"
echo "To restart: sudo systemctl restart ims-integration"
echo "To stop: sudo systemctl stop ims-integration"