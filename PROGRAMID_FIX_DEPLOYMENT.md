# ProgramID Assignment Fix - Deployment Guide

## Issue Summary
The `ProgramID` field in `tblQuoteDetails` was not being set correctly during bind transactions because:
1. The `market_segment_code` was being extracted from the JSON payload but not stored in `tblTritonQuoteData`
2. Missing debug logging made it impossible to diagnose why ProgramID assignment was failing
3. The stored procedure's INSERT and UPDATE statements didn't include the `market_segment_code` column

## Files Created
1. `sql/fix_programid_assignment.sql` - Adds missing columns to tblTritonQuoteData
2. `sql/spProcessTritonPayload_WS_FIXED.sql` - Fixed stored procedure with logging
3. `test_programid_fix.py` - Test script to verify the fix

## Deployment Steps

### Step 1: Apply Database Schema Changes
Run the following SQL script to add missing columns:
```sql
-- Run in SQL Server Management Studio
-- File: sql/fix_programid_assignment.sql
```

This will add:
- `market_segment_code` column
- `opportunity_type` column  
- `commission_percent` column
- `full_payload_json` column

### Step 2: Update the Stored Procedure
Replace the existing `spProcessTritonPayload_WS` with the fixed version:
```sql
-- Run in SQL Server Management Studio
-- File: sql/spProcessTritonPayload_WS_FIXED.sql
```

Key improvements:
- Stores `market_segment_code` in tblTritonQuoteData
- Comprehensive debug logging for ProgramID assignment
- Shows exactly why ProgramID is or isn't being set
- Verifies tblQuoteDetails exists before attempting update

### Step 3: Enable SQL Server Print Output (for debugging)
In SQL Server Management Studio:
1. Go to Query → Query Options → Results → Text
2. Check "Include the query in the result set"
3. Go to Messages tab to see PRINT output

### Step 4: Test the Fix
Run the test script:
```bash
python test_programid_fix.py
```

This will create test bind transactions with different market segments and verify ProgramID assignment.

## ProgramID Mapping Rules

The stored procedure sets ProgramID based on these combinations:

| Market Segment | Line Type | CompanyLineGuid | ProgramID |
|---------------|-----------|-----------------|-----------|
| RT (Retail) | Primary | 07564291-CBFE-4BBE-88D1-0548C88ACED4 | 11615 |
| WL (Wholesale) | Primary | 07564291-CBFE-4BBE-88D1-0548C88ACED4 | 11613 |
| RT (Retail) | Excess | 08798559-321C-4FC0-98ED-A61B92215F31 | 11612 |
| WL (Wholesale) | Excess | 08798559-321C-4FC0-98ED-A61B92215F31 | 11614 |

## Debug Output Example

When the stored procedure runs, you'll see output like:
```
===== ProgramID Assignment Debug Info =====
Transaction Type: bind
Extracted market_segment_code: RT
QuoteGuid: 12345678-1234-1234-1234-123456789012
Retrieved CompanyLineGuid from tblQuotes: 07564291-CBFE-4BBE-88D1-0548C88ACED4
tblQuoteDetails record EXISTS for this quote
Current ProgramID in tblQuoteDetails: NULL
MATCHED: Set ProgramID to 11615 (RT market segment, Primary LineGuid 07564291)
Final ProgramID in tblQuoteDetails: 11615
===== End ProgramID Assignment Debug =====
```

## Verification Query

After deployment, verify the fix with:
```sql
SELECT TOP 10
    tqd.QuoteGuid,
    tqd.policy_number,
    tqd.market_segment_code,
    tqd.transaction_type,
    tq.CompanyLineGuid,
    td.ProgramID,
    CASE 
        WHEN tqd.market_segment_code = 'RT' AND tq.CompanyLineGuid = '07564291-CBFE-4BBE-88D1-0548C88ACED4' THEN '11615 (Expected)'
        WHEN tqd.market_segment_code = 'WL' AND tq.CompanyLineGuid = '07564291-CBFE-4BBE-88D1-0548C88ACED4' THEN '11613 (Expected)'
        WHEN tqd.market_segment_code = 'RT' AND tq.CompanyLineGuid = '08798559-321C-4FC0-98ED-A61B92215F31' THEN '11612 (Expected)'
        WHEN tqd.market_segment_code = 'WL' AND tq.CompanyLineGuid = '08798559-321C-4FC0-98ED-A61B92215F31' THEN '11614 (Expected)'
        ELSE 'Unknown Combination'
    END as Expected_ProgramID,
    tqd.created_date
FROM tblTritonQuoteData tqd
LEFT JOIN tblQuotes tq ON tq.QuoteGuid = tqd.QuoteGuid
LEFT JOIN tblQuoteDetails td ON td.QuoteGuid = tqd.QuoteGuid
WHERE tqd.transaction_type = 'bind'
    AND tqd.created_date >= DATEADD(day, -1, GETDATE())
ORDER BY tqd.created_date DESC;
```

## Rollback Plan

If issues occur, you can rollback:

1. Restore the original stored procedure:
```sql
-- Restore from backup or use the version in:
-- sql/Procs_8_25_24/spProcessTritonPayload_WS.sql
```

2. The new columns are nullable and won't affect existing functionality, so they can remain.

## Notes

- The fix preserves all existing functionality
- Added columns are nullable and won't break existing code
- Debug logging only appears in SQL Server Messages tab, not in application
- Auto-fee application still works based on market_segment_code (RT = auto-apply, WL = no auto-apply)

## Support

If ProgramID is still not being set after applying this fix:
1. Check the SQL Server Messages tab for debug output
2. Verify the CompanyLineGuid matches one of the expected values
3. Verify tblQuoteDetails exists for the quote
4. Check that market_segment_code is being passed in the payload