-- =============================================
-- Author:      RSG Integration
-- Create date: 2025-08-07
-- Description: Cancels a policy for Triton
--              Uses spCopyQuote (native IMS procedure) like Ascot does
-- =============================================

USE [IMS_DEV]
GO

-- Drop procedure if it exists
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Triton_CancelPolicy_WS]') AND type in (N'P', N'PC'))
DROP PROCEDURE [dbo].[Triton_CancelPolicy_WS]
GO

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE PROCEDURE [dbo].[Triton_CancelPolicy_WS]
    @OpportunityID INT = NULL,
    @QuoteGuid UNIQUEIDENTIFIER = NULL,
    @UserGuid UNIQUEIDENTIFIER,
    @CancellationType VARCHAR(20) = 'flat',  -- 'flat' or 'earned'
    @CancellationDate VARCHAR(50),
    @ReasonCode INT = 30,  -- Default to "Insured Request"
    @Comment VARCHAR(255) = 'Policy Cancellation',
    @RefundAmount MONEY = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Variables
    DECLARE @Result INT = 0
    DECLARE @Message VARCHAR(MAX) = ''
    DECLARE @OriginalQuoteGuid UNIQUEIDENTIFIER
    DECLARE @CancellationQuoteGuid UNIQUEIDENTIFIER
    DECLARE @CancellationQuoteID INT
    DECLARE @PolicyNumber VARCHAR(50)
    DECLARE @CancellationDateTime DATETIME
    DECLARE @ControlNumber INT
    DECLARE @QuoteOptionGuid UNIQUEIDENTIFIER
    DECLARE @NewQuoteOptionGuid UNIQUEIDENTIFIER
    DECLARE @PolicyEffectiveDate DATETIME
    DECLARE @PolicyExpirationDate DATETIME
    DECLARE @QuoteStatusID INT = 7  -- Cancelled
    DECLARE @CalcType CHAR(1)
    
    BEGIN TRY
        BEGIN TRANSACTION
        
        -- Convert date string to datetime
        SET @CancellationDateTime = CONVERT(DATETIME, @CancellationDate, 101)
        
        -- Set calculation type based on cancellation type
        IF @CancellationType = 'flat'
            SET @CalcType = 'F'  -- Flat
        ELSE
            SET @CalcType = 'P'  -- Pro-rata
        
        -- Step 1: Find the original quote
        IF @OpportunityID IS NOT NULL
        BEGIN
            -- Find by opportunity_id - join with tblQuotes to ensure quote exists
            SELECT TOP 1 
                @OriginalQuoteGuid = tq.QuoteGuid,
                @PolicyNumber = tq.policy_number,
                @QuoteOptionGuid = tq.QuoteOptionGuid,
                @ControlNumber = q.ControlNo,
                @PolicyEffectiveDate = q.EffectiveDate,
                @PolicyExpirationDate = q.ExpirationDate
            FROM tblTritonQuoteData tq
            INNER JOIN tblQuotes q ON q.QuoteGUID = tq.QuoteGuid
            WHERE tq.opportunity_id = @OpportunityID
            AND tq.status = 'bound'  -- Only cancel bound policies
            ORDER BY tq.created_date DESC
        END
        ELSE IF @QuoteGuid IS NOT NULL
        BEGIN
            -- Find by QuoteGuid
            SET @OriginalQuoteGuid = @QuoteGuid
            
            SELECT TOP 1 
                @PolicyNumber = PolicyNumber,
                @ControlNumber = ControlNo,
                @PolicyEffectiveDate = EffectiveDate,
                @PolicyExpirationDate = ExpirationDate
            FROM tblQuotes
            WHERE QuoteGUID = @QuoteGuid
            
            -- Get the quote option
            SELECT TOP 1 @QuoteOptionGuid = QuoteOptionGUID
            FROM tblQuoteOptions
            WHERE QuoteGUID = @QuoteGuid
        END
        
        IF @OriginalQuoteGuid IS NULL
        BEGIN
            SET @Result = 0
            SET @Message = 'No bound policy found for cancellation'
            GOTO ReturnResult
        END
        
        -- Validate cancellation date
        -- Can't cancel before effective date
        IF @CancellationDateTime < @PolicyEffectiveDate
        BEGIN
            SET @CancellationDateTime = @PolicyEffectiveDate
        END
        
        -- Can't cancel after expiration
        IF @CancellationDateTime > @PolicyExpirationDate
        BEGIN
            SET @Result = 0
            SET @Message = 'Cannot cancel after policy expiration date'
            GOTO ReturnResult
        END
        
        -- Validate reason code
        IF NOT EXISTS (SELECT 1 FROM lstQuoteStatusReasons WHERE QuoteStatusID = 7 AND ID = @ReasonCode)
        BEGIN
            -- Default to a valid reason if the provided one doesn't exist
            SELECT TOP 1 @ReasonCode = ID 
            FROM lstQuoteStatusReasons 
            WHERE QuoteStatusID = 7
            ORDER BY ID
            
            IF @ReasonCode IS NULL
            BEGIN
                SET @Result = 0
                SET @Message = 'No valid cancellation reason codes found'
                GOTO ReturnResult
            END
        END
        
        -- Step 2: Use spCopyQuote to create the cancellation (like Ascot does)
        EXEC spCopyQuote
            @QuoteGuid = @OriginalQuoteGuid,
            @TransactionTypeID = 'C',  -- Cancellation
            @QuoteStatusID = @QuoteStatusID,  -- 7 = Cancelled
            @QuoteStatusReasonID = @ReasonCode,
            @EndorsementEffective = @CancellationDateTime,
            @EndtRequestDate = GETDATE(),
            @EndorsementComment = @Comment,
            @EndorsementCalculationType = @CalcType,
            @copyOptions = 0
        
        -- Get the newly created cancellation quote
        SELECT TOP 1 
            @CancellationQuoteGuid = QuoteGUID,
            @CancellationQuoteID = QuoteID
        FROM tblQuotes
        WHERE ControlNo = @ControlNumber
        AND TransactionTypeID = 'C'
        ORDER BY QuoteID DESC
        
        -- Get the new quote option that was created
        SELECT TOP 1 
            @NewQuoteOptionGuid = QuoteOptionGUID
        FROM tblQuoteOptions
        WHERE QuoteGUID = @CancellationQuoteGuid
        
        -- Step 3: Handle refund amount for flat cancellations
        IF @CancellationType = 'flat' AND @RefundAmount IS NOT NULL AND @NewQuoteOptionGuid IS NOT NULL
        BEGIN
            -- Get the charge code for premium
            DECLARE @PremiumChargeCode INT
            SELECT TOP 1 @PremiumChargeCode = ChargeCode
            FROM tblFin_PolicyCharges
            WHERE ChargeID = 'PREM'
            
            IF @PremiumChargeCode IS NOT NULL
            BEGIN
                -- Insert negative premium (refund)
                INSERT INTO tblQuoteOptionPremiums (
                    QuoteOptionGuid,
                    ChargeCode,
                    OfficeID,
                    Premium,
                    AnnualPremium,
                    Commissionable,
                    Added
                )
                VALUES (
                    @NewQuoteOptionGuid,
                    @PremiumChargeCode,
                    1,  -- Default office ID
                    -ABS(@RefundAmount),  -- Ensure negative for refund
                    -ABS(@RefundAmount),  -- Annual = total for cancellation
                    1,  -- Commissionable
                    GETDATE()
                )
            END
        END
        
        -- Step 4: Update tblTritonQuoteData for the cancellation
        IF @OpportunityID IS NOT NULL
        BEGIN
            INSERT INTO tblTritonQuoteData (
                QuoteGuid,
                QuoteOptionGuid,
                opportunity_id,
                policy_number,
                transaction_type,
                transaction_date,
                gross_premium,
                cancellation_effective_date,
                cancellation_reason,
                cancellation_type,
                status,
                created_date,
                last_updated,
                -- Copy these from original
                renewal_of_quote_guid,
                class_of_business,
                program_name,
                underwriter_name,
                producer_name,
                effective_date,
                expiration_date,
                insured_name,
                insured_state,
                insured_zip
            )
            SELECT 
                @CancellationQuoteGuid,
                @NewQuoteOptionGuid,
                @OpportunityID,
                policy_number,
                'cancellation',
                CONVERT(VARCHAR(50), GETDATE(), 101),
                CASE WHEN @RefundAmount IS NOT NULL THEN -ABS(@RefundAmount) ELSE 0 END,
                @CancellationDate,
                @Comment,
                @CancellationType,
                'cancelled',
                GETDATE(),
                GETDATE(),
                -- Copy from original
                renewal_of_quote_guid,
                class_of_business,
                program_name,
                underwriter_name,
                producer_name,
                effective_date,
                expiration_date,
                insured_name,
                insured_state,
                insured_zip
            FROM tblTritonQuoteData
            WHERE QuoteGuid = @OriginalQuoteGuid
        END
        
        COMMIT TRANSACTION
        
        -- Return success
        SET @Result = 1
        SET @Message = 'Policy cancelled successfully'
        
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION
            
        SET @Result = 0
        SET @Message = ERROR_MESSAGE()
    END CATCH
    
ReturnResult:
    -- Return result set
    SELECT 
        @Result AS Result,
        @Message AS Message,
        @CancellationQuoteGuid AS CancellationQuoteGuid,
        @OriginalQuoteGuid AS OriginalQuoteGuid,
        @PolicyNumber AS PolicyNumber,
        @RefundAmount AS RefundAmount,
        @NewQuoteOptionGuid AS QuoteOptionGuid
END
GO

PRINT 'Procedure [dbo].[Triton_CancelPolicy_WS] created successfully'