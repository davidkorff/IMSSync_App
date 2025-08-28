# IMS DATABASE DEPLOYMENT
## Target: IMS SQL Server Database

### STEP 1: CREATE TABLES

Run script: `01_CREATE_TABLES_PRODUCTION.sql`

This creates:
- **tblTritonQuoteData** (48 columns with indexes)
- **tblTritonTransactionData** (12 columns with indexes)

**IMPORTANT**: Change the database name on line 7:
```sql
USE [YourDatabaseName]; -- CHANGE THIS TO YOUR IMS DATABASE NAME
```

### STEP 2: VERIFY TABLES

Run script: `02_VERIFY_TABLES.sql`

This will confirm:
- Tables exist
- All columns are present
- Indexes are created
- Constraints are in place

### STEP 3: DEPLOY STORED PROCEDURES

Deploy ALL procedures from: `C:\Users\david\OneDrive\Documents\RSG_Integration_2\sql\Procs_8_25_25\`

**Order of deployment:**

#### Core Procedures (Deploy First)
1. `spProcessTritonPayload_WS.sql`
2. `spStoreTritonTransaction_WS.sql`

#### Quote Retrieval Procedures
3. `spGetQuoteByOpportunityID_WS.sql`
4. `spGetLatestQuoteByOpportunityID_WS.sql`  
5. `spGetQuoteByPolicyNumber_WS.sql`
6. `spGetQuoteByExpiringPolicyNumber_WS.sql`
7. `spGetQuoteByOptionID_WS.sql`
8. `spCheckQuoteBoundStatus_WS.sql`
9. `spGetPolicyPremiumTotal_WS.sql`

#### Transaction Processing Procedures
10. `ProcessFlatEndorsement.sql`
11. `ProcessFlatCancellation.sql`
12. `ProcessFlatReinstatement.sql`
13. `Triton_ProcessFlatEndorsement_WS.sql`
14. `Triton_ProcessFlatCancellation_WS.sql`
15. `Triton_ProcessFlatReinstatement_WS.sql`
16. `Triton_UnbindPolicy_WS.sql`

#### Supporting Procedures
17. `getProducerGuid_WS.sql`
18. `spChangeProducer_Triton.sql`
19. `spApplyTritonPolicyFee_WS.sql`
20. `ryan_rptInvoice_WS.sql`

### STEP 4: POST-DEPLOYMENT VERIFICATION

Run these queries to confirm everything is deployed:

```sql
-- Check tables
SELECT name FROM sys.tables 
WHERE name IN ('tblTritonQuoteData', 'tblTritonTransactionData');

-- Check stored procedures
SELECT name FROM sys.procedures 
WHERE name LIKE '%_WS%' 
   OR name LIKE 'Process%' 
   OR name LIKE 'Triton_%'
ORDER BY name;

-- Count should be ~20 procedures
SELECT COUNT(*) as ProcedureCount FROM sys.procedures 
WHERE name LIKE '%_WS%' OR name LIKE 'Process%' OR name LIKE 'Triton_%';

-- Test table structure
SELECT COUNT(*) as ColumnCount FROM sys.columns 
WHERE object_id = OBJECT_ID('tblTritonQuoteData');
-- Should return 48

SELECT COUNT(*) as ColumnCount FROM sys.columns 
WHERE object_id = OBJECT_ID('tblTritonTransactionData');
-- Should return 12
```

### DEPLOYMENT CHECKLIST

- [ ] Backup IMS database
- [ ] Run 01_CREATE_TABLES_PRODUCTION.sql
- [ ] Run 02_VERIFY_TABLES.sql
- [ ] Deploy all 20+ stored procedures
- [ ] Run verification queries
- [ ] Test with sample data insert

### ROLLBACK IF NEEDED

```sql
-- ONLY IN EMERGENCY - This will delete all data!
DROP TABLE IF EXISTS tblTritonTransactionData;
DROP TABLE IF EXISTS tblTritonQuoteData;

-- Drop procedures (list each one)
DROP PROCEDURE IF EXISTS spProcessTritonPayload_WS;
DROP PROCEDURE IF EXISTS spStoreTritonTransaction_WS;
-- ... etc for all procedures
```