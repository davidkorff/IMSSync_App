-- Corrected stored procedure that takes Quote GUID and returns Quote Option ID
-- This is what spGetTritonQuoteData_WS should look like

CREATE PROCEDURE spGetTritonQuoteData_WS
    @QuoteGuid UNIQUEIDENTIFIER
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Get the first (or only) quote option ID for the given QUOTE
    SELECT TOP 1 
        QuoteOptionID as quoteoptionid  -- lowercase to match what we expect in response
    FROM tblQuoteOptions 
    WHERE QuoteGuid = @QuoteGuid
    ORDER BY QuoteOptionID;  -- Get the lowest ID if multiple exist
END
GO

-- Grant execute permissions
GRANT EXECUTE ON spGetTritonQuoteData_WS TO [IMS_User];
GO