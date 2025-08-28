-- Check the ProgramID for the latest quote
DECLARE @QuoteGuid UNIQUEIDENTIFIER = 'bd93c340-ac25-4308-ae43-dd592727c5e4'; -- From test74bind

PRINT 'Checking Quote: ' + CAST(@QuoteGuid AS NVARCHAR(50));
PRINT '================================================';
PRINT '';

-- Main check
SELECT 
    'ProgramID Check' AS Test,
    q.PolicyNumber,
    q.CompanyLineGuid,
    UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) AS LineGuid_Upper,
    tqd.market_segment_code,
    qd.ProgramID,
    CASE 
        WHEN tqd.market_segment_code = 'WL' AND UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '07564291-CBFE-4BBE-88D1-0548C88ACED4' 
            AND qd.ProgramID = 11613 THEN 'SUCCESS - Correct ProgramID (WL Primary)'
        WHEN tqd.market_segment_code = 'RT' AND UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '07564291-CBFE-4BBE-88D1-0548C88ACED4' 
            AND qd.ProgramID = 11615 THEN 'SUCCESS - Correct ProgramID (RT Primary)'
        WHEN tqd.market_segment_code = 'WL' AND UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '08798559-321C-4FC0-98ED-A61B92215F31' 
            AND qd.ProgramID = 11614 THEN 'SUCCESS - Correct ProgramID (WL Excess)'
        WHEN tqd.market_segment_code = 'RT' AND UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '08798559-321C-4FC0-98ED-A61B92215F31' 
            AND qd.ProgramID = 11612 THEN 'SUCCESS - Correct ProgramID (RT Excess)'
        WHEN qd.ProgramID IS NULL THEN 'FAILED - ProgramID is NULL'
        ELSE 'FAILED - Wrong ProgramID'
    END AS Status,
    tqd.created_date
FROM tblQuotes q
LEFT JOIN tblTritonQuoteData tqd ON tqd.QuoteGuid = q.QuoteGuid
LEFT JOIN tblQuoteDetails qd ON qd.QuoteGuid = q.QuoteGuid
WHERE q.QuoteGuid = @QuoteGuid;

-- Also check the last 5 bind transactions to see the pattern
PRINT '';
PRINT 'Recent Bind Transactions:';
PRINT '========================';

SELECT TOP 5
    q.PolicyNumber,
    tqd.market_segment_code AS Market,
    CASE 
        WHEN UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '07564291-CBFE-4BBE-88D1-0548C88ACED4' THEN 'Primary'
        WHEN UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '08798559-321C-4FC0-98ED-A61B92215F31' THEN 'Excess'
        ELSE 'Unknown'
    END AS LineType,
    qd.ProgramID,
    CASE 
        WHEN qd.ProgramID = 11613 THEN 'WL Primary'
        WHEN qd.ProgramID = 11615 THEN 'RT Primary'
        WHEN qd.ProgramID = 11614 THEN 'WL Excess'
        WHEN qd.ProgramID = 11612 THEN 'RT Excess'
        WHEN qd.ProgramID IS NULL THEN 'NOT SET'
        ELSE 'OTHER (' + CAST(qd.ProgramID AS VARCHAR(10)) + ')'
    END AS ProgramType,
    CASE 
        WHEN (tqd.market_segment_code = 'WL' AND UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '07564291-CBFE-4BBE-88D1-0548C88ACED4' AND qd.ProgramID = 11613)
          OR (tqd.market_segment_code = 'RT' AND UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '07564291-CBFE-4BBE-88D1-0548C88ACED4' AND qd.ProgramID = 11615)
          OR (tqd.market_segment_code = 'WL' AND UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '08798559-321C-4FC0-98ED-A61B92215F31' AND qd.ProgramID = 11614)
          OR (tqd.market_segment_code = 'RT' AND UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '08798559-321C-4FC0-98ED-A61B92215F31' AND qd.ProgramID = 11612)
        THEN 'CORRECT'
        WHEN qd.ProgramID IS NULL THEN 'MISSING'
        ELSE 'WRONG'
    END AS IsCorrect,
    tqd.created_date
FROM tblTritonQuoteData tqd
INNER JOIN tblQuotes q ON q.QuoteGuid = tqd.QuoteGuid
LEFT JOIN tblQuoteDetails qd ON qd.QuoteGuid = q.QuoteGuid
WHERE tqd.transaction_type = 'bind'
ORDER BY tqd.created_date DESC;