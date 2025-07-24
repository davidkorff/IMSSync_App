-- Simple stored procedure to get the integer QuoteOptionID for a given QuoteGuid
-- This bypasses the DataAccess parameter format issues
CREATE PROCEDURE spGetQuoteOptionID_WS
    @QuoteGuid UNIQUEIDENTIFIER
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Get the first (or only) quote option ID for the given quote
    SELECT TOP 1 
        QuoteOptionID,
        QuoteOptionGuid,
        QuoteGuid
    FROM tblQuoteOptions 
    WHERE QuoteGuid = @QuoteGuid
    ORDER BY QuoteOptionID;  -- Get the lowest ID if multiple exist
END
GO

-- Grant execute permissions
GRANT EXECUTE ON spGetQuoteOptionID_WS TO [IMS_User];
GO