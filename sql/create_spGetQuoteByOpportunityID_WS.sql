-- =============================================
-- Stored Procedure: spGetQuoteByOpportunityID_WS
-- Description: Find quote information by opportunity_id and check if bound
-- Purpose: Used for rebind detection and finding existing quotes
-- =============================================

IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[spGetQuoteByOpportunityID_WS]') AND type in (N'P', N'PC'))
    DROP PROCEDURE [dbo].[spGetQuoteByOpportunityID_WS]
GO

CREATE PROCEDURE [dbo].[spGetQuoteByOpportunityID_WS]
    @OpportunityID INT
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Find quote by opportunity_id and check if it's bound
    SELECT TOP 1
        tqd.QuoteGuid,
        tqd.QuoteOptionGuid,
        tqd.policy_number,
        tqd.insured_name,
        tqd.opportunity_id,
        tqd.created_date,
        q.QuoteStatusID,
        q.PolicyNumber AS QuotePolicyNumber,
        q.DateBound,
        q.DateIssued,
        CASE 
            WHEN qs.Bound = 1 THEN 1
            ELSE 0
        END AS IsBound,
        qs.Bound AS BoundFlag
    FROM tblTritonQuoteData tqd
    INNER JOIN tblQuotes q ON tqd.QuoteGuid = q.QuoteGuid
    LEFT JOIN lstQuoteStatus qs ON q.QuoteStatusID = qs.QuoteStatusID
    WHERE tqd.opportunity_id = @OpportunityID
    ORDER BY tqd.created_date DESC;  -- Get the most recent if multiple exist
END
GO


GO

PRINT 'Stored procedure spGetQuoteByOpportunityID_WS created successfully';