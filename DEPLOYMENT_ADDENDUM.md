# Deployment Requirements - Key Clarifications

## Quick Reference for Deployment Team

### Essential Software Stack
```bash
# Core Requirements (in order)
1. Python 3.11 + pip + venv
2. MySQL Server (local) + client libraries  
3. Application dependencies (via requirements.txt)
4. Uvicorn ASGI server (included in requirements.txt)
5. Optional: AWS CLI + Session Manager (for SSM tunnel)
```

### Installation Sequence
```bash
# 1. System packages first
apt-get update
apt-get install -y python3.11 python3.11-venv python3-pip
apt-get install -y build-essential libssl-dev libffi-dev
apt-get install -y libxml2-dev libxslt1-dev zlib1g-dev
apt-get install -y default-libmysqlclient-dev

# 2. MySQL Server (for local transaction logs)
apt-get install -y mysql-server
systemctl enable mysql
systemctl start mysql

# 3. Application setup
cd /opt/rsg-integration
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt  # This includes uvicorn

# 4. Database setup
mysql -u root -p < create_ims_transaction_logs_table.sql

# 5. Configure and start
cp .env.example .env
# Edit .env with actual values
systemctl enable rsg-api
systemctl start rsg-api
```

### Key Dependencies in requirements.txt
```
fastapi>=0.100.0          # Web framework
uvicorn[standard]>=0.22.0  # ASGI server (THIS IS THE KEY ONE)
mysql-connector-python     # MySQL connectivity
pydantic>=2.0.0           # Data validation
requests>=2.31.0          # HTTP client for SOAP calls
openpyxl>=3.1.2           # Excel processing
```

### Verification Commands
```bash
# Check Python
python3.11 --version

# Check virtual environment
source /opt/rsg-integration/venv/bin/activate
which uvicorn  # Should show: /opt/rsg-integration/venv/bin/uvicorn

# Check dependencies
pip list | grep -E "(fastapi|uvicorn|mysql-connector)"

# Test service start
cd /opt/rsg-integration && venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Common Deployment Issues
1. **"uvicorn command not found"** → Virtual environment not activated
2. **"No module named mysql.connector"** → libmysqlclient-dev not installed
3. **"Permission denied"** → File ownership/permissions not set correctly
4. **"Port 8000 already in use"** → Change port or kill existing process

The main Deployment_Requirements.md is comprehensive - this just clarifies the essentials!