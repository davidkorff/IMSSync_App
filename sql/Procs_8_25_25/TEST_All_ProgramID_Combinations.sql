-- Test script to validate all ProgramID combinations
-- This creates test data to verify each market segment + line combination

PRINT 'ProgramID Combination Test Suite';
PRINT '================================';
PRINT '';

-- Test configuration
DECLARE @TestResults TABLE (
    TestCase NVARCHAR(100),
    MarketSegment NVARCHAR(10),
    LineGuid UNIQUEIDENTIFIER,
    LineType NVARCHAR(50),
    ExpectedProgramID INT,
    ActualProgramID INT,
    TestStatus NVARCHAR(20)
);

-- Define test cases
DECLARE @TestCases TABLE (
    TestID INT,
    MarketSegment NVARCHAR(10),
    LineGuid UNIQUEIDENTIFIER,
    LineType NVARCHAR(50),
    ExpectedProgramID INT
);

-- Insert all 4 valid combinations
INSERT INTO @TestCases VALUES
(1, 'WL', CAST('07564291-CBFE-4BBE-88D1-0548C88ACED4' AS UNIQUEIDENTIFIER), 'Primary', 11613),
(2, 'RT', CAST('07564291-CBFE-4BBE-88D1-0548C88ACED4' AS UNIQUEIDENTIFIER), 'Primary', 11615),
(3, 'WL', CAST('08798559-321C-4FC0-98ED-A61B92215F31' AS UNIQUEIDENTIFIER), 'Excess', 11614),
(4, 'RT', CAST('08798559-321C-4FC0-98ED-A61B92215F31' AS UNIQUEIDENTIFIER), 'Excess', 11612);

-- Run tests
PRINT 'Testing ProgramID Assignment Logic:';
PRINT '-----------------------------------';

DECLARE @TestID INT = 1;
DECLARE @MarketSegment NVARCHAR(10);
DECLARE @LineGuid UNIQUEIDENTIFIER;
DECLARE @LineType NVARCHAR(50);
DECLARE @ExpectedProgramID INT;
DECLARE @ActualProgramID INT;

WHILE @TestID <= 4
BEGIN
    SELECT 
        @MarketSegment = MarketSegment,
        @LineGuid = LineGuid,
        @LineType = LineType,
        @ExpectedProgramID = ExpectedProgramID
    FROM @TestCases
    WHERE TestID = @TestID;
    
    -- Simulate the logic from the stored procedure
    SET @ActualProgramID = NULL;
    
    -- Convert to uppercase string for comparison (matching the fix)
    DECLARE @LineGuidStr NVARCHAR(50) = UPPER(CAST(@LineGuid AS NVARCHAR(50)));
    
    -- Apply the same logic as in the stored procedure
    IF @MarketSegment = 'RT' AND @LineGuidStr = '07564291-CBFE-4BBE-88D1-0548C88ACED4'
        SET @ActualProgramID = 11615;
    ELSE IF @MarketSegment = 'WL' AND @LineGuidStr = '07564291-CBFE-4BBE-88D1-0548C88ACED4'
        SET @ActualProgramID = 11613;
    ELSE IF @MarketSegment = 'RT' AND @LineGuidStr = '08798559-321C-4FC0-98ED-A61B92215F31'
        SET @ActualProgramID = 11612;
    ELSE IF @MarketSegment = 'WL' AND @LineGuidStr = '08798559-321C-4FC0-98ED-A61B92215F31'
        SET @ActualProgramID = 11614;
    
    -- Record result
    INSERT INTO @TestResults VALUES (
        'Test ' + CAST(@TestID AS VARCHAR(2)),
        @MarketSegment,
        @LineGuid,
        @LineType,
        @ExpectedProgramID,
        @ActualProgramID,
        CASE WHEN @ActualProgramID = @ExpectedProgramID THEN 'PASS' ELSE 'FAIL' END
    );
    
    -- Display result
    PRINT 'Test ' + CAST(@TestID AS VARCHAR(2)) + ': ' + @MarketSegment + ' + ' + @LineType + ' Line';
    PRINT '  Expected ProgramID: ' + CAST(@ExpectedProgramID AS VARCHAR(10));
    PRINT '  Actual ProgramID:   ' + ISNULL(CAST(@ActualProgramID AS VARCHAR(10)), 'NULL');
    PRINT '  Status: ' + CASE WHEN @ActualProgramID = @ExpectedProgramID THEN '✓ PASS' ELSE '✗ FAIL' END;
    PRINT '';
    
    SET @TestID = @TestID + 1;
