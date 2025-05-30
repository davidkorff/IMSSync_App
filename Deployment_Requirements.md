# RSG Integration API - Deployment Requirements

## Executive Summary

The RSG Integration API is a FastAPI-based middleware service that facilitates insurance policy data integration between external systems (Triton and Xuber) and the IMS (Insurance Management System). This document outlines all requirements for deploying this application on an internal server.

## Application Overview

- **Application Type**: REST API Service with optional background polling service
- **Framework**: FastAPI (Python 3.11)
- **Architecture**: Microservice with asynchronous processing capabilities
- **Primary Function**: Transform and route insurance policy transactions between systems

## Server Requirements

### Hardware Requirements

**Minimum Requirements:**
- **CPU**: 2 vCPUs
- **RAM**: 4 GB
- **Storage**: 20 GB (SSD preferred)
  - Application: ~500 MB
  - SQLite Database: ~5 GB (grows with transaction volume)
  - Logs: ~5 GB (with rotation)
  - Temporary files: ~1 GB

**Recommended Production Requirements:**
- **CPU**: 4 vCPUs
- **RAM**: 8 GB
- **Storage**: 50 GB SSD
- **Network**: 100 Mbps minimum

### Operating System

- **Recommended**: Ubuntu 20.04 LTS or 22.04 LTS
- **Alternative**: RHEL 8+ or CentOS 8+
- **Container Support**: Docker 20.10+ (optional but recommended)

### Software Dependencies

#### Required Software
1. **Python 3.11**
   - Can be installed via system package manager or pyenv
   - Required for running the application

2. **System Packages**
   ```bash
   # Ubuntu/Debian
   apt-get update
   apt-get install -y python3.11 python3.11-venv python3-pip
   apt-get install -y build-essential libssl-dev libffi-dev
   apt-get install -y libxml2-dev libxslt1-dev zlib1g-dev
   
   # For MySQL connectivity
   apt-get install -y default-libmysqlclient-dev
   ```

3. **AWS CLI** (if accessing Triton MySQL via SSM tunnel)
   ```bash
   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
   unzip awscliv2.zip
   sudo ./aws/install
   ```

4. **AWS Session Manager Plugin** (if using SSM tunnel)
   ```bash
   curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "session-manager-plugin.deb"
   sudo dpkg -i session-manager-plugin.deb
   ```

## Network Requirements

### Inbound Connectivity

1. **API Service Port**
   - **Port**: 8000 (configurable)
   - **Protocol**: HTTP/HTTPS
   - **Access Required From**:
     - Triton systems
     - Xuber systems
     - Internal monitoring systems
     - Admin access for health checks

2. **Recommended Reverse Proxy Setup**
   - Use Nginx or Apache as reverse proxy
   - Handle SSL/TLS termination
   - Implement rate limiting and security headers

### Outbound Connectivity

1. **IMS Web Services**
   - **IMS One Environment**:
     - Host: `dc02imsws01.rsgcorp.local`
     - Ports: 80 (HTTP), 9213 (custom)
     - Protocols: HTTP/SOAP
   
   - **ISCMGA Test Environment**:
     - Host: `ws2.mgasystems.com`
     - Port: 443 (HTTPS)
     - Protocol: HTTPS/SOAP

2. **Triton MySQL Database** (AWS RDS)
   - **Direct Connection**:
     - Host: `triton-staging.ctfcgagzmyca.us-east-1.rds.amazonaws.com`
     - Port: 3306
     - Protocol: MySQL
   
   - **Via SSM Tunnel** (if direct connection not available):
     - AWS SSM endpoints
     - Local tunnel port: 13306

3. **External Services**
   - DNS resolution
   - NTP for time synchronization
   - Package repositories for updates

### Firewall Rules Summary

```
# Inbound
8000/tcp from [Triton IP ranges]
8000/tcp from [Xuber IP ranges]
8000/tcp from [Admin/Monitoring IP ranges]

# Outbound
80/tcp to dc02imsws01.rsgcorp.local
9213/tcp to dc02imsws01.rsgcorp.local
443/tcp to ws2.mgasystems.com
3306/tcp to triton-staging.ctfcgagzmyca.us-east-1.rds.amazonaws.com
443/tcp to AWS endpoints (if using SSM)
```

## Environment Configuration

### Required Environment Variables

Create a `.env` file with the following variables:

