# Deploy to AWS - Quick Guide

## Option 1: Deploy with Docker on EC2

### On your local machine:
```bash
# 1. Commit your changes (with logging updates)
git add -A
git commit -m "Add file-based logging for API requests"
git push origin release

# 2. Build and test Docker image locally (optional)
docker build -t rsg-integration .
```

### On your AWS EC2 instance:
```bash
# 1. Clone or pull latest code
git clone <your-repo-url> RSG_Integration_2
# OR if already cloned:
cd RSG_Integration_2
git pull origin release

# 2. Create .env file with IMS credentials
cp .env.example .env
nano .env  # Edit with your actual IMS credentials

# 3. Build Docker image
docker build -t rsg-integration .

# 4. Run with Docker
docker run -d \
  --name rsg-integration \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  --restart unless-stopped \
  rsg-integration

# 5. Check logs
docker logs rsg-integration
# Or check file logs
tail -f logs/api_*.log

# 6. Test the deployment
curl http://localhost:8000/health
```

## Option 2: Deploy with Python directly on EC2

### On your AWS EC2 instance:
```bash
# 1. Install Python 3.11 and dependencies
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip -y

# 2. Clone repository
git clone <your-repo-url> RSG_Integration_2
cd RSG_Integration_2

# 3. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# 5. Configure environment
cp .env.example .env
nano .env  # Edit with your actual IMS credentials

# 6. Run with systemd (for production)
# Create service file:
sudo nano /etc/systemd/system/rsg-integration.service
```

Add this content to the service file:
```ini
[Unit]
Description=RSG Integration Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/RSG_Integration_2
Environment="PATH=/home/ubuntu/RSG_Integration_2/venv/bin"
ExecStart=/home/ubuntu/RSG_Integration_2/venv/bin/python main.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Then:
```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable rsg-integration
sudo systemctl start rsg-integration

# Check status
sudo systemctl status rsg-integration

# View logs
sudo journalctl -u rsg-integration -f
# Or check file logs
tail -f logs/api_*.log
```

## Option 3: Deploy with Docker Compose

```bash
# On EC2 instance
docker-compose up -d

# View logs
docker-compose logs -f
```

## Security Notes for AWS

1. **Security Group Settings:**
   - Allow inbound port 8000 from your application servers only
   - Allow outbound to IMS server (10.64.32.234)

2. **Environment Variables:**
   - Never commit .env file with real credentials
   - Consider using AWS Secrets Manager or Parameter Store

3. **Logs:**
   - Logs are stored in `/app/logs/` directory
   - New log file created on each restart
   - Logs directory is in .gitignore (won't be committed)

## Testing the Deployment

```bash
# From EC2 instance or allowed network:
curl http://<ec2-ip>:8000/health

# Test transaction endpoint (will need valid payload)
curl -X POST http://<ec2-ip>:8000/api/triton/transaction/new \
  -H "Content-Type: application/json" \
  -d @test_payload.json
```

## Monitoring

- API logs: `logs/api_YYYYMMDD_HHMMSS.log`
- Each restart creates a new log file
- Logs include all API requests, errors, and debug info

## Troubleshooting

If service won't start:
```bash
# Check logs
tail -f logs/api_*.log
docker logs rsg-integration
sudo journalctl -u rsg-integration -n 50

# Test IMS connectivity from EC2
curl http://10.64.32.234/ims_one

# Check environment variables
docker exec rsg-integration env | grep IMS
```