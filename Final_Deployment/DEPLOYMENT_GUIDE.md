# RSG Integration 2.0 - Deployment Guide

## Quick Overview

This deployment consists of two main parts:
1. **Database Deployment** - Creating tables and stored procedures
2. **Python Application Deployment** - Running the FastAPI/Uvicorn application

---

## PART 1: DATABASE DEPLOYMENT

### Step 1: Create Tables
Run the script `01_CREATE_TABLES_PRODUCTION.sql` on your SQL Server:

```sql
-- This creates:
-- 1. tblTritonQuoteData (with 48 columns)
-- 2. tblTritonTransactionData (with 12 columns)
-- Plus all indexes and constraints
```

### Step 2: Verify Tables
Run `02_VERIFY_TABLES.sql` to confirm everything was created correctly.

### Step 3: Deploy Stored Procedures
Deploy all procedures from `C:\Users\david\OneDrive\Documents\RSG_Integration_2\sql\Procs_8_25_25\`

Priority order:
1. `spProcessTritonPayload_WS.sql` (main processor)
2. `spStoreTritonTransaction_WS.sql`
3. All quote retrieval procedures (spGetQuote*.sql)
4. All transaction procedures (Process*.sql, Triton_*.sql)
5. Supporting procedures

---

## PART 2: PYTHON APPLICATION DEPLOYMENT

### Option A: Simple Development Mode (Your Current Method)

```bash
# From your project directory
python main.py
```

This runs uvicorn internally on port 8000 as configured in your `main.py`.

### Option B: Production with Nohup

```bash
# Use the provided script
./Final_Deployment/04_START_APP_NOHUP.sh start

# Or manually:
cd /opt/rsg-integration
nohup python main.py > logs/app.log 2>&1 &

# To check status:
ps aux | grep main.py
tail -f logs/app.log
```

### Option C: Production with Systemd (Recommended)

1. Run the deployment script:
```bash
sudo ./Final_Deployment/03_DEPLOY_PYTHON_APP.sh
```

2. Edit configuration:
```bash
sudo nano /opt/rsg-integration/.env
```

3. Start service:
```bash
sudo systemctl enable rsg-integration
sudo systemctl start rsg-integration
sudo systemctl status rsg-integration
```

### Option D: Direct Uvicorn (Alternative)

```bash
# With virtual environment activated
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Or with nohup:
nohup uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 > logs/uvicorn.log 2>&1 &
```

---

## ENVIRONMENT CONFIGURATION

Your `.env` file needs these key settings:

```env
# Database
DB_SERVER=your-sql-server
DB_NAME=your-database
DB_USERNAME=your-username
DB_PASSWORD=your-password

# IMS Settings
IMS_BASE_URL=http://10.64.32.234/ims_one
IMS_ONE_USERNAME=your-username
IMS_ONE_PASSWORD=your-password

# Application
DEBUG=False
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
```

---

## VERIFICATION STEPS

### 1. Test Database Connection
```python
# Run your test scripts
python test_dataaccess_simple.py
```

### 2. Test API Health
```bash
curl http://localhost:8000/health
```

### 3. Check Logs
```bash
# Application logs
tail -f logs/app_*.log

# Or if using systemd
journalctl -u rsg-integration -f
```

---

## DEPLOYMENT CHECKLIST

### Database
- [ ] Backup existing database
- [ ] Run `01_CREATE_TABLES_PRODUCTION.sql`
- [ ] Run `02_VERIFY_TABLES.sql` 
- [ ] Deploy all stored procedures from Procs_8_25_25
- [ ] Test with sample queries

### Application
- [ ] Install Python 3.9+
- [ ] Copy application files to server
- [ ] Create and activate virtual environment
- [ ] Install requirements: `pip install -r requirements.txt`
- [ ] Configure `.env` file with production values
- [ ] Create logs directory
- [ ] Start application (choose method above)
- [ ] Test `/health` endpoint
- [ ] Monitor logs for errors

### Post-Deployment
- [ ] Run test transactions
- [ ] Verify database writes
- [ ] Check error logs
- [ ] Document any issues

---

## ROLLBACK PROCEDURE

### Database Rollback
```sql
-- Only if needed!
DROP TABLE tblTritonTransactionData;
DROP TABLE tblTritonQuoteData;
-- Drop stored procedures as needed
```

### Application Rollback
```bash
# Stop the service
sudo systemctl stop rsg-integration
# Or kill the python process
pkill -f "python main.py"

# Restore previous version
git checkout <previous-version>
```

---

## MONITORING

### Check Application Status
```bash
# If using systemd
sudo systemctl status rsg-integration

# If using nohup
ps aux | grep main.py

# Check port
netstat -tlnp | grep 8000
```

### Monitor Logs
```bash
# Real-time log monitoring
tail -f logs/app_*.log

# Check for errors
grep ERROR logs/app_*.log
```

### Database Monitoring
```sql
-- Check recent transactions
SELECT TOP 10 * FROM tblTritonTransactionData 
ORDER BY date_created DESC;

-- Check processing status
SELECT transaction_type, COUNT(*) as count, 
       SUM(CASE WHEN ProcessedFlag = 1 THEN 1 ELSE 0 END) as processed
FROM tblTritonTransactionData
GROUP BY transaction_type;
```

---

## CONTACT FOR ISSUES

If you encounter issues during deployment:
1. Check the logs first
2. Verify environment variables
3. Test database connectivity
4. Ensure all dependencies are installed

---

## NOTES

- The application runs internally with uvicorn as shown in `main.py`
- Default port is 8000 (configurable in .env)
- Logs are created in the `logs/` directory with timestamps
- The application uses FastAPI with automatic API documentation at `/docs`