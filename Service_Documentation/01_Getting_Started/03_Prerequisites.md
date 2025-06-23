# Prerequisites

This document outlines all prerequisites needed before setting up the RSG Integration Service.

## System Requirements

### Hardware Requirements

#### Minimum (Development/Testing)
- **CPU**: 2 vCPUs
- **RAM**: 4 GB
- **Storage**: 20 GB SSD
- **Network**: 10 Mbps

#### Recommended (Production)
- **CPU**: 4 vCPUs
- **RAM**: 8 GB
- **Storage**: 50 GB SSD
- **Network**: 100 Mbps

### Operating System
- **Ubuntu**: 20.04 LTS or 22.04 LTS (recommended)
- **RHEL/CentOS**: 8 or higher
- **Windows**: Server 2019 or higher (with WSL2 for development)
- **macOS**: 12.0 or higher (development only)

## Software Requirements

### Required Software

#### Python
- **Version**: 3.11.x (required)
- **Installation**:
  ```bash
  # Ubuntu/Debian
  sudo apt update
  sudo apt install python3.11 python3.11-venv python3-pip

  # RHEL/CentOS
  sudo yum install python3.11

  # macOS (using Homebrew)
  brew install python@3.11

  # Windows
  # Download from python.org or use Windows Store
  ```

#### System Dependencies
```bash
# Ubuntu/Debian
sudo apt install -y \
  build-essential \
  libssl-dev \
  libffi-dev \
  libxml2-dev \
  libxslt1-dev \
  zlib1g-dev \
  default-libmysqlclient-dev

# RHEL/CentOS
sudo yum install -y \
  gcc \
  openssl-devel \
  python3-devel \
  libxml2-devel \
  libxslt-devel \
  mysql-devel
```

### Optional Software

#### MySQL (for Triton polling and/or local logs)
```bash
# Ubuntu/Debian
sudo apt install mysql-server mysql-client

# RHEL/CentOS
sudo yum install mysql-server mysql

# Start and enable
sudo systemctl start mysql
sudo systemctl enable mysql
```

#### Docker (for containerized deployment)
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo pip3 install docker-compose
```

#### AWS CLI (if using SSM tunnel for Triton)
```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Install Session Manager plugin
curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "session-manager-plugin.deb"
sudo dpkg -i session-manager-plugin.deb
```

## Access Requirements

### IMS Access

#### Credentials Needed
- **IMS Username**: For API authentication
- **IMS Password**: Encrypted format
- **Environment Access**: Either "ims_one" or "iscmga_test"

#### Network Access Required
- **IMS One Environment**:
  - Host: `dc02imsws01.rsgcorp.local`
  - Ports: 80, 9213
  - Protocol: HTTP/SOAP

- **ISCMGA Test Environment**:
  - Host: `ws2.mgasystems.com`
  - Port: 443
  - Protocol: HTTPS/SOAP

### Database Access

#### For Triton Integration (Optional)
- **MySQL/MariaDB Access**
- **Host**: Triton database server
- **Port**: 3306 (or custom)
- **Credentials**: Read access minimum
- **Tables**: Access to policy tables

#### For Local Transaction Logs
- **MySQL/MariaDB**: Local or remote
- **Database**: Create permissions
- **Tables**: Create and write permissions

### API Keys

You'll need to generate:
- **API Keys**: For general API access
- **Source-Specific Keys**: For Triton, Xuber, etc.
- **Minimum Length**: 32 characters
- **Format**: Alphanumeric with symbols

## Network Requirements

### Firewall Rules

#### Inbound (if exposing API)
```
Port 8000 (or custom) from authorized IPs
Port 443 (if using HTTPS) from authorized IPs
```

#### Outbound
```
Port 80/9213 to IMS One servers
Port 443 to ISCMGA servers
Port 3306 to database servers
Port 443 to AWS (if using SSM)
```

### DNS Resolution
Ensure you can resolve:
- IMS server hostnames
- Database server hostnames
- External API endpoints

## Development Tools

### Recommended IDE/Editors
- **VS Code**: With Python extension
- **PyCharm**: Professional or Community
- **Sublime Text**: With Python packages

### Testing Tools
- **Postman**: For API testing
- **curl**: Command-line testing
- **Python requests**: For scripting

### Version Control
- **Git**: For code management
- **GitHub/GitLab**: For repository hosting

## Knowledge Prerequisites

### Technical Skills Needed
- **Python**: Basic understanding
- **REST APIs**: Concept understanding
- **JSON/XML**: Data format familiarity
- **MySQL**: Basic SQL knowledge (optional)
- **Linux/Bash**: Command line basics

### IMS Knowledge
- **IMS Workflow**: Quote → Bind → Issue process
- **IMS Entities**: Insured, Producer, Quote concepts
- **SOAP APIs**: Basic understanding helpful

## Pre-Installation Checklist

Before proceeding with installation:

- [ ] **Python 3.11** installed and accessible
- [ ] **System dependencies** installed
- [ ] **IMS credentials** obtained
- [ ] **Network connectivity** verified:
  ```bash
  # Test IMS connectivity
  ping dc02imsws01.rsgcorp.local  # For IMS One
  ping ws2.mgasystems.com         # For ISCMGA
  
  # Test ports
  nc -zv dc02imsws01.rsgcorp.local 9213
  nc -zv ws2.mgasystems.com 443
  ```
- [ ] **API keys** generated (or plan to generate)
- [ ] **Database access** confirmed (if needed)
- [ ] **Disk space** available (minimum 5GB)
- [ ] **Repository access** granted

## Troubleshooting Prerequisites

### Python Version Issues
```bash
# Check Python version
python3.11 --version

# If not found, try:
python3 --version

# Create alias if needed
alias python3.11=python3
```

### Network Connectivity
```bash
# Test DNS resolution
nslookup dc02imsws01.rsgcorp.local
nslookup ws2.mgasystems.com

# Test with curl
curl -I http://dc02imsws01.rsgcorp.local:9213
curl -I https://ws2.mgasystems.com
```

### Permission Issues
```bash
# Fix permission issues
sudo chown -R $USER:$USER ~/RSG\ Integration
chmod -R 755 ~/RSG\ Integration
```

## Next Steps

Once all prerequisites are met:
1. Follow the [Quick Start Guide](./02_Quick_Start.md)
2. Configure your [Environment Variables](../02_Configuration/01_Environment_Variables.md)
3. Test your setup with provided scripts
4. Begin integration development

## Getting Help

If you encounter issues with prerequisites:
- Check system logs: `journalctl -xe`
- Verify network routes: `traceroute <hostname>`
- Test connectivity: `telnet <host> <port>`
- Review firewall rules: `sudo iptables -L`