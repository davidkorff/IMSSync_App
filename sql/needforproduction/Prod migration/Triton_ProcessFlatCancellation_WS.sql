-- =============================================
-- Triton Wrapper for ProcessFlatCancellation
-- Retrieves prior transaction's QuoteGuid and calls base procedure
-- Returns QuoteGuid and QuoteOptionGuid for the cancellation
-- =============================================

CREATE OR ALTER PROCEDURE [dbo].[Triton_ProcessFlatCancellation_WS]
    @OpportunityID INT,
    @CancellationDate VARCHAR(50),
    @ReturnPremium MONEY,
    @CancellationReason VARCHAR(500) = 'Policy Cancellation',
    @UserGuid UNIQUEIDENTIFIER = NULL
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
        
        -- Step 3: Retrieve the QuoteOptionGuid for the new cancellation quote
        -- The ProcessFlatCancellation procedure creates a new QuoteOption record
        PRINT 'STEP 4: Looking for QuoteOptionGuid for NewQuoteGuid: ' + CAST(@NewQuoteGuid AS VARCHAR(50))
        
        SELECT TOP 1 @NewQuoteOptionGuid = QuoteOptionGuid
        FROM tblQuoteOptions
        WHERE QuoteGuid = @NewQuoteGuid
        ORDER BY DateCreated DESC  -- Get the most recently created one
        
        PRINT '  Found QuoteOptionGuid: ' + ISNULL(CAST(@NewQuoteOptionGuid AS VARCHAR(50)), 'NULL')
        PRINT ''
        
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
        
        PRINT 'STEP 6: Returning results'
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
GO

-- =============================================
-- SAMPLE EXECUTION SCRIPT
-- =============================================
/*
-- Test the procedure
EXEC [dbo].[Triton_ProcessFlatCancellation_WS]
    @OpportunityID = 106208,
    @CancellationDate = '08/18/2025',
    @ReturnPremium = 1125,
    @CancellationReason = 'Policy Cancellation'

-- Expected result:
-- Should return Result = 1 with NewQuoteGuid and NewQuoteOptionGuid
*/