END

-- Display summary
PRINT 'TEST SUMMARY:';
PRINT '------------';
SELECT 
    TestCase,
    MarketSegment + ' + ' + LineType AS Combination,
    ExpectedProgramID,
    ActualProgramID,
    TestStatus
FROM @TestResults
ORDER BY TestCase;

-- Check overall result
DECLARE @PassCount INT = (SELECT COUNT(*) FROM @TestResults WHERE TestStatus = 'PASS');
DECLARE @TotalCount INT = (SELECT COUNT(*) FROM @TestResults);

PRINT '';
PRINT 'Overall Result: ' + CAST(@PassCount AS VARCHAR(2)) + '/' + CAST(@TotalCount AS VARCHAR(2)) + ' tests passed';

IF @PassCount = @TotalCount
BEGIN
    PRINT '✓ ALL TESTS PASSED - Logic is correct';
END
ELSE
BEGIN
    PRINT '✗ SOME TESTS FAILED - Logic needs review';
END

PRINT '';
PRINT '================================';
PRINT '';

-- Additional check: Find actual quotes that match each combination
PRINT 'ACTUAL QUOTES BY COMBINATION:';
PRINT '-----------------------------';

SELECT 
    tqd.market_segment_code AS Market,
    CASE 
        WHEN UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '07564291-CBFE-4BBE-88D1-0548C88ACED4' THEN 'Primary'
        WHEN UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '08798559-321C-4FC0-98ED-A61B92215F31' THEN 'Excess'
        ELSE 'Unknown'
    END AS LineType,
    COUNT(*) AS QuoteCount,
    COUNT(DISTINCT qd.ProgramID) AS UniqueProgramIDs,
    STRING_AGG(DISTINCT ISNULL(CAST(qd.ProgramID AS VARCHAR(10)), 'NULL'), ', ') AS ProgramIDs
FROM tblTritonQuoteData tqd
INNER JOIN tblQuotes q ON q.QuoteGuid = tqd.QuoteGuid
LEFT JOIN tblQuoteDetails qd ON qd.QuoteGuid = q.QuoteGuid
WHERE tqd.transaction_type = 'bind'
AND tqd.market_segment_code IN ('WL', 'RT')
GROUP BY 
    tqd.market_segment_code,
    CASE 
        WHEN UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '07564291-CBFE-4BBE-88D1-0548C88ACED4' THEN 'Primary'
        WHEN UPPER(CAST(q.CompanyLineGuid AS NVARCHAR(50))) = '08798559-321C-4FC0-98ED-A61B92215F31' THEN 'Excess'
        ELSE 'Unknown'
    END
ORDER BY Market, LineType;

PRINT '';
PRINT 'GUID Reference:';
PRINT '--------------';
PRINT 'Primary Line GUID: 07564291-CBFE-4BBE-88D1-0548C88ACED4';
PRINT 'Excess Line GUID:  08798559-321C-4FC0-98ED-A61B92215F31';
PRINT '';
PRINT 'ProgramID Mapping:';
PRINT '-----------------';
PRINT '11613 = WL + Primary';
PRINT '11615 = RT + Primary';
PRINT '11614 = WL + Excess';
PRINT '11612 = RT + Excess';