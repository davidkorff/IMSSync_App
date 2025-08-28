# MASTER DEPLOYMENT GUIDE - RSG INTEGRATION 2.0

## ARCHITECTURE OVERVIEW

**Two Separate Systems:**
1. **IMS Database Server** - SQL Server with tables and stored procedures
2. **AWS Application Server** - Python FastAPI application

---

## PART 1: IMS DATABASE DEPLOYMENT

### What Gets Deployed
- 2 new tables (tblTritonQuoteData, tblTritonTransactionData)
- 20+ stored procedures from `sql/Procs_8_25_25/`

### Deployment Steps

1. **Run Table Creation Script**
   - File: `01_CREATE_TABLES_PRODUCTION.sql`
   - IMPORTANT: Change database name on line 7
   - Creates both tables with all indexes

2. **Verify Tables**
   - File: `02_VERIFY_TABLES.sql`
   - Confirms tables, columns, indexes

3. **Deploy Stored Procedures**
   - Location: `C:\Users\david\OneDrive\Documents\RSG_Integration_2\sql\Procs_8_25_25\`
   - Deploy all 20+ procedures in order listed in `IMS_DATABASE_DEPLOYMENT.md`

### Critical Stored Procedures (Must Have)
- spProcessTritonPayload_WS.sql
- spStoreTritonTransaction_WS.sql
- spGetQuoteByOpportunityID_WS.sql
- spGetLatestQuoteByOpportunityID_WS.sql
- Triton_ProcessFlatEndorsement_WS.sql
- Triton_ProcessFlatCancellation_WS.sql
- Triton_UnbindPolicy_WS.sql

---

## PART 2: AWS APPLICATION DEPLOYMENT

### What Gets Deployed
- Python FastAPI application
- Runs on port 8000
- Connects to IMS database and web services

### Quick Deployment Steps

1. **Copy Files to AWS**
   ```bash
   scp -r RSG_Integration_2/ ubuntu@aws-server:/home/ubuntu/
   ```

2. **SSH to AWS Server**
   ```bash
   ssh ubuntu@aws-server
   ```

3. **Install Dependencies**
   ```bash
   cd RSG_Integration_2
   pip3 install -r requirements.txt
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   nano .env  # Edit with actual values
   ```

5. **Start Application**
   ```bash
   # Simple method (your current approach):
   python3 main.py
   
   # Or use the startup script:
   chmod +x Final_Deployment/AWS_STARTUP_SCRIPT.sh
   ./Final_Deployment/AWS_STARTUP_SCRIPT.sh
   ```

---

## CRITICAL CONFIGURATION (.env file)

```env
# These MUST be correct or app won't work!

# IMS Database (where you created the tables)
DB_SERVER=your-ims-sql-server.domain.com
DB_NAME=IMS_Database_Name
DB_USERNAME=sql_username
DB_PASSWORD=sql_password

# IMS Web Services
IMS_BASE_URL=http://10.64.32.234/ims_one
IMS_ONE_USERNAME=web_service_username
IMS_ONE_PASSWORD=web_service_password
```

---

## VERIFICATION CHECKLIST

### IMS Database
- [ ] Tables created (check with: `SELECT * FROM sys.tables WHERE name LIKE '%Triton%'`)
- [ ] 48 columns in tblTritonQuoteData
- [ ] 12 columns in tblTritonTransactionData
- [ ] All stored procedures deployed
- [ ] Test query works: `EXEC spGetLatestQuoteByOpportunityID_WS @OpportunityID = 1`

### AWS Application
- [ ] Application starts without errors
- [ ] Health check responds: `curl http://localhost:8000/health`
- [ ] Can connect to database (check logs)
- [ ] API docs accessible: `http://server:8000/docs`

---

## TROUBLESHOOTING

### Database Issues
```sql
-- Check if tables exist
SELECT name FROM sys.tables WHERE name IN ('tblTritonQuoteData', 'tblTritonTransactionData');

-- Check stored procedures
SELECT name FROM sys.procedures WHERE name LIKE '%_WS%';

-- Test connection
EXEC sp_helpdb;
```

