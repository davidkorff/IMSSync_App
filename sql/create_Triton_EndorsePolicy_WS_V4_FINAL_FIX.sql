-- =============================================
-- Author:      RSG Integration
-- Create date: 2025-08-07
-- Description: Creates a midterm endorsement for Triton policies
--              V4: FINAL FIX - Ensure quote option is NOT bound when created
--                  so premium can be applied without triggering CantModifyPremiumOnBoundPolicy
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
    @BindEndorsement BIT = 0  -- Default to FALSE - binding happens later in Python
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
        
        -- ALWAYS create as unbound initially - premium must be applied before binding
        SET @QuoteStatusID = 1  -- Quote (not bound)
        SET @DateBound = NULL
        
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
        IF @PolicyEffectiveDate IS NOT NULL AND @TransEffDateTime < @PolicyEffectiveDate
        BEGIN
            SET @TransEffDateTime = @PolicyEffectiveDate
        END
        
        IF @PolicyExpirationDate IS NOT NULL AND @TransEffDateTime > @PolicyExpirationDate
        BEGIN
            SET @Result = 0
            SET @Message = 'Endorsement effective date cannot be after policy expiration date'
            GOTO ReturnResult
        END
        
        -- Step 2: Use spCopyQuote to create the endorsement
        EXEC spCopyQuote
            @QuoteGuid = @OriginalQuoteGuid,
            @TransactionTypeID = 'E',  -- Endorsement
            @QuoteStatusID = @QuoteStatusID,  -- Always 1 (Quote) initially
            @QuoteStatusReasonID = @QuoteStatusReasonID,
            @EndorsementEffective = @TransEffDateTime,
            @EndtRequestDate = @DateBound,  -- Always NULL initially
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
        
        -- Step 3: CRITICAL FIX - Ensure the quote option is NOT bound
        -- Update the quote option that was created by spCopyQuote to ensure it's not bound
        UPDATE tblQuoteOptions
        SET Bound = 0  -- MUST be 0 to allow premium insertion
        WHERE QuoteGUID = @EndorsementQuoteGuid
        
        -- Get the quote option GUID
        SELECT TOP 1 
            @NewQuoteOptionGuid = QuoteOptionGUID,
            @LineGuid = LineGUID,
            @CompanyLocationID = CompanyLocationID
        FROM tblQuoteOptions
        WHERE QuoteGUID = @EndorsementQuoteGuid
        
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
                'quoted',  -- Always start as quoted, not bound
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
        
        -- Step 5: Auto apply fees if applicable (but don't bind)
        IF @NewQuoteOptionGuid IS NOT NULL AND EXISTS (SELECT * FROM sys.procedures WHERE name = 'spAutoApplyFees')
        BEGIN
            EXEC dbo.spAutoApplyFees
                @quoteOptionGuid = @NewQuoteOptionGuid
        END
        
        -- Step 6: DO NOT BIND HERE - Python will handle binding after premium is applied
        -- The binding will happen via bind_service.bind_quote() after spProcessTritonPayload
        
        COMMIT TRANSACTION
        
        -- Return success result
        SET @Result = 1
        SET @Message = 'Endorsement created successfully (unbound - ready for premium application)'
        
        ReturnResult:
        
        -- Return result set
        SELECT 
            @Result AS Result,
            @Message AS Message,
            @EndorsementQuoteGuid AS EndorsementQuoteGuid,
            @NewQuoteOptionGuid AS QuoteOptionGuid,
            @OriginalQuoteGuid AS OriginalQuoteGuid,
            @PolicyNumber AS PolicyNumber,
            @NextEndorsementNumber AS EndorsementNumber
            
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION
            
        SET @Result = 0
        SET @Message = ERROR_MESSAGE()
        
        -- Return error result
        SELECT 
            @Result AS Result,
            @Message AS Message,
            NULL AS EndorsementQuoteGuid,
            NULL AS QuoteOptionGuid,
            @OriginalQuoteGuid AS OriginalQuoteGuid,
            @PolicyNumber AS PolicyNumber,
            NULL AS EndorsementNumber
    END CATCH
END
GO