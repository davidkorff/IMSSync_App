-- Complete verification script for ProgramID assignment
-- This checks if the fix is working correctly

PRINT 'ProgramID Assignment Verification Suite';
PRINT '=======================================';
PRINT '';
PRINT 'Testing Date: ' + CONVERT(VARCHAR, GETDATE(), 120);
PRINT '';

-- 1. Check if market_segment_code column exists
PRINT '1. CHECKING TABLE STRUCTURE:';
PRINT '----------------------------';
IF EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'market_segment_code')
BEGIN
    PRINT '✓ market_segment_code column EXISTS in tblTritonQuoteData';
    
    -- Get column details
    SELECT 
        'Column Details' AS Info,
        c.name AS ColumnName,
        t.name AS DataType,
        c.max_length AS MaxLength,
        c.is_nullable AS IsNullable
    FROM sys.columns c
    INNER JOIN sys.types t ON c.user_type_id = t.user_type_id
    WHERE c.object_id = OBJECT_ID('tblTritonQuoteData') 
    AND c.name = 'market_segment_code';
END
ELSE
BEGIN
    PRINT '✗ ERROR: market_segment_code column NOT FOUND in tblTritonQuoteData';
    PRINT '  Run: ADD_market_segment_code_column_FIXED.sql';
END

PRINT '';

-- 2. Check the stored procedure for updated logic
PRINT '2. CHECKING STORED PROCEDURE:';
PRINT '-----------------------------';
DECLARE @ProcText NVARCHAR(MAX);
SELECT @ProcText = OBJECT_DEFINITION(OBJECT_ID('dbo.spProcessTritonPayload_WS'));

IF @ProcText IS NOT NULL
BEGIN
    -- Check for case-insensitive GUID comparison
    IF CHARINDEX('UPPER(CAST(@CompanyLineGuid', @ProcText) > 0 OR 
       CHARINDEX('UPPER(CAST(CompanyLineGuid', @ProcText) > 0
    BEGIN
        PRINT '✓ Case-insensitive GUID comparison FOUND';
    END
    ELSE
    BEGIN
        PRINT '✗ WARNING: Case-insensitive GUID comparison NOT found';
        PRINT '  The stored procedure may not have the latest fix';
    END
    
    -- Check for market_segment_code extraction
    IF CHARINDEX('JSON_VALUE(@full_payload_json, ''$.market_segment_code'')', @ProcText) > 0
    BEGIN
        PRINT '✓ market_segment_code extraction from JSON FOUND';
    END
    ELSE
    BEGIN
        PRINT '✗ ERROR: market_segment_code extraction NOT found';
    END
    
    -- Check if all ProgramIDs are referenced
    IF CHARINDEX('11613', @ProcText) > 0 AND 
       CHARINDEX('11615', @ProcText) > 0 AND 
       CHARINDEX('11612', @ProcText) > 0 AND 
       CHARINDEX('11614', @ProcText) > 0
    BEGIN
        PRINT '✓ All ProgramID values (11613, 11615, 11612, 11614) FOUND';
    END
    ELSE
    BEGIN
        PRINT '✗ ERROR: Not all ProgramID values found in procedure';
    END
END
ELSE
BEGIN
    PRINT '✗ ERROR: spProcessTritonPayload_WS NOT FOUND';
END

PRINT '';

-- 3. Check recent bind transactions
PRINT '3. RECENT BIND TRANSACTIONS (Last 10):';
PRINT '--------------------------------------';

SELECT TOP 10
    tqd.transaction_id,
    tqd.transaction_type,
    tqd.market_segment_code,
    q.PolicyNumber,
    UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) AS LineGuid_Upper,
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
        WHEN qd.ProgramID IS NULL THEN '*** NULL ***'
        ELSE 'OTHER (' + CAST(qd.ProgramID AS VARCHAR(10)) + ')'
    END AS ProgramType,
    CASE 
        WHEN (tqd.market_segment_code = 'WL' AND UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '07564291-CBFE-4BBE-88D1-0548C88ACED4' AND qd.ProgramID = 11613)
          OR (tqd.market_segment_code = 'RT' AND UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '07564291-CBFE-4BBE-88D1-0548C88ACED4' AND qd.ProgramID = 11615)
          OR (tqd.market_segment_code = 'WL' AND UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '08798559-321C-4FC0-98ED-A61B92215F31' AND qd.ProgramID = 11614)
          OR (tqd.market_segment_code = 'RT' AND UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '08798559-321C-4FC0-98ED-A61B92215F31' AND qd.ProgramID = 11612)
        THEN '✓ CORRECT'
        WHEN qd.ProgramID IS NULL THEN '✗ NULL'
        ELSE '✗ WRONG'
    END AS Status,
    tqd.created_date
