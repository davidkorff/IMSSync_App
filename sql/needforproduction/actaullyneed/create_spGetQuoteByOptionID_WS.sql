-- =============================================
-- Stored Procedure: spGetQuoteByOptionID_WS
-- Description: Find quote information by option_id (opportunity_id from Triton)
-- Used for: Issue and Unbind transactions that need to find existing quotes
-- =============================================

IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[spGetQuoteByOptionID_WS]') AND type in (N'P', N'PC'))
    DROP PROCEDURE [dbo].[spGetQuoteByOptionID_WS]
GO

CREATE PROCEDURE [dbo].[spGetQuoteByOptionID_WS]
    @OptionID INT
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Return just the QuoteGuid for the given option_id
    -- Look in tblTritonQuoteData for the opportunity_id
    -- IMPORTANT: Exclude cancellation and reinstatement quotes
    SELECT TOP 1
        tqd.QuoteGuid
    FROM tblTritonQuoteData tqd
    WHERE tqd.opportunity_id = @OptionID
    AND ISNULL(tqd.transaction_type, '') NOT IN ('cancellation', 'reinstatement')
    ORDER BY tqd.created_date DESC;  -- Get the most recent if multiple exist
END
GO

-- Grant execute permission to IMS user
GRANT EXECUTE ON [dbo].[spGetQuoteByOptionID_WS] TO [IMS_User]
GO