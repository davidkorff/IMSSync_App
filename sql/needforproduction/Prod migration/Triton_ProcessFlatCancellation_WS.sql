-- =============================================
-- Triton Wrapper for ProcessFlatCancellation
-- Follows same pattern as Triton_ProcessFlatEndorsement_WS
-- Retrieves QuoteOptionGuid and stores in tblTritonQuoteData
-- =============================================

CREATE OR ALTER PROCEDURE [dbo].[Triton_ProcessFlatCancellation_WS]
    @OpportunityID INT,
    @CancellationType VARCHAR(20) = 'flat',  -- 'flat' or 'earned'
    @CancellationDate VARCHAR(50),
    @ReasonCode INT = 30,  -- Default to "Insured Request"
    @Comment VARCHAR(500) = 'Policy Cancellation',
    @RefundAmount MONEY = NULL,
    @UserGuid UNIQUEIDENTIFIER = NULL,
    @CancellationID INT = NULL  -- Similar to MidtermEndtID for tracking
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Debug: Log input parameters
    PRINT '==============================================='
    PRINT 'Triton_ProcessFlatCancellation_WS Called with:'
    PRINT '  @OpportunityID: ' + CAST(@OpportunityID AS VARCHAR(20))
    PRINT '  @CancellationType: ' + @CancellationType
    PRINT '  @CancellationDate: ' + @CancellationDate
    PRINT '  @RefundAmount: ' + ISNULL(CAST(@RefundAmount AS VARCHAR(20)), 'NULL')
    PRINT '  @ReasonCode: ' + CAST(@ReasonCode AS VARCHAR(10))
    PRINT '  @Comment: ' + @Comment
    PRINT '==============================================='
    
    DECLARE @Result INT = 0
    DECLARE @Message VARCHAR(MAX) = ''
    DECLARE @LatestQuoteGuid UNIQUEIDENTIFIER
    DECLARE @ControlNo INT
    DECLARE @PolicyPremium MONEY = 0
    DECLARE @CalculatedRefund MONEY
    DECLARE @CancellationDateTime DATETIME
    DECLARE @NewQuoteGuid UNIQUEIDENTIFIER
    DECLARE @NewQuoteOptionGuid UNIQUEIDENTIFIER
    DECLARE @PolicyEffectiveDate DATETIME
    DECLARE @PolicyExpirationDate DATETIME
    DECLARE @DaysInPolicy INT
    DECLARE @DaysElapsed INT
    
    BEGIN TRY
        -- Convert date string to datetime
        SET @CancellationDateTime = CONVERT(DATETIME, @CancellationDate, 101)
        
        -- Check for duplicate cancellation if CancellationID provided
        IF @CancellationID IS NOT NULL
        BEGIN
            IF EXISTS (
                SELECT 1 
                FROM tblTritonQuoteData 
                WHERE cancellation_id = @CancellationID
            )
            BEGIN
                SELECT 
                    0 AS Result,
                    'Cancellation Already Processed' AS Message,
                    @CancellationID AS CancellationID
                RETURN
            END
        END
        
        -- Step 1: Find the latest quote in the chain for this opportunity_id
        DECLARE @QuoteStatusID INT
        
        -- First, find the most recent bound quote directly from tblTritonQuoteData
        SELECT TOP 1 
            @LatestQuoteGuid = tq.QuoteGuid,
            @ControlNo = q.ControlNo,
            @QuoteStatusID = q.QuoteStatusID,
            @PolicyEffectiveDate = q.EffectiveDate,
            @PolicyExpirationDate = q.ExpirationDate
        FROM tblTritonQuoteData tq
        INNER JOIN tblQuotes q ON q.QuoteGUID = tq.QuoteGuid
        WHERE tq.opportunity_id = @OpportunityID
        AND tq.status = 'bound'  -- Only look at bound quotes
        AND tq.transaction_type IN ('new_business', 'renewal', 'rebind', 'midterm_endorsement')  -- Exclude cancellations
        AND NOT EXISTS (
            -- Make sure this quote is not the original for another quote (find the end of the chain)
            SELECT 1 
            FROM tblQuotes q3 
            WHERE q3.OriginalQuoteGUID = q.QuoteGUID
        )
        ORDER BY tq.created_date DESC, q.QuoteID DESC
        
        PRINT 'Quote Selection Debug:'
        PRINT '  Found Quote GUID: ' + ISNULL(CAST(@LatestQuoteGuid AS VARCHAR(50)), 'NULL')
        PRINT '  Quote Status ID: ' + ISNULL(CAST(@QuoteStatusID AS VARCHAR(10)), 'NULL')
        
        -- Check if the latest quote is bound
        IF @QuoteStatusID <> 3  -- Not bound
        BEGIN
            SELECT 
                0 AS Result,
                'Cannot cancel - latest quote in chain is not bound' AS Message,
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
        
        -- Step 2: Get the premium from the LATEST quote (the one being cancelled)
        DECLARE @LatestQuoteID INT
        
        -- Get the QuoteID of the latest quote
        SELECT @LatestQuoteID = QuoteID
        FROM tblQuotes
        WHERE QuoteGUID = @LatestQuoteGuid
        
        -- Get the current premium from the latest quote's invoice
        SELECT @PolicyPremium = ISNULL(AnnualPremium, 0)
        FROM tblFin_Invoices
        WHERE QuoteID = @LatestQuoteID
        
        PRINT 'Premium Lookup Debug:'
        PRINT '  Latest Quote ID: ' + CAST(@LatestQuoteID AS VARCHAR(20))
        PRINT '  Policy Premium from Invoice: $' + CAST(@PolicyPremium AS VARCHAR(20))
        
        -- If no invoice found, try to get premium from quote option premiums
        IF @PolicyPremium = 0
        BEGIN
            SELECT @PolicyPremium = ISNULL(SUM(qop.Premium), 0)
            FROM tblQuoteOptionPremiums qop
            INNER JOIN tblQuoteOptions qo ON qop.QuoteOptionGuid = qo.QuoteOptionGuid
            WHERE qo.QuoteGuid = @LatestQuoteGuid
            AND qo.Bound = 1
            
            PRINT '  No invoice found, premium from QuoteOptionPremiums: $' + CAST(@PolicyPremium AS VARCHAR(20))
        END
        
        -- Step 3: Calculate refund based on cancellation type
        IF @RefundAmount IS NOT NULL
        BEGIN
            -- Use provided refund amount (from policy_cancellation_premium)
            -- The ProcessFlatCancellation expects a positive value
            SET @CalculatedRefund = ABS(@RefundAmount)
        END
        ELSE IF @CancellationType = 'flat'
        BEGIN
            -- Flat cancellation = full refund of current premium
            SET @CalculatedRefund = @PolicyPremium
        END
        ELSE  -- 'earned' or pro-rata
        BEGIN
            -- Calculate based on time elapsed
            SET @DaysInPolicy = DATEDIFF(day, @PolicyEffectiveDate, @PolicyExpirationDate)
            SET @DaysElapsed = DATEDIFF(day, @PolicyEffectiveDate, @CancellationDateTime)
            
            -- Calculate unearned premium (refund)
            IF @DaysInPolicy > 0 AND @DaysElapsed >= 0
            BEGIN
                -- Refund = Premium * (Days Remaining / Total Days)
                DECLARE @DaysRemaining INT = @DaysInPolicy - @DaysElapsed
                IF @DaysRemaining > 0
                    SET @CalculatedRefund = @PolicyPremium * (@DaysRemaining * 1.0 / @DaysInPolicy)
                ELSE
                    SET @CalculatedRefund = 0
            END
            ELSE
            BEGIN
                SET @CalculatedRefund = 0
            END
        END
        
        PRINT 'Cancellation calculation:'
        PRINT '  Opportunity ID: ' + CAST(@OpportunityID AS VARCHAR(20))
        PRINT '  Latest Quote GUID: ' + CAST(@LatestQuoteGuid AS VARCHAR(50))
        PRINT '  Latest Quote ID: ' + CAST(@LatestQuoteID AS VARCHAR(20))
        PRINT '  Control No: ' + CAST(@ControlNo AS VARCHAR(20))
        PRINT '  Current Policy Premium: $' + CAST(@PolicyPremium AS VARCHAR(20))
        PRINT '  Cancellation Type: ' + @CancellationType
        PRINT '  RefundAmount Parameter: $' + CAST(ISNULL(@RefundAmount, 0) AS VARCHAR(20))
        PRINT '  Calculated Refund: $' + CAST(ABS(@CalculatedRefund) AS VARCHAR(20))
        PRINT '  Cancellation Date: ' + @CancellationDate
        
        -- Log the exact call to ProcessFlatCancellation
        PRINT ''
        PRINT 'Calling ProcessFlatCancellation with:'
        PRINT 'exec [dbo].[ProcessFlatCancellation]'
        PRINT '    @OriginalQuoteGuid = ''' + CAST(@LatestQuoteGuid AS VARCHAR(50)) + ''','
        PRINT '    @CancellationDate = ''' + CONVERT(VARCHAR(10), @CancellationDateTime, 120) + ''','
        PRINT '    @ReturnPremium = ' + CAST(@CalculatedRefund AS VARCHAR(20))
        PRINT ''
        
        -- Step 4: Call the base ProcessFlatCancellation procedure
        EXEC [dbo].[ProcessFlatCancellation]
            @OriginalQuoteGuid = @LatestQuoteGuid,
            @CancellationDate = @CancellationDateTime,
            @ReturnPremium = @CalculatedRefund,
            @CancellationReason = @Comment,
            @UserGuid = @UserGuid,
            @NewQuoteGuid = @NewQuoteGuid OUTPUT
        
        -- Step 5: Retrieve the QuoteOptionGuid for the new cancellation quote
        SELECT TOP 1 @NewQuoteOptionGuid = QuoteOptionGuid
        FROM tblQuoteOptions
        WHERE QuoteGuid = @NewQuoteGuid
        ORDER BY DateCreated DESC
        
        -- Store the cancellation_id if provided to track this cancellation
        IF @CancellationID IS NOT NULL AND @NewQuoteGuid IS NOT NULL
        BEGIN
            -- Check if record exists for this quote
            IF EXISTS (SELECT 1 FROM tblTritonQuoteData WHERE QuoteGuid = @NewQuoteGuid)
            BEGIN
                -- Update existing record with QuoteOptionGuid
                UPDATE tblTritonQuoteData 
                SET cancellation_id = @CancellationID,
                    QuoteOptionGuid = @NewQuoteOptionGuid,
                    transaction_type = 'cancellation',
                    gross_premium = -ABS(@CalculatedRefund),  -- Store as negative for refund
                    last_updated = GETDATE()
                WHERE QuoteGuid = @NewQuoteGuid
            END
            ELSE
            BEGIN
                -- Insert record with QuoteOptionGuid
                INSERT INTO tblTritonQuoteData (
                    QuoteGuid,
                    QuoteOptionGuid,
                    opportunity_id,
                    cancellation_id,
                    transaction_type,
                    gross_premium,
                    status,
                    created_date,
                    last_updated
                )
                VALUES (
                    @NewQuoteGuid,
                    @NewQuoteOptionGuid,
                    @OpportunityID,
                    @CancellationID,
                    'cancellation',
                    -ABS(@CalculatedRefund),  -- Store as negative for refund
                    'cancelled',
                    GETDATE(),
                    GETDATE()
                )
            END
        END
        
        -- Return success with the new quote guid AND QuoteOptionGuid
        SELECT 
            1 AS Result,
            'Cancellation created successfully' AS Message,
            @NewQuoteGuid AS NewQuoteGuid,
            @NewQuoteOptionGuid AS NewQuoteOptionGuid,
            @LatestQuoteGuid AS OriginalQuoteGuid,
            @ControlNo AS ControlNo,
            @PolicyPremium AS PolicyPremium,
            ABS(@CalculatedRefund) AS RefundAmount,
            @CancellationType AS CancellationType,
            @CancellationDateTime AS CancellationDate
            
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