-- =============================================
-- Author:      RSG Integration
-- Create date: 2025-08-07
-- Description: Creates a midterm endorsement for Triton policies
--              V2: Uses spCopyQuote (native IMS procedure) like Ascot does
-- =============================================

USE [IMS_DEV]
GO

-- Drop procedure if it exists
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Triton_EndorsePolicy_WS]') AND type in (N'P', N'PC'))
DROP PROCEDURE [dbo].[Triton_EndorsePolicy_WS]
GO

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE PROCEDURE [dbo].[Triton_EndorsePolicy_WS]
    @OpportunityID INT = NULL,
    @QuoteGuid UNIQUEIDENTIFIER = NULL,
    @UserGuid UNIQUEIDENTIFIER,
    @TransEffDate VARCHAR(50),
    @EndorsementPremium MONEY,
    @Comment VARCHAR(255) = 'Midterm Endorsement',
    @BindEndorsement BIT = 1
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Variables
    DECLARE @Result INT = 0
    DECLARE @Message VARCHAR(MAX) = ''
    DECLARE @OriginalQuoteGuid UNIQUEIDENTIFIER
    DECLARE @EndorsementQuoteGuid UNIQUEIDENTIFIER
    DECLARE @EndorsementQuoteID INT
    DECLARE @PolicyNumber VARCHAR(50)
    DECLARE @TransEffDateTime DATETIME
    DECLARE @NextEndorsementNumber INT
    DECLARE @ControlNumber INT
    DECLARE @QuoteOptionGuid UNIQUEIDENTIFIER
    DECLARE @NewQuoteOptionGuid UNIQUEIDENTIFIER
    DECLARE @LineGuid UNIQUEIDENTIFIER
    DECLARE @CompanyLocationID INT
    DECLARE @QuoteStatusID INT
    DECLARE @QuoteStatusReasonID INT = 20  -- Default reason ID for endorsements
    DECLARE @DateBound DATETIME = NULL
    DECLARE @PolicyEffectiveDate DATETIME
    DECLARE @PolicyExpirationDate DATETIME
    
    BEGIN TRY
        BEGIN TRANSACTION
        
        -- Convert date string to datetime
        SET @TransEffDateTime = CONVERT(DATETIME, @TransEffDate, 101)
        
        -- Set quote status based on bind flag
        IF @BindEndorsement = 1
        BEGIN
            SET @QuoteStatusID = 3  -- Bound
            SET @DateBound = GETDATE()
        END
        ELSE
        BEGIN
            SET @QuoteStatusID = 1  -- Quote
            SET @DateBound = NULL
        END
        
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
            AND tq.status = 'bound'  -- Only endorse bound policies
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
            SET @Message = 'No bound policy found for endorsement'
            GOTO ReturnResult
        END
        
        -- Validate endorsement effective date is within policy period
        -- The CHECK constraint requires endorsement date to be within the policy term
        IF @PolicyEffectiveDate IS NOT NULL AND @TransEffDateTime < @PolicyEffectiveDate
        BEGIN
            -- If endorsement date is before policy effective, use policy effective date
            SET @TransEffDateTime = @PolicyEffectiveDate
        END
        
        IF @PolicyExpirationDate IS NOT NULL AND @TransEffDateTime > @PolicyExpirationDate
        BEGIN
            -- If endorsement date is after expiration, that's an error
            SET @Result = 0
            SET @Message = 'Endorsement effective date cannot be after policy expiration date'
            GOTO ReturnResult
        END
        
        -- Step 2: Use spCopyQuote to create the endorsement (like Ascot does)
        -- This native IMS procedure handles all the complexity
        EXEC spCopyQuote
            @QuoteGuid = @OriginalQuoteGuid,
            @TransactionTypeID = 'E',  -- Endorsement
            @QuoteStatusID = @QuoteStatusID,
            @QuoteStatusReasonID = @QuoteStatusReasonID,  -- Required for endorsements
            @EndorsementEffective = @TransEffDateTime,
            @EndtRequestDate = @DateBound,
            @EndorsementComment = @Comment,
            @EndorsementCalculationType = 'F',  -- Fixed
            @copyOptions = 0
        
        -- Get the newly created endorsement quote
        SELECT TOP 1 
            @EndorsementQuoteGuid = QuoteGUID,
            @EndorsementQuoteID = QuoteID,
            @NextEndorsementNumber = EndorsementNum
        FROM tblQuotes
        WHERE ControlNo = @ControlNumber
        AND TransactionTypeID = 'E'
        ORDER BY QuoteID DESC
        
        -- Get the new quote option that was created
        SELECT TOP 1 
            @NewQuoteOptionGuid = QuoteOptionGUID,
            @LineGuid = LineGUID,
            @CompanyLocationID = CompanyLocationID
        FROM tblQuoteOptions
        WHERE QuoteGUID = @EndorsementQuoteGuid
        
        -- Step 3: Insert premium into tblQuoteOptionPremiums
        -- Get the charge code for premium
        DECLARE @PremiumChargeCode INT
        SELECT TOP 1 @PremiumChargeCode = ChargeCode
        FROM tblFin_PolicyCharges
        WHERE ChargeID = 'PREM'
        
        IF @NewQuoteOptionGuid IS NOT NULL AND @PremiumChargeCode IS NOT NULL
        BEGIN
            INSERT INTO tblQuoteOptionPremiums (
                QuoteOptionGuid,
                ChargeCode,
                OfficeID,
                Premium,
                AnnualPremium,
                Commissionable,
                Added
            )
            SELECT 
                @NewQuoteOptionGuid,
                @PremiumChargeCode,
                1,  -- Default office ID
                @EndorsementPremium,
                @EndorsementPremium,  -- Annual = total for endorsement
                1,  -- Commissionable
                GETDATE()
        END
        
        -- Step 4: Update tblTritonQuoteData for the endorsement
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
                midterm_endt_effective_from,
                midterm_endt_description,
                midterm_endt_endorsement_number,
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
                @EndorsementQuoteGuid,
                @NewQuoteOptionGuid,
                @OpportunityID,
                policy_number,
                'midterm_endorsement',
                CONVERT(VARCHAR(50), GETDATE(), 101),
                @EndorsementPremium,
                @TransEffDate,
                @Comment,
                CAST(@NextEndorsementNumber AS VARCHAR(50)),
                CASE WHEN @BindEndorsement = 1 THEN 'bound' ELSE 'quoted' END,
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
        
        -- Step 5: Auto apply fees if applicable
        IF @NewQuoteOptionGuid IS NOT NULL AND EXISTS (SELECT * FROM sys.procedures WHERE name = 'spAutoApplyFees')
        BEGIN
            EXEC dbo.spAutoApplyFees
                @quoteOptionGuid = @NewQuoteOptionGuid;
        END
        
        COMMIT TRANSACTION
        
        -- Return success
        SET @Result = 1
        SET @Message = 'Endorsement created successfully'
        
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
        @EndorsementQuoteGuid AS EndorsementQuoteGuid,
        @OriginalQuoteGuid AS OriginalQuoteGuid,
        @PolicyNumber AS PolicyNumber,
        @NextEndorsementNumber AS EndorsementNumber,
        @NewQuoteOptionGuid AS QuoteOptionGuid
END
GO

PRINT 'Procedure [dbo].[Triton_EndorsePolicy_WS] V2 created successfully'