### Application Issues
```bash
# Check if running
ps aux | grep main.py

# Check logs
tail -f logs/app_*.log

# Test database connection
python3 -c "import pyodbc; print('DB OK')"

# Kill stuck process
pkill -f "python.*main.py"
```

---

## ROLLBACK PLAN

### Database Rollback
```sql
-- WARNING: This deletes everything including data!
-- Step 1: Drop tables (order matters due to dependencies)
DROP TABLE IF EXISTS tblTritonTransactionData;
DROP TABLE IF EXISTS tblTritonQuoteData;

-- Step 2: Drop stored procedures
DROP PROCEDURE IF EXISTS spProcessTritonPayload_WS;
DROP PROCEDURE IF EXISTS spStoreTritonTransaction_WS;
DROP PROCEDURE IF EXISTS spGetQuoteByOpportunityID_WS;
DROP PROCEDURE IF EXISTS spGetLatestQuoteByOpportunityID_WS;
DROP PROCEDURE IF EXISTS spGetQuoteByPolicyNumber_WS;
DROP PROCEDURE IF EXISTS spGetQuoteByExpiringPolicyNumber_WS;
DROP PROCEDURE IF EXISTS spGetQuoteByOptionID_WS;
DROP PROCEDURE IF EXISTS spCheckQuoteBoundStatus_WS;
DROP PROCEDURE IF EXISTS spGetPolicyPremiumTotal_WS;
DROP PROCEDURE IF EXISTS ProcessFlatEndorsement;
DROP PROCEDURE IF EXISTS ProcessFlatCancellation;
DROP PROCEDURE IF EXISTS ProcessFlatReinstatement;
DROP PROCEDURE IF EXISTS Triton_ProcessFlatEndorsement_WS;
DROP PROCEDURE IF EXISTS Triton_ProcessFlatCancellation_WS;
DROP PROCEDURE IF EXISTS Triton_ProcessFlatReinstatement_WS;
DROP PROCEDURE IF EXISTS Triton_UnbindPolicy_WS;
DROP PROCEDURE IF EXISTS getProducerGuid_WS;
DROP PROCEDURE IF EXISTS spChangeProducer_Triton;
DROP PROCEDURE IF EXISTS spApplyTritonPolicyFee_WS;
DROP PROCEDURE IF EXISTS ryan_rptInvoice_WS;

-- Verify cleanup
SELECT 'Tables:', COUNT(*) FROM sys.tables WHERE name LIKE '%Triton%';
SELECT 'Procedures:', COUNT(*) FROM sys.procedures WHERE name LIKE '%_WS%';
```

### Application Rollback
```bash
# Step 1: Stop application
pkill -f "python.*main.py"
# Or if using systemd:
sudo systemctl stop rsg-integration

# Step 2: Verify stopped
ps aux | grep main.py

# Step 3: Restore previous version (if using git)
cd /home/ubuntu/RSG_Integration_2
git checkout <previous-commit-or-tag>

# Step 4: Restore previous .env if needed
cp .env.backup .env

# Step 5: Restart with old version
python3 main.py
# Or: ./Final_Deployment/AWS_STARTUP_SCRIPT.sh
```

---

## SUPPORT CONTACTS

During deployment, if issues arise:
1. Check logs first
2. Verify network connectivity
3. Confirm credentials in .env
4. Test database access separately

---

## POST-DEPLOYMENT

After successful deployment:
1. Monitor logs for first hour
2. Run test transactions
3. Verify data in tables
4. Document any issues encountered

---

## IMPORTANT NOTES

1. **The database and app are on DIFFERENT servers**
2. **Ensure firewall allows AWS -> IMS database connection**
3. **The app uses uvicorn internally when you run `python main.py`**
4. **Logs are created with timestamps in the logs/ folder**
5. **All stored procedures from Procs_8_25_25 must be deployed**

---

## DEPLOYMENT TIMELINE

- Database changes: ~30 minutes
- Application deployment: ~15 minutes
- Testing: ~15 minutes
- **Total: ~1 hour**