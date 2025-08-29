CREATE OR ALTER PROCEDURE [dbo].[spGetQuoteByOptionID_WS]
    @OptionID INT
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Return just the QuoteGuid for the given option_id
    -- Look in tblTritonQuoteData for the opportunity_id
    SELECT TOP 1
        tqd.QuoteGuid
    FROM tblTritonQuoteData tqd
    WHERE tqd.opportunity_id = @OptionID
    ORDER BY tqd.created_date DESC;  -- Get the most recent if multiple exist
END