FROM tblTritonQuoteData tqd
INNER JOIN tblQuotes q ON q.QuoteGuid = tqd.QuoteGuid
LEFT JOIN tblQuoteDetails qd ON qd.QuoteGuid = q.QuoteGuid
WHERE tqd.transaction_type = 'bind'
ORDER BY tqd.created_date DESC;

PRINT '';

-- 4. Statistics on ProgramID assignments
PRINT '4. PROGRAMID ASSIGNMENT STATISTICS:';
PRINT '-----------------------------------';

WITH ProgramStats AS (
    SELECT 
        tqd.market_segment_code,
        CASE 
            WHEN UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '07564291-CBFE-4BBE-88D1-0548C88ACED4' THEN 'Primary'
            WHEN UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '08798559-321C-4FC0-98ED-A61B92215F31' THEN 'Excess'
            ELSE 'Unknown'
        END AS LineType,
        qd.ProgramID,
        COUNT(*) AS Count
    FROM tblTritonQuoteData tqd
    INNER JOIN tblQuotes q ON q.QuoteGuid = tqd.QuoteGuid
    LEFT JOIN tblQuoteDetails qd ON qd.QuoteGuid = q.QuoteGuid
    WHERE tqd.transaction_type = 'bind'
    AND tqd.created_date >= DATEADD(DAY, -30, GETDATE()) -- Last 30 days
    GROUP BY 
        tqd.market_segment_code,
        UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))),
        qd.ProgramID
)
SELECT 
    market_segment_code AS Market,
    LineType,
    CASE 
        WHEN ProgramID = 11613 THEN '11613 (WL Primary)'
        WHEN ProgramID = 11615 THEN '11615 (RT Primary)'
        WHEN ProgramID = 11614 THEN '11614 (WL Excess)'
        WHEN ProgramID = 11612 THEN '11612 (RT Excess)'
        WHEN ProgramID IS NULL THEN 'NULL'
        ELSE CAST(ProgramID AS VARCHAR(10))
    END AS ProgramID,
    Count,
    CASE 
        WHEN (market_segment_code = 'WL' AND LineType = 'Primary' AND ProgramID = 11613)
          OR (market_segment_code = 'RT' AND LineType = 'Primary' AND ProgramID = 11615)
          OR (market_segment_code = 'WL' AND LineType = 'Excess' AND ProgramID = 11614)
          OR (market_segment_code = 'RT' AND LineType = 'Excess' AND ProgramID = 11612)
        THEN 'CORRECT'
        WHEN ProgramID IS NULL THEN 'MISSING'
        ELSE 'WRONG'
    END AS Status
FROM ProgramStats
ORDER BY market_segment_code, LineType, ProgramID;

PRINT '';

-- 5. Check for NULL ProgramIDs that should have values
PRINT '5. QUOTES WITH MISSING PROGRAMID:';
PRINT '---------------------------------';

