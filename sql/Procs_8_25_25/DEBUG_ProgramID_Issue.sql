-- Debug script to check why ProgramID is not being set
-- Run this after a bind transaction to see what's happening

DECLARE @QuoteGuid UNIQUEIDENTIFIER = 'a770985e-cf67-4883-8457-fd6f068b6bbe'; -- From your test

PRINT 'Checking Quote: ' + CAST(@QuoteGuid AS NVARCHAR(50));
PRINT '================================================';
PRINT '';

-- 1. Check if tblQuoteDetails record exists
IF EXISTS (SELECT 1 FROM tblQuoteDetails WHERE QuoteGuid = @QuoteGuid)
BEGIN
    PRINT '✓ tblQuoteDetails record EXISTS';
    
    SELECT 
        QuoteDetailsID,
        QuoteGuid,
        ProgramID,
        ProducerCommission,
        CompanyCommission
    FROM tblQuoteDetails 
    WHERE QuoteGuid = @QuoteGuid;
END
ELSE
BEGIN
    PRINT '✗ tblQuoteDetails record DOES NOT EXIST - This is the problem!';
    PRINT '  The stored procedure checks IF EXISTS before updating ProgramID';
    PRINT '  No record means no ProgramID can be set';
END

PRINT '';

-- 2. Check tblQuotes for CompanyLineGuid
SELECT 
    'tblQuotes' AS [Table],
    QuoteGuid,
    CompanyLineGuid,
    PolicyNumber,
    ControlNo,
    DateCreated
FROM tblQuotes 
WHERE QuoteGuid = @QuoteGuid;

-- 3. Check tblTritonQuoteData for market_segment_code
SELECT 
    'tblTritonQuoteData' AS [Table],
    QuoteGuid,
    market_segment_code,
    class_of_business,
    program_name,
    transaction_type,
    policy_number,
    created_date
FROM tblTritonQuoteData 
WHERE QuoteGuid = @QuoteGuid;

-- 4. Check tblQuoteOptions for LineGuid (backup location)
SELECT 
    'tblQuoteOptions' AS [Table],
    QuoteOptionGuid,
    QuoteGuid,
    LineGuid,
    CompanyLocationGuid
FROM tblQuoteOptions
WHERE QuoteGuid = @QuoteGuid;

PRINT '';
PRINT 'ANALYSIS:';
PRINT '=========';

-- Get all the values we need
DECLARE @CompanyLineGuid UNIQUEIDENTIFIER;
DECLARE @market_segment_code NVARCHAR(10);
DECLARE @ProgramID INT;
DECLARE @QuoteDetailsExists BIT = 0;

SELECT @CompanyLineGuid = CompanyLineGuid FROM tblQuotes WHERE QuoteGuid = @QuoteGuid;
SELECT @market_segment_code = market_segment_code FROM tblTritonQuoteData WHERE QuoteGuid = @QuoteGuid;
SELECT @ProgramID = ProgramID FROM tblQuoteDetails WHERE QuoteGuid = @QuoteGuid;

IF EXISTS (SELECT 1 FROM tblQuoteDetails WHERE QuoteGuid = @QuoteGuid)
    SET @QuoteDetailsExists = 1;

PRINT 'CompanyLineGuid: ' + ISNULL(CAST(@CompanyLineGuid AS NVARCHAR(50)), 'NULL');
PRINT 'market_segment_code: ' + ISNULL(@market_segment_code, 'NULL');
PRINT 'Current ProgramID: ' + ISNULL(CAST(@ProgramID AS NVARCHAR(10)), 'NULL');
PRINT 'QuoteDetails Exists: ' + CASE WHEN @QuoteDetailsExists = 1 THEN 'YES' ELSE 'NO' END;

PRINT '';
PRINT 'Expected ProgramID based on rules:';
IF @market_segment_code = 'WL' AND @CompanyLineGuid = '07564291-CBFE-4BBE-88D1-0548C88ACED4'
    PRINT '  Should be: 11613 (WL + Primary Line)';
ELSE IF @market_segment_code = 'RT' AND @CompanyLineGuid = '07564291-CBFE-4BBE-88D1-0548C88ACED4'
    PRINT '  Should be: 11615 (RT + Primary Line)';
ELSE IF @market_segment_code = 'WL' AND @CompanyLineGuid = '08798559-321C-4FC0-98ED-A61B92215F31'
    PRINT '  Should be: 11614 (WL + Excess Line)';
ELSE IF @market_segment_code = 'RT' AND @CompanyLineGuid = '08798559-321C-4FC0-98ED-A61B92215F31'
    PRINT '  Should be: 11612 (RT + Excess Line)';
ELSE
    PRINT '  No matching rule for this combination';

PRINT '';
PRINT 'POSSIBLE ISSUES:';
PRINT '================';

IF @QuoteDetailsExists = 0
BEGIN
    PRINT '1. tblQuoteDetails record does not exist for this quote';
    PRINT '   Solution: Check when/how tblQuoteDetails is created during quote creation';
END

IF @CompanyLineGuid IS NULL
BEGIN
    PRINT '2. CompanyLineGuid is NULL in tblQuotes';
    PRINT '   Solution: Check quote creation process';
END

IF @market_segment_code IS NULL
BEGIN
    PRINT '3. market_segment_code is NULL in tblTritonQuoteData';
    PRINT '   Solution: Check if column exists and is being populated';
END

-- Check when tblQuoteDetails gets created
PRINT '';
PRINT 'When does tblQuoteDetails get created?';
PRINT '======================================';
PRINT 'tblQuoteDetails is typically created during:';
PRINT '1. Quote creation (AddQuote procedures)';
PRINT '2. Quote option creation (AutoAddQuoteOptions)';
PRINT '3. Sometimes during bind process';
PRINT '';
PRINT 'The stored procedure spProcessTritonPayload_WS runs AFTER quote creation';
PRINT 'but BEFORE binding. If tblQuoteDetails doesn''t exist at this point,';
PRINT 'the ProgramID cannot be set.';