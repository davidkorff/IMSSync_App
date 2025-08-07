-- Test the V5 Endorsement Procedure
-- This script tests the new endorsement procedure that uses Ascot's approach

-- First, run the V5 stored procedure creation script:
-- File: create_Triton_EndorsePolicy_WS_V5_ASCOT_APPROACH.sql

-- Then test with this:
DECLARE @Result INT
DECLARE @Message VARCHAR(MAX)
DECLARE @EndorsementQuoteGuid UNIQUEIDENTIFIER
DECLARE @QuoteOptionGuid UNIQUEIDENTIFIER
DECLARE @PolicyNumber VARCHAR(50)
DECLARE @EndorsementNumber INT

-- Test parameters
DECLARE @OpportunityID INT = 306955  -- Your test opportunity ID
DECLARE @UserGuid UNIQUEIDENTIFIER = 'YOUR-USER-GUID-HERE'  -- Get from auth
DECLARE @TransEffDate VARCHAR(50) = '08/06/2025'
DECLARE @EndorsementPremium MONEY = 1600.00
DECLARE @Comment VARCHAR(255) = 'Midterm Endorsement Test V5'
DECLARE @BindEndorsement BIT = 0  -- Let Python handle binding

-- Execute the procedure
EXEC Triton_EndorsePolicy_WS
    @OpportunityID = @OpportunityID,
    @UserGuid = @UserGuid,
    @TransEffDate = @TransEffDate,
    @EndorsementPremium = @EndorsementPremium,
    @Comment = @Comment,
    @BindEndorsement = @BindEndorsement

-- Check the results
SELECT TOP 1 
    'Latest Endorsement' as Section,
    q.QuoteGUID,
    q.PolicyNumber,
    q.TransactionTypeID,
    q.EndorsementNum,
    q.Bound,
    q.QuoteStatusID,
    tq.gross_premium
FROM tblQuotes q
LEFT JOIN tblTritonQuoteData tq ON tq.QuoteGuid = q.QuoteGUID
WHERE q.TransactionTypeID = 'E'
ORDER BY q.QuoteID DESC

-- Check if premium was inserted
SELECT 
    'Premium Records' as Section,
    qop.*
FROM tblQuotes q
INNER JOIN tblQuoteOptions qo ON qo.QuoteGUID = q.QuoteGUID
INNER JOIN tblQuoteOptionPremiums qop ON qop.QuoteOptionGUID = qo.QuoteOptionGUID
WHERE q.TransactionTypeID = 'E'
AND q.QuoteID = (SELECT MAX(QuoteID) FROM tblQuotes WHERE TransactionTypeID = 'E')

-- Verify the quote option status
SELECT 
    'Quote Option Status' as Section,
    qo.QuoteOptionGUID,
    qo.Bound,
    qo.DateCreated
FROM tblQuotes q
INNER JOIN tblQuoteOptions qo ON qo.QuoteGUID = q.QuoteGUID
WHERE q.TransactionTypeID = 'E'
AND q.QuoteID = (SELECT MAX(QuoteID) FROM tblQuotes WHERE TransactionTypeID = 'E')