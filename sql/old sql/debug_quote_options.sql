-- Debug script to understand quote option ID patterns
-- Run this after creating a quote to see the relationship between quote IDs and quote option IDs

-- Example: If error shows "quote ID 613648", use that here
DECLARE @QuoteID INT = 613648

-- Check if we can find quote options by quote ID
SELECT TOP 10
    qo.QuoteOptionID,
    qo.QuoteOptionGuid,
    qo.QuoteGuid,
    q.QuoteID,
    q.QuoteNumber,
    qo.LineGuid,
    qo.CompanyLocationGuid,
    qo.InstallmentBillingQuoteOptionID,
    qo.PremiumTotal
FROM tblQuoteOptions qo
INNER JOIN tblQuotes q ON q.QuoteGuid = qo.QuoteGuid
WHERE q.QuoteID = @QuoteID

-- Also check for patterns in QuoteOptionID values
SELECT 
    MIN(QuoteOptionID) as MinOptionID,
    MAX(QuoteOptionID) as MaxOptionID,
    COUNT(*) as TotalOptions,
    COUNT(DISTINCT QuoteGuid) as UniqueQuotes
FROM tblQuoteOptions
WHERE QuoteOptionID > 600000  -- Recent options

-- Check installment billing configuration
SELECT TOP 10
    CompanyInstallmentID,
    CompanyID,
    InstallmentName,
    NumberOfPayments,
    Active
FROM tblCompanyInstallments
ORDER BY CompanyInstallmentID