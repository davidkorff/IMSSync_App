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
        
        -- Step 1: Find the latest quote for this opportunity_id
        SELECT TOP 1 
            @LatestQuoteGuid = tq.QuoteGuid,
            @ControlNo = q.ControlNo
        FROM tblTritonQuoteData tq
        INNER JOIN tblQuotes q ON q.QuoteGUID = tq.QuoteGuid
        WHERE tq.opportunity_id = @OpportunityID
        AND tq.status = 'bound'
        ORDER BY q.QuoteID DESC  -- Get the latest quote
        
        IF @LatestQuoteGuid IS NULL
        BEGIN
            SELECT 
                0 AS Result,
                'No bound quote found for opportunity_id ' + CAST(@OpportunityID AS VARCHAR(20)) AS Message
            RETURN
        END
        
        -- Step 2: Get the total existing premium from invoices
        SELECT @ExistingPremium = ISNULL(SUM(AnnualPremium), 0)
        FROM tblFin_Invoices
        WHERE QuoteControlNum = @ControlNo
        
        -- Step 3: Calculate total premium
        SET @TotalPremium = @ExistingPremium + @EndorsementPremium
        
        PRINT 'Endorsement calculation:'
        PRINT '  Opportunity ID: ' + CAST(@OpportunityID AS VARCHAR(20))
        PRINT '  Latest Quote GUID: ' + CAST(@LatestQuoteGuid AS VARCHAR(50))
        PRINT '  Control No: ' + CAST(@ControlNo AS VARCHAR(20))
        PRINT '  Existing Premium: $' + CAST(@ExistingPremium AS VARCHAR(20))
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