-- =============================================
-- Author:      RSG Integration
-- Create date: 2025-08-07
-- Description: Creates a midterm endorsement for Triton policies
--              V7: Complete implementation with support for multiple premium types
--                  Handles PREM, TERR, and other charges with proper calculations
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
    @TerrorismPremium MONEY = 0,  -- Optional terrorism premium
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
    DECLARE @NextEndorsementNumber INT
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
    DECLARE @ProrateFactor DECIMAL(10,6) = 1.0
    
    BEGIN TRY
        BEGIN TRANSACTION
        
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
        
        -- Calculate proration factor if needed
        IF @EndorsementCalcType = 'P'
        BEGIN
            DECLARE @DaysRemaining INT = DATEDIFF(DAY, @TransEffDateTime, @PolicyExpirationDate)
            DECLARE @TotalDays INT = DATEDIFF(DAY, @PolicyEffectiveDate, @PolicyExpirationDate)
            IF @TotalDays > 0
                SET @ProrateFactor = CAST(@DaysRemaining AS DECIMAL(10,6)) / CAST(@TotalDays AS DECIMAL(10,6))
        END
        
        -- Get next endorsement number
        -- Check if EndorsementNumber column exists
        IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblQuotes') AND name = 'EndorsementNumber')
        BEGIN
            SELECT @NextEndorsementNumber = ISNULL(MAX(CAST(
                CASE 
                    WHEN ISNUMERIC(EndorsementNumber) = 1 THEN EndorsementNumber 
                    ELSE '0' 
                END AS INT)), 0) + 1
            FROM tblQuotes
            WHERE ControlNo = @ControlNumber
            AND TransactionTypeID = 'E'
        END
        ELSE
        BEGIN
            -- If EndorsementNumber column doesn't exist, generate based on count
            SELECT @NextEndorsementNumber = COUNT(*) + 1
            FROM tblQuotes
            WHERE ControlNo = @ControlNumber
            AND TransactionTypeID = 'E'
        END
        
        IF @NextEndorsementNumber IS NULL
            SET @NextEndorsementNumber = 1
        
        PRINT 'Creating endorsement #' + CAST(@NextEndorsementNumber AS VARCHAR(10)) + ' for policy ' + @PolicyNumber
        
        -- Step 2: Create the endorsement quote
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
            RAISERROR('Failed to create endorsement quote', 16, 1)
        END
        
        -- Update endorsement details (only update columns that exist)
        -- Update DateBound if binding
        IF @DateBound IS NOT NULL
        BEGIN
            UPDATE tblQuotes
            SET DateBound = @DateBound
            WHERE QuoteGUID = @EndorsementQuoteGuid
        END
        
        -- Update EndorsementNumber if column exists
        IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblQuotes') AND name = 'EndorsementNumber')
        BEGIN
            EXEC('UPDATE tblQuotes SET EndorsementNumber = ' + @NextEndorsementNumber + ' WHERE QuoteGUID = ''' + @EndorsementQuoteGuid + '''')
        END
        
        -- Update UserGuid if column exists
        IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblQuotes') AND name = 'UserGuid')
        BEGIN
            EXEC('UPDATE tblQuotes SET UserGuid = ''' + @UserGuid + ''' WHERE QuoteGUID = ''' + @EndorsementQuoteGuid + '''')
        END
        
        -- Get the endorsement quote ID
        SELECT @EndorsementQuoteID = QuoteID
        FROM tblQuotes
        WHERE QuoteGUID = @EndorsementQuoteGuid
        
        -- Step 3: Handle quote options
        SELECT TOP 1 
            @NewQuoteOptionGuid = QuoteOptionGUID,
            @LineGuid = LineGUID,
            @CompanyLocationID = CompanyLocationID
        FROM tblQuoteOptions
        WHERE QuoteGUID = @EndorsementQuoteGuid
        
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
                1,
                0
            FROM tblQuoteOptions
            WHERE QuoteGUID = @OriginalQuoteGuid
        END
        ELSE
        BEGIN
            UPDATE tblQuoteOptions
            SET Bound = 1
            WHERE QuoteGUID = @EndorsementQuoteGuid
        END
        
        -- Step 4: Process premiums - Full Ascot approach with proper calculations
        PRINT 'Processing endorsement premiums'
        PRINT '  Base Premium: $' + CAST(@EndorsementPremium AS VARCHAR(20))
        PRINT '  Terrorism Premium: $' + CAST(@TerrorismPremium AS VARCHAR(20))
        PRINT '  Calculation Type: ' + @EndorsementCalcType
        IF @EndorsementCalcType = 'P'
            PRINT '  Proration Factor: ' + CAST(@ProrateFactor AS VARCHAR(20))
        
        -- Create temporary table to track what we've inserted
        CREATE TABLE #InsertedPremiums (
            ChargeCode INT,
            ChargeID VARCHAR(10),
            Premium MONEY
        )
        
        -- Variables for cursor
        DECLARE @CursorChargeCode INT
        DECLARE @CursorOfficeID INT
        DECLARE @CursorCommissionable BIT
        DECLARE @ChargeID VARCHAR(10)
        DECLARE @OriginalPremium MONEY
        DECLARE @PremiumToInsert MONEY
        DECLARE @TotalOriginalPremium MONEY = 0
        DECLARE @PremiumRatio DECIMAL(10,6)
        
        -- Get total original base premium for ratio calculations
        SELECT @TotalOriginalPremium = SUM(qop.Premium)
        FROM tblQuoteOptions qo
        INNER JOIN tblQuoteOptionPremiums qop ON qo.QuoteOptionGUID = qop.QuoteOptionGuid
        INNER JOIN tblFin_PolicyCharges pc ON pc.ChargeCode = qop.ChargeCode
        WHERE qo.QuoteGUID = @OriginalQuoteGuid
        AND pc.ChargeID = 'PREM'
        
        IF @TotalOriginalPremium IS NULL OR @TotalOriginalPremium = 0
            SET @TotalOriginalPremium = 1  -- Avoid division by zero
        
        -- Process each premium type
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
            
            -- Calculate premium based on charge type
            IF @ChargeID = 'PREM'  -- Base premium
            BEGIN
                IF @EndorsementCalcType = 'P'  -- Prorate
                BEGIN
                    -- Apply proration to the endorsement premium
                    SET @PremiumToInsert = @EndorsementPremium * @ProrateFactor
                END
                ELSE  -- Flat
                BEGIN
                    -- Use the full endorsement premium
                    -- If multiple PREM records, distribute proportionally
                    SET @PremiumRatio = @OriginalPremium / @TotalOriginalPremium
                    SET @PremiumToInsert = @EndorsementPremium * @PremiumRatio
                END
                PRINT 'Base premium (PREM) for ChargeCode ' + CAST(@CursorChargeCode AS VARCHAR(10)) + ': $' + CAST(@PremiumToInsert AS VARCHAR(20))
            END
            ELSE IF @ChargeID = 'TERR'  -- Terrorism premium
            BEGIN
                IF @TerrorismPremium > 0
                BEGIN
                    IF @EndorsementCalcType = 'P'
                        SET @PremiumToInsert = @TerrorismPremium * @ProrateFactor
                    ELSE
                        SET @PremiumToInsert = @TerrorismPremium
                    PRINT 'Terrorism premium (TERR): $' + CAST(@PremiumToInsert AS VARCHAR(20))
                END
                ELSE
                BEGIN
                    -- If no terrorism premium provided, keep original or set to 0 for midterm
                    SET @PremiumToInsert = 0
                    PRINT 'No terrorism premium provided, setting to 0'
                END
            END
            ELSE IF @ChargeID IN ('INSP', 'FACU', 'ERPP')  -- Other known charges
            BEGIN
                -- For other charges, typically copy original or prorate
                IF @EndorsementCalcType = 'P'
                    SET @PremiumToInsert = @OriginalPremium * @ProrateFactor
                ELSE
                    SET @PremiumToInsert = @OriginalPremium  -- Keep original for flat
                PRINT 'Other charge (' + @ChargeID + '): $' + CAST(@PremiumToInsert AS VARCHAR(20))
            END
            ELSE
            BEGIN
                -- Unknown charge type - be conservative and copy original
                SET @PremiumToInsert = @OriginalPremium
                PRINT 'Unknown charge type (' + ISNULL(@ChargeID, 'NULL') + '), copying original: $' + CAST(@PremiumToInsert AS VARCHAR(20))
            END
            
            -- Insert the premium record if it's not zero
            IF @PremiumToInsert <> 0
            BEGIN
                -- Delete any existing record first
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
                    @PremiumToInsert,  -- For endorsements, annual = actual
                    @CursorCommissionable
                )
                
                -- Track what we inserted
                INSERT INTO #InsertedPremiums (ChargeCode, ChargeID, Premium)
                VALUES (@CursorChargeCode, @ChargeID, @PremiumToInsert)
                
                PRINT '  Inserted premium record for ChargeCode ' + CAST(@CursorChargeCode AS VARCHAR(10))
            END
            
            FETCH NEXT FROM EndorsePremiumCursor INTO 
                @CursorChargeCode, @CursorOfficeID, @OriginalPremium, 
                @CursorCommissionable, @ChargeID
        END
        
        CLOSE EndorsePremiumCursor
        DEALLOCATE EndorsePremiumCursor
        
        -- Summary of inserted premiums
        DECLARE @TotalInserted MONEY
        SELECT @TotalInserted = SUM(Premium) FROM #InsertedPremiums
        PRINT 'Total premium inserted: $' + CAST(@TotalInserted AS VARCHAR(20))
        
        -- Clean up temp table
        DROP TABLE #InsertedPremiums
        
        -- Step 5: Update tblTritonQuoteData
        IF @OpportunityID IS NOT NULL
        BEGIN
            -- Delete any existing record for this endorsement
            DELETE FROM tblTritonQuoteData
            WHERE QuoteGuid = @EndorsementQuoteGuid
            
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
        END
        
        -- Step 6: Auto apply fees
        IF @NewQuoteOptionGuid IS NOT NULL AND EXISTS (SELECT * FROM sys.procedures WHERE name = 'spAutoApplyFees')
        BEGIN
            PRINT 'Applying automatic fees'
            EXEC dbo.spAutoApplyFees @quoteOptionGuid = @NewQuoteOptionGuid
        END
        
        COMMIT TRANSACTION
        
        -- Success
        SET @Result = 1
        SET @Message = 'Endorsement created successfully with all premiums applied. Total premium: $' + CAST(@TotalInserted AS VARCHAR(20))
        
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
            @TotalInserted AS TotalPremiumApplied
            
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
            NULL AS BasePremiumApplied,
            NULL AS TerrorismPremiumApplied,
            NULL AS TotalPremiumApplied
            
        -- Re-raise the error for debugging
        ;THROW
    END CATCH
END
GO