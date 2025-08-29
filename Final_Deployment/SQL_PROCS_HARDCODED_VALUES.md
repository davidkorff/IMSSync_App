# SQL STORED PROCEDURES - HARDCODED VALUES AUDIT
## Analysis of /Final_Deployment/Procs_8_28_25/

---

## 🚨 CRITICAL HARDCODED VALUES IN SQL PROCEDURES

### 1. LINE GUIDs (Found in Multiple Procedures)

**Primary Line GUID: `07564291-CBFE-4BBE-88D1-0548C88ACED4`**
- Location: `spProcessTritonPayload_WS.sql` (lines 452, 460, 488)
- Location: `spProcessTritonPayload_WS_BACKUP.sql` (lines 438, 446)

**Excess Line GUID: `08798559-321C-4FC0-98ED-A61B92215F31`**
- Location: `spProcessTritonPayload_WS.sql` (lines 468, 476, 489)
- Location: `spProcessTritonPayload_WS_BACKUP.sql` (lines 454, 462)

### 2. PROGRAM IDs (Hardcoded Business Logic)

**Complete Mapping in SQL:**
```sql
-- From spProcessTritonPayload_WS.sql
IF @market_segment_code = 'RT' AND @CompanyLineGuidStr = '07564291-CBFE-4BBE-88D1-0548C88ACED4'
    SET ProgramID = 11615  -- RT + Primary

ELSE IF @market_segment_code = 'WL' AND @CompanyLineGuidStr = '07564291-CBFE-4BBE-88D1-0548C88ACED4'
    SET ProgramID = 11613  -- WL + Primary

ELSE IF @market_segment_code = 'RT' AND @CompanyLineGuidStr = '08798559-321C-4FC0-98ED-A61B92215F31'
    SET ProgramID = 11612  -- RT + Excess

ELSE IF @market_segment_code = 'WL' AND @CompanyLineGuidStr = '08798559-321C-4FC0-98ED-A61B92215F31'
    SET ProgramID = 11614  -- WL + Excess
```

**Files Containing Program ID Logic:**
- `spProcessTritonPayload_WS.sql` (lines 455, 463, 471, 479)
- `spProcessTritonPayload_WS_BACKUP.sql` (lines 441, 449, 457, 465)

### 3. TABLE NAMES (OK - These are Database Schema)

These are acceptable as hardcoded since they're part of the database schema:
- `tblTritonQuoteData` - Used in 15+ procedures
- `tblTritonTransactionData` - Used in spProcessTritonPayload_WS.sql
- `tblQuotes`
- `tblQuoteOptions`
- `tblPremiumHistory`

### 4. NULL GUID REFERENCE

**Null GUID: `00000000-0000-0000-0000-000000000000`**
- Used for validation/default in `spProcessTritonPayload_WS_BACKUP.sql`

---

## 📊 IMPACT ANALYSIS

### Which Procedures Are Affected?

| Procedure | Contains GUIDs | Contains Program IDs | Risk Level |
|-----------|---------------|---------------------|------------|
| spProcessTritonPayload_WS.sql | YES | YES | **CRITICAL** |
| spProcessTritonPayload_WS_BACKUP.sql | YES | YES | **CRITICAL** |
| Triton_ProcessFlatCancellation_WS.sql | NO | NO | Low |
| Triton_ProcessFlatEndorsement_WS.sql | NO | NO | Low |
| Triton_ProcessFlatReinstatement_WS.sql | NO | NO | Low |
| ProcessFlatCancellation.sql | NO | NO | Low |
| ProcessFlatEndorsement.sql | NO | NO | Low |
| ProcessFlatReinstatement.sql | NO | NO | Low |

---

## ⚠️ PRODUCTION DEPLOYMENT CONCERNS

### The Problem with Hardcoded Values in SQL:

1. **Can't use environment variables in SQL**
2. **Must be manually updated for each environment**
3. **Risk of forgetting to update before deployment**

### Recommended Solutions:

