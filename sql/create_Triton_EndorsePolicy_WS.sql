-- =============================================
-- Author:      RSG Integration
-- Create date: 2025-08-07
-- Description: Creates a midterm endorsement for Triton policies
--              Simple version that works with actual IMS schema
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
    DECLARE @PolicyNumber VARCHAR(50)
    DECLARE @TransEffDateTime DATETIME
    DECLARE @NextEndorsementNumber INT
    DECLARE @ControlNumber INT
    DECLARE @QuoteOptionGuid UNIQUEIDENTIFIER
    DECLARE @NewQuoteOptionGuid UNIQUEIDENTIFIER
    DECLARE @LineGuid UNIQUEIDENTIFIER
    DECLARE @CompanyLocationID INT
    
    BEGIN TRY
        BEGIN TRANSACTION
        
        -- Convert date string to datetime
        SET @TransEffDateTime = CONVERT(DATETIME, @TransEffDate, 101)
        
        -- Step 1: Find the original quote
        IF @OpportunityID IS NOT NULL
        BEGIN
            -- Find by opportunity_id
            SELECT TOP 1 
                @OriginalQuoteGuid = tq.QuoteGuid,
                @PolicyNumber = tq.policy_number,
                @QuoteOptionGuid = tq.QuoteOptionGuid
            FROM tblTritonQuoteData tq
            WHERE tq.opportunity_id = @OpportunityID
            AND tq.status = 'bound'  -- Only endorse bound policies
            ORDER BY tq.created_date DESC
        END
        ELSE IF @QuoteGuid IS NOT NULL
        BEGIN
            -- Find by QuoteGuid
            SELECT TOP 1 
                @OriginalQuoteGuid = q.QuoteGUID,
                @PolicyNumber = q.PolicyNumber,
                @ControlNumber = q.ControlNo
            FROM tblQuotes q
            WHERE q.QuoteGUID = @QuoteGuid
            
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
        
        -- Get control number and other info from original quote
        SELECT 
            @ControlNumber = ControlNo,
            @PolicyNumber = PolicyNumber
        FROM tblQuotes
        WHERE QuoteGUID = @OriginalQuoteGuid
        
        -- Get the next endorsement number
        SELECT @NextEndorsementNumber = ISNULL(MAX(EndorsementNum), 0) + 1
        FROM tblQuotes
        WHERE ControlNo = @ControlNumber
        
        -- Step 2: Create the endorsement quote
        SET @EndorsementQuoteGuid = NEWID()
        
        INSERT INTO tblQuotes (
            QuoteGUID,
            OriginalQuoteGUID,
            ControlNo,
            EndorsementNum,
            EndorsementEffective,
            EndorsementComment,
            EndorsementCalculationType,
            TransactionTypeID,
            QuoteStatusID,
            PolicyNumber,
            DateCreated,
            DateBound,
            -- Copy these fields from original
            QuotingLocationGuid,
            IssuingLocationGuid,
            CompanyLocationGuid,
            LineGUID,
            StateID,
            ProducerContactGuid,
            UnderwriterUserGuid,
            EffectiveDate,
            ExpirationDate,
            InsuredPolicyName,
            InsuredCorporationName,
            InsuredFirstName,
            InsuredLastName,
            InsuredAddress1,
            InsuredCity,
            InsuredState,
            InsuredZipCode
        )
        SELECT 
            @EndorsementQuoteGuid,              -- New GUID
            @OriginalQuoteGuid,                 -- Link to original
            ControlNo,                           -- Same control number
            @NextEndorsementNumber,              -- New endorsement number
            @TransEffDateTime,                   -- Endorsement effective date
            @Comment,                            -- Endorsement comment
            'F',                                 -- Fixed calculation type
            'E',                                 -- Endorsement transaction
            CASE WHEN @BindEndorsement = 1 THEN 3 ELSE 1 END,  -- Status: 3=Bound, 1=Quote
            PolicyNumber,                        -- Keep same policy number
            GETDATE(),                          -- Created now
            CASE WHEN @BindEndorsement = 1 THEN GETDATE() ELSE NULL END,  -- Bound date if binding
            -- Copy from original
            QuotingLocationGuid,
            IssuingLocationGuid,
            CompanyLocationGuid,
            LineGUID,
            StateID,
            ProducerContactGuid,
            UnderwriterUserGuid,
            EffectiveDate,
            ExpirationDate,
            InsuredPolicyName,
            InsuredCorporationName,
            InsuredFirstName,
            InsuredLastName,
            InsuredAddress1,
            InsuredCity,
            InsuredState,
            InsuredZipCode
        FROM tblQuotes
        WHERE QuoteGUID = @OriginalQuoteGuid
        
        -- Step 3: Create quote option for endorsement
        IF @QuoteOptionGuid IS NOT NULL
        BEGIN
            SET @NewQuoteOptionGuid = NEWID()
            
            -- Get line and company info from original option
            SELECT 
                @LineGuid = LineGUID,
                @CompanyLocationID = CompanyLocationID
            FROM tblQuoteOptions
            WHERE QuoteOptionGUID = @QuoteOptionGuid
            
            INSERT INTO tblQuoteOptions (
                QuoteOptionGUID,
                OriginalQuoteOptionGUID,
                QuoteGUID,
                LineGUID,
                CompanyLocationID,
                DateCreated,
                Bound,
                Quote
                -- Premium is computed, don't insert directly
            )
            VALUES (
                @NewQuoteOptionGuid,            -- New option GUID
                @QuoteOptionGuid,                -- Link to original option
                @EndorsementQuoteGuid,           -- Link to new quote
                @LineGuid,                       -- Same line
                @CompanyLocationID,              -- Same company location
                GETDATE(),                       -- Created now
                CASE WHEN @BindEndorsement = 1 THEN 1 ELSE 0 END,  -- Bound if binding
                CASE WHEN @BindEndorsement = 1 THEN 0 ELSE 1 END   -- Quote if not binding
            )
            
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
        
        -- Step 5: Register the premium using UpdatePremiumHistoricV3
        -- This reads from tblTritonQuoteData.gross_premium and populates tblQuoteOptionPremiums
        IF @NewQuoteOptionGuid IS NOT NULL AND EXISTS (SELECT * FROM sys.procedures WHERE name = 'UpdatePremiumHistoricV3')
        BEGIN
            EXEC dbo.UpdatePremiumHistoricV3
                @quoteOptionGuid        = @NewQuoteOptionGuid,
                @RawPremiumHistoryTable = 'tblTritonQuoteData',
                @PremiumField           = 'gross_premium';
        END
        
        -- Step 6: Auto apply fees if applicable
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

PRINT 'Procedure [dbo].[Triton_EndorsePolicy_WS] created successfully'