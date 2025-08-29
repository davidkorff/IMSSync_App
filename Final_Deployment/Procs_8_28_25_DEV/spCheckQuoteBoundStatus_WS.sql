CREATE OR ALTER PROCEDURE [dbo].[spCheckQuoteBoundStatus_WS]
    @QuoteGuid UNIQUEIDENTIFIER
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Check if quote exists and get its bound status
    IF EXISTS (SELECT 1 FROM tblQuotes WHERE QuoteGuid = @QuoteGuid)
    BEGIN
        SELECT 
            q.QuoteGuid,
            q.QuoteStatusID,
            q.PolicyNumber,
            q.DateBound,
            q.DateIssued,
            qs.Bound,
            CASE 
                WHEN qs.Bound = 1 THEN 1
                ELSE 0
            END AS IsBound,
            CASE 
                WHEN qs.Bound = 1 THEN 'Policy is already bound'
                ELSE 'Policy is not bound'
            END AS BoundMessage
        FROM tblQuotes q
        LEFT JOIN lstQuoteStatus qs ON q.QuoteStatusID = qs.QuoteStatusID
        WHERE q.QuoteGuid = @QuoteGuid;
    END
    ELSE
    BEGIN
        -- Quote not found
        SELECT 
            @QuoteGuid AS QuoteGuid,
            NULL AS QuoteStatusID,
            NULL AS PolicyNumber,
            NULL AS DateBound,
            NULL AS DateIssued,
            NULL AS Bound,
            0 AS IsBound,
            'Quote not found' AS BoundMessage;
    END
END






