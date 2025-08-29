CREATE OR ALTER PROCEDURE [dbo].[spGetQuoteByExpiringPolicyNumber_WS]
    @ExpiringPolicyNumber NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Find the most recent quote with this policy number
    -- This will be used as the RenewalOfQuoteGuid for the new renewal quote
    SELECT TOP 1
        tqd.QuoteGuid,
        tqd.QuoteOptionGuid,
        tqd.policy_number,
        tqd.insured_name,
        tqd.opportunity_id,
        tqd.effective_date,
        tqd.expiration_date,
        tqd.created_date,
        q.QuoteStatusID,
        q.DateBound,
        q.DateIssued
    FROM tblTritonQuoteData tqd
    INNER JOIN tblQuotes q ON tqd.QuoteGuid = q.QuoteGuid
    WHERE tqd.policy_number = @ExpiringPolicyNumber
    ORDER BY tqd.created_date DESC;  -- Get the most recent
END






