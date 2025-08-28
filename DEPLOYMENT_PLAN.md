# RSG Integration 2.0 - Production Deployment Plan

## Overview
This document outlines the comprehensive deployment plan for the RSG Integration system, consisting of database schema changes and AWS application deployment.

---

## PHASE 1: DATABASE DEPLOYMENT

### 1.1 Pre-Deployment Checklist
- [ ] Backup existing production database
- [ ] Verify SQL Server version compatibility (2016+)
- [ ] Confirm database user permissions for DDL operations
- [ ] Schedule maintenance window
- [ ] Prepare rollback scripts

### 1.2 Table Creation

#### Step 1: Export Existing Table Structures (if upgrading)
Run the script in `sql/EXPORT_TABLE_SCRIPTS.sql` to capture current table definitions with all constraints.

#### Step 2: Create Core Tables
Execute the following scripts in order:

1. **tblTritonQuoteData** - Stores current state of each quote
   ```sql
   -- Location: sql/old sql/needforproduction/actaullyneed/PRODUCTION_create_tblTritonQuoteData.sql
   -- This table includes:
   - Primary key: TritonQuoteDataID (INT IDENTITY)
   - Unique constraint on QuoteGuid
   - Indexes on QuoteOptionGuid, policy_number, opportunity_id, etc.
   ```

2. **tblTritonTransactionData** - Stores transaction history (append-only)
   ```sql
   -- Location: sql/old sql/needforproduction/actaullyneed/PRODUCTION_create_tblTritonTransactionData.sql
   -- This table includes:
   - Primary key: TritonTransactionDataID (INT IDENTITY)
   - Unique constraint on transaction_id
   - Full JSON payload storage for audit trail
   ```

### 1.3 Stored Procedure Deployment

Deploy all stored procedures from: `C:\Users\david\OneDrive\Documents\RSG_Integration_2\sql\Procs_8_25_25\`

#### Core Transaction Procedures (Deploy First)
1. `spProcessTritonPayload_WS.sql` - Main payload processor
2. `spStoreTritonTransaction_WS.sql` - Transaction storage

#### Quote Management Procedures
3. `spGetQuoteByOpportunityID_WS.sql`
4. `spGetLatestQuoteByOpportunityID_WS.sql`
5. `spGetQuoteByPolicyNumber_WS.sql`
6. `spGetQuoteByExpiringPolicyNumber_WS.sql`
7. `spGetQuoteByOptionID_WS.sql`
8. `spCheckQuoteBoundStatus_WS.sql`

#### Transaction Processing Procedures
9. `ProcessFlatEndorsement.sql`
10. `ProcessFlatCancellation.sql`
11. `ProcessFlatReinstatement.sql`
12. `Triton_ProcessFlatEndorsement_WS.sql`
13. `Triton_ProcessFlatCancellation_WS.sql`
14. `Triton_ProcessFlatReinstatement_WS.sql`
15. `Triton_UnbindPolicy_WS.sql`

#### Supporting Procedures
16. `getProducerGuid_WS.sql`
17. `spChangeProducer_Triton.sql`
18. `spApplyTritonPolicyFee_WS.sql`
19. `spGetPolicyPremiumTotal_WS.sql`
20. `ryan_rptInvoice_WS.sql`

### 1.4 Post-Deployment Verification

```sql
-- Verify table creation
SELECT name FROM sys.tables WHERE name IN ('tblTritonQuoteData', 'tblTritonTransactionData');

-- Verify stored procedures
SELECT name FROM sys.procedures WHERE name LIKE '%_WS%' OR name LIKE 'Process%' OR name LIKE 'Triton_%';

-- Check indexes
SELECT t.name AS TableName, i.name AS IndexName, i.type_desc
FROM sys.indexes i
JOIN sys.tables t ON i.object_id = t.object_id
WHERE t.name IN ('tblTritonQuoteData', 'tblTritonTransactionData');
```

---

## PHASE 2: AWS APPLICATION DEPLOYMENT

### 2.1 Pre-Deployment Requirements

#### System Requirements
- Python 3.9+
- Ubuntu 20.04 LTS or Amazon Linux 2
- 2 vCPUs minimum, 4GB RAM recommended
- Security groups configured for ports 80/443 (external) and 8000 (internal)

#### Dependencies Installation
```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Python and pip
sudo apt-get install python3.9 python3-pip python3.9-venv -y

# Install system dependencies
sudo apt-get install build-essential libssl-dev libffi-dev python3-dev -y
```

### 2.2 Application Setup

#### Step 1: Deploy Application Code
```bash
# Create application directory
sudo mkdir -p /opt/rsg-integration
sudo chown ubuntu:ubuntu /opt/rsg-integration

# Clone or copy application files
cd /opt/rsg-integration
# Copy all application files here

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 2: Configure Environment Variables
```bash
# Create .env file
cat > /opt/rsg-integration/.env << 'EOF'
# Database Configuration
DB_SERVER=your-db-server.amazonaws.com
DB_NAME=your-database-name
DB_USERNAME=your-username
DB_PASSWORD=your-password

# IMS Configuration
IMS_BASE_URL=https://your-ims-url.com
IMS_USERNAME=your-ims-username
IMS_PASSWORD=your-ims-password

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
MAX_WORKERS=4

# Azure Function Settings (if applicable)
AZURE_STORAGE_CONNECTION_STRING=your-connection-string
EOF

# Secure the file
chmod 600 /opt/rsg-integration/.env
```

