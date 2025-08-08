-- =============================================
-- Author:      RSG Integration
-- Create date: 2025-08-07
-- Description: Creates a midterm endorsement for Triton policies
--              V6: Full Ascot approach - iterate through ALL premium records
--                  Handles multiple charge types (PREM, TERR, fees, etc.)
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
        
        -- Set quote status based on bind flag
        SET @QuoteStatusID = 3  -- Bound
        IF @BindEndorsement = 1
        BEGIN
            SET @DateBound = GETDATE()
        END
        
        -- Step 1: Find the original quote
        IF @OpportunityID IS NOT NULL
        BEGIN
            -- Find by opportunity_id
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
            AND tq.status = 'bound'
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
        ELSE
        BEGIN
            SET @Result = 0
            SET @Message = 'Either OpportunityID or QuoteGuid must be provided'
            GOTO ReturnResult
        END
        
        -- Validate we found the quote
        IF @OriginalQuoteGuid IS NULL
        BEGIN
            SET @Result = 0
            SET @Message = 'Original quote not found'
            GOTO ReturnResult
        END
        
        -- Get next endorsement number
        SELECT @NextEndorsementNumber = ISNULL(MAX(CAST(
            CASE 
                WHEN ISNUMERIC(EndorsementNumber) = 1 THEN EndorsementNumber 
                ELSE '0' 
            END AS INT)), 0) + 1
        FROM tblQuotes
        WHERE ControlNo = @ControlNumber
        AND TransactionTypeID = 'E'
        
        -- Step 2: Create the endorsement quote using spCopyQuote
        DECLARE @NewQuoteTable TABLE (NewQuoteGuid UNIQUEIDENTIFIER)
        
        INSERT INTO @NewQuoteTable
        EXEC dbo.spCopyQuote
            @QuoteGuid = @OriginalQuoteGuid,
            @TransactionTypeID = 'E',
            @QuoteStatusID = @QuoteStatusID,
            @QuoteStatusReasonID = @QuoteStatusReasonID,
            @EndorsementEffective = @TransEffDateTime,
            @EndtRequestDate = @DateBound,
            @EndorsementComment = @Comment,
            @EndorsementCalculationType = 'F',  -- Flat endorsement
            @copyOptions = 0
        
        SELECT TOP 1 @EndorsementQuoteGuid = NewQuoteGuid FROM @NewQuoteTable
        
        IF @EndorsementQuoteGuid IS NULL
        BEGIN
            SET @Result = 0
            SET @Message = 'Failed to create endorsement quote'
            GOTO ReturnResult
        END
        
        -- Update endorsement details
        UPDATE tblQuotes
        SET EndorsementNumber = @NextEndorsementNumber,
            UserGuid = @UserGuid,
            DateBound = @DateBound
        WHERE QuoteGUID = @EndorsementQuoteGuid
        
        -- Get the endorsement quote ID
        SELECT @EndorsementQuoteID = QuoteID
        FROM tblQuotes
        WHERE QuoteGUID = @EndorsementQuoteGuid
        
        -- Step 3: Create or get quote option for the endorsement
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
                DateCreated,
                Bound,
                Quote
            )
            SELECT 
                @NewQuoteOptionGuid,
                QuoteOptionGUID,
                @EndorsementQuoteGuid,
                LineGUID,
                CompanyLocationID,
                GETDATE(),
                1,  -- Bound
                0
            FROM tblQuoteOptions
            WHERE QuoteGUID = @OriginalQuoteGuid
        END
        ELSE
        BEGIN
            -- Update existing quote option to be bound
            UPDATE tblQuoteOptions
            SET Bound = 1
            WHERE QuoteGUID = @EndorsementQuoteGuid
        END
        
        -- Step 4: Apply premiums using Ascot's approach - iterate through ALL premium records
        -- This handles multiple charge types (PREM, TERR, fees, etc.)
        
        PRINT 'Processing endorsement premiums using full Ascot approach'
        
        -- Variables for cursor
        DECLARE @CursorQuoteOptionGuid UNIQUEIDENTIFIER
        DECLARE @CursorChargeCode INT
        DECLARE @CursorOfficeID INT
        DECLARE @CursorPremium MONEY
        DECLARE @CursorCommissionable BIT
        DECLARE @ChargeID VARCHAR(10)
        DECLARE @OriginalPremium MONEY
        DECLARE @PremiumToInsert MONEY
        
        -- Create cursor to iterate through ALL premium records from original quote
        DECLARE EndorsePremiumCursor CURSOR FAST_FORWARD FOR
        SELECT 
            @NewQuoteOptionGuid AS NewQuoteOptionGuid,
            qop.ChargeCode,
            qop.OfficeID,
            qop.Premium AS OriginalPremium,
            qop.Commissionable,
            pc.ChargeID
        FROM tblQuoteOptions qo
        INNER JOIN tblQuoteOptionPremiums qop ON qo.QuoteOptionGUID = qop.QuoteOptionGuid
        LEFT JOIN tblFin_PolicyCharges pc ON pc.ChargeCode = qop.ChargeCode
        WHERE qo.QuoteGUID = @OriginalQuoteGuid
        ORDER BY pc.ChargeID, qop.ChargeCode
        
        OPEN EndorsePremiumCursor
        FETCH NEXT FROM EndorsePremiumCursor INTO 
            @CursorQuoteOptionGuid, @CursorChargeCode, @CursorOfficeID, 
            @OriginalPremium, @CursorCommissionable, @ChargeID
        
        WHILE @@FETCH_STATUS = 0
        BEGIN
            -- Determine the premium amount based on charge type
            IF @ChargeID = 'PREM'  -- Base premium
            BEGIN
                SET @PremiumToInsert = @EndorsementPremium
                PRINT 'Inserting base premium (PREM): ' + CAST(@PremiumToInsert AS VARCHAR(20))
            END
            ELSE IF @ChargeID = 'TERR'  -- Terrorism premium
            BEGIN
                -- For terrorism, you might want to calculate as a percentage of base premium
                -- For now, we'll skip it unless you have specific terrorism premium
                SET @PremiumToInsert = 0
                PRINT 'Skipping terrorism premium (TERR) - no value provided'
            END
            ELSE IF @ChargeID IS NOT NULL
            BEGIN
                -- For other charges (fees, taxes), copy the original amount
                -- You could also prorate these based on the endorsement
                SET @PremiumToInsert = @OriginalPremium
                PRINT 'Copying original amount for ' + @ChargeID + ': ' + CAST(@PremiumToInsert AS VARCHAR(20))
            END
            ELSE
            BEGIN
                -- Unknown charge type, copy original
                SET @PremiumToInsert = @OriginalPremium
                PRINT 'Unknown charge type, copying original: ' + CAST(@PremiumToInsert AS VARCHAR(20))
            END
            
            -- Only insert if premium is not zero (or if it's a credit)
            IF @PremiumToInsert <> 0 OR @OriginalPremium <> 0
            BEGIN
                -- Delete any existing record first (in case of retry)
                DELETE FROM tblQuoteOptionPremiums
                WHERE QuoteOptionGuid = @CursorQuoteOptionGuid
                AND ChargeCode = @CursorChargeCode
                
                -- Insert the premium record
                INSERT INTO tblQuoteOptionPremiums (
                    QuoteOptionGuid,
                    ChargeCode,
                    OfficeID,
                    Premium,
                    AnnualPremium,
                    Commissionable
                )
                VALUES (
                    @CursorQuoteOptionGuid,
                    @CursorChargeCode,
                    @CursorOfficeID,
                    @PremiumToInsert,
                    @PremiumToInsert,
                    @CursorCommissionable
                )
                
                IF @@ROWCOUNT > 0
                BEGIN
                    PRINT '  Successfully inserted premium for ChargeCode ' + CAST(@CursorChargeCode AS VARCHAR(10))
                END
            END
            
            FETCH NEXT FROM EndorsePremiumCursor INTO 
                @CursorQuoteOptionGuid, @CursorChargeCode, @CursorOfficeID, 
                @OriginalPremium, @CursorCommissionable, @ChargeID
        END
        
        CLOSE EndorsePremiumCursor
        DEALLOCATE EndorsePremiumCursor
        
        -- Step 5: Handle additional premium types if needed
        -- If you have specific terrorism premium or other charges, handle them here
        
        -- Step 6: Update tblTritonQuoteData for the endorsement
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
        
        -- Step 7: Auto apply fees if applicable
        IF @NewQuoteOptionGuid IS NOT NULL AND EXISTS (SELECT * FROM sys.procedures WHERE name = 'spAutoApplyFees')
        BEGIN
            EXEC dbo.spAutoApplyFees
                @quoteOptionGuid = @NewQuoteOptionGuid
        END
        
        COMMIT TRANSACTION
        
        -- Return success result
        SET @Result = 1
        SET @Message = 'Endorsement created successfully with all premiums applied'
        
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