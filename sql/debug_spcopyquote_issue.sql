-- Debug why spCopyQuote is not creating a new quote
USE [IMS_DEV]
GO

DECLARE @TestQuoteGuid UNIQUEIDENTIFIER = '1D4998F3-A184-4825-BB63-57329F9CE4FE'
DECLARE @ControlNo INT
DECLARE @QuoteCount INT

PRINT '=== DEBUGGING spCopyQuote FOR QUOTE ' + CAST(@TestQuoteGuid AS VARCHAR(50)) + ' ==='
PRINT ''

-- Step 1: Check the current quote
PRINT '1. CURRENT QUOTE DETAILS:'
SELECT 
    QuoteGuid,
    QuoteID,
    ControlNo,
    QuoteStatusID,
    TransactionTypeID,
    PolicyNumber,
    DateBound,
    OriginalQuoteGuid,
    CASE 
        WHEN OriginalQuoteGuid IS NOT NULL THEN 'This is already an endorsement/copy'
        ELSE 'This is an original quote'
    END AS QuoteType
FROM tblQuotes
WHERE QuoteGuid = @TestQuoteGuid

-- Get the control number
SELECT @ControlNo = ControlNo
FROM tblQuotes
WHERE QuoteGuid = @TestQuoteGuid

PRINT ''
PRINT '2. ALL QUOTES WITH SAME CONTROL NUMBER (' + CAST(@ControlNo AS VARCHAR(20)) + '):'
SELECT 
    QuoteGuid,
    QuoteID,
    QuoteStatusID,
    TransactionTypeID,
    DateCreated,
    PolicyNumber,
    OriginalQuoteGuid
FROM tblQuotes
WHERE ControlNo = @ControlNo
ORDER BY QuoteID

-- Count quotes with this control number
SELECT @QuoteCount = COUNT(*)
FROM tblQuotes
WHERE ControlNo = @ControlNo

PRINT ''
PRINT 'Total quotes with ControlNo ' + CAST(@ControlNo AS VARCHAR(20)) + ': ' + CAST(@QuoteCount AS VARCHAR(10))

-- Step 2: Test spCopyQuote in a transaction
PRINT ''
PRINT '3. TESTING spCopyQuote:'
PRINT '   (This will rollback - no changes will be saved)'
PRINT ''

BEGIN TRANSACTION TestCopy

-- Count before
DECLARE @CountBefore INT
SELECT @CountBefore = COUNT(*) FROM tblQuotes WHERE ControlNo = @ControlNo

-- Try to copy the quote
PRINT 'Executing: EXEC spCopyQuote @QuoteGuid = ''' + CAST(@TestQuoteGuid AS VARCHAR(50)) + ''''
EXEC spCopyQuote @QuoteGuid = @TestQuoteGuid

-- Count after
DECLARE @CountAfter INT
SELECT @CountAfter = COUNT(*) FROM tblQuotes WHERE ControlNo = @ControlNo

PRINT 'Quotes before spCopyQuote: ' + CAST(@CountBefore AS VARCHAR(10))
PRINT 'Quotes after spCopyQuote: ' + CAST(@CountAfter AS VARCHAR(10))

IF @CountAfter > @CountBefore
BEGIN
    PRINT '✓ SUCCESS: spCopyQuote created a new quote'
    
    -- Show the new quote
    SELECT TOP 1
        'NEW QUOTE CREATED' AS Status,
        QuoteGuid,
        QuoteID,
        QuoteStatusID,
        TransactionTypeID,
        OriginalQuoteGuid
    FROM tblQuotes
    WHERE ControlNo = @ControlNo
    ORDER BY QuoteID DESC
END
ELSE
BEGIN
    PRINT '✗ FAILED: spCopyQuote did not create a new quote'
    PRINT ''
    PRINT 'Possible reasons:'
    PRINT '1. The quote is locked or in use'
    PRINT '2. spCopyQuote has restrictions on copying bound quotes'
    PRINT '3. Permission issues'
    PRINT '4. The stored procedure needs different parameters'
END

-- Always rollback the test
ROLLBACK TRANSACTION TestCopy

PRINT ''
PRINT '4. ALTERNATIVE APPROACH:'
PRINT 'If spCopyQuote cannot copy this quote, we may need to:'
PRINT '1. Use a different stored procedure'
PRINT '2. Create the endorsement quote manually'
PRINT '3. Check if there are IMS-specific procedures for creating endorsements'

-- Check for endorsement-specific procedures
PRINT ''
PRINT '5. CHECKING FOR ENDORSEMENT-SPECIFIC PROCEDURES:'
SELECT 
    name AS ProcedureName,
    create_date,
    modify_date
FROM sys.procedures
WHERE name LIKE '%endors%' 
   OR name LIKE '%copy%'
   OR name LIKE '%renew%'
ORDER BY name