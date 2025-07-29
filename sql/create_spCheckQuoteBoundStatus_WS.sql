-- =============================================
-- Stored Procedure: spCheckQuoteBoundStatus_WS
-- Description: Check if a quote is already bound
-- Purpose: Prevent double binding of policies
-- =============================================

IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[spCheckQuoteBoundStatus_WS]') AND type in (N'P', N'PC'))
    DROP PROCEDURE [dbo].[spCheckQuoteBoundStatus_WS]
GO

CREATE PROCEDURE [dbo].[spCheckQuoteBoundStatus_WS]
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
            qs.QuoteStatus,
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
            NULL AS QuoteStatus,
            NULL AS Bound,
            0 AS IsBound,
            'Quote not found' AS BoundMessage;
    END
END
GO

-- Grant execute permission to IMS user
GRANT EXECUTE ON [dbo].[spCheckQuoteBoundStatus_WS] TO [IMS_User]
GO

PRINT 'Stored procedure spCheckQuoteBoundStatus_WS created successfully';