-- Script to verify which version of spProcessTritonPayload_WS is running
-- This checks if our updates have been applied

DECLARE @ProcText NVARCHAR(MAX);

-- Get the stored procedure text
SELECT @ProcText = OBJECT_DEFINITION(OBJECT_ID('dbo.spProcessTritonPayload_WS'));

IF @ProcText IS NULL
BEGIN
    PRINT 'ERROR: Stored procedure spProcessTritonPayload_WS not found!';
    RETURN;
END

PRINT 'Checking stored procedure spProcessTritonPayload_WS...';
PRINT '================================================';
PRINT '';

-- Check for key indicators of the updated version

-- 1. Check if market_segment_code is being extracted from JSON
IF CHARINDEX('SET @market_segment_code = JSON_VALUE(@full_payload_json, ''$.market_segment_code'')', @ProcText) > 0
BEGIN
    PRINT '✓ market_segment_code extraction from JSON found (line ~121)';
END
ELSE
BEGIN
    PRINT '✗ market_segment_code extraction NOT found - old version?';
END

-- 2. Check if market_segment_code is in the UPDATE statement
IF CHARINDEX('market_segment_code = @market_segment_code', @ProcText) > 0
BEGIN
    PRINT '✓ market_segment_code in UPDATE statement found';
END
ELSE
BEGIN
    PRINT '✗ market_segment_code NOT in UPDATE statement - need to update stored proc';
END

-- 3. Check if ProgramID assignment logic exists
IF CHARINDEX('ProgramID = 11613', @ProcText) > 0
BEGIN
    PRINT '✓ ProgramID assignment logic found (11613 for WL Primary)';
END
ELSE
BEGIN
    PRINT '✗ ProgramID assignment logic NOT found';
END

-- 4. Check if the IF conditions for bind transaction exist
IF CHARINDEX('@transaction_type = ''bind'' AND @market_segment_code IS NOT NULL', @ProcText) > 0
BEGIN
    PRINT '✓ Bind transaction check with market_segment_code found';
END
ELSE
BEGIN
    PRINT '✗ Bind transaction check NOT found or different format';
END

-- 5. Count how many times each ProgramID appears
DECLARE @Count11613 INT = (LEN(@ProcText) - LEN(REPLACE(@ProcText, '11613', ''))) / 5;
DECLARE @Count11615 INT = (LEN(@ProcText) - LEN(REPLACE(@ProcText, '11615', ''))) / 5;
DECLARE @Count11612 INT = (LEN(@ProcText) - LEN(REPLACE(@ProcText, '11612', ''))) / 5;
DECLARE @Count11614 INT = (LEN(@ProcText) - LEN(REPLACE(@ProcText, '11614', ''))) / 5;

PRINT '';
PRINT 'ProgramID References:';
PRINT '  11613 (WL Primary): ' + CAST(@Count11613 AS VARCHAR(10)) + ' times';
PRINT '  11615 (RT Primary): ' + CAST(@Count11615 AS VARCHAR(10)) + ' times';
PRINT '  11612 (RT Excess): ' + CAST(@Count11612 AS VARCHAR(10)) + ' times';
PRINT '  11614 (WL Excess): ' + CAST(@Count11614 AS VARCHAR(10)) + ' times';

-- 6. Check last modification date
DECLARE @ModifyDate DATETIME;
SELECT @ModifyDate = modify_date 
FROM sys.procedures 
WHERE name = 'spProcessTritonPayload_WS';

PRINT '';
PRINT 'Last Modified: ' + CONVERT(VARCHAR, @ModifyDate, 120);

-- 7. Show a snippet of the ProgramID logic if it exists
DECLARE @StartPos INT = CHARINDEX('-- 5. Set ProgramID based on market_segment_code', @ProcText);
IF @StartPos > 0
BEGIN
    PRINT '';
    PRINT 'Found ProgramID Section at character position: ' + CAST(@StartPos AS VARCHAR(10));
    
    -- Check what transaction types it applies to
    DECLARE @CheckPos INT = CHARINDEX('@transaction_type', @ProcText, @StartPos);
    IF @CheckPos > 0 AND @CheckPos < @StartPos + 500
    BEGIN
        DECLARE @LineStart INT = @CheckPos - 50;
        DECLARE @LineEnd INT = @CheckPos + 200;
        PRINT '';
        PRINT 'Transaction type check:';
        PRINT SUBSTRING(@ProcText, @LineStart, @LineEnd - @LineStart);
    END
END

PRINT '';
PRINT 'SUMMARY:';
PRINT '========';
PRINT 'If any items above show ✗, the stored procedure needs to be updated.';
PRINT 'Run the latest version from: sql/Procs_8_25_25/spProcessTritonPayload_WS.sql';