#### Option 1: Configuration Table (BEST)
Create a configuration table in the database:
```sql
CREATE TABLE tblTritonConfiguration (
    ConfigKey NVARCHAR(100) PRIMARY KEY,
    ConfigValue NVARCHAR(500),
    Environment NVARCHAR(50),
    Description NVARCHAR(500)
);

-- Insert configuration
INSERT INTO tblTritonConfiguration VALUES 
('PRIMARY_LINE_GUID', '07564291-CBFE-4BBE-88D1-0548C88ACED4', 'PROD', 'Primary Line GUID'),
('EXCESS_LINE_GUID', '08798559-321C-4FC0-98ED-A61B92215F31', 'PROD', 'Excess Line GUID'),
('PROGRAM_ID_RT_PRIMARY', '11615', 'PROD', 'RT + Primary Line'),
('PROGRAM_ID_WL_PRIMARY', '11613', 'PROD', 'WL + Primary Line'),
('PROGRAM_ID_RT_EXCESS', '11612', 'PROD', 'RT + Excess Line'),
('PROGRAM_ID_WL_EXCESS', '11614', 'PROD', 'WL + Excess Line');
```

Then update procedures to read from config:
```sql
DECLARE @PrimaryLineGuid NVARCHAR(50)
SELECT @PrimaryLineGuid = ConfigValue 
FROM tblTritonConfiguration 
WHERE ConfigKey = 'PRIMARY_LINE_GUID'
```

#### Option 2: Parameters in Procedures
Modify procedures to accept parameters:
```sql
ALTER PROCEDURE spProcessTritonPayload_WS
    @Json NVARCHAR(MAX),
    @PrimaryLineGuid UNIQUEIDENTIFIER = '07564291-CBFE-4BBE-88D1-0548C88ACED4',
    @ExcessLineGuid UNIQUEIDENTIFIER = '08798559-321C-4FC0-98ED-A61B92215F31'
AS
```

#### Option 3: Environment-Specific Scripts (Current Approach)
Have separate SQL scripts for each environment:
- `spProcessTritonPayload_WS_DEV.sql`
- `spProcessTritonPayload_WS_PROD.sql`

---

## 🔴 IMMEDIATE ACTION REQUIRED

### Before Production Deployment:

1. **VERIFY with IMS Team:**
   - [ ] Are Line GUIDs the same in DEV and PROD?
   - [ ] Are Program IDs (11612-11615) correct for PROD?

2. **UPDATE These Procedures:**
   - [ ] spProcessTritonPayload_WS.sql
   - [ ] spProcessTritonPayload_WS_BACKUP.sql

3. **TEST the Mapping:**
   ```sql
   -- Test query to verify Program IDs exist
   SELECT ProgramID FROM tblPrograms 
   WHERE ProgramID IN (11612, 11613, 11614, 11615)
   
   -- Test query to verify Line GUIDs exist
   SELECT CompanyLineGuid FROM tblCompanyLines
   WHERE CompanyLineGuid IN (
       '07564291-CBFE-4BBE-88D1-0548C88ACED4',
       '08798559-321C-4FC0-98ED-A61B92215F31'
   )
   ```

---

## 📝 DEPLOYMENT SCRIPT MODIFICATION

If values are different for production, create a SQL script to update:

```sql
-- RUN THIS AFTER DEPLOYING PROCEDURES TO PRODUCTION
-- Update_Procs_For_Production.sql

-- Only run if GUIDs are different!
/*
UPDATE LOGIC:
Find: '07564291-CBFE-4BBE-88D1-0548C88ACED4'
Replace: 'YOUR-PROD-PRIMARY-LINE-GUID'

Find: '08798559-321C-4FC0-98ED-A61B92215F31'  
Replace: 'YOUR-PROD-EXCESS-LINE-GUID'

Find: 11615
Replace: YOUR-PROD-RT-PRIMARY-ID

Find: 11613
Replace: YOUR-PROD-WL-PRIMARY-ID

Find: 11612
Replace: YOUR-PROD-RT-EXCESS-ID

Find: 11614
Replace: YOUR-PROD-WL-EXCESS-ID
*/
```

---

## ✅ SAFE HARDCODED VALUES

These are OK to leave hardcoded:
- Table names (tblTritonQuoteData, etc.)
- Column names
- Field size limits
- Default status values
- Error messages

---

## 🎯 SUMMARY

**Most Critical Files to Review:**
1. `spProcessTritonPayload_WS.sql` - Main payload processor with all hardcoded values
2. `spProcessTritonPayload_WS_BACKUP.sql` - Backup with same issues

**Critical Values to Verify:**
- 2 Line GUIDs
- 4 Program IDs
- All must match production IMS configuration

**Risk if Wrong:**
- Policies assigned to wrong program
- Incorrect pricing
- Failed transactions