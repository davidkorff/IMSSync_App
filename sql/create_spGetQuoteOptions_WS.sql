-- Stored procedure to get quote options with their integer IDs
-- This is needed to map from Quote GUID to Quote Option ID for the Bind method

CREATE PROCEDURE spGetQuoteOptions_WS
    @QuoteGuid UNIQUEIDENTIFIER
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Get quote options for the specified quote
    -- Including the integer QuoteOptionID which is needed for the Bind method
    SELECT 
        qo.QuoteOptionID,          -- Integer ID needed for Bind method
        qo.QuoteOptionGuid,         -- GUID returned by AddQuoteOption
        qo.QuoteGuid,
        qo.LineGuid,
        qo.PremiumTotal,
        qo.CompanyCommission,
        qo.ProducerCommission,
        l.LineName,
        cl.CompanyLocationName,
        -- Include any installment billing info if available
        qo.InstallmentBillingQuoteOptionID,
        CASE 
            WHEN qo.InstallmentBillingQuoteOptionID IS NULL THEN 'Single Pay'
            ELSE 'Installment'
        END AS BillingType
    FROM tblQuoteOptions qo
    LEFT JOIN tblLines l ON qo.LineGuid = l.LineGuid
    LEFT JOIN tblCompanyLocations cl ON qo.CompanyLocationGuid = cl.CompanyLocationGuid
    WHERE qo.QuoteGuid = @QuoteGuid
    ORDER BY qo.QuoteOptionID;
END
GO

-- Grant execute permission
GRANT EXECUTE ON spGetQuoteOptions_WS TO [IMS_WebServices];
GO