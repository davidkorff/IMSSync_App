#!/bin/bash

# =============================================
# RSG Integration Python Application Deployment Script
# For AWS/Linux deployment with uvicorn
# =============================================

# Exit on any error
set -e

echo "=========================================="
echo "RSG Integration Deployment Script"
echo "=========================================="

# Configuration
APP_DIR="/opt/rsg-integration"
APP_USER="ubuntu"  # Change if different
PYTHON_VERSION="python3.9"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if running as root or with sudo
if [[ $EUID -eq 0 ]]; then
   echo "This script is running as root/sudo"
else
   print_error "This script must be run as root or with sudo"
   exit 1
fi

# Step 1: System Dependencies
echo ""
echo "Installing System Dependencies..."
echo "---------------------------------"

apt-get update
apt-get install -y \
    python3.9 \
    python3.9-venv \
    python3-pip \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    unixodbc-dev \
    nginx \
    supervisor

print_status "System dependencies installed"

# Step 2: Create Application Directory
echo ""
echo "Setting up Application Directory..."
echo "-----------------------------------"

if [ ! -d "$APP_DIR" ]; then
    mkdir -p $APP_DIR
    print_status "Created directory: $APP_DIR"
else
    print_warning "Directory already exists: $APP_DIR"
fi

chown -R $APP_USER:$APP_USER $APP_DIR

# Step 3: Copy Application Files
echo ""
echo "Copying Application Files..."
echo "----------------------------"
echo "Please ensure your application files are in the current directory"
echo "Press Enter to continue or Ctrl+C to abort..."
read

# Copy all Python files and directories
cp -r app/ $APP_DIR/
cp -r sql/ $APP_DIR/
cp main.py $APP_DIR/
cp config.py $APP_DIR/
cp requirements.txt $APP_DIR/
cp .env.example $APP_DIR/.env

print_status "Application files copied"

# Step 4: Setup Python Virtual Environment
echo ""
echo "Setting up Python Virtual Environment..."
echo "----------------------------------------"

cd $APP_DIR
sudo -u $APP_USER $PYTHON_VERSION -m venv venv

print_status "Virtual environment created"

# Step 5: Install Python Dependencies
echo ""
echo "Installing Python Dependencies..."
echo "---------------------------------"

sudo -u $APP_USER $APP_DIR/venv/bin/pip install --upgrade pip
sudo -u $APP_USER $APP_DIR/venv/bin/pip install -r requirements.txt

print_status "Python dependencies installed"

# Step 6: Configure Environment Variables
echo ""
echo "Configuring Environment Variables..."
echo "------------------------------------"
print_warning "Please edit $APP_DIR/.env with your actual values"

cat > $APP_DIR/.env.template << 'EOF'
# Database Configuration
DB_SERVER=your-db-server
DB_NAME=your-database
DB_USERNAME=your-username
DB_PASSWORD=your-password

# IMS Configuration
IMS_BASE_URL=http://10.64.32.234/ims_one
IMS_ONE_USERNAME=your-ims-username
IMS_ONE_PASSWORD=your-ims-password
IMS_PROGRAM_CODE=TRTON
IMS_PROJECT_NAME=RSG_Integration

# Quote Configuration
IMS_QUOTING_LOCATION=C5C006BB-6437-42F3-95D4-C090ADD3B37D
IMS_ISSUING_LOCATION=C5C006BB-6437-42F3-95D4-C090ADD3B37D
IMS_COMPANY_LOCATION=DF35D4C7-C663-4974-A886-A1E18D3C9618
TRITON_PRIMARY_LINE_GUID=07564291-CBFE-4BBE-88D1-0548C88ACED4

# Application Settings
DEBUG=False
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# API Keys
TRITON_API_KEY=your-triton-api-key
TRITON_WEBHOOK_SECRET=your-webhook-secret
EOF

chmod 600 $APP_DIR/.env
chown $APP_USER:$APP_USER $APP_DIR/.env

print_status "Environment template created. Please update with actual values!"

# Step 7: Create Log Directory
echo ""
echo "Creating Log Directory..."
echo "-------------------------"

mkdir -p $APP_DIR/logs
chown -R $APP_USER:$APP_USER $APP_DIR/logs

print_status "Log directory created"

# Step 8: Create Systemd Service for Production
echo ""
echo "Creating Systemd Service..."
echo "---------------------------"

cat > /etc/systemd/system/rsg-integration.service << EOF
[Unit]
Description=RSG Integration API Service
After=network.target

[Service]
Type=exec
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/main.py
Restart=always
RestartSec=10
StandardOutput=append:$APP_DIR/logs/app.log
StandardError=append:$APP_DIR/logs/error.log

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
print_status "Systemd service created"

# Step 9: Alternative - Supervisor Configuration (for better process management)
echo ""
echo "Creating Supervisor Configuration..."
echo "------------------------------------"

cat > /etc/supervisor/conf.d/rsg-integration.conf << EOF
[program:rsg-integration]
command=$APP_DIR/venv/bin/python $APP_DIR/main.py
directory=$APP_DIR
user=$APP_USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=$APP_DIR/logs/supervisor.log
environment=PATH="$APP_DIR/venv/bin",HOME="/home/$APP_USER",USER="$APP_USER"
EOF

print_status "Supervisor configuration created"

# Step 10: Nginx Configuration
echo ""
echo "Configuring Nginx..."
echo "--------------------"

cat > /etc/nginx/sites-available/rsg-integration << 'EOF'
upstream rsg_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name _;  # Replace with your domain
    
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://rsg_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    location /health {
        proxy_pass http://rsg_backend/health;
        access_log off;
    }
}
EOF

ln -sf /etc/nginx/sites-available/rsg-integration /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx

print_status "Nginx configured"

# Step 11: Setup Log Rotation
echo ""
echo "Setting up Log Rotation..."
echo "--------------------------"

cat > /etc/logrotate.d/rsg-integration << EOF
$APP_DIR/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 640 $APP_USER $APP_USER
    sharedscripts
    postrotate
        supervisorctl restart rsg-integration > /dev/null 2>&1 || true
    endscript
}
EOF

print_status "Log rotation configured"

# Step 12: Start Services
echo ""
echo "=========================================="
echo "DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "Next Steps:"
echo "1. Edit the environment file: $APP_DIR/.env"
echo "2. Choose your process manager:"
echo ""
echo "   Option A: Use Systemd (simpler):"
echo "     sudo systemctl enable rsg-integration"
echo "     sudo systemctl start rsg-integration"
echo "     sudo systemctl status rsg-integration"
echo ""
echo "   Option B: Use Supervisor (recommended for production):"
echo "     sudo supervisorctl reread"
echo "     sudo supervisorctl update"
echo "     sudo supervisorctl start rsg-integration"
echo "     sudo supervisorctl status rsg-integration"
echo ""
echo "3. Check application logs:"
echo "   tail -f $APP_DIR/logs/app.log"
echo ""
echo "4. Test the API:"
echo "   curl http://localhost:8000/health"
echo ""
echo "5. Access via Nginx:"
echo "   curl http://your-server-ip/"
echo ""
echo "=========================================="