SELECT TOP 10
    tqd.transaction_id,
    q.PolicyNumber,
    tqd.market_segment_code,
    CASE 
        WHEN UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '07564291-CBFE-4BBE-88D1-0548C88ACED4' THEN 'Primary'
        WHEN UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '08798559-321C-4FC0-98ED-A61B92215F31' THEN 'Excess'
        ELSE 'Unknown'
    END AS LineType,
    CASE 
        WHEN tqd.market_segment_code = 'WL' AND UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '07564291-CBFE-4BBE-88D1-0548C88ACED4' THEN 11613
        WHEN tqd.market_segment_code = 'RT' AND UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '07564291-CBFE-4BBE-88D1-0548C88ACED4' THEN 11615
        WHEN tqd.market_segment_code = 'WL' AND UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '08798559-321C-4FC0-98ED-A61B92215F31' THEN 11614
        WHEN tqd.market_segment_code = 'RT' AND UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '08798559-321C-4FC0-98ED-A61B92215F31' THEN 11612
        ELSE NULL
    END AS Expected_ProgramID,
    'UPDATE tblQuoteDetails SET ProgramID = ' + 
    CASE 
        WHEN tqd.market_segment_code = 'WL' AND UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '07564291-CBFE-4BBE-88D1-0548C88ACED4' THEN '11613'
        WHEN tqd.market_segment_code = 'RT' AND UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '07564291-CBFE-4BBE-88D1-0548C88ACED4' THEN '11615'
        WHEN tqd.market_segment_code = 'WL' AND UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '08798559-321C-4FC0-98ED-A61B92215F31' THEN '11614'
        WHEN tqd.market_segment_code = 'RT' AND UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '08798559-321C-4FC0-98ED-A61B92215F31' THEN '11612'
        ELSE 'NULL'
    END + ' WHERE QuoteGuid = ''' + CAST(q.QuoteGuid AS VARCHAR(50)) + '''' AS Fix_SQL,
    tqd.created_date
FROM tblTritonQuoteData tqd
INNER JOIN tblQuotes q ON q.QuoteGuid = tqd.QuoteGuid
LEFT JOIN tblQuoteDetails qd ON qd.QuoteGuid = q.QuoteGuid
WHERE tqd.transaction_type = 'bind'
AND qd.ProgramID IS NULL
AND tqd.market_segment_code IS NOT NULL
ORDER BY tqd.created_date DESC;

PRINT '';

-- 6. Summary
PRINT '6. SUMMARY:';
PRINT '----------';

DECLARE @TotalBinds INT, @CorrectPrograms INT, @NullPrograms INT, @WrongPrograms INT;

SELECT 
    @TotalBinds = COUNT(*),
    @CorrectPrograms = SUM(CASE 
        WHEN (tqd.market_segment_code = 'WL' AND UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '07564291-CBFE-4BBE-88D1-0548C88ACED4' AND qd.ProgramID = 11613)
          OR (tqd.market_segment_code = 'RT' AND UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '07564291-CBFE-4BBE-88D1-0548C88ACED4' AND qd.ProgramID = 11615)
          OR (tqd.market_segment_code = 'WL' AND UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '08798559-321C-4FC0-98ED-A61B92215F31' AND qd.ProgramID = 11614)
          OR (tqd.market_segment_code = 'RT' AND UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '08798559-321C-4FC0-98ED-A61B92215F31' AND qd.ProgramID = 11612)
        THEN 1 ELSE 0 END),
    @NullPrograms = SUM(CASE WHEN qd.ProgramID IS NULL THEN 1 ELSE 0 END),
    @WrongPrograms = SUM(CASE 
        WHEN qd.ProgramID IS NOT NULL 
        AND NOT (
            (tqd.market_segment_code = 'WL' AND UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '07564291-CBFE-4BBE-88D1-0548C88ACED4' AND qd.ProgramID = 11613)
          OR (tqd.market_segment_code = 'RT' AND UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '07564291-CBFE-4BBE-88D1-0548C88ACED4' AND qd.ProgramID = 11615)
          OR (tqd.market_segment_code = 'WL' AND UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '08798559-321C-4FC0-98ED-A61B92215F31' AND qd.ProgramID = 11614)
          OR (tqd.market_segment_code = 'RT' AND UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '08798559-321C-4FC0-98ED-A61B92215F31' AND qd.ProgramID = 11612)
        )
        THEN 1 ELSE 0 END)
FROM tblTritonQuoteData tqd
INNER JOIN tblQuotes q ON q.QuoteGuid = tqd.QuoteGuid
LEFT JOIN tblQuoteDetails qd ON qd.QuoteGuid = q.QuoteGuid
WHERE tqd.transaction_type = 'bind'
AND tqd.created_date >= DATEADD(DAY, -30, GETDATE());

PRINT 'Total Bind Transactions (Last 30 days): ' + CAST(@TotalBinds AS VARCHAR(10));
PRINT 'Correct ProgramIDs: ' + CAST(@CorrectPrograms AS VARCHAR(10)) + ' (' + 
    CAST(CASE WHEN @TotalBinds > 0 THEN CAST(@CorrectPrograms * 100.0 / @TotalBinds AS DECIMAL(5,2)) ELSE 0 END AS VARCHAR(10)) + '%)';
PRINT 'NULL ProgramIDs: ' + CAST(@NullPrograms AS VARCHAR(10)) + ' (' + 
    CAST(CASE WHEN @TotalBinds > 0 THEN CAST(@NullPrograms * 100.0 / @TotalBinds AS DECIMAL(5,2)) ELSE 0 END AS VARCHAR(10)) + '%)';
PRINT 'Wrong ProgramIDs: ' + CAST(@WrongPrograms AS VARCHAR(10)) + ' (' + 
    CAST(CASE WHEN @TotalBinds > 0 THEN CAST(@WrongPrograms * 100.0 / @TotalBinds AS DECIMAL(5,2)) ELSE 0 END AS VARCHAR(10)) + '%)';

IF @NullPrograms > 0 OR @WrongPrograms > 0
BEGIN
    PRINT '';
    PRINT 'ACTION REQUIRED: There are ' + CAST(@NullPrograms + @WrongPrograms AS VARCHAR(10)) + ' quotes that need ProgramID correction.';
    PRINT 'Run the UPDATE statements from section 5 to fix missing ProgramIDs.';
END
ELSE IF @CorrectPrograms = @TotalBinds AND @TotalBinds > 0
BEGIN
    PRINT '';
    PRINT '✓ SUCCESS: All ProgramIDs are correctly assigned!';
END

PRINT '';
PRINT 'End of verification report';
PRINT '=========================';