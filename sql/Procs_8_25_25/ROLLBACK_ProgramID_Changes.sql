-- Rollback script for ProgramID changes
-- Use this if the fixes cause issues and need to be reverted

PRINT 'ProgramID Fix Rollback Script';
PRINT '============================';
PRINT '';
PRINT 'WARNING: This will revert the ProgramID assignment fixes.';
PRINT 'Only run this if the changes are causing issues.';
PRINT '';

-- Step 1: Remove market_segment_code column from tblTritonQuoteData
IF EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'market_segment_code')
BEGIN
    PRINT 'Step 1: Removing market_segment_code column from tblTritonQuoteData...';
    
    -- First backup the data
    PRINT '  Creating backup of market_segment_code values...';
    
    IF OBJECT_ID('tblTritonQuoteData_MarketSegmentBackup', 'U') IS NOT NULL
        DROP TABLE tblTritonQuoteData_MarketSegmentBackup;
    
    SELECT 
        QuoteGuid,
        transaction_id,
        market_segment_code,
        GETDATE() AS backup_date
    INTO tblTritonQuoteData_MarketSegmentBackup
    FROM tblTritonQuoteData
    WHERE market_segment_code IS NOT NULL;
    
    DECLARE @BackupCount INT = @@ROWCOUNT;
    PRINT '  Backed up ' + CAST(@BackupCount AS VARCHAR(10)) + ' records with market_segment_code values';
    
    -- Now remove the column
    ALTER TABLE tblTritonQuoteData
    DROP COLUMN market_segment_code;
    
    PRINT '  ✓ Column removed';
END
ELSE
BEGIN
    PRINT 'Step 1: market_segment_code column does not exist (already removed)';
END

GO

-- Step 2: Restore the original stored procedure (without ProgramID logic)
PRINT '';
PRINT 'Step 2: Reverting spProcessTritonPayload_WS to original version...';
PRINT '  NOTE: You need to manually restore the original stored procedure';
PRINT '  The original should be in your version control or database backup';
PRINT '  Key sections to remove:';
PRINT '    - market_segment_code extraction from JSON (around line 121)';
PRINT '    - market_segment_code in UPDATE/INSERT statements';
PRINT '    - ProgramID assignment logic (section 5, around line 416-476)';
PRINT '';

-- Step 3: Clear any incorrectly set ProgramIDs (optional)
PRINT 'Step 3: Review incorrectly set ProgramIDs...';
PRINT '  The following queries help identify quotes that may have wrong ProgramIDs:';
PRINT '';

-- Show quotes with the new ProgramIDs
SELECT 
    'Quotes with RSG ProgramIDs' AS Category,
    qd.ProgramID,
    COUNT(*) AS Count,
    MIN(q.QuoteDate) AS FirstUsed,
    MAX(q.QuoteDate) AS LastUsed
FROM tblQuoteDetails qd
INNER JOIN tblQuotes q ON q.QuoteGuid = qd.QuoteGuid
WHERE qd.ProgramID IN (11612, 11613, 11614, 11615)
GROUP BY qd.ProgramID
ORDER BY qd.ProgramID;

PRINT '';
PRINT 'To clear specific ProgramIDs (if needed):';
PRINT '-- UPDATE tblQuoteDetails SET ProgramID = NULL WHERE ProgramID IN (11612, 11613, 11614, 11615);';
PRINT '';

-- Step 4: Document what was rolled back
PRINT 'Step 4: Rollback Summary';
PRINT '------------------------';
PRINT '✓ market_segment_code column removed from tblTritonQuoteData';
PRINT '✓ Backup created in tblTritonQuoteData_MarketSegmentBackup';
PRINT '⚠ spProcessTritonPayload_WS needs manual restoration';
PRINT '⚠ Review ProgramID values in tblQuoteDetails';
PRINT '';

-- Step 5: Verify rollback
PRINT 'Step 5: Verification';
PRINT '-------------------';

-- Check if column is gone
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'market_segment_code')
BEGIN
    PRINT '✓ market_segment_code column successfully removed';
END
ELSE
BEGIN
    PRINT '✗ ERROR: market_segment_code column still exists';
END

-- Check stored procedure
DECLARE @ProcText NVARCHAR(MAX);
SELECT @ProcText = OBJECT_DEFINITION(OBJECT_ID('dbo.spProcessTritonPayload_WS'));

IF @ProcText IS NOT NULL
BEGIN
    IF CHARINDEX('market_segment_code', @ProcText) > 0
    BEGIN
        PRINT '⚠ WARNING: spProcessTritonPayload_WS still contains market_segment_code references';
        PRINT '  Manual restoration of the stored procedure is required';
    END
    ELSE
    BEGIN
        PRINT '✓ spProcessTritonPayload_WS does not contain market_segment_code references';
    END
END

PRINT '';
PRINT 'ROLLBACK COMPLETE';
PRINT '================';
PRINT 'Next steps:';
PRINT '1. Manually restore spProcessTritonPayload_WS to original version';
PRINT '2. Test a bind transaction to ensure it works without the fixes';
PRINT '3. If needed, restore ProgramID values from backup';
PRINT '';
PRINT 'To restore market_segment_code data later:';
PRINT 'SELECT * FROM tblTritonQuoteData_MarketSegmentBackup;';