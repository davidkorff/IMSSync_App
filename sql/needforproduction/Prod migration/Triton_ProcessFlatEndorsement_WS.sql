-- =============================================
-- Triton Wrapper for ProcessFlatEndorsement
-- Calculates total premium and calls base procedure
-- =============================================

CREATE OR ALTER PROCEDURE [dbo].[Triton_ProcessFlatEndorsement_WS]
    @OpportunityID INT,
    @EndorsementPremium MONEY,
    @EndorsementEffectiveDate VARCHAR(50),
    @EndorsementComment VARCHAR(500) = 'Midterm Endorsement',
    @UserGuid UNIQUEIDENTIFIER = NULL,
    @MidtermEndtID INT = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @Result INT = 0
    DECLARE @Message VARCHAR(MAX) = ''
    DECLARE @LatestQuoteGuid UNIQUEIDENTIFIER
    DECLARE @ControlNo INT
    DECLARE @ExistingPremium MONEY = 0
    DECLARE @TotalPremium MONEY
    DECLARE @EffectiveDateTime DATETIME
    DECLARE @NewQuoteGuid UNIQUEIDENTIFIER
    
    BEGIN TRY
        -- Convert date string to datetime
        SET @EffectiveDateTime = CONVERT(DATETIME, @EndorsementEffectiveDate, 101)
        
        -- Check for duplicate endorsement
        IF @MidtermEndtID IS NOT NULL
        BEGIN
            IF EXISTS (
                SELECT 1 
                FROM tblTritonQuoteData 
                WHERE midterm_endt_id = @MidtermEndtID
            )
            BEGIN
                SELECT 
                    0 AS Result,
                    'Midterm Endorsement Already Processed' AS Message,
                    @MidtermEndtID AS MidtermEndtID
                RETURN
            END
        END
        
        -- Step 1: Find the latest quote in the chain for this opportunity_id
        -- Find the quote that is NOT an OriginalQuoteGuid for any other quote (end of chain)
        DECLARE @QuoteStatusID INT
        
        SELECT TOP 1 
            @LatestQuoteGuid = q.QuoteGUID,
            @ControlNo = q.ControlNo,
            @QuoteStatusID = q.QuoteStatusID
        FROM tblQuotes q
        WHERE q.ControlNo IN (
            -- Find the control number for this opportunity
            SELECT DISTINCT q2.ControlNo
            FROM tblTritonQuoteData tq
            INNER JOIN tblQuotes q2 ON q2.QuoteGUID = tq.QuoteGuid
            WHERE tq.opportunity_id = @OpportunityID
        )
        AND NOT EXISTS (
            -- Make sure this quote is not the original for another quote (find the end of the chain)
            SELECT 1 
            FROM tblQuotes q3 
            WHERE q3.OriginalQuoteGUID = q.QuoteGUID
        )
        ORDER BY q.QuoteID DESC  -- If somehow multiple, get the most recent
        
        -- Check if the latest quote is bound
        IF @QuoteStatusID <> 3  -- Not bound
        BEGIN
            SELECT 
                0 AS Result,
                'Cannot create endorsement - latest quote in chain is not bound' AS Message,
                @LatestQuoteGuid AS LatestQuoteGuid,
                @QuoteStatusID AS QuoteStatusID
            RETURN
        END
        
        IF @LatestQuoteGuid IS NULL
        BEGIN
            SELECT 
                0 AS Result,
                'No bound quote found for opportunity_id ' + CAST(@OpportunityID AS VARCHAR(20)) AS Message
            RETURN
        END
        
        -- Step 2: Find the original quote (first in the chain) and get its premium
        DECLARE @CurrentQuoteGuid UNIQUEIDENTIFIER = @LatestQuoteGuid
        DECLARE @OriginalQuoteGuid UNIQUEIDENTIFIER
        DECLARE @OriginalQuoteID INT
        
        -- Backtrack through the chain to find the original quote
        WHILE 1=1
        BEGIN
            SELECT @OriginalQuoteGuid = OriginalQuoteGUID
            FROM tblQuotes
            WHERE QuoteGUID = @CurrentQuoteGuid
            
            IF @OriginalQuoteGuid IS NULL
                BREAK  -- Found the original (no OriginalQuoteGUID)
            
            SET @CurrentQuoteGuid = @OriginalQuoteGuid
        END
        
        -- Get the QuoteID of the original quote
        SELECT @OriginalQuoteID = QuoteID
        FROM tblQuotes
        WHERE QuoteGUID = @CurrentQuoteGuid
        
        -- Get the original premium from the invoice
        SELECT @ExistingPremium = ISNULL(AnnualPremium, 0)
        FROM tblFin_Invoices
        WHERE QuoteID = @OriginalQuoteID
        
        -- Step 3: Calculate total premium
        SET @TotalPremium = @ExistingPremium + @EndorsementPremium
        
        PRINT 'Endorsement calculation:'
        PRINT '  Opportunity ID: ' + CAST(@OpportunityID AS VARCHAR(20))
        PRINT '  Latest Quote GUID: ' + CAST(@LatestQuoteGuid AS VARCHAR(50))
        PRINT '  Original Quote GUID: ' + CAST(@CurrentQuoteGuid AS VARCHAR(50))
        PRINT '  Original Quote ID: ' + CAST(@OriginalQuoteID AS VARCHAR(20))
        PRINT '  Control No: ' + CAST(@ControlNo AS VARCHAR(20))
        PRINT '  Original Policy Premium: $' + CAST(@ExistingPremium AS VARCHAR(20))
        PRINT '  Endorsement Premium: $' + CAST(@EndorsementPremium AS VARCHAR(20))
        PRINT '  Total Premium: $' + CAST(@TotalPremium AS VARCHAR(20))
        PRINT '  Effective Date: ' + @EndorsementEffectiveDate
        
        -- Step 4: Call the base ProcessFlatEndorsement procedure
        EXEC [dbo].[ProcessFlatEndorsement]
            @OriginalQuoteGuid = @LatestQuoteGuid,
            @NewPremium = @TotalPremium,
            @EndorsementEffectiveDate = @EffectiveDateTime,
            @EndorsementComment = @EndorsementComment,
            @UserGuid = @UserGuid,
            @NewQuoteGuid = @NewQuoteGuid OUTPUT
        
        -- Return success with the new quote guid
        SELECT 
            1 AS Result,
            'Endorsement created successfully' AS Message,
            @NewQuoteGuid AS NewQuoteGuid,
            @LatestQuoteGuid AS OriginalQuoteGuid,
            @ControlNo AS ControlNo,
            @ExistingPremium AS ExistingPremium,
            @EndorsementPremium AS EndorsementPremium,
            @TotalPremium AS TotalPremium
            
    END TRY
    BEGIN CATCH
        SELECT 
            0 AS Result,
            ERROR_MESSAGE() AS Message,
            ERROR_LINE() AS ErrorLine,
            ERROR_PROCEDURE() AS ErrorProcedure
    END CATCH
END
GO