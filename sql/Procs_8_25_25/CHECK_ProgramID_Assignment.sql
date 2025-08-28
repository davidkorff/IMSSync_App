-- Diagnostic query to verify ProgramID assignment is working correctly
-- Run this after processing a bind transaction to check results

-- Check the most recent bind transaction
DECLARE @QuoteGuid UNIQUEIDENTIFIER;

-- Option 1: Check a specific quote (update this GUID)
-- SET @QuoteGuid = 'd5f59086-799d-4c23-9b6a-e73cec18b37f';

-- Option 2: Get the most recent bind transaction
SELECT TOP 1 @QuoteGuid = QuoteGuid
FROM tblTritonQuoteData
WHERE transaction_type = 'bind'
ORDER BY created_date DESC;

IF @QuoteGuid IS NULL
BEGIN
    PRINT 'No bind transactions found in tblTritonQuoteData';
    RETURN;
END

PRINT 'Checking Quote: ' + CAST(@QuoteGuid AS NVARCHAR(50));
PRINT '================================================';

-- Main diagnostic query
SELECT 
    'DIAGNOSTIC RESULTS' AS [Check],
    q.QuoteGuid,
    q.PolicyNumber,
    q.CompanyLineGuid,
    CASE 
        WHEN q.CompanyLineGuid = '07564291-CBFE-4BBE-88D1-0548C88ACED4' THEN 'Primary Line'
        WHEN q.CompanyLineGuid = '08798559-321C-4FC0-98ED-A61B92215F31' THEN 'Excess Line'
        ELSE 'Unknown Line'
    END AS LineType,
    tqd.market_segment_code,
    tqd.class_of_business,
    tqd.program_name,
    tqd.transaction_type,
    qd.ProgramID AS Current_ProgramID,
    CASE 
        WHEN tqd.market_segment_code = 'RT' AND q.CompanyLineGuid = '07564291-CBFE-4BBE-88D1-0548C88ACED4' THEN 11615
        WHEN tqd.market_segment_code = 'WL' AND q.CompanyLineGuid = '07564291-CBFE-4BBE-88D1-0548C88ACED4' THEN 11613
        WHEN tqd.market_segment_code = 'RT' AND q.CompanyLineGuid = '08798559-321C-4FC0-98ED-A61B92215F31' THEN 11612
        WHEN tqd.market_segment_code = 'WL' AND q.CompanyLineGuid = '08798559-321C-4FC0-98ED-A61B92215F31' THEN 11614
        ELSE NULL
    END AS Expected_ProgramID,
    CASE 
        WHEN qd.ProgramID IS NULL THEN 'ERROR: ProgramID not set'
        WHEN tqd.market_segment_code IS NULL THEN 'ERROR: market_segment_code is NULL'
        WHEN q.CompanyLineGuid IS NULL THEN 'ERROR: CompanyLineGuid is NULL'
        WHEN qd.ProgramID = 
            CASE 
                WHEN tqd.market_segment_code = 'RT' AND q.CompanyLineGuid = '07564291-CBFE-4BBE-88D1-0548C88ACED4' THEN 11615
                WHEN tqd.market_segment_code = 'WL' AND q.CompanyLineGuid = '07564291-CBFE-4BBE-88D1-0548C88ACED4' THEN 11613
                WHEN tqd.market_segment_code = 'RT' AND q.CompanyLineGuid = '08798559-321C-4FC0-98ED-A61B92215F31' THEN 11612
                WHEN tqd.market_segment_code = 'WL' AND q.CompanyLineGuid = '08798559-321C-4FC0-98ED-A61B92215F31' THEN 11614
                ELSE NULL
            END
        THEN 'SUCCESS: ProgramID matches expected'
        ELSE 'ERROR: ProgramID mismatch'
    END AS Status,
    tqd.created_date
FROM tblQuotes q
LEFT JOIN tblTritonQuoteData tqd ON tqd.QuoteGuid = q.QuoteGuid
LEFT JOIN tblQuoteDetails qd ON qd.QuoteGuid = q.QuoteGuid
WHERE q.QuoteGuid = @QuoteGuid;

-- Check if market_segment_code column exists
IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'market_segment_code')
BEGIN
    PRINT '';
    PRINT 'Column Check: market_segment_code EXISTS in tblTritonQuoteData';
END
ELSE
BEGIN
    PRINT '';
    PRINT 'WARNING: market_segment_code column DOES NOT EXIST!';
    PRINT 'ACTION REQUIRED: Run ADD_market_segment_code_column.sql first';
END

-- Show recent bind transactions with their ProgramID status
PRINT '';
PRINT 'Recent Bind Transactions:';
PRINT '========================';

SELECT TOP 10
    q.PolicyNumber,
    tqd.insured_name,
    tqd.market_segment_code,
    CASE 
        WHEN q.CompanyLineGuid = '07564291-CBFE-4BBE-88D1-0548C88ACED4' THEN 'Primary'
        WHEN q.CompanyLineGuid = '08798559-321C-4FC0-98ED-A61B92215F31' THEN 'Excess'
        ELSE 'Unknown'
    END AS LineType,
    qd.ProgramID,
    CASE 
        WHEN qd.ProgramID = 11615 THEN 'RT Primary'
        WHEN qd.ProgramID = 11613 THEN 'WL Primary'
        WHEN qd.ProgramID = 11612 THEN 'RT Excess'
        WHEN qd.ProgramID = 11614 THEN 'WL Excess'
        WHEN qd.ProgramID IS NULL THEN 'NOT SET'
        ELSE 'OTHER'
    END AS ProgramType,
    tqd.created_date
FROM tblTritonQuoteData tqd
INNER JOIN tblQuotes q ON q.QuoteGuid = tqd.QuoteGuid
LEFT JOIN tblQuoteDetails qd ON qd.QuoteGuid = q.QuoteGuid
WHERE tqd.transaction_type = 'bind'
ORDER BY tqd.created_date DESC;

-- Summary statistics
PRINT '';
PRINT 'Summary Statistics:';
PRINT '==================';

SELECT 
    COUNT(*) AS TotalBindTransactions,
    COUNT(CASE WHEN tqd.market_segment_code IS NOT NULL THEN 1 END) AS WithMarketSegment,
    COUNT(CASE WHEN qd.ProgramID IS NOT NULL THEN 1 END) AS WithProgramID,
    COUNT(CASE WHEN tqd.market_segment_code IS NOT NULL AND qd.ProgramID IS NOT NULL THEN 1 END) AS BothSet,
    COUNT(CASE WHEN tqd.market_segment_code IS NULL OR qd.ProgramID IS NULL THEN 1 END) AS MissingData
FROM tblTritonQuoteData tqd
INNER JOIN tblQuotes q ON q.QuoteGuid = tqd.QuoteGuid
LEFT JOIN tblQuoteDetails qd ON qd.QuoteGuid = q.QuoteGuid
WHERE tqd.transaction_type = 'bind'
  AND tqd.created_date >= DATEADD(day, -30, GETDATE());