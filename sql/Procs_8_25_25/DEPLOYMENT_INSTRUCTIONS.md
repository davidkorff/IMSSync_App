# Deployment Instructions for ProgramID Fix

## Overview
The ProgramID is not being set during bind transactions because the `market_segment_code` value from the JSON payload is not being stored in the database table `tblTritonQuoteData`.

## The Fix Has Two Parts:

### Part 1: Database Schema Change
Add the missing `market_segment_code` column to `tblTritonQuoteData` table

### Part 2: Stored Procedure Update  
Update `spProcessTritonPayload_WS` to store the `market_segment_code` value in the new column

## Deployment Steps (IN ORDER):

### Step 1: Add the Column
Run this script FIRST to add the column to the table:
```sql
-- File: sql/Procs_8_25_25/ADD_market_segment_code_column.sql
-- This will:
-- 1. Add market_segment_code column to tblTritonQuoteData
-- 2. Populate it from existing JSON data where available
```

### Step 2: Update the Stored Procedure
Run this script SECOND to update the stored procedure:
```sql
-- File: sql/Procs_8_25_25/spProcessTritonPayload_WS.sql
-- This updated version:
-- 1. Extracts market_segment_code from JSON (line 121)
-- 2. Stores it in UPDATE statement (line 201)
-- 3. Stores it in INSERT statement (line 254, 303)
-- 4. Uses it for ProgramID assignment (lines 415-476)
```

### Step 3: Verify the Fix
Run this script to check if everything is working:
```sql
-- File: sql/Procs_8_25_25/CHECK_ProgramID_Assignment.sql
-- This will show:
-- 1. Recent bind transactions
-- 2. Their market_segment_code values
-- 3. Their ProgramID assignments
-- 4. Whether they match expected values
```

## What the Fix Does:

The stored procedure now:
1. **Extracts** `market_segment_code` from the JSON payload (line 121):
   ```sql
   SET @market_segment_code = JSON_VALUE(@full_payload_json, '$.market_segment_code');
   ```

2. **Stores** it in the database table during UPDATE (line 201):
   ```sql
   UPDATE tblTritonQuoteData
   SET ...
       market_segment_code = @market_segment_code,
   ...
   ```

3. **Stores** it in the database table during INSERT (lines 254, 303):
   ```sql
   INSERT INTO tblTritonQuoteData (..., market_segment_code, ...)
   VALUES (..., @market_segment_code, ...)
   ```

4. **Uses** it to set ProgramID based on these rules (lines 415-476):
   - `WL` + Primary Line (07564291-CBFE-4BBE-88D1-0548C88ACED4) = ProgramID 11613
   - `RT` + Primary Line (07564291-CBFE-4BBE-88D1-0548C88ACED4) = ProgramID 11615
   - `WL` + Excess Line (08798559-321C-4FC0-98ED-A61B92215F31) = ProgramID 11614
   - `RT` + Excess Line (08798559-321C-4FC0-98ED-A61B92215F31) = ProgramID 11612

## Testing:

After deployment, run a new bind transaction and check:
```sql
-- Check the most recent bind
SELECT TOP 1
    q.PolicyNumber,
    tqd.market_segment_code,
    q.CompanyLineGuid,
    qd.ProgramID,
    CASE 
        WHEN qd.ProgramID = 11613 THEN 'WL Primary (Correct)'
        WHEN qd.ProgramID = 11615 THEN 'RT Primary (Correct)'
        WHEN qd.ProgramID = 11614 THEN 'WL Excess (Correct)'
        WHEN qd.ProgramID = 11612 THEN 'RT Excess (Correct)'
        ELSE 'Check Assignment'
    END AS Status
FROM tblTritonQuoteData tqd
JOIN tblQuotes q ON q.QuoteGuid = tqd.QuoteGuid
LEFT JOIN tblQuoteDetails qd ON qd.QuoteGuid = q.QuoteGuid
WHERE tqd.transaction_type = 'bind'
ORDER BY tqd.created_date DESC;
```

## Rollback (if needed):
If you need to rollback:
1. Restore the original stored procedure from: `spProcessTritonPayload_WS_BACKUP.sql`
2. The column can remain as it won't affect existing functionality

## Notes:
- The column is nullable so it won't break existing code
- Existing records will be updated with market_segment_code from their stored JSON
- The fix preserves all existing functionality while adding the missing data storage