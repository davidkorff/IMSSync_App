# Non-Docker Deployment Instructions

This guide explains how to deploy and run the IMS Integration Service without Docker.

## Prerequisites

### System Requirements
- **Python**: 3.8 or higher (3.9, 3.10, or 3.11 recommended)
- **Operating System**: Windows, Linux, or macOS
- **Network Access**: 
  - IMS SOAP endpoints
  - MySQL databases (Triton and local)
  - Required ports (default: 8000)

### Software Dependencies
- Python pip package manager
- Virtual environment support (venv)
- Git (for cloning repository)

## Installation Steps

### 1. Clone Repository
```bash
git clone <repository-url>
cd "RSG Integration"
```

### 2. Set Up Python Environment

#### Option A: Using PowerShell Script (Windows)
```powershell
.\start_service.ps1
```
This script automatically:
- Checks Python installation
- Creates virtual environment
- Installs dependencies
- Sets up configuration
- Starts the service

#### Option B: Manual Setup (All Platforms)

##### Create Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

##### Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment

#### Create Configuration File
```bash
cp .env.example .env
```

#### Edit .env File
Configure all required environment variables:

```env
# IMS Configuration
IMS_URL=https://your-ims-instance/IMSWebServices/Service.asmx
IMS_USERNAME=your_username
IMS_PASSWORD=your_password
IMS_SOURCE=your_source_name

# Database Configuration
MYSQL_HOST=your-mysql-host
MYSQL_PORT=3306
MYSQL_DATABASE=your_database
MYSQL_USER=your_user
MYSQL_PASSWORD=your_password

# Triton Database
TRITON_MYSQL_HOST=triton-host
TRITON_MYSQL_PORT=3306
TRITON_MYSQL_DATABASE=triton_db
TRITON_MYSQL_USER=triton_user
TRITON_MYSQL_PASSWORD=triton_password

# Service Configuration
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8000
LOG_LEVEL=INFO

# Security
API_KEY=your-secure-api-key
SECRET_KEY=your-secret-key
```

### 4. Create Required Directories
```bash
mkdir -p logs data templates IMS_Configs
```

### 5. Verify IMS Configuration Files
Ensure the following files exist in `IMS_Configs/`:
- `IMS_ONE.config` (or your specific IMS configuration)

## Running the Service

### Option 1: Using run_service.py (Recommended)
```bash
python run_service.py --host 0.0.0.0 --port 8000 --reload
```

Command-line options:
- `--host`: Host IP (default: 0.0.0.0)
- `--port`: Port number (default: 8000)
- `--reload`: Enable auto-reload for development
- `--workers`: Number of worker processes (production)

### Option 2: Using Uvicorn Directly
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Option 3: Production Deployment with Gunicorn
```bash
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Option 4: MySQL Polling Service Only
```bash
python run_mysql_polling.py
```
This runs only the Triton database polling component.

## Service Management

### Linux Systemd Service
For production Linux deployments, create a systemd service:

1. Copy the service file:
```bash
sudo cp ims-integration.service /etc/systemd/system/
```

2. Edit the service file to match your paths:
```bash
sudo nano /etc/systemd/system/ims-integration.service
```

3. Enable and start the service:
```bash
sudo systemctl enable ims-integration
sudo systemctl start ims-integration
sudo systemctl status ims-integration
```

### Windows Service
For Windows production deployments:

1. Install as Windows Service using NSSM:
```powershell
nssm install IMSIntegration "C:\Python39\python.exe" "C:\path\to\run_service.py"
```

2. Or use the PowerShell script:
```powershell
.\start_service.ps1
```

## Testing the Installation

### 1. Test IMS Connection
```bash
python test_ims_login.py
```

### 2. Test API Endpoints
```bash
python test_client.py
```

### 3. Test Full Integration Flow
```bash
python test_triton_integration.py
```

### 4. Health Check
```bash
curl http://localhost:8000/health
```

## Monitoring and Logs

### Log Files
- Application logs: `logs/ims_integration.log`
- Error logs: `logs/ims_integration_error.log`

### Log Rotation
Configure log rotation in your environment:
```bash
# Linux logrotate example
/path/to/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Find process using port 8000
   netstat -an | grep 8000
   # Change port in .env file or command line
   ```

2. **Module Import Errors**
   ```bash
   # Ensure virtual environment is activated
   # Reinstall dependencies
   pip install -r requirements.txt --force-reinstall
   ```

3. **Database Connection Issues**
   - Verify database credentials in .env
   - Check network connectivity
   - Ensure database user has required permissions

4. **IMS Connection Failed**
   - Verify IMS URL and credentials
   - Check SSL certificates
   - Review firewall settings

### Debug Mode
Run with debug logging:
```bash
LOG_LEVEL=DEBUG python run_service.py
```

## Performance Tuning

### Development
```bash
python run_service.py --reload
```

### Production
```bash
# Multiple workers for better performance
python run_service.py --workers 4

# Or with gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log
```

## Security Considerations

1. **Environment Variables**
   - Never commit .env files
   - Use secure passwords
   - Rotate API keys regularly

2. **Network Security**
   - Use HTTPS in production
   - Configure firewall rules
   - Limit access to necessary IPs

3. **File Permissions**
   ```bash
   chmod 600 .env
   chmod 700 logs/
   ```

## Maintenance

### Updating Dependencies
```bash
pip install --upgrade -r requirements.txt
```

### Backup Configuration
```bash
cp .env .env.backup
cp -r IMS_Configs/ IMS_Configs.backup/
```

### Database Maintenance
- Regular backups of local MySQL database
- Monitor database size and performance
- Clean up old transaction logs

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review Service_Documentation/ folder
3. Run diagnostic scripts in tests/ directory
4. Contact system administrator

## Additional Resources

- [Service Documentation](Service_Documentation/README.md)
- [API Reference](Service_Documentation/03_API_Reference/01_Endpoints_Overview.md)
- [Troubleshooting Guide](Service_Documentation/07_Operations/03_Troubleshooting.md)
- [Integration Guides](Service_Documentation/04_Integration_Guides/)