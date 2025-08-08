-- =============================================
-- Author:      RSG Integration
-- Create date: 2025-08-07
-- Description: Creates a midterm endorsement for Triton policies
--              V8: Compatible version - works with standard IMS tables
--                  Handles missing columns gracefully
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
    @TerrorismPremium MONEY = 0,
    @Comment VARCHAR(255) = 'Midterm Endorsement',
    @EndorsementCalcType CHAR(1) = 'F',  -- F=Flat, P=Prorate
    @BindEndorsement BIT = 0
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
    DECLARE @NextEndorsementNumber INT = 1
    DECLARE @ControlNumber INT
    DECLARE @QuoteOptionGuid UNIQUEIDENTIFIER
    DECLARE @NewQuoteOptionGuid UNIQUEIDENTIFIER
    DECLARE @LineGuid UNIQUEIDENTIFIER
    DECLARE @CompanyLocationID INT
    DECLARE @QuoteStatusID INT
    DECLARE @QuoteStatusReasonID INT = 20
    DECLARE @DateBound DATETIME = NULL
    DECLARE @PolicyEffectiveDate DATETIME
    DECLARE @PolicyExpirationDate DATETIME
    
    BEGIN TRY
        BEGIN TRANSACTION
        
        PRINT '=== Starting Triton Endorsement Process ==='
        PRINT 'Parameters:'
        PRINT '  OpportunityID: ' + ISNULL(CAST(@OpportunityID AS VARCHAR(20)), 'NULL')
        PRINT '  QuoteGuid: ' + ISNULL(CAST(@QuoteGuid AS VARCHAR(50)), 'NULL')
        PRINT '  EndorsementPremium: $' + CAST(@EndorsementPremium AS VARCHAR(20))
        PRINT '  TerrorismPremium: $' + CAST(@TerrorismPremium AS VARCHAR(20))
        PRINT '  EffectiveDate: ' + @TransEffDate
        
        -- Convert date string to datetime
        SET @TransEffDateTime = CONVERT(DATETIME, @TransEffDate, 101)
        
        -- Set quote status
        SET @QuoteStatusID = 3  -- Bound
        IF @BindEndorsement = 1
        BEGIN
            SET @DateBound = GETDATE()
        END
        
        -- Step 1: Find the original quote
        IF @OpportunityID IS NOT NULL
        BEGIN
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
            
            PRINT 'Found original quote by OpportunityID: ' + CAST(@OriginalQuoteGuid AS VARCHAR(50))
        END
        ELSE IF @QuoteGuid IS NOT NULL
        BEGIN
            SET @OriginalQuoteGuid = @QuoteGuid
            
            SELECT TOP 1 
                @PolicyNumber = PolicyNumber,
                @ControlNumber = ControlNo,
                @PolicyEffectiveDate = EffectiveDate,
                @PolicyExpirationDate = ExpirationDate
            FROM tblQuotes
            WHERE QuoteGUID = @QuoteGuid
            
            SELECT TOP 1 @QuoteOptionGuid = QuoteOptionGUID
            FROM tblQuoteOptions
            WHERE QuoteGUID = @QuoteGuid
            
            PRINT 'Using provided QuoteGuid: ' + CAST(@OriginalQuoteGuid AS VARCHAR(50))
        END
        ELSE
        BEGIN
            RAISERROR('Either OpportunityID or QuoteGuid must be provided', 16, 1)
        END
        
        -- Validate we found the quote
        IF @OriginalQuoteGuid IS NULL
        BEGIN
            RAISERROR('Original quote not found', 16, 1)
        END
        
        PRINT 'Original Policy: ' + ISNULL(@PolicyNumber, 'Unknown')
        PRINT 'Control Number: ' + CAST(@ControlNumber AS VARCHAR(20))
        
        -- Calculate next endorsement number (simplified - just count existing endorsements)
        SELECT @NextEndorsementNumber = COUNT(*) + 1
        FROM tblQuotes
        WHERE ControlNo = @ControlNumber
        AND TransactionTypeID = 'E'
        
        PRINT 'Creating endorsement #' + CAST(@NextEndorsementNumber AS VARCHAR(10))
        
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
            @EndorsementCalculationType = @EndorsementCalcType,
            @copyOptions = 0
        
        SELECT TOP 1 @EndorsementQuoteGuid = NewQuoteGuid FROM @NewQuoteTable
        
        IF @EndorsementQuoteGuid IS NULL
        BEGIN
            RAISERROR('Failed to create endorsement quote via spCopyQuote', 16, 1)
        END
        
        PRINT 'Created endorsement quote: ' + CAST(@EndorsementQuoteGuid AS VARCHAR(50))
        
        -- Update DateBound if binding
        IF @DateBound IS NOT NULL
        BEGIN
            UPDATE tblQuotes
            SET DateBound = @DateBound
            WHERE QuoteGUID = @EndorsementQuoteGuid
        END
        
        -- Get the endorsement quote ID
        SELECT @EndorsementQuoteID = QuoteID
        FROM tblQuotes
        WHERE QuoteGUID = @EndorsementQuoteGuid
        
        PRINT 'Endorsement QuoteID: ' + CAST(@EndorsementQuoteID AS VARCHAR(20))
        
        -- Step 3: Handle quote options
        SELECT TOP 1 
            @NewQuoteOptionGuid = QuoteOptionGUID,
            @LineGuid = LineGUID,
            @CompanyLocationID = CompanyLocationID
        FROM tblQuoteOptions
        WHERE QuoteGUID = @EndorsementQuoteGuid
        
        IF @NewQuoteOptionGuid IS NULL
        BEGIN
            PRINT 'No quote option found, creating new one'
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
            
            PRINT 'Created new quote option: ' + CAST(@NewQuoteOptionGuid AS VARCHAR(50))
        END
        ELSE
        BEGIN
            -- Update existing quote option to be bound
            UPDATE tblQuoteOptions
            SET Bound = 1
            WHERE QuoteGUID = @EndorsementQuoteGuid
            
            PRINT 'Updated existing quote option: ' + CAST(@NewQuoteOptionGuid AS VARCHAR(50))
        END
        
        -- Step 4: Apply premiums using Ascot approach
        PRINT ''
        PRINT '=== Processing Premiums ==='
        
        DECLARE @InsertedCount INT = 0
        DECLARE @TotalPremiumInserted MONEY = 0
        
        -- Variables for cursor
        DECLARE @CursorChargeCode INT
        DECLARE @CursorOfficeID INT
        DECLARE @CursorCommissionable BIT
        DECLARE @ChargeID VARCHAR(10)
        DECLARE @OriginalPremium MONEY
        DECLARE @PremiumToInsert MONEY
        
        -- Get all premium records from original quote
        DECLARE EndorsePremiumCursor CURSOR FAST_FORWARD FOR
        SELECT DISTINCT
            qop.ChargeCode,
            qop.OfficeID,
            qop.Premium AS OriginalPremium,
            qop.Commissionable,
            ISNULL(pc.ChargeID, 'UNKNOWN') AS ChargeID
        FROM tblQuoteOptions qo
        INNER JOIN tblQuoteOptionPremiums qop ON qo.QuoteOptionGUID = qop.QuoteOptionGuid
        LEFT JOIN tblFin_PolicyCharges pc ON pc.ChargeCode = qop.ChargeCode
        WHERE qo.QuoteGUID = @OriginalQuoteGuid
        ORDER BY ChargeID, qop.ChargeCode
        
        OPEN EndorsePremiumCursor
        FETCH NEXT FROM EndorsePremiumCursor INTO 
            @CursorChargeCode, @CursorOfficeID, @OriginalPremium, 
            @CursorCommissionable, @ChargeID
        
        WHILE @@FETCH_STATUS = 0
        BEGIN
            SET @PremiumToInsert = 0
            
            -- Determine premium amount based on charge type
            IF @ChargeID = 'PREM'  -- Base premium
            BEGIN
                SET @PremiumToInsert = @EndorsementPremium
                PRINT '  Base Premium (PREM): ChargeCode=' + CAST(@CursorChargeCode AS VARCHAR(10)) + 
                      ', Amount=$' + CAST(@PremiumToInsert AS VARCHAR(20))
            END
            ELSE IF @ChargeID = 'TERR' AND @TerrorismPremium > 0  -- Terrorism
            BEGIN
                SET @PremiumToInsert = @TerrorismPremium
                PRINT '  Terrorism Premium (TERR): ChargeCode=' + CAST(@CursorChargeCode AS VARCHAR(10)) + 
                      ', Amount=$' + CAST(@PremiumToInsert AS VARCHAR(20))
            END
            ELSE IF @ChargeID NOT IN ('PREM', 'TERR')
            BEGIN
                -- For other charges, copy original (fees, taxes, etc.)
                SET @PremiumToInsert = @OriginalPremium
                PRINT '  Other Charge (' + @ChargeID + '): ChargeCode=' + CAST(@CursorChargeCode AS VARCHAR(10)) + 
                      ', Amount=$' + CAST(@PremiumToInsert AS VARCHAR(20))
            END
            
            -- Insert the premium if not zero
            IF @PremiumToInsert <> 0
            BEGIN
                -- Delete any existing record
                DELETE FROM tblQuoteOptionPremiums
                WHERE QuoteOptionGuid = @NewQuoteOptionGuid
                AND ChargeCode = @CursorChargeCode
                
                -- Insert the premium
                INSERT INTO tblQuoteOptionPremiums (
                    QuoteOptionGuid,
                    ChargeCode,
                    OfficeID,
                    Premium,
                    AnnualPremium,
                    Commissionable
                )
                VALUES (
                    @NewQuoteOptionGuid,
                    @CursorChargeCode,
                    @CursorOfficeID,
                    @PremiumToInsert,
                    @PremiumToInsert,
                    @CursorCommissionable
                )
                
                SET @InsertedCount = @InsertedCount + 1
                SET @TotalPremiumInserted = @TotalPremiumInserted + @PremiumToInsert
            END
            
            FETCH NEXT FROM EndorsePremiumCursor INTO 
                @CursorChargeCode, @CursorOfficeID, @OriginalPremium, 
                @CursorCommissionable, @ChargeID
        END
        
        CLOSE EndorsePremiumCursor
        DEALLOCATE EndorsePremiumCursor
        
        PRINT ''
        PRINT 'Premium Summary:'
        PRINT '  Records Inserted: ' + CAST(@InsertedCount AS VARCHAR(10))
        PRINT '  Total Premium: $' + CAST(@TotalPremiumInserted AS VARCHAR(20))
        
        -- If no premiums were inserted and we have an endorsement premium, insert a default
        IF @InsertedCount = 0 AND @EndorsementPremium <> 0
        BEGIN
            PRINT ''
            PRINT 'WARNING: No premium records found in original quote'
            PRINT 'Inserting default premium record'
            
            -- Look up the charge code for PREM
            DECLARE @DefaultChargeCode INT
            SELECT TOP 1 @DefaultChargeCode = ChargeCode
            FROM tblFin_PolicyCharges
            WHERE ChargeID = 'PREM'
            ORDER BY ChargeCode
            
            -- If not found, use 1 as default
            IF @DefaultChargeCode IS NULL
                SET @DefaultChargeCode = 1
            
            INSERT INTO tblQuoteOptionPremiums (
                QuoteOptionGuid,
                ChargeCode,
                OfficeID,
                Premium,
                AnnualPremium,
                Commissionable
            )
            VALUES (
                @NewQuoteOptionGuid,
                @DefaultChargeCode,
                1,  -- Default office
                @EndorsementPremium,
                @EndorsementPremium,
                1   -- Commissionable
            )
            
            SET @TotalPremiumInserted = @EndorsementPremium
            PRINT 'Inserted default premium with ChargeCode=' + CAST(@DefaultChargeCode AS VARCHAR(10))
        END
        
        -- Step 5: Update tblTritonQuoteData
        IF @OpportunityID IS NOT NULL
        BEGIN
            -- Delete any existing record
            DELETE FROM tblTritonQuoteData
            WHERE QuoteGuid = @EndorsementQuoteGuid
            
            -- Insert endorsement record
            INSERT INTO tblTritonQuoteData (
                QuoteGuid,
                QuoteOptionGuid,
                opportunity_id,
                policy_number,
                transaction_type,
                transaction_date,
                gross_premium,
                terrorism_premium,
                midterm_endt_effective_from,
                midterm_endt_description,
                midterm_endt_endorsement_number,
                status,
                created_date,
                last_updated,
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
                @TerrorismPremium,
                @TransEffDate,
                @Comment,
                CAST(@NextEndorsementNumber AS VARCHAR(50)),
                CASE WHEN @BindEndorsement = 1 THEN 'bound' ELSE 'quoted' END,
                GETDATE(),
                GETDATE(),
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
            
            PRINT 'Updated tblTritonQuoteData for endorsement'
        END
        
        -- Step 6: Apply automatic fees if procedure exists
        IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'spAutoApplyFees')
        BEGIN
            PRINT 'Applying automatic fees'
            EXEC dbo.spAutoApplyFees @quoteOptionGuid = @NewQuoteOptionGuid
        END
        
        COMMIT TRANSACTION
        
        -- Success
        SET @Result = 1
        SET @Message = 'Endorsement created successfully. Total premium: $' + CAST(@TotalPremiumInserted AS VARCHAR(20))
        
        PRINT ''
        PRINT '=== Endorsement Process Complete ==='
        PRINT @Message
        
        -- Return result
        SELECT 
            @Result AS Result,
            @Message AS Message,
            @EndorsementQuoteGuid AS EndorsementQuoteGuid,
            @NewQuoteOptionGuid AS QuoteOptionGuid,
            @OriginalQuoteGuid AS OriginalQuoteGuid,
            @PolicyNumber AS PolicyNumber,
            @NextEndorsementNumber AS EndorsementNumber,
            @EndorsementPremium AS BasePremiumApplied,
            @TerrorismPremium AS TerrorismPremiumApplied,
            @TotalPremiumInserted AS TotalPremiumApplied
            
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION
        
        SET @Result = 0
        SET @Message = 'ERROR: ' + ERROR_MESSAGE() + ' (Line: ' + CAST(ERROR_LINE() AS VARCHAR(10)) + ')'
        
        PRINT ''
        PRINT '=== ERROR IN ENDORSEMENT PROCESS ==='
        PRINT @Message
        
        -- Return error result
        SELECT 
            @Result AS Result,
            @Message AS Message,
            NULL AS EndorsementQuoteGuid,
            NULL AS QuoteOptionGuid,
            @OriginalQuoteGuid AS OriginalQuoteGuid,
            @PolicyNumber AS PolicyNumber,
            NULL AS EndorsementNumber,
            NULL AS BasePremiumApplied,
            NULL AS TerrorismPremiumApplied,
            NULL AS TotalPremiumApplied
    END CATCH
END
GO