-- Diagnostic script to identify why ProgramID is not being set
-- Run this in SQL Server Management Studio

PRINT '===== DIAGNOSTIC CHECK FOR PROGRAMID ISSUE ====='
PRINT ''

-- 1. Check if the column exists
IF EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'market_segment_code')
BEGIN
    PRINT '✓ Column market_segment_code EXISTS in tblTritonQuoteData'
END
ELSE
BEGIN
    PRINT '✗ Column market_segment_code DOES NOT EXIST in tblTritonQuoteData'
    PRINT '  ACTION REQUIRED: Run fix_programid_assignment.sql first!'
END

-- 2. Check the latest quote from your test
DECLARE @QuoteGuid UNIQUEIDENTIFIER = 'd5f59086-799d-4c23-9b6a-e73cec18b37f';

PRINT ''
PRINT 'Checking Quote: d5f59086-799d-4c23-9b6a-e73cec18b37f'
PRINT '------------------------------------------------'

-- 3. Check what's in tblQuotes
DECLARE @CompanyLineGuid UNIQUEIDENTIFIER;
DECLARE @PolicyNumber NVARCHAR(50);

SELECT 
    @CompanyLineGuid = CompanyLineGuid,
    @PolicyNumber = PolicyNumber
FROM tblQuotes 
WHERE QuoteGuid = @QuoteGuid;

PRINT 'PolicyNumber: ' + ISNULL(@PolicyNumber, 'NULL')
PRINT 'CompanyLineGuid: ' + ISNULL(CAST(@CompanyLineGuid AS NVARCHAR(50)), 'NULL')

-- 4. Check what's in tblTritonQuoteData
DECLARE @market_segment_code NVARCHAR(10);
DECLARE @transaction_type NVARCHAR(50);

-- Dynamic SQL to handle if column doesn't exist
DECLARE @sql NVARCHAR(MAX) = '
SELECT @market_segment_code = NULL
'

IF EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'market_segment_code')
BEGIN
    SET @sql = '
    SELECT 
        @market_segment_code = market_segment_code,
        @transaction_type = transaction_type
    FROM tblTritonQuoteData 
    WHERE QuoteGuid = @QuoteGuid'
    
    EXEC sp_executesql @sql, 
        N'@market_segment_code NVARCHAR(10) OUTPUT, @transaction_type NVARCHAR(50) OUTPUT, @QuoteGuid UNIQUEIDENTIFIER',
        @market_segment_code OUTPUT, @transaction_type OUTPUT, @QuoteGuid;
    
    PRINT 'market_segment_code: ' + ISNULL(@market_segment_code, 'NULL (not stored)')
    PRINT 'transaction_type: ' + ISNULL(@transaction_type, 'NULL')
END
ELSE
BEGIN
    SELECT @transaction_type = transaction_type
    FROM tblTritonQuoteData 
    WHERE QuoteGuid = @QuoteGuid;
    
    PRINT 'market_segment_code: COLUMN DOES NOT EXIST'
    PRINT 'transaction_type: ' + ISNULL(@transaction_type, 'NULL')
END

-- 5. Check what's in tblQuoteDetails
DECLARE @ProgramID INT;

SELECT @ProgramID = ProgramID
FROM tblQuoteDetails
WHERE QuoteGuid = @QuoteGuid;

PRINT 'Current ProgramID: ' + ISNULL(CAST(@ProgramID AS NVARCHAR(10)), 'NULL')

-- 6. Determine what ProgramID should be
PRINT ''
PRINT 'Expected ProgramID Logic:'
PRINT '-------------------------'

IF @market_segment_code IS NOT NULL
BEGIN
    IF @market_segment_code = 'WL' AND @CompanyLineGuid = '07564291-CBFE-4BBE-88D1-0548C88ACED4'
    BEGIN
        PRINT 'Market: WL + Line: Primary (07564291) = Expected ProgramID: 11613'
    END
    ELSE IF @market_segment_code = 'RT' AND @CompanyLineGuid = '07564291-CBFE-4BBE-88D1-0548C88ACED4'
    BEGIN
        PRINT 'Market: RT + Line: Primary (07564291) = Expected ProgramID: 11615'
    END
    ELSE IF @market_segment_code = 'WL' AND @CompanyLineGuid = '08798559-321C-4FC0-98ED-A61B92215F31'
    BEGIN
        PRINT 'Market: WL + Line: Excess (08798559) = Expected ProgramID: 11614'
    END
    ELSE IF @market_segment_code = 'RT' AND @CompanyLineGuid = '08798559-321C-4FC0-98ED-A61B92215F31'
    BEGIN
        PRINT 'Market: RT + Line: Excess (08798559) = Expected ProgramID: 11612'
    END
    ELSE
    BEGIN
        PRINT 'No matching rule for Market: ' + ISNULL(@market_segment_code, 'NULL') + ' + Line: ' + ISNULL(CAST(@CompanyLineGuid AS NVARCHAR(50)), 'NULL')
    END
END
ELSE
BEGIN
    PRINT 'Cannot determine expected ProgramID - market_segment_code is NULL'
END

-- 7. Check if tblQuoteDetails exists
IF EXISTS (SELECT 1 FROM tblQuoteDetails WHERE QuoteGuid = @QuoteGuid)
BEGIN
    PRINT ''
    PRINT '✓ tblQuoteDetails record EXISTS for this quote'
END
ELSE
BEGIN
    PRINT ''
    PRINT '✗ tblQuoteDetails record DOES NOT EXIST for this quote'
    PRINT '  This would prevent ProgramID from being set!'
END

-- 8. Check stored procedure text to see if it's the updated version
PRINT ''
PRINT 'Checking stored procedure version:'
PRINT '----------------------------------'

DECLARE @proc_text NVARCHAR(MAX);
SELECT @proc_text = OBJECT_DEFINITION(OBJECT_ID('spProcessTritonPayload_WS'));

IF @proc_text LIKE '%market_segment_code%'
BEGIN
    PRINT '✓ Stored procedure contains market_segment_code references'
    
    IF @proc_text LIKE '%ProgramID Assignment Debug%'
    BEGIN
        PRINT '✓ Stored procedure has debug logging (FIXED version)'
    END
    ELSE
    BEGIN
        PRINT '✗ Stored procedure does NOT have debug logging (OLD version)'
        PRINT '  ACTION REQUIRED: Run spProcessTritonPayload_WS_FIXED.sql'
    END
END
ELSE
BEGIN
    PRINT '✗ Stored procedure does NOT reference market_segment_code'
    PRINT '  ACTION REQUIRED: Update the stored procedure!'
END

PRINT ''
PRINT '===== END DIAGNOSTIC CHECK ====='

-- Summary query
SELECT 
    'SUMMARY' AS [Check],
    CASE WHEN EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'market_segment_code')
         THEN 'YES' ELSE 'NO' END AS [Column_Exists],
    CASE WHEN EXISTS (SELECT 1 FROM tblTritonQuoteData WHERE QuoteGuid = @QuoteGuid)
         THEN 'YES' ELSE 'NO' END AS [TritonData_Exists],
    CASE WHEN EXISTS (SELECT 1 FROM tblQuoteDetails WHERE QuoteGuid = @QuoteGuid)
         THEN 'YES' ELSE 'NO' END AS [QuoteDetails_Exists],
    @PolicyNumber AS [PolicyNumber],
    @ProgramID AS [Current_ProgramID];