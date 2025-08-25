CREATE OR ALTER PROCEDURE [dbo].[spGetQuoteByPolicyNumber_WS]
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






