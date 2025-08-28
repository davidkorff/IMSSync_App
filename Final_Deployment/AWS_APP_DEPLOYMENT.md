# AWS APPLICATION DEPLOYMENT
## Target: AWS EC2/Server Running Python Application

### PREREQUISITES

- Python 3.9+ installed on AWS instance
- Access to IMS database from AWS (network connectivity)
- Application files copied to AWS instance

### DEPLOYMENT OPTIONS

## Option 1: Simple Python Execution (Development/Testing)

```bash
# Navigate to application directory
cd /path/to/RSG_Integration_2

# Run directly
python main.py
```

## Option 2: Production with Nohup (Recommended)

Create this startup script on your AWS instance:

```bash
#!/bin/bash
# File: start_rsg_app.sh

APP_DIR="/home/ubuntu/RSG_Integration_2"  # Change to your path
LOG_DIR="$APP_DIR/logs"

# Create logs directory
mkdir -p $LOG_DIR

# Navigate to app directory
cd $APP_DIR

# Kill any existing process
pkill -f "python main.py" || true

# Start application in background
nohup python main.py > $LOG_DIR/app.log 2>&1 &

# Save PID
echo $! > $APP_DIR/app.pid

echo "Application started with PID: $(cat $APP_DIR/app.pid)"
echo "Logs: tail -f $LOG_DIR/app.log"
```

Make it executable and run:
```bash
chmod +x start_rsg_app.sh
./start_rsg_app.sh
```

## Option 3: Systemd Service (Most Robust)

Create service file: `/etc/systemd/system/rsg-integration.service`

```ini
[Unit]
Description=RSG Integration Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/RSG_Integration_2
ExecStart=/usr/bin/python3 /home/ubuntu/RSG_Integration_2/main.py
Restart=always
RestartSec=10
StandardOutput=append:/home/ubuntu/RSG_Integration_2/logs/app.log
StandardError=append:/home/ubuntu/RSG_Integration_2/logs/error.log

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable rsg-integration
sudo systemctl start rsg-integration
sudo systemctl status rsg-integration
```

### ENVIRONMENT CONFIGURATION

Create `.env` file in application directory:

```env
# IMS Database Connection
DB_SERVER=ims-database-server.domain.com
DB_NAME=IMS_Database_Name
DB_USERNAME=your_db_username
DB_PASSWORD=your_db_password

# IMS Web Service Settings
IMS_BASE_URL=http://10.64.32.234/ims_one
IMS_ONE_USERNAME=ims_username
IMS_ONE_PASSWORD=ims_password
IMS_PROGRAM_CODE=TRTON
IMS_PROJECT_NAME=RSG_Integration

# Application Settings
DEBUG=False
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# Quote Configuration (GUIDs from IMS)
IMS_QUOTING_LOCATION=C5C006BB-6437-42F3-95D4-C090ADD3B37D
IMS_ISSUING_LOCATION=C5C006BB-6437-42F3-95D4-C090ADD3B37D
IMS_COMPANY_LOCATION=DF35D4C7-C663-4974-A886-A1E18D3C9618
TRITON_PRIMARY_LINE_GUID=07564291-CBFE-4BBE-88D1-0548C88ACED4

# Triton API Keys
TRITON_API_KEY=your_api_key
TRITON_WEBHOOK_SECRET=your_webhook_secret
```

### STARTUP COMMANDS

#### Quick Start (Foreground)
```bash
cd /home/ubuntu/RSG_Integration_2
python main.py
```

#### Background with Nohup
```bash
cd /home/ubuntu/RSG_Integration_2
nohup python main.py > logs/app.log 2>&1 &
```

#### Using Screen (Alternative)
```bash
screen -S rsg-app
cd /home/ubuntu/RSG_Integration_2
python main.py
# Press Ctrl+A then D to detach
# Reattach with: screen -r rsg-app
```

### MONITORING

#### Check if Running
```bash
# Check process
ps aux | grep "python main.py"

# Check port
netstat -tlnp | grep 8000

# Check logs
tail -f logs/app_*.log
```

#### Test Health Endpoint
```bash
curl http://localhost:8000/health
```

#### View API Documentation
Open in browser: `http://your-aws-ip:8000/docs`

### STOPPING THE APPLICATION

#### If using nohup
```bash
# Find PID
ps aux | grep "python main.py"
# Kill process
kill <PID>
```

#### If using systemd
```bash
sudo systemctl stop rsg-integration
```

### TROUBLESHOOTING

1. **Cannot connect to database**
   - Check `.env` database settings
   - Verify network connectivity to IMS database
   - Test with: `telnet ims-database-server 1433`

2. **Port 8000 already in use**
   - Change PORT in `.env` file
   - Or kill existing process: `fuser -k 8000/tcp`

3. **Module not found errors**
   - Install requirements: `pip install -r requirements.txt`

4. **Permission denied**
   - Check file ownership: `chown -R ubuntu:ubuntu /path/to/app`

### AWS SECURITY GROUP SETTINGS

Ensure these ports are open:
- **Inbound**: 
  - Port 8000 (or your configured port) from allowed IPs
  - Port 22 for SSH access
- **Outbound**:
  - Port 1433 to IMS database server
  - Port 80/443 for IMS web services

### DEPLOYMENT CHECKLIST

- [ ] Copy application files to AWS instance
- [ ] Install Python 3.9+
- [ ] Install requirements: `pip install -r requirements.txt`
- [ ] Configure `.env` with correct values
- [ ] Test database connectivity
- [ ] Create logs directory
- [ ] Start application
- [ ] Verify health endpoint responds
- [ ] Check logs for errors
- [ ] Test sample transaction