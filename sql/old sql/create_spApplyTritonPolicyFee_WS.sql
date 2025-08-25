-- Stored procedure to apply Policy_Fee from tblTritonQuoteData to a quote
-- This procedure reads the policy_fee from tblTritonQuoteData and applies it using charge code 12374
-- Based on Distinguished_ExpressHotels_RateOptionV2 pattern

IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'spApplyTritonPolicyFee_WS')
BEGIN
    DROP PROCEDURE [dbo].[spApplyTritonPolicyFee_WS];
END
GO

CREATE PROCEDURE [dbo].[spApplyTritonPolicyFee_WS]
(
    @QuoteGuid UNIQUEIDENTIFIER
)
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE 
        @Policy_FeeCode SMALLINT = 12374,  -- Charge code for Policy Fee
        @Policy_Fee MONEY,
        @QuoteOptionGuid UNIQUEIDENTIFIER;
    
    BEGIN TRY
        -- Get the Policy_Fee from tblTritonQuoteData
        SELECT @Policy_Fee = policy_fee
        FROM dbo.tblTritonQuoteData
        WHERE QuoteGuid = @QuoteGuid;
        
        -- Only proceed if we have a policy fee to apply
        IF @Policy_Fee IS NOT NULL AND @Policy_Fee > 0
        BEGIN
            -- Get all QuoteOptionGuids for this quote
            DECLARE option_cursor CURSOR FOR
            SELECT QuoteOptionGUID
            FROM dbo.tblQuoteOptions
            WHERE QuoteGUID = @QuoteGuid;
            
            OPEN option_cursor;
            FETCH NEXT FROM option_cursor INTO @QuoteOptionGuid;
            
            WHILE @@FETCH_STATUS = 0
            BEGIN
                -- Apply the policy fee to each quote option
                -- SetManualFlatRateFee requires that:
                -- 1. The fee is already set up for the Company Line
                -- 2. UpdatePremiumHistoric has been called
                -- 3. spAutoApplyFees has been called
                -- These should have been done already in spProcessTritonPayload_WS
                
                -- Check if the charge already exists in tblQuoteOptionCharges
                IF EXISTS (
                    SELECT 1 
                    FROM tblQuoteOptionCharges 
                    WHERE QuoteOptionGUID = @QuoteOptionGuid 
                    AND ChargeCode = @Policy_FeeCode
                )
                BEGIN
                    -- Update existing charge with the new fee value
                    UPDATE tblQuoteOptionCharges
                    SET FlatRate = @Policy_Fee,
                        CompanyFeeID = 37277712,  -- Ensure correct CompanyFeeID
                        Payable = 1,
                        AutoApplied = 0
                    WHERE QuoteOptionGUID = @QuoteOptionGuid 
                    AND ChargeCode = @Policy_FeeCode;
                    
                    PRINT 'Updated Policy Fee to $' + CAST(@Policy_Fee AS VARCHAR(20)) + 
                          ' for QuoteOption ' + CAST(@QuoteOptionGuid AS VARCHAR(50));
                END
                ELSE
                BEGIN
                    -- Get the OfficeID and CompanyLineGuid from the quote
                    DECLARE @OfficeID INT, @CompanyFeeID INT, @CompanyLineGuid UNIQUEIDENTIFIER;
                    
                    -- Get OfficeID from the quote
                    SELECT @OfficeID = tblClientOffices.OfficeID
                    FROM tblQuotes q
                    INNER JOIN tblQuoteOptions qo ON q.QuoteGuid = qo.QuoteGuid
                    INNER JOIN tblClientOffices ON q.QuotingLocationGuid = tblClientOffices.OfficeGuid
                    WHERE qo.QuoteOptionGuid = @QuoteOptionGuid;
                    
                    -- Get CompanyLineGuid from the quote
                    SELECT @CompanyLineGuid = CompanyLineGuid
                    FROM tblQuotes
                    WHERE QuoteGuid = @QuoteGuid;
                    
                    -- Always use the specific CompanyFeeID for Triton Policy Fee
                    SET @CompanyFeeID = 37277712;  -- Triton Policy Fee CompanyFeeID
                    
                    -- Insert new charge record for the policy fee
                    INSERT INTO tblQuoteOptionCharges (
                        QuoteOptionGuid,
                        CompanyFeeID,
                        ChargeCode,
                        OfficeID,
                        CompanyLineGuid,
                        FeeTypeID,
                        Payable,
                        FlatRate,
                        Splittable,
                        AutoApplied
                    )
                    VALUES (
                        @QuoteOptionGuid,
                        @CompanyFeeID,
                        @Policy_FeeCode,
                        ISNULL(@OfficeID, 1),  -- Default to 1 if not found
                        @CompanyLineGuid,
                        2,  -- Flat fee type
                        1,  -- Payable
                        @Policy_Fee,
                        0,  -- Not splittable
                        0   -- Not auto-applied (manual)
                    );
                    
                    PRINT 'Inserted Policy Fee of $' + CAST(@Policy_Fee AS VARCHAR(20)) + 
                          ' for QuoteOption ' + CAST(@QuoteOptionGuid AS VARCHAR(50));
                END
                
                FETCH NEXT FROM option_cursor INTO @QuoteOptionGuid;
            END
            
            CLOSE option_cursor;
            DEALLOCATE option_cursor;
            
            -- Return success
            SELECT 
                'Success' AS Status,
                'Policy Fee applied successfully' AS Message,
                @QuoteGuid AS QuoteGuid,
                @Policy_Fee AS PolicyFeeApplied;
        END
        ELSE
        BEGIN
            -- No policy fee to apply
            SELECT 
                'Success' AS Status,
                'No Policy Fee to apply' AS Message,
                @QuoteGuid AS QuoteGuid,
                ISNULL(@Policy_Fee, 0) AS PolicyFee;
        END
        
    END TRY
    BEGIN CATCH
        -- Clean up cursor if error occurred
        IF CURSOR_STATUS('global', 'option_cursor') >= -1
        BEGIN
            IF CURSOR_STATUS('global', 'option_cursor') > -1
            BEGIN
                CLOSE option_cursor;
            END
            DEALLOCATE option_cursor;
        END
        
        -- Return error information
        SELECT 
            'Error' AS Status,
            ERROR_MESSAGE() AS Message,
            ERROR_NUMBER() AS ErrorNumber,
            ERROR_LINE() AS ErrorLine,
            ERROR_PROCEDURE() AS ErrorProcedure;
    END CATCH
END
GO

PRINT 'Stored procedure spApplyTritonPolicyFee_WS created successfully';
GO