```bash
# Application Settings
API_V1_STR="/api/v1"
PROJECT_NAME="IMS Integration API"
LOG_LEVEL="INFO"
DEFAULT_ENVIRONMENT="iscmga_test"

# CORS Settings (adjust for production)
CORS_ORIGINS='["https://your-domain.com"]'

# Security - API Keys (generate secure keys for production)
API_KEYS='["your-secure-api-key-1","your-secure-api-key-2"]'
TRITON_API_KEYS='["triton-secure-key-1"]'
TRITON_CLIENT_IDS='["triton"]'

# IMS Credentials (obtain from IMS team)
IMS_ONE_USERNAME="your_ims_one_username"
IMS_ONE_PASSWORD="encrypted_password"
ISCMGA_TEST_USERNAME="your_iscmga_username"
ISCMGA_TEST_PASSWORD="encrypted_password"

# Triton Integration Settings
TRITON_DEFAULT_PRODUCER_GUID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
TRITON_PRIMARY_LINE_GUID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
TRITON_EXCESS_LINE_GUID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
TRITON_PRIMARY_RATER_ID=12345
TRITON_PRIMARY_FACTOR_SET_GUID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
TRITON_EXCESS_RATER_ID=67890
TRITON_EXCESS_FACTOR_SET_GUID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

# Xuber Integration Settings
XUBER_DEFAULT_PRODUCER_GUID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
XUBER_DEFAULT_LINE_GUID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
XUBER_PRIMARY_RATER_ID=11111
XUBER_PRIMARY_FACTOR_SET_GUID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

# MySQL Database Settings (for Triton)
TRITON_MYSQL_HOST="triton-staging.ctfcgagzmyca.us-east-1.rds.amazonaws.com"
TRITON_MYSQL_PORT="3306"
TRITON_MYSQL_DATABASE="triton_staging"
TRITON_MYSQL_USER="your_mysql_user"
TRITON_MYSQL_PASSWORD="your_mysql_password"

# Polling Service Settings
POLL_INTERVAL_SECONDS=60
POLL_BATCH_SIZE=10
```

### AWS Credentials (if using SSM tunnel)

Configure AWS credentials:
```bash
# ~/.aws/credentials
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
region = us-east-1
```

## File System Requirements

### Directory Structure

```
/opt/rsg-integration/          # Application root
├── app/                       # Application code
├── templates/                 # Excel templates (auto-created)
├── logs/                      # Log files
├── data/                      # SQLite database
└── temp/                      # Temporary files
```

### Permissions

```bash
# Create application user
sudo useradd -m -s /bin/bash rsgapi

# Set ownership
sudo chown -R rsgapi:rsgapi /opt/rsg-integration

# Set permissions
chmod 755 /opt/rsg-integration
chmod 755 /opt/rsg-integration/app
chmod 755 /opt/rsg-integration/templates
chmod 755 /opt/rsg-integration/logs
chmod 755 /opt/rsg-integration/data
chmod 755 /opt/rsg-integration/temp
```

### Storage Considerations

1. **Database Growth**: SQLite database grows ~1KB per transaction
2. **Log Rotation**: Configure logrotate for application logs
3. **Temp Files**: Cleaned automatically, but monitor /tmp usage
4. **Backup Requirements**: Daily backup of SQLite database recommended

## Deployment Options

### Option 1: Direct Python Deployment

