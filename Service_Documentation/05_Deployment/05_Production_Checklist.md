# Production Deployment Checklist

This checklist ensures all requirements are met before deploying the RSG Integration Service to production.

## Pre-Deployment Verification

### ✅ Infrastructure Requirements

#### Hardware
- [ ] **CPU**: Minimum 4 vCPUs available
- [ ] **RAM**: Minimum 8 GB available
- [ ] **Storage**: 50 GB SSD with growth capacity
- [ ] **Network**: 100 Mbps minimum bandwidth
- [ ] **Backup**: Automated backup solution configured

#### Software
- [ ] **OS**: Ubuntu 20.04/22.04 LTS or RHEL 8+
- [ ] **Python**: Version 3.11 installed
- [ ] **Docker**: Version 20.10+ (if using containers)
- [ ] **MySQL**: Local instance for transaction logs
- [ ] **SSL Certificates**: Valid certificates installed

### ✅ Network Configuration

#### Connectivity Verification
- [ ] **IMS SOAP Endpoints**: Accessible from server
  ```bash
  # Test IMS One
  curl -I http://dc02imsws01.rsgcorp.local:9213
  
  # Test ISCMGA
  curl -I https://ws2.mgasystems.com
  ```

- [ ] **Database Connectivity**: 
  - [ ] Triton MySQL accessible (direct or via SSM)
  - [ ] Local MySQL accessible
  ```bash
  # Test Triton connection
  mysql -h triton-host -P 3306 -u user -p
  
  # Test local MySQL
  mysql -h localhost -u root -p
  ```

#### Firewall Rules
- [ ] **Inbound Rules Configured**:
  ```
  Port 80/443 from authorized source IPs
  Port 8000 from internal monitoring
  ```

- [ ] **Outbound Rules Configured**:
  ```
  Port 80/9213 to IMS One servers
  Port 443 to ISCMGA servers
  Port 3306 to Triton database
  Port 443 to AWS (if using SSM)
  ```

### ✅ Security Configuration

#### API Security
- [ ] **Production API Keys Generated** (32+ characters)
- [ ] **API Keys Stored Securely** (not in code)
- [ ] **CORS Origins Restricted** (not ["*"])
- [ ] **SSL/TLS Enabled** for all endpoints
- [ ] **IP Whitelisting** configured (if applicable)

#### Credentials
- [ ] **IMS Credentials**:
  - [ ] Production username configured
  - [ ] Password properly encrypted
  - [ ] Credentials tested successfully
  
- [ ] **Database Credentials**:
  - [ ] Triton database user created
  - [ ] Local MySQL user created
  - [ ] Minimum required permissions granted

#### File Permissions
- [ ] **Application User Created**:
  ```bash
  sudo useradd -m -s /bin/bash rsgapi
  ```
- [ ] **Directory Permissions Set**:
  ```bash
  sudo chown -R rsgapi:rsgapi /opt/rsg-integration
  chmod 755 /opt/rsg-integration
  ```

### ✅ Configuration Validation

#### Environment Variables
- [ ] **All Required Variables Set** in `.env`
- [ ] **No Default/Test Values** remaining
- [ ] **Production GUIDs Configured**:
  - [ ] Producer GUIDs valid
  - [ ] Line GUIDs valid
  - [ ] Underwriter GUIDs valid
  - [ ] Rater IDs configured

#### Configuration Files
- [ ] **IMS Config Files** present:
  - [ ] `IMS_Configs/IMS_ONE.config`
  - [ ] `IMS_Configs/ISCMGA_Test.config`
- [ ] **SSL Certificates** installed (if using Docker)
- [ ] **Nginx Configuration** updated with domain

### ✅ Database Setup

#### Local MySQL
- [ ] **Database Created**:
  ```sql
  CREATE DATABASE ims_integration;
  ```
- [ ] **Tables Created**:
  ```sql
  CREATE TABLE ims_transaction_logs (
      id INT AUTO_INCREMENT PRIMARY KEY,
      transaction_id VARCHAR(255) UNIQUE NOT NULL,
      source_system VARCHAR(50) NOT NULL,
      transaction_type VARCHAR(50) NOT NULL,
      status VARCHAR(50) NOT NULL,
      ims_response TEXT,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      INDEX idx_status (status),
      INDEX idx_created_at (created_at)
  );
  ```

#### SQLite Database
- [ ] **Directory Created** with write permissions
- [ ] **Backup Strategy** implemented

### ✅ Application Testing

#### Component Tests
- [ ] **IMS Login Test** passes:
  ```bash
  python test_ims_login.py
  ```
- [ ] **Producer Search** returns results:
  ```bash
  python test_producer_search.py
  ```
- [ ] **Database Connection** successful:
  ```bash
  python test_db_connection.py
  ```

#### Integration Tests
- [ ] **Test Transaction** processes successfully
- [ ] **All Transaction Types** tested:
  - [ ] New business
  - [ ] Updates/Endorsements
  - [ ] Cancellations
