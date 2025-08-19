-- =============================================
-- Triton Wrapper for ProcessFlatReinstatement
-- Retrieves cancelled transaction's QuoteGuid and calls base procedure
-- Returns QuoteGuid and QuoteOptionGuid for the reinstatement
-- =============================================

CREATE OR ALTER PROCEDURE [dbo].[Triton_ProcessFlatReinstatement_WS]
    @OpportunityID INT,
    @ReinstatementComment VARCHAR(500) = 'Policy Reinstatement',
    @UserGuid UNIQUEIDENTIFIER = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @Result INT = 0
    DECLARE @Message VARCHAR(MAX) = ''
    DECLARE @CancelledQuoteGuid UNIQUEIDENTIFIER
    DECLARE @LatestQuoteGuid UNIQUEIDENTIFIER
    DECLARE @ControlNo INT
    DECLARE @PolicyNumber VARCHAR(50)
    DECLARE @ReinstatementEffectiveDate DATETIME
    DECLARE @ReinstatementEffectiveDateStr VARCHAR(50)
    DECLARE @ReinstatementPremium MONEY
    DECLARE @NewQuoteGuid UNIQUEIDENTIFIER
    DECLARE @NewQuoteOptionGuid UNIQUEIDENTIFIER
    DECLARE @QuoteID INT
    DECLARE @QuoteStatusID INT
    DECLARE @TransactionTypeID CHAR(1)
    
    BEGIN TRY
        PRINT '=========================================='
        PRINT 'Triton_ProcessFlatReinstatement_WS START'
        PRINT '=========================================='
        PRINT 'Input Parameters:'
        PRINT '  OpportunityID: ' + CAST(@OpportunityID AS VARCHAR(20))
        PRINT '  ReinstatementComment: ' + ISNULL(@ReinstatementComment, 'NULL')
        PRINT '  UserGuid: ' + ISNULL(CAST(@UserGuid AS VARCHAR(50)), 'NULL')
        PRINT ''
        
        -- Step 1: Find the latest quote in the chain for this opportunity_id
        -- First find ANY quote to get the ControlNo
        PRINT 'STEP 1: Looking for ControlNo using OpportunityID ' + CAST(@OpportunityID AS VARCHAR(20))
        PRINT 'Searching in tblTritonQuoteData joined with tblQuotes...'
        
        -- Get the ControlNo from any quote associated with this opportunity
        SELECT TOP 1 @ControlNo = q.ControlNo
        FROM tblTritonQuoteData tq
        INNER JOIN tblQuotes q ON q.QuoteGUID = tq.QuoteGuid
        WHERE tq.opportunity_id = @OpportunityID
        
        IF @ControlNo IS NULL
        BEGIN
            PRINT 'ERROR: No ControlNo found for OpportunityID ' + CAST(@OpportunityID AS VARCHAR(20))
            SELECT 
                0 AS Result,
                'No quotes found for opportunity_id ' + CAST(@OpportunityID AS VARCHAR(20)) AS Message
            RETURN
        END
        
        PRINT 'Found ControlNo: ' + CAST(@ControlNo AS VARCHAR(20))
        PRINT ''
        
        PRINT 'STEP 2: Finding latest quote in chain for ControlNo ' + CAST(@ControlNo AS VARCHAR(20))
        PRINT 'Looking for quote that is NOT an OriginalQuoteGuid for any other quote...'
        
        -- Now find the ACTUAL latest quote in the chain
        SELECT TOP 1 
            @LatestQuoteGuid = q.QuoteGUID,
            @QuoteStatusID = q.QuoteStatusID,
            @PolicyNumber = q.PolicyNumber,
            @TransactionTypeID = q.TransactionTypeID,
            @QuoteID = q.QuoteID
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
        PRINT '  QuoteID: ' + CAST(@QuoteID AS VARCHAR(20))
        PRINT '  QuoteStatusID: ' + CAST(@QuoteStatusID AS VARCHAR(10))
        PRINT '  TransactionTypeID: ' + ISNULL(@TransactionTypeID, 'NULL')
        PRINT '  PolicyNumber: ' + @PolicyNumber
        PRINT ''
        
        -- Check if the latest quote is cancelled
        IF @TransactionTypeID != 'C' OR @QuoteStatusID != 7
        BEGIN
            SELECT 
                0 AS Result,
                'Policy is not cancelled - cannot reinstate' AS Message,
                @LatestQuoteGuid AS LatestQuoteGuid,
                @PolicyNumber AS PolicyNumber
            RETURN
        END
        
        -- Store the cancelled quote guid
        SET @CancelledQuoteGuid = @LatestQuoteGuid
        
        -- Step 3: Get the EndorsementEffective date from the cancelled quote
        -- Format it from '2025-12-15 00:00:00' to '2025-12-15'
        PRINT 'STEP 3: Getting EndorsementEffective date from cancelled quote...'
        
        SELECT @ReinstatementEffectiveDate = EndorsementEffective
        FROM tblQuotes
        WHERE QuoteGUID = @CancelledQuoteGuid
        
        IF @ReinstatementEffectiveDate IS NULL
        BEGIN
            -- If no EndorsementEffective, use current date
            SET @ReinstatementEffectiveDate = GETDATE()
        END
        
        -- Format the date as 'YYYY-MM-DD'
        SET @ReinstatementEffectiveDateStr = CONVERT(VARCHAR(10), @ReinstatementEffectiveDate, 120)
        
        PRINT '  EndorsementEffective from cancelled quote: ' + CAST(@ReinstatementEffectiveDate AS VARCHAR(50))
        PRINT '  Formatted ReinstatementEffectiveDate: ' + @ReinstatementEffectiveDateStr
        PRINT ''
        
        -- Step 4: Get the AnnualPremium from tblFin_Invoices for the reinstatement premium
        PRINT 'STEP 4: Getting AnnualPremium from tblFin_Invoices for QuoteID: ' + CAST(@QuoteID AS VARCHAR(20))
        
        SELECT @ReinstatementPremium = ABS(AnnualPremium)
        FROM tblFin_Invoices
        WHERE QuoteID = @QuoteID
        
        -- If no invoice found, try to get premium from quote options
        IF @ReinstatementPremium IS NULL OR @ReinstatementPremium = 0
        BEGIN
            PRINT '  No invoice found, checking tblQuoteOptions for premium...'
            SELECT @ReinstatementPremium = ABS(Premium)
            FROM tblQuoteOptions
            WHERE QuoteGuid = @CancelledQuoteGuid
        END
        
        -- If still no premium, use a default (this should rarely happen)
        IF @ReinstatementPremium IS NULL OR @ReinstatementPremium = 0
        BEGIN
            PRINT '  WARNING: No premium found, using default value of 1000'
            SET @ReinstatementPremium = 1000
        END
        
        PRINT '  ReinstatementPremium: $' + CAST(@ReinstatementPremium AS VARCHAR(20))
        PRINT ''
        
        PRINT 'STEP 5: Calling ProcessFlatReinstatement with:'
        PRINT '  @OpportunityID = ' + CAST(@OpportunityID AS VARCHAR(20))
        PRINT '  @CancelledQuoteGuid = ' + CAST(@CancelledQuoteGuid AS VARCHAR(50))
        PRINT '  @ReinstatementPremium = ' + CAST(@ReinstatementPremium AS VARCHAR(20))
        PRINT '  @ReinstatementEffectiveDate = ' + @ReinstatementEffectiveDateStr
        PRINT '  @ReinstatementComment = ' + @ReinstatementComment
        PRINT '  @UserGuid = ' + ISNULL(CAST(@UserGuid AS VARCHAR(50)), 'NULL')
        PRINT ''
        
        -- Step 5: Call the base ProcessFlatReinstatement procedure
        EXEC [dbo].[ProcessFlatReinstatement]
            @OpportunityID = @OpportunityID,
            @CancelledQuoteGuid = @CancelledQuoteGuid,
            @ReinstatementPremium = @ReinstatementPremium,
            @ReinstatementEffectiveDate = @ReinstatementEffectiveDate,
            @ReinstatementComment = @ReinstatementComment,
            @UserGuid = @UserGuid,
            @NewQuoteGuid = @NewQuoteGuid OUTPUT
        
        PRINT 'ProcessFlatReinstatement completed.'
        PRINT '  NewQuoteGuid returned: ' + ISNULL(CAST(@NewQuoteGuid AS VARCHAR(50)), 'NULL')
        PRINT ''
        
        -- Step 6: Retrieve the QuoteOptionGuid for the new reinstatement quote
        PRINT 'STEP 6: Looking for QuoteOptionGuid for NewQuoteGuid: ' + CAST(@NewQuoteGuid AS VARCHAR(50))
        
        SELECT TOP 1 @NewQuoteOptionGuid = QuoteOptionGuid
        FROM tblQuoteOptions
        WHERE QuoteGuid = @NewQuoteGuid
        ORDER BY DateCreated DESC  -- Get the most recently created one
        
        PRINT '  Found QuoteOptionGuid: ' + ISNULL(CAST(@NewQuoteOptionGuid AS VARCHAR(50)), 'NULL')
        PRINT ''
        
        -- Step 7: Store the reinstatement result in tblTritonQuoteData
        PRINT 'STEP 7: Storing result in tblTritonQuoteData'
        IF @NewQuoteGuid IS NOT NULL
        BEGIN
            -- Check if record exists for this quote
            IF EXISTS (SELECT 1 FROM tblTritonQuoteData WHERE QuoteGuid = @NewQuoteGuid)
            BEGIN
                -- Update existing record with QuoteOptionGuid
                UPDATE tblTritonQuoteData 
                SET QuoteOptionGuid = @NewQuoteOptionGuid,
                    transaction_type = 'reinstatement',
                    status = 'reinstated',
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
                    'reinstatement',
                    'reinstated',
                    GETDATE(),
                    GETDATE()
                )
            END
        END
        
        PRINT 'STEP 8: Returning results'
        PRINT '=========================================='
        PRINT 'Triton_ProcessFlatReinstatement_WS END'
        PRINT '=========================================='
        PRINT ''
        
        -- Return success with the new quote guid AND QuoteOptionGuid
        SELECT 
            1 AS Result,
            'Reinstatement created successfully' AS Message,
            @NewQuoteGuid AS NewQuoteGuid,
            @NewQuoteOptionGuid AS NewQuoteOptionGuid,
            @CancelledQuoteGuid AS CancelledQuoteGuid,
            @ControlNo AS ControlNo,
            @PolicyNumber AS PolicyNumber,
            @ReinstatementPremium AS ReinstatementPremium,
            @ReinstatementEffectiveDate AS ReinstatementEffectiveDate
            
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
EXEC [dbo].[Triton_ProcessFlatReinstatement_WS]
    @OpportunityID = 106208,
    @ReinstatementComment = 'Policy Reinstatement'

-- Expected result:
-- Should return Result = 1 with NewQuoteGuid and NewQuoteOptionGuid
*/