1. **Setup Python Virtual Environment**
   ```bash
   cd /opt/rsg-integration
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run with systemd**
   Create `/etc/systemd/system/rsg-api.service`:
   ```ini
   [Unit]
   Description=RSG Integration API
   After=network.target

   [Service]
   Type=exec
   User=rsgapi
   WorkingDirectory=/opt/rsg-integration
   Environment="PATH=/opt/rsg-integration/venv/bin"
   EnvironmentFile=/opt/rsg-integration/.env
   ExecStart=/opt/rsg-integration/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and Start Service**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable rsg-api
   sudo systemctl start rsg-api
   ```

### Option 2: Docker Deployment

1. **Build Docker Image**
   ```bash
   cd /opt/rsg-integration
   docker build -t rsg-integration:latest .
   ```

2. **Run with Docker Compose**
   Create `docker-compose.yml`:
   ```yaml
   version: '3.8'
   services:
     api:
       image: rsg-integration:latest
       ports:
         - "8000:8000"
       volumes:
         - ./data:/app/data
         - ./logs:/app/logs
         - ./templates:/app/templates
       env_file:
         - .env
       restart: unless-stopped
   ```

3. **Start Container**
   ```bash
   docker-compose up -d
   ```

## Monitoring and Logging

### Application Logs

- **Location**: `/opt/rsg-integration/logs/ims_integration.log`
- **Format**: JSON structured logging
- **Rotation**: Configure with logrotate
- **Retention**: 30-90 days recommended

### Health Monitoring

- **Health Check Endpoint**: `GET /api/health`
- **Monitoring Interval**: Every 30 seconds
- **Alert on**: 3 consecutive failures

### Metrics to Monitor

1. **Application Metrics**
   - API response times
   - Transaction processing rate
   - Error rates by type
   - Queue depth

2. **System Metrics**
   - CPU utilization
   - Memory usage
   - Disk space (especially for SQLite)
   - Network connectivity to IMS

## Security Considerations

### API Security

1. **API Key Management**
   - Generate strong, unique API keys
   - Rotate keys every 90 days
   - Store keys securely (not in version control)

2. **Network Security**
   - Use HTTPS for all external connections
   - Implement IP whitelisting for API access
   - Use VPN for database connections if possible

3. **Application Security**
   - Run as non-root user
   - Enable Python security updates
   - Regular security scanning

### Data Security

1. **Encryption**
   - Use SSL/TLS for all external communications
   - Encrypt sensitive data at rest
   - Secure credential storage

2. **Access Control**
   - Limit file system permissions
   - Implement role-based access
   - Audit log all transactions

## Backup and Recovery

### Backup Requirements

1. **Database Backup**
   - Daily backup of SQLite database
   - 30-day retention minimum
   - Test restore procedures monthly

2. **Configuration Backup**
   - Version control for code
   - Backup .env files securely
   - Document all configuration changes

### Disaster Recovery

1. **RPO**: 24 hours
2. **RTO**: 4 hours
3. **Procedure**: Document restore process

## Performance Tuning

### Application Tuning

1. **Worker Processes**
   ```bash
   # For production, use multiple workers
   uvicorn app.main:app --workers 4
   ```

2. **Database Optimization**
   - Regular VACUUM on SQLite
   - Monitor database size
   - Consider PostgreSQL for high volume

3. **Connection Pooling**
   - MySQL connection pool size: 5-10
   - HTTP connection reuse

## Maintenance Procedures

### Regular Maintenance

1. **Daily**
   - Monitor logs for errors
   - Check transaction processing
   - Verify disk space

2. **Weekly**
   - Review performance metrics
   - Check for failed transactions
   - Update transaction status

3. **Monthly**
   - Security updates
   - Certificate renewal check
   - Backup verification

### Update Procedures

1. **Application Updates**
   - Test in staging environment
   - Schedule maintenance window
   - Have rollback plan ready

2. **Dependency Updates**
   - Review security advisories
   - Test compatibility
   - Update in stages

## Support and Troubleshooting

### Common Issues

1. **IMS Connection Failures**
   - Check network connectivity
   - Verify credentials
   - Review IMS service status

2. **Database Issues**
   - Check disk space
   - Verify file permissions
   - Run database integrity check

3. **Performance Issues**
   - Review transaction volume
   - Check system resources
   - Analyze slow queries

### Support Contacts

- **Application Team**: [Your contact info]
- **IMS Support**: [IMS team contact]
- **Infrastructure**: [IT team contact]

## Appendix A: Quick Start Checklist

- [ ] Server meets minimum requirements
- [ ] Python 3.11 installed
- [ ] Required system packages installed
- [ ] Network connectivity verified
- [ ] Firewall rules configured
- [ ] Application files copied
- [ ] Environment variables configured
- [ ] File permissions set
- [ ] Service configured and started
- [ ] Health check passing
- [ ] Test transaction processed successfully
- [ ] Monitoring configured
- [ ] Backup scheduled
- [ ] Documentation updated

## Appendix B: Environment Variable Template

A complete `.env.example` file is provided in the repository. Copy this to `.env` and update with production values.

## Appendix C: Testing Procedures

1. **API Health Check**
   ```bash
   curl http://localhost:8000/api/health
   ```

2. **Test Transaction**
   ```bash
   curl -X POST http://localhost:8000/api/transaction/new_business \
     -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     -d @test_transaction.json
   ```

3. **Check Transaction Status**
   ```bash
   curl http://localhost:8000/api/transaction/{transaction_id} \
     -H "X-API-Key: your-api-key"
   ```