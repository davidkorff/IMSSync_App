-- =============================================
-- Get Latest Quote By Opportunity ID
-- Finds the most recent quote in tblTritonQuoteData for an opportunity,
-- then follows the quote chain to find the latest endorsement/renewal
-- =============================================
CREATE OR ALTER PROCEDURE [dbo].[spGetLatestQuoteByOpportunityID_WS]
    @OpportunityID INT
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Get the most recent quote from tblTritonQuoteData for this opportunity
    DECLARE @InitialQuoteGuid UNIQUEIDENTIFIER;
    DECLARE @CreatedDate DATETIME;
    
    SELECT TOP 1 
        @InitialQuoteGuid = QuoteGuid,
        @CreatedDate = created_date
    FROM tblTritonQuoteData
    WHERE opportunity_id = @OpportunityID
    ORDER BY created_date DESC;
    
    -- If no quote found in tblTritonQuoteData, return empty
    IF @InitialQuoteGuid IS NULL
    BEGIN
        SELECT 
            NULL as QuoteGuid,
            NULL as ControlNo,
            NULL as PolicyNumber,
            NULL as QuoteStatusID,
            'No quote found for opportunity' as Message;
        RETURN;
    END;
    
    -- Now find the latest quote in the chain by following OriginalQuoteGuid references
    WITH QuoteChain AS (
        -- Start with the initial quote
        SELECT 
            QuoteGuid,
            OriginalQuoteGuid,
            ControlNo,
            PolicyNumber,
            QuoteStatusID,
            EndorsementNum,
            TransactionTypeID,
            DateCreated,
            0 as ChainLevel
        FROM tblQuotes
        WHERE QuoteGuid = @InitialQuoteGuid
        
        UNION ALL
        
        -- Recursively find quotes that reference previous quotes
        SELECT 
            q.QuoteGuid,
            q.OriginalQuoteGuid,
            q.ControlNo,
            q.PolicyNumber,
            q.QuoteStatusID,
            q.EndorsementNum,
            q.TransactionTypeID,
            q.DateCreated,
            qc.ChainLevel + 1
        FROM tblQuotes q
        INNER JOIN QuoteChain qc ON q.OriginalQuoteGuid = qc.QuoteGuid
    )
    -- Select the latest quote in the chain (highest level)
    SELECT TOP 1
        QuoteGuid,
        ControlNo,
        PolicyNumber,
        QuoteStatusID,
        EndorsementNum,
        TransactionTypeID,
        ChainLevel,
        @CreatedDate as TritonQuoteCreatedDate,
        'Success' as Message
    FROM QuoteChain
    ORDER BY ChainLevel DESC;
    
END
GO

-- =============================================
-- GRANT PERMISSIONS
-- =============================================
GRANT EXECUTE ON [dbo].[spGetLatestQuoteByOpportunityID_WS] TO [IMSUser]
GO