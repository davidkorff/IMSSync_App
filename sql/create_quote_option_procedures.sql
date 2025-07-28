-- Stored procedure to get quote option details including the integer ID
CREATE PROCEDURE spGetQuoteOptions_WS
    @QuoteGuid UNIQUEIDENTIFIER
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        qo.QuoteOptionID,
        qo.QuoteOptionGuid,
        qo.QuoteGuid,
        qo.LineGuid,
        qo.PremiumTotal,
        qo.CompanyCommission,
        qo.ProducerCommission,
        l.LineName
    FROM tblQuoteOptions qo
    LEFT JOIN tblLines l ON qo.LineGuid = l.LineGuid
    WHERE qo.QuoteGuid = @QuoteGuid
    ORDER BY qo.QuoteOptionID
END
GO

-- Stored procedure to get quote option ID from GUID
CREATE PROCEDURE spGetQuoteOptionIDFromGuid_WS
    @QuoteOptionGuid UNIQUEIDENTIFIER
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT QuoteOptionID
    FROM tblQuoteOptions
    WHERE QuoteOptionGuid = @QuoteOptionGuid
END
GO