- [ ] **Error Handling** verified
- [ ] **Retry Logic** functioning

#### Performance Tests
- [ ] **Load Test** completed (expected volume)
- [ ] **Response Times** within SLA
- [ ] **Memory Usage** stable under load
- [ ] **Database Performance** acceptable

### ✅ Monitoring & Logging

#### Logging Configuration
- [ ] **Log Rotation** configured:
  ```bash
  /opt/rsg-integration/logs/*.log {
      daily
      rotate 30
      compress
      delaycompress
      notifempty
      create 0640 rsgapi rsgapi
  }
  ```
- [ ] **Log Level** set to INFO (not DEBUG)
- [ ] **Log Storage** has sufficient space

#### Monitoring Setup
- [ ] **Health Check Endpoint** accessible
- [ ] **Monitoring Tool** configured:
  - [ ] Health check every 30 seconds
  - [ ] Alert on 3 consecutive failures
- [ ] **Metrics Collection** enabled:
  - [ ] Transaction success rate
  - [ ] Processing time
  - [ ] Error rates

### ✅ Deployment Process

#### If Using Docker
- [ ] **Docker Image Built**:
  ```bash
  docker build -t rsg-integration:prod .
  ```
- [ ] **Docker Compose** configured
- [ ] **Container Registry** accessible (if using)

#### If Using Direct Deployment
- [ ] **Virtual Environment** created:
  ```bash
  python3.11 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```
- [ ] **Systemd Service** configured:
  ```bash
  sudo systemctl enable rsg-api
  sudo systemctl start rsg-api
  ```

### ✅ Backup & Recovery

#### Backup Configuration
- [ ] **Database Backup** scheduled:
  - [ ] SQLite daily backup
  - [ ] MySQL daily backup
  - [ ] 30-day retention minimum
- [ ] **Configuration Backup**:
  - [ ] .env file backed up securely
  - [ ] Config files version controlled

#### Recovery Testing
- [ ] **Restore Procedure** documented
- [ ] **Recovery Test** performed
- [ ] **RTO/RPO** requirements met:
  - [ ] RTO: 4 hours
  - [ ] RPO: 24 hours

### ✅ Documentation

#### Operational Documentation
- [ ] **Runbook** created with:
  - [ ] Startup procedures
  - [ ] Shutdown procedures
  - [ ] Common troubleshooting
- [ ] **Contact List** updated:
  - [ ] On-call rotation
  - [ ] Escalation path
  - [ ] Vendor contacts

#### Configuration Documentation
- [ ] **Architecture Diagram** current
- [ ] **Network Diagram** documented
- [ ] **Data Flow Diagram** created
- [ ] **API Documentation** accessible

### ✅ Go-Live Preparation

#### Communication
- [ ] **Stakeholders Notified** of go-live date
- [ ] **Maintenance Window** scheduled
- [ ] **Rollback Plan** documented and tested

#### Final Validation
- [ ] **Smoke Test Script** prepared
- [ ] **Production Test Data** identified
- [ ] **Success Criteria** defined

## Go-Live Checklist

### During Deployment
- [ ] **Stop Existing Services** (if applicable)
- [ ] **Deploy New Version**
- [ ] **Verify Service Started**:
  ```bash
  systemctl status rsg-api
  curl http://localhost:8000/api/health
  ```
- [ ] **Run Smoke Tests**
- [ ] **Monitor Logs** for errors

### Post-Deployment
- [ ] **Process Test Transaction**
- [ ] **Verify IMS Integration**
- [ ] **Check All Endpoints**
- [ ] **Monitor Performance**
- [ ] **Review Error Logs**

### First 24 Hours
- [ ] **Monitor Transaction Volume**
- [ ] **Check Error Rates**
- [ ] **Verify Processing Times**
- [ ] **Review Resource Usage**
- [ ] **Address Any Issues**

## Rollback Procedure

If issues arise:

1. **Stop Current Service**:
   ```bash
   sudo systemctl stop rsg-api
   ```

2. **Restore Previous Version**:
   ```bash
   cd /opt/rsg-integration
   git checkout previous-version-tag
   ```

3. **Restart Service**:
   ```bash
   sudo systemctl start rsg-api
   ```

4. **Verify Rollback**:
   ```bash
   curl http://localhost:8000/api/health
   ```

## Sign-Off

### Deployment Approval
- [ ] **Technical Lead**: ___________________ Date: _______
- [ ] **Operations Manager**: _______________ Date: _______
- [ ] **Security Officer**: ________________ Date: _______
- [ ] **Business Owner**: __________________ Date: _______

### Post-Deployment Review
- [ ] **Deployment Successful**
- [ ] **All Tests Passed**
- [ ] **No Critical Issues**
- [ ] **Performance Acceptable**

## Support Information

**24/7 Support Contact**: [Your support number]
**Escalation Contact**: [Escalation number]
**Documentation**: [Documentation URL]
**Monitoring Dashboard**: [Dashboard URL]