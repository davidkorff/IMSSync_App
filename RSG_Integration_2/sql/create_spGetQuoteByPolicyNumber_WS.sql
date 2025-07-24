-- =============================================
-- Stored Procedure: spGetQuoteByPolicyNumber_WS
-- Description: Find quote information by policy number
-- Used for: Issue transactions that need to find existing bound quotes
-- =============================================

IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[spGetQuoteByPolicyNumber_WS]') AND type in (N'P', N'PC'))
    DROP PROCEDURE [dbo].[spGetQuoteByPolicyNumber_WS]
GO

CREATE PROCEDURE [dbo].[spGetQuoteByPolicyNumber_WS]
    @PolicyNumber NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Return quote information for the given policy number
    SELECT TOP 1
        q.QuoteGuid,
        q.PolicyNumber,
        q.InsuredGuid,
        q.Effective,
        q.Expiration,
        q.QuoteStatusID,
        qs.Name as QuoteStatusName,
        q.StateID,
        q.ProducerContactGuid,
        q.UnderwriterGuid,
        -- Include Triton data if available
        td.transaction_id as LastTransactionId,
        td.insured_name,
        td.net_premium,
        td.status as TritonStatus,
        td.created_date as LastTransactionDate
    FROM tblquotes q
    LEFT JOIN tblQuoteStatus qs ON q.QuoteStatusID = qs.ID
    LEFT JOIN tblTritonQuoteData td ON q.QuoteGuid = td.QuoteGuid
    WHERE q.PolicyNumber = @PolicyNumber
    ORDER BY td.created_date DESC;  -- Get the most recent transaction data
END
GO

-- Grant execute permission to IMS user
GRANT EXECUTE ON [dbo].[spGetQuoteByPolicyNumber_WS] TO [IMS_User]
GO