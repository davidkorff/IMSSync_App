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
    DECLARE @DateRequested DATETIME
    DECLARE @OriginalPremium MONEY
    DECLARE @CalculatedRefund MONEY
    DECLARE @DaysInPolicy INT
    DECLARE @DaysElapsed INT
    
    BEGIN TRY
        BEGIN TRANSACTION
        
        -- Set request date
        SET @DateRequested = GETDATE()
        
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
        
        -- Get the original premium from the policy
        SELECT @OriginalPremium = SUM(ISNULL(qop.Premium, 0))
        FROM tblQuoteOptionPremiums qop
        INNER JOIN tblQuoteOptions qo ON qo.QuoteOptionGUID = qop.QuoteOptionGuid
        INNER JOIN tblFin_PolicyCharges pc ON pc.ChargeCode = qop.ChargeCode
        WHERE qo.QuoteGUID = @OriginalQuoteGuid
        AND pc.ChargeID = 'PREM'  -- Only get premium charges
        
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
        
        -- Skip reason code validation for now (table might not exist)
        -- Just use the provided reason code or default
        IF @ReasonCode IS NULL
        BEGIN
            SET @ReasonCode = 30  -- Default to "Insured Request"
        END
        
        -- Calculate refund based on cancellation type
        IF @CancellationType = 'flat'
        BEGIN
            -- Flat cancellation = full refund
            SET @CalculatedRefund = @OriginalPremium
        END
        ELSE
        BEGIN
            -- Pro-rata cancellation = calculate based on time elapsed
            SET @DaysInPolicy = DATEDIFF(day, @PolicyEffectiveDate, @PolicyExpirationDate)
            SET @DaysElapsed = DATEDIFF(day, @PolicyEffectiveDate, @CancellationDateTime)
            
            -- Calculate unearned premium (refund)
            IF @DaysInPolicy > 0
            BEGIN
                SET @CalculatedRefund = @OriginalPremium * ((@DaysInPolicy - @DaysElapsed) * 1.0 / @DaysInPolicy)
            END
            ELSE
            BEGIN
                SET @CalculatedRefund = 0
            END
        END
        
        -- Override with provided refund amount if specified
        IF @RefundAmount IS NOT NULL
        BEGIN
            SET @CalculatedRefund = @RefundAmount
        END
        
        -- Step 2: Use spCopyQuote to create the cancellation (like Ascot does)
        -- This native IMS procedure handles all the complexity
        EXEC spCopyQuote
            @QuoteGuid = @OriginalQuoteGuid,
            @TransactionTypeID = 'C',  -- Cancellation
            @QuoteStatusID = @QuoteStatusID,
            @QuoteStatusReasonID = @ReasonCode,
            @EndorsementEffective = @CancellationDateTime,
            @EndtRequestDate = @DateRequested,
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
        
        -- Step 3: Insert the refund amount as negative premium
        IF @CalculatedRefund IS NOT NULL AND @CalculatedRefund > 0 AND @NewQuoteOptionGuid IS NOT NULL
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
                    -ABS(@CalculatedRefund),  -- Ensure negative for refund
                    -ABS(@CalculatedRefund),  -- Annual = total for cancellation
                    1,  -- Commissionable
                    GETDATE()
                )
            END
        END
        
        -- Step 4: Bind the cancellation to finalize it
        UPDATE tblQuotes
        SET DateBound = GETDATE(),
            BoundByUserID = 1  -- System user
        WHERE QuoteGUID = @CancellationQuoteGuid
        
        -- Step 5: Update tblTritonQuoteData for the cancellation
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
                status,
                created_date,
                last_updated,
                -- Use midterm fields to store cancellation data
                midterm_endt_description,  -- Store cancellation reason here
                midterm_endt_effective_from,  -- Store cancellation date here
                -- Copy these from original
                renewal_of_quote_guid,
                umr,
                agreement_number,
                section_number,
                class_of_business,
                program_name,
                expiring_policy_number,
                underwriter_name,
                producer_name,
                effective_date,
                expiration_date,
                bound_date,
                insured_name,
                insured_state,
                insured_zip,
                business_type,
                limit_amount,
                deductible_amount,
                commission_rate,
                additional_insured,
                address_1,
                address_2,
                city,
                state,
                zip,
                source_system,
                expiring_opportunity_id,
                opportunity_type,
                full_payload_json
            )
            SELECT 
                @CancellationQuoteGuid,
                @NewQuoteOptionGuid,
                @OpportunityID,
                policy_number,
                'cancellation',
                CONVERT(VARCHAR(50), GETDATE(), 101),
                CASE WHEN @CalculatedRefund IS NOT NULL THEN -ABS(@CalculatedRefund) ELSE 0 END,
                'cancelled',
                GETDATE(),
                GETDATE(),
                -- Store cancellation info in midterm fields
                @Comment + ' (' + @CancellationType + ' cancellation)',  -- midterm_endt_description
                @CancellationDate,  -- midterm_endt_effective_from
                -- Copy from original
                renewal_of_quote_guid,
                umr,
                agreement_number,
                section_number,
                class_of_business,
                program_name,
                expiring_policy_number,
                underwriter_name,
                producer_name,
                effective_date,
                expiration_date,
                bound_date,
                insured_name,
                insured_state,
                insured_zip,
                business_type,
                limit_amount,
                deductible_amount,
                commission_rate,
                additional_insured,
                address_1,
                address_2,
                city,
                state,
                zip,
                source_system,
                expiring_opportunity_id,
                opportunity_type,
                full_payload_json
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
        @CalculatedRefund AS RefundAmount,
        @NewQuoteOptionGuid AS QuoteOptionGuid
END
GO

PRINT 'Procedure [dbo].[Triton_CancelPolicy_WS] created successfully'