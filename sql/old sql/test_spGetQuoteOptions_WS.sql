-- Test script to verify spGetQuoteOptions_WS exists and works
-- Run this in SQL Server Management Studio to see what it returns

-- Replace this GUID with an actual quote GUID from your test
DECLARE @TestQuoteGuid UNIQUEIDENTIFIER = 'f4bbe818-2d6f-4b9d-91fb-e4916549c4c5'

-- Test the stored procedure
EXEC spGetQuoteOptions_WS @QuoteGuid = @TestQuoteGuid

-- If the above works, check the table structure directly
-- This will help us understand what columns are available
SELECT TOP 10 
    QuoteOptionID,
    QuoteOptionGuid,
    QuoteGuid,
    LineGuid,
    CompanyLocationGuid,
    InstallmentBillingQuoteOptionID
FROM tblQuoteOptions
WHERE QuoteGuid = @TestQuoteGuid