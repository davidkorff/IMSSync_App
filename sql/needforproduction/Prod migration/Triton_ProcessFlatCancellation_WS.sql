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
        -- Convert date string to datetime
        SET @CancellationDateTime = CONVERT(DATETIME, @CancellationDate, 101)
        
        -- Step 1: Find the latest quote in the chain for this opportunity_id
        -- First find ANY quote to get the ControlNo
        DECLARE @QuoteStatusID INT
        DECLARE @TransactionTypeID CHAR(1)
        
        -- Get the ControlNo from any quote associated with this opportunity
        SELECT TOP 1 @ControlNo = q.ControlNo
        FROM tblTritonQuoteData tq
        INNER JOIN tblQuotes q ON q.QuoteGUID = tq.QuoteGuid
        WHERE tq.opportunity_id = @OpportunityID
        
        IF @ControlNo IS NULL
        BEGIN
            SELECT 
                0 AS Result,
                'No quotes found for opportunity_id ' + CAST(@OpportunityID AS VARCHAR(20)) AS Message
            RETURN
        END
        
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
        
        PRINT 'Cancellation calculation:'
        PRINT '  Opportunity ID: ' + CAST(@OpportunityID AS VARCHAR(20))
        PRINT '  Latest Quote GUID: ' + CAST(@LatestQuoteGuid AS VARCHAR(50))
        PRINT '  Control No: ' + CAST(@ControlNo AS VARCHAR(20))
        PRINT '  Policy Number: ' + ISNULL(@PolicyNumber, 'N/A')
        PRINT '  Cancellation Date: ' + @CancellationDate
        PRINT '  Return Premium: $' + CAST(@ReturnPremium AS VARCHAR(20))
        
        -- Step 2: Call the base ProcessFlatCancellation procedure
        EXEC [dbo].[ProcessFlatCancellation]
            @OriginalQuoteGuid = @LatestQuoteGuid,
            @CancellationDate = @CancellationDateTime,
            @ReturnPremium = @ReturnPremium,
            @CancellationReason = @CancellationReason,
            @UserGuid = @UserGuid,
            @NewQuoteGuid = @NewQuoteGuid OUTPUT
        
        -- Step 3: Retrieve the QuoteOptionGuid for the new cancellation quote
        -- The ProcessFlatCancellation procedure creates a new QuoteOption record
        SELECT TOP 1 @NewQuoteOptionGuid = QuoteOptionGuid
        FROM tblQuoteOptions
        WHERE QuoteGuid = @NewQuoteGuid
        ORDER BY DateCreated DESC  -- Get the most recently created one
        
        -- Step 4: Store the cancellation result in tblTritonQuoteData
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
    @CancellationReason = 'Policy Cancellation',
    @CancellationID = 12345

-- Expected result:
-- Should return Result = 1 with NewQuoteGuid and NewQuoteOptionGuid
*/