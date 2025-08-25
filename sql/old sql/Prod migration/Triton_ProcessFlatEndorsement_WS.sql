-- =============================================
-- Triton Wrapper for ProcessFlatEndorsement
-- Calculates total premium and calls base procedure
-- FIXED: Now retrieves and returns QuoteOptionGuid
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
    DECLARE @NewQuoteOptionGuid UNIQUEIDENTIFIER  -- Added to store the QuoteOptionGuid
    
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
        
        -- Step 2: Get the premium from the LATEST quote (the one we're endorsing)
        DECLARE @LatestQuoteID INT
        
        -- Get the QuoteID of the latest quote
        SELECT @LatestQuoteID = QuoteID
        FROM tblQuotes
        WHERE QuoteGUID = @LatestQuoteGuid
        
        -- Get the current premium from the latest quote's invoice
        SELECT @ExistingPremium = ISNULL(AnnualPremium, 0)
        FROM tblFin_Invoices
        WHERE QuoteID = @LatestQuoteID
        
        -- Step 3: Calculate total premium
        SET @TotalPremium = @ExistingPremium + @EndorsementPremium
        
        PRINT 'Endorsement calculation:'
        PRINT '  Opportunity ID: ' + CAST(@OpportunityID AS VARCHAR(20))
        PRINT '  Latest Quote GUID: ' + CAST(@LatestQuoteGuid AS VARCHAR(50))
        PRINT '  Latest Quote ID: ' + CAST(@LatestQuoteID AS VARCHAR(20))
        PRINT '  Control No: ' + CAST(@ControlNo AS VARCHAR(20))
        PRINT '  Current Policy Premium: $' + CAST(@ExistingPremium AS VARCHAR(20))
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
        
        -- Step 5: Retrieve the QuoteOptionGuid for the new endorsement quote
        -- The ProcessFlatEndorsement procedure creates a new QuoteOption record
        SELECT TOP 1 @NewQuoteOptionGuid = QuoteOptionGuid
        FROM tblQuoteOptions
        WHERE QuoteGuid = @NewQuoteGuid
        ORDER BY DateCreated DESC  -- Get the most recently created one
        
        -- Store the midterm_endt_id if provided to track this endorsement
        IF @MidtermEndtID IS NOT NULL AND @NewQuoteGuid IS NOT NULL
        BEGIN
            -- Check if record exists for this quote
            IF EXISTS (SELECT 1 FROM tblTritonQuoteData WHERE QuoteGuid = @NewQuoteGuid)
            BEGIN
                -- Update existing record with QuoteOptionGuid
                UPDATE tblTritonQuoteData 
                SET midterm_endt_id = @MidtermEndtID,
                    QuoteOptionGuid = @NewQuoteOptionGuid,  -- Store the QuoteOptionGuid
                    transaction_type = 'midterm_endorsement',
                    last_updated = GETDATE()
                WHERE QuoteGuid = @NewQuoteGuid
            END
            ELSE
            BEGIN
                -- Insert record with QuoteOptionGuid
                INSERT INTO tblTritonQuoteData (
                    QuoteGuid,
                    QuoteOptionGuid,  -- Include QuoteOptionGuid
                    opportunity_id,
                    midterm_endt_id,
                    transaction_type,
                    status,
                    created_date,
                    last_updated
                )
                VALUES (
                    @NewQuoteGuid,
                    @NewQuoteOptionGuid,  -- Store the QuoteOptionGuid
                    @OpportunityID,
                    @MidtermEndtID,
                    'midterm_endorsement',
                    'bound',
                    GETDATE(),
                    GETDATE()
                )
            END
        END
        
        -- Return success with the new quote guid AND QuoteOptionGuid
        SELECT 
            1 AS Result,
            'Endorsement created successfully' AS Message,
            @NewQuoteGuid AS NewQuoteGuid,
            @NewQuoteOptionGuid AS NewQuoteOptionGuid,  -- Return the QuoteOptionGuid
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