### 2.3 Uvicorn Deployment

#### Step 1: Create Systemd Service
```bash
sudo cat > /etc/systemd/system/rsg-integration.service << 'EOF'
[Unit]
Description=RSG Integration API Service
After=network.target

[Service]
Type=exec
User=ubuntu
Group=ubuntu
WorkingDirectory=/opt/rsg-integration
Environment="PATH=/opt/rsg-integration/venv/bin"
ExecStart=/opt/rsg-integration/venv/bin/uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --loop uvloop \
    --log-level info \
    --access-log \
    --use-colors \
    --reload-dir /opt/rsg-integration/app

Restart=always
RestartSec=10
StandardOutput=append:/var/log/rsg-integration/app.log
StandardError=append:/var/log/rsg-integration/error.log

[Install]
WantedBy=multi-user.target
EOF
```

#### Step 2: Configure Logging
```bash
# Create log directory
sudo mkdir -p /var/log/rsg-integration
sudo chown ubuntu:ubuntu /var/log/rsg-integration

# Setup log rotation
sudo cat > /etc/logrotate.d/rsg-integration << 'EOF'
/var/log/rsg-integration/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 640 ubuntu ubuntu
    sharedscripts
    postrotate
        systemctl reload rsg-integration
    endscript
}
EOF
```

#### Step 3: Start and Enable Service
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable rsg-integration

# Start the service
sudo systemctl start rsg-integration

# Check status
sudo systemctl status rsg-integration
```

### 2.4 Nginx Reverse Proxy Configuration

```bash
# Install Nginx
sudo apt-get install nginx -y

# Configure Nginx
sudo cat > /etc/nginx/sites-available/rsg-integration << 'EOF'
upstream rsg_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL Configuration
    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.pem;
    
    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    
    # Proxy settings
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
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://rsg_backend/health;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/rsg-integration /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 2.5 Production Optimizations

#### Performance Tuning
```bash
# Increase file descriptor limits
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Tune kernel parameters
sudo cat >> /etc/sysctl.conf << 'EOF'
net.core.somaxconn = 1024
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.tcp_synack_retries = 2
net.ipv4.tcp_syn_retries = 2
EOF

sudo sysctl -p
```

#### Monitoring Setup
```bash
# Install monitoring tools
pip install prometheus-client

# Add health check endpoint to main.py
# Add metrics endpoint for Prometheus
```

### 2.6 Deployment Verification

#### Application Health Checks
```bash
# Check service status
sudo systemctl status rsg-integration

# Test API endpoint
curl -X GET http://localhost:8000/health

# Check logs
tail -f /var/log/rsg-integration/app.log

# Test database connectivity
curl -X POST http://localhost:8000/api/test-connection
```

#### Performance Testing
```bash
# Install Apache Bench
sudo apt-get install apache2-utils -y

# Run load test
ab -n 1000 -c 10 http://localhost:8000/api/health
```

---

## PHASE 3: ROLLBACK PROCEDURES

### Database Rollback
```sql
-- Drop new tables if needed
DROP TABLE IF EXISTS tblTritonTransactionData;
DROP TABLE IF EXISTS tblTritonQuoteData;

-- Drop new stored procedures
-- List all procedures and drop them
```

### Application Rollback
```bash
# Stop service
sudo systemctl stop rsg-integration

# Restore previous version
cd /opt/rsg-integration
git checkout previous-version-tag

# Restart service
sudo systemctl start rsg-integration
```

---

## PHASE 4: POST-DEPLOYMENT TASKS

### 4.1 Monitoring Setup
- [ ] Configure CloudWatch/Datadog alerts
- [ ] Set up database performance monitoring
- [ ] Configure application APM
- [ ] Set up error tracking (Sentry/Rollbar)

### 4.2 Documentation Updates
- [ ] Update API documentation
- [ ] Update runbook with new procedures
- [ ] Document configuration changes
- [ ] Update disaster recovery plan

### 4.3 Performance Baseline
- [ ] Capture initial performance metrics
- [ ] Document response times for key endpoints
- [ ] Record database query performance
- [ ] Set up performance trending

---

## DEPLOYMENT SCHEDULE

| Phase | Task | Duration | Team |
|-------|------|----------|------|
| 1 | Database Backup | 30 min | DBA |
| 2 | Table Creation | 15 min | DBA |
| 3 | Stored Procedure Deployment | 45 min | DBA |
| 4 | Database Verification | 15 min | DBA |
| 5 | Application Deployment | 30 min | DevOps |
| 6 | Configuration | 15 min | DevOps |
| 7 | Service Start | 10 min | DevOps |
| 8 | Smoke Testing | 30 min | QA |
| 9 | Performance Testing | 30 min | QA |
| 10 | Go/No-Go Decision | 15 min | All |

**Total Duration: ~3.5 hours**

---

## CONTACT INFORMATION

| Role | Name | Contact |
|------|------|---------|
| Database Lead | TBD | email@company.com |
| DevOps Lead | TBD | email@company.com |
| Application Owner | TBD | email@company.com |
| Emergency Contact | TBD | phone-number |

---

## APPROVAL SIGNATURES

- [ ] Database Team Lead: _________________ Date: _______
- [ ] DevOps Team Lead: _________________ Date: _______
- [ ] Application Owner: _________________ Date: _______
- [ ] Change Advisory Board: _________________ Date: _______