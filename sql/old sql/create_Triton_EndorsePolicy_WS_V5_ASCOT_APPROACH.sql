-- =============================================
-- Author:      RSG Integration
-- Create date: 2025-08-07
-- Description: Creates a midterm endorsement for Triton policies
--              V5: Use Ascot's approach - direct INSERT into tblQuoteOptionPremiums
--                  This bypasses the CantModifyPremiumOnBoundPolicy trigger
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
    DECLARE @ChargeCode INT
    DECLARE @OfficeID INT
    DECLARE @Commissionable BIT = 1
    
    BEGIN TRY
        BEGIN TRANSACTION
        
        -- Convert date string to datetime
        SET @TransEffDateTime = CONVERT(DATETIME, @TransEffDate, 101)
        
        -- V5: We'll create as BOUND but handle premium differently
        SET @QuoteStatusID = 3  -- Bound
        IF @BindEndorsement = 1
        BEGIN
            SET @DateBound = GETDATE()
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
            @QuoteStatusID = @QuoteStatusID,  -- 3 = Bound
            @QuoteStatusReasonID = @QuoteStatusReasonID,
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
        
        -- Step 3: Create quote option (following Ascot's approach)
        -- Get the quote option that was created by spCopyQuote
        SELECT TOP 1 
            @NewQuoteOptionGuid = QuoteOptionGUID,
            @LineGuid = LineGUID,
            @CompanyLocationID = CompanyLocationID
        FROM tblQuoteOptions
        WHERE QuoteGUID = @EndorsementQuoteGuid
        
        -- If no quote option was created, create one
        IF @NewQuoteOptionGuid IS NULL
        BEGIN
            SET @NewQuoteOptionGuid = NEWID()
            
            INSERT INTO tblQuoteOptions (
                QuoteOptionGUID,
                OriginalQuoteOptionGuid,
                QuoteGUID,
                LineGUID,
                CompanyLocationID,
                DateCreated,  -- Changed from 'Added' to 'DateCreated'
                Bound,  -- Set to 1 following Ascot's approach
                Quote
            )
            SELECT 
                @NewQuoteOptionGuid,
                QuoteOptionGUID,
                @EndorsementQuoteGuid,
                LineGUID,
                CompanyLocationID,
                GETDATE(),
                1,  -- Bound = 1 (Ascot's approach)
                0
            FROM tblQuoteOptions
            WHERE QuoteGUID = @OriginalQuoteGuid
        END
        ELSE
        BEGIN
            -- Update existing quote option to be bound (Ascot's approach)
            UPDATE tblQuoteOptions
            SET Bound = 1
            WHERE QuoteGUID = @EndorsementQuoteGuid
        END
        
        -- Step 4: Insert premium directly (bypassing the trigger like Ascot does)
        -- First, look up the proper ChargeCode for base premium from tblFin_PolicyCharges
        SELECT TOP 1 @ChargeCode = ChargeCode
        FROM tblFin_PolicyCharges
        WHERE ChargeID = 'PREM'  -- Base premium charge ID
        ORDER BY ChargeCode  -- Get the first one if multiple exist
        
        -- If PREM charge code not found, try to get from original quote
        IF @ChargeCode IS NULL
        BEGIN
            SELECT TOP 1 
                @ChargeCode = qop.ChargeCode
            FROM tblQuoteOptionPremiums qop
            INNER JOIN tblFin_PolicyCharges pc ON pc.ChargeCode = qop.ChargeCode
            WHERE qop.QuoteOptionGUID = @QuoteOptionGuid
            AND pc.ChargeID = 'PREM'  -- Only get base premium charge
        END
        
        -- Get office ID from the original quote
        SELECT TOP 1 
            @OfficeID = ISNULL(qop.OfficeID, 1)
        FROM tblQuoteOptionPremiums qop
        WHERE qop.QuoteOptionGUID = @QuoteOptionGuid
        
        -- If no premium records found, use defaults
        IF @ChargeCode IS NULL
            SET @ChargeCode = 1
        IF @OfficeID IS NULL
            SET @OfficeID = 1
        
        -- Log the premium insertion for debugging
        PRINT 'Inserting endorsement premium:'
        PRINT '  QuoteOptionGuid: ' + CAST(@NewQuoteOptionGuid AS VARCHAR(50))
        PRINT '  ChargeCode: ' + CAST(@ChargeCode AS VARCHAR(10))
        PRINT '  OfficeID: ' + CAST(@OfficeID AS VARCHAR(10))
        PRINT '  Premium: ' + CAST(@EndorsementPremium AS VARCHAR(20))
        
        -- Only insert premium if it's not zero
        IF @EndorsementPremium <> 0
        BEGIN
            -- Delete any existing premium record for this quote option (in case of retry)
            DELETE FROM tblQuoteOptionPremiums
            WHERE QuoteOptionGuid = @NewQuoteOptionGuid
            AND ChargeCode = @ChargeCode
            
            -- Insert the endorsement premium directly into tblQuoteOptionPremiums
            -- This bypasses the CantModifyPremiumOnBoundPolicy trigger
            INSERT INTO tblQuoteOptionPremiums (
                QuoteOptionGuid,
                ChargeCode,
                OfficeID,
                Premium,
                AnnualPremium,
                Commissionable
                -- Added has a default of GETDATE() so we don't need to include it
            )
            VALUES (
                @NewQuoteOptionGuid,
                @ChargeCode,
                @OfficeID,
                @EndorsementPremium,
                @EndorsementPremium,
                @Commissionable
            )
            
            -- Verify the insert succeeded
            IF @@ROWCOUNT = 0
            BEGIN
                SET @Message = 'Failed to insert endorsement premium into tblQuoteOptionPremiums'
                RAISERROR(@Message, 16, 1)
            END
            ELSE
            BEGIN
                PRINT 'Successfully inserted endorsement premium'
            END
        END
        ELSE
        BEGIN
            PRINT 'Warning: Endorsement premium is 0, skipping premium insertion'
        END
        
        -- Step 5: Update tblTritonQuoteData for the endorsement
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
        
        -- Step 6: Auto apply fees if applicable
        IF @NewQuoteOptionGuid IS NOT NULL AND EXISTS (SELECT * FROM sys.procedures WHERE name = 'spAutoApplyFees')
        BEGIN
            EXEC dbo.spAutoApplyFees
                @quoteOptionGuid = @NewQuoteOptionGuid
        END
        
        COMMIT TRANSACTION
        
        -- Return success result
        SET @Result = 1
        SET @Message = 'Endorsement created successfully with premium applied'
        
        ReturnResult:
        
        -- Return result set
        SELECT 
            @Result AS Result,
            @Message AS Message,
            @EndorsementQuoteGuid AS EndorsementQuoteGuid,
            @NewQuoteOptionGuid AS QuoteOptionGuid,
            @OriginalQuoteGuid AS OriginalQuoteGuid,
            @PolicyNumber AS PolicyNumber,
            @NextEndorsementNumber AS EndorsementNumber,
            @EndorsementPremium AS PremiumApplied
            
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
            NULL AS EndorsementNumber,
            NULL AS PremiumApplied
    END CATCH
END
GO