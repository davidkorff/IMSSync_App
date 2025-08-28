CREATE or ALTER   PROCEDURE [dbo].[Triton_ProcessFlatCancellation_WS]
    @OpportunityID INT,
    @CancellationDate VARCHAR(50),
    @ReturnPremium MONEY,
    @CancellationReason VARCHAR(500) = 'Policy Cancellation',
    @UserGuid UNIQUEIDENTIFIER = NULL,
    @PolicyEffectiveDate VARCHAR(50) = NULL,  -- For flat cancel detection
    @MarketSegmentCode VARCHAR(10) = NULL,    -- For auto-apply fees (RT/WL)
    @PolicyFee MONEY = NULL                   -- Policy fee to apply as negative if flat cancel
AS
BEGIN
    SET NOCOUNT ON;
   
    DECLARE @Result INT = 0
    DECLARE @Message VARCHAR(MAX) = ''
    DECLARE @LatestQuoteGuid UNIQUEIDENTIFIER
    DECLARE @ControlNo INT
    DECLARE @PolicyNumber VARCHAR(50)
    DECLARE @CancellationDateTime DATETIME
    DECLARE @NewQuoteGuid UNIQUEIDENTIFIER
    DECLARE @NewQuoteOptionGuid UNIQUEIDENTIFIER
   
    BEGIN TRY
        PRINT '=========================================='
        PRINT 'Triton_ProcessFlatCancellation_WS START'
        PRINT '=========================================='
        PRINT 'Input Parameters:'
        PRINT '  OpportunityID: ' + CAST(@OpportunityID AS VARCHAR(20))
        PRINT '  CancellationDate: ' + @CancellationDate
        PRINT '  ReturnPremium: $' + CAST(@ReturnPremium AS VARCHAR(20))
        PRINT '  CancellationReason: ' + ISNULL(@CancellationReason, 'NULL')
        PRINT '  UserGuid: ' + ISNULL(CAST(@UserGuid AS VARCHAR(50)), 'NULL')
        PRINT ''
       
        -- Convert date string to datetime
        SET @CancellationDateTime = CONVERT(DATETIME, @CancellationDate, 101)
        PRINT 'Converted CancellationDate to: ' + CAST(@CancellationDateTime AS VARCHAR(50))
        PRINT ''
       
        -- Step 1: Find the latest quote in the chain for this opportunity_id
        -- First find ANY quote to get the ControlNo
        DECLARE @QuoteStatusID INT
        DECLARE @TransactionTypeID CHAR(1)
        DECLARE @QuoteCount INT
       
        PRINT 'STEP 1: Looking for ControlNo using OpportunityID ' + CAST(@OpportunityID AS VARCHAR(20))
        PRINT 'Searching in tblTritonQuoteData joined with tblQuotes...'
       
        -- First, let's see what's in tblTritonQuoteData for this opportunity
        SELECT @QuoteCount = COUNT(*)
        FROM tblTritonQuoteData
        WHERE opportunity_id = @OpportunityID
       
        PRINT 'Found ' + CAST(@QuoteCount AS VARCHAR(10)) + ' records in tblTritonQuoteData for OpportunityID ' + CAST(@OpportunityID AS VARCHAR(20))
       
        -- Show what we find
        PRINT 'Records in tblTritonQuoteData for this opportunity:'
        SELECT QuoteGuid, opportunity_id, transaction_type, status
        FROM tblTritonQuoteData
        WHERE opportunity_id = @OpportunityID
       
        -- Get the ControlNo from any quote associated with this opportunity
        SELECT TOP 1 @ControlNo = q.ControlNo
        FROM tblTritonQuoteData tq
        INNER JOIN tblQuotes q ON q.QuoteGUID = tq.QuoteGuid
        WHERE tq.opportunity_id = @OpportunityID
       
        IF @ControlNo IS NULL
        BEGIN
            PRINT 'ERROR: No ControlNo found for OpportunityID ' + CAST(@OpportunityID AS VARCHAR(20))
            PRINT 'This means no quotes in tblQuotes match the QuoteGuids in tblTritonQuoteData'
            SELECT
                0 AS Result,
                'No quotes found for opportunity_id ' + CAST(@OpportunityID AS VARCHAR(20)) AS Message
            RETURN
        END
       
        PRINT 'Found ControlNo: ' + CAST(@ControlNo AS VARCHAR(20))
        PRINT ''
       
        PRINT 'STEP 2: Finding latest quote in chain for ControlNo ' + CAST(@ControlNo AS VARCHAR(20))
        PRINT 'Looking for quote that is NOT an OriginalQuoteGuid for any other quote...'
       
        -- Show all quotes in the chain for debugging
        PRINT 'All quotes in chain for ControlNo ' + CAST(@ControlNo AS VARCHAR(20)) + ':'
        SELECT
            QuoteGUID,
            OriginalQuoteGUID,
            QuoteStatusID,
            TransactionTypeID,
            EndorsementNum,
            PolicyNumber,
            DateCreated
        FROM tblQuotes
        WHERE ControlNo = @ControlNo
        ORDER BY QuoteID
       
        -- Now find the ACTUAL latest quote in the chain (including cancelled ones)
        SELECT TOP 1
            @LatestQuoteGuid = q.QuoteGUID,
            @QuoteStatusID = q.QuoteStatusID,
            @PolicyNumber = q.PolicyNumber,
            @TransactionTypeID = q.TransactionTypeID
        FROM tblQuotes q
        WHERE q.ControlNo = @ControlNo
        AND NOT EXISTS (
            -- Make sure this quote is not the original for another quote (find the end of the chain)
            SELECT 1
            FROM tblQuotes q3
            WHERE q3.OriginalQuoteGUID = q.QuoteGUID
        )
        ORDER BY q.QuoteID DESC
       
        PRINT ''
        PRINT 'Found Latest Quote:'
        PRINT '  QuoteGuid: ' + CAST(@LatestQuoteGuid AS VARCHAR(50))
        PRINT '  QuoteStatusID: ' + CAST(@QuoteStatusID AS VARCHAR(10))
        PRINT '  TransactionTypeID: ' + ISNULL(@TransactionTypeID, 'NULL')
        PRINT '  PolicyNumber: ' + @PolicyNumber
        PRINT ''
       
        -- Check if already cancelled
        IF @TransactionTypeID = 'C' OR @QuoteStatusID = 7
        BEGIN
            SELECT
                0 AS Result,
                'Policy is already cancelled' AS Message,
                @LatestQuoteGuid AS LatestQuoteGuid,
                @PolicyNumber AS PolicyNumber
            RETURN
        END
       
        -- Check if the latest quote is bound
        IF @QuoteStatusID NOT IN (3, 4)  -- Not bound or issued
        BEGIN
            SELECT
                0 AS Result,
                'Cannot create cancellation - latest quote in chain is not bound' AS Message,
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
       
        PRINT 'STEP 3: Calling ProcessFlatCancellation with:'
        PRINT '  @OriginalQuoteGuid = ' + CAST(@LatestQuoteGuid AS VARCHAR(50))
        PRINT '  @CancellationDate = ' + CAST(@CancellationDateTime AS VARCHAR(50))
        PRINT '  @ReturnPremium = ' + CAST(@ReturnPremium AS VARCHAR(20))
        PRINT '  @CancellationReason = ' + @CancellationReason
        PRINT '  @UserGuid = ' + ISNULL(CAST(@UserGuid AS VARCHAR(50)), 'NULL')
        PRINT ''
       
        -- Step 2: Call the base ProcessFlatCancellation procedure
        EXEC [dbo].[ProcessFlatCancellation]
            @OriginalQuoteGuid = @LatestQuoteGuid,
            @CancellationDate = @CancellationDateTime,
            @ReturnPremium = @ReturnPremium,
            @CancellationReason = @CancellationReason,
            @UserGuid = @UserGuid,
            @NewQuoteGuid = @NewQuoteGuid OUTPUT
       
        PRINT 'ProcessFlatCancellation completed.'
        PRINT '  NewQuoteGuid returned: ' + ISNULL(CAST(@NewQuoteGuid AS VARCHAR(50)), 'NULL')
        PRINT ''
       
        -- Step 3: Get the QuoteOptionGuid first (needed for fee application later)
        IF @NewQuoteGuid IS NOT NULL
        BEGIN
            PRINT 'STEP 3: Getting QuoteOptionGuid for fee application'
           
            -- Get the QuoteOptionGuid
            SELECT TOP 1 @NewQuoteOptionGuid = QuoteOptionGuid
            FROM tblQuoteOptions
            WHERE QuoteGuid = @NewQuoteGuid
            ORDER BY DateCreated DESC
            
            PRINT '  Found QuoteOptionGuid: ' + ISNULL(CAST(@NewQuoteOptionGuid AS VARCHAR(50)), 'NULL')
           
            -- Apply auto-fees for RT market segment
            IF @MarketSegmentCode = 'RT' AND @NewQuoteOptionGuid IS NOT NULL
            BEGIN
                PRINT '  RT market segment - applying auto fees'
               
                IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'spAutoApplyFees')
                BEGIN
                    EXEC dbo.spAutoApplyFees
                        @quoteOptionGuid = @NewQuoteOptionGuid;
                   
                    PRINT '  Auto-applied fees for RT cancellation'
                END
            END
            ELSE IF @MarketSegmentCode = 'WL'
            BEGIN
                PRINT '  WL market segment - skipping auto fees'
            END
        END
       
        -- Step 4 removed - QuoteOptionGuid already retrieved in Step 3
       
        -- Step 4: Store the cancellation result in tblTritonQuoteData
        PRINT 'STEP 5: Storing result in tblTritonQuoteData'
        IF @NewQuoteGuid IS NOT NULL
        BEGIN
            -- Check if record exists for this quote
            IF EXISTS (SELECT 1 FROM tblTritonQuoteData WHERE QuoteGuid = @NewQuoteGuid)
            BEGIN
                -- Update existing record with QuoteOptionGuid
                UPDATE tblTritonQuoteData
                SET QuoteOptionGuid = @NewQuoteOptionGuid,
                    transaction_type = 'cancellation',
                    status = 'cancelled',
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
                    transaction_type,
                    status,
                    created_date,
                    last_updated
                )
                VALUES (
                    @NewQuoteGuid,
                    @NewQuoteOptionGuid,
                    @OpportunityID,
                    'cancellation',
                    'cancelled',
                    GETDATE(),
                    GETDATE()
                )
            END
        END
       
        -- STEP 6: Apply fees as the VERY LAST STEP before returning (so they're there when quote is bound)
        IF @NewQuoteGuid IS NOT NULL
        BEGIN
            PRINT 'STEP 6: Final fee application before returning'
            
            -- Apply negative policy fee for flat cancellations
            IF @PolicyFee IS NOT NULL AND @PolicyFee > 0
                AND @PolicyEffectiveDate IS NOT NULL
                AND @CancellationDate IS NOT NULL
            BEGIN
                -- Check if this is a flat cancel (cancellation date = effective date)
                DECLARE @FinalCancellationDateConverted DATE;
                DECLARE @FinalEffectiveDateConverted DATE;
               
                -- Convert dates for comparison
                -- Use the already converted datetime for cancellation date
                SET @FinalCancellationDateConverted = CAST(@CancellationDateTime AS DATE);
               
                -- Try to convert effective date (could be MM/DD/YYYY or YYYY-MM-DD)
                SET @FinalEffectiveDateConverted = TRY_CONVERT(DATE, @PolicyEffectiveDate, 101); -- Try MM/DD/YYYY
                IF @FinalEffectiveDateConverted IS NULL
                BEGIN
                    SET @FinalEffectiveDateConverted = TRY_CONVERT(DATE, @PolicyEffectiveDate); -- Try YYYY-MM-DD
                END
                
                -- Debug output
                PRINT '  Final PolicyEffectiveDate input: ' + ISNULL(@PolicyEffectiveDate, 'NULL')
                PRINT '  Final CancellationDate converted: ' + ISNULL(CAST(@FinalCancellationDateConverted AS VARCHAR(20)), 'NULL')
                PRINT '  Final EffectiveDate converted: ' + ISNULL(CAST(@FinalEffectiveDateConverted AS VARCHAR(20)), 'NULL')
               
                -- If dates match, this is a flat cancel - apply negative policy fee
                IF @FinalCancellationDateConverted = @FinalEffectiveDateConverted
                BEGIN
                    PRINT '  Flat cancel detected - applying negative policy fee of $' + CAST(@PolicyFee AS VARCHAR(20))
                   
                    -- Apply negative policy fee directly to tblQuoteOptionCharges
                    DECLARE @FinalNegativePolicyFee MONEY = -1 * ABS(@PolicyFee);
                    DECLARE @Policy_FeeCode SMALLINT = 12374;  -- Charge code for Policy Fee
                    DECLARE @CompanyFeeID INT = 37277712;  -- Triton Policy Fee CompanyFeeID
                    DECLARE @OfficeID INT;
                    DECLARE @CompanyLineGuid UNIQUEIDENTIFIER;
                    
                    -- Get OfficeID from the quote
                    SELECT @OfficeID = tblClientOffices.OfficeID
                    FROM tblQuotes q
                    INNER JOIN tblQuoteOptions qo ON q.QuoteGuid = qo.QuoteGuid
                    INNER JOIN tblClientOffices ON q.QuotingLocationGuid = tblClientOffices.OfficeGuid
                    WHERE qo.QuoteOptionGuid = @NewQuoteOptionGuid;
                    
                    -- Get CompanyLineGuid from the quote
                    SELECT @CompanyLineGuid = CompanyLineGuid
                    FROM tblQuotes
                    WHERE QuoteGuid = @NewQuoteGuid;
                    
                    -- Check if the charge already exists
                    IF EXISTS (
                        SELECT 1
                        FROM tblQuoteOptionCharges
                        WHERE QuoteOptionGUID = @NewQuoteOptionGuid
                        AND ChargeCode = @Policy_FeeCode
                    )
                    BEGIN
                        -- Update existing charge with the negative fee value
                        UPDATE tblQuoteOptionCharges
                        SET FlatRate = @FinalNegativePolicyFee,
                            CompanyFeeID = @CompanyFeeID,
                            Payable = 1,
                            AutoApplied = 0
                        WHERE QuoteOptionGUID = @NewQuoteOptionGuid
                        AND ChargeCode = @Policy_FeeCode;
                       
                        PRINT '  Updated Policy Fee to $' + CAST(@FinalNegativePolicyFee AS VARCHAR(20)) +
                              ' for QuoteOption ' + CAST(@NewQuoteOptionGuid AS VARCHAR(50));
                    END
                    ELSE
                    BEGIN
                        -- Insert new charge record for the negative policy fee
                        INSERT INTO tblQuoteOptionCharges (
                            QuoteOptionGuid,
                            CompanyFeeID,
                            ChargeCode,
                            OfficeID,
                            CompanyLineGuid,
                            FeeTypeID,
                            Payable,
                            FlatRate,
                            Splittable,
                            AutoApplied
                        )
                        VALUES (
                            @NewQuoteOptionGuid,
                            @CompanyFeeID,
                            @Policy_FeeCode,
                            ISNULL(@OfficeID, 1),  -- Default to 1 if not found
                            @CompanyLineGuid,
                            2,  -- Flat fee type
                            1,  -- Payable
                            @FinalNegativePolicyFee,
                            0,  -- Not splittable
                            0   -- Not auto-applied (manual)
                        );
                       
                        PRINT '  Inserted Policy Fee of $' + CAST(@FinalNegativePolicyFee AS VARCHAR(20)) +
                              ' for QuoteOption ' + CAST(@NewQuoteOptionGuid AS VARCHAR(50));
                    END
                    
                    PRINT '  Applied negative policy fee to cancellation directly in tblQuoteOptionCharges'
                END
                ELSE
                BEGIN
                    PRINT '  Not a flat cancel (dates do not match) - skipping policy fee'
                END
            END
        END
        
        PRINT 'STEP 7: Returning results'
        PRINT '=========================================='
        PRINT 'Triton_ProcessFlatCancellation_WS END'
        PRINT '=========================================='
        PRINT ''
       
        -- Return success with the new quote guid AND QuoteOptionGuid
        SELECT
            1 AS Result,
            'Cancellation created successfully' AS Message,
            @NewQuoteGuid AS NewQuoteGuid,
            @NewQuoteOptionGuid AS NewQuoteOptionGuid,
            @LatestQuoteGuid AS OriginalQuoteGuid,
            @ControlNo AS ControlNo,
            @PolicyNumber AS PolicyNumber,
            @ReturnPremium AS ReturnPremium,
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






