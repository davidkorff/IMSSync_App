-- DEPRECATED: This stored procedure is no longer used
-- Other_Fee from Triton is stored in tblTritonQuoteData but NOT applied to quotes
-- Kept for reference only - DO NOT USE
-- Last modified: Removed other_fee application per business requirement

-- IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'spApplyTritonOtherFee_WS')
-- BEGIN
--     DROP PROCEDURE [dbo].[spApplyTritonOtherFee_WS];
-- END
-- GO

/* DEPRECATED - DO NOT CREATE
CREATE PROCEDURE [dbo].[spApplyTritonOtherFee_WS]
(
    @QuoteGuid UNIQUEIDENTIFIER
)
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE 
        @Other_FeeCode SMALLINT = 12375,  -- Charge code for Other Fee
        @Other_Fee MONEY,
        @QuoteOptionGuid UNIQUEIDENTIFIER;
    
    BEGIN TRY
        -- Get the Other_Fee from tblTritonQuoteData
        SELECT @Other_Fee = other_fee
        FROM dbo.tblTritonQuoteData
        WHERE QuoteGuid = @QuoteGuid;
        
        -- Only proceed if we have an other fee to apply
        IF @Other_Fee IS NOT NULL AND @Other_Fee > 0
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
                -- Check if the charge already exists in tblQuoteOptionCharges
                IF EXISTS (
                    SELECT 1 
                    FROM tblQuoteOptionCharges 
                    WHERE QuoteOptionGUID = @QuoteOptionGuid 
                    AND ChargeCode = @Other_FeeCode
                )
                BEGIN
                    -- Update existing charge with the new fee value
                    UPDATE tblQuoteOptionCharges
                    SET FlatRate = @Other_Fee,
                        CompanyFeeID = 37277715,  -- Ensure correct CompanyFeeID for Other Fee
                        Payable = 1,
                        AutoApplied = 0
                    WHERE QuoteOptionGUID = @QuoteOptionGuid 
                    AND ChargeCode = @Other_FeeCode;
                    
                    PRINT 'Updated Other Fee to $' + CAST(@Other_Fee AS VARCHAR(20)) + 
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
                    
                    -- Always use the specific CompanyFeeID for Triton Other Fee
                    SET @CompanyFeeID = 37277715;  -- Triton Other Fee CompanyFeeID
                    
                    -- Insert new charge record for the other fee
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
                        @Other_FeeCode,
                        ISNULL(@OfficeID, 1),  -- Default to 1 if not found
                        @CompanyLineGuid,
                        2,  -- Flat fee type
                        1,  -- Payable
                        @Other_Fee,
                        0,  -- Not splittable
                        0   -- Not auto-applied (manual)
                    );
                    
                    PRINT 'Inserted Other Fee of $' + CAST(@Other_Fee AS VARCHAR(20)) + 
                          ' for QuoteOption ' + CAST(@QuoteOptionGuid AS VARCHAR(50));
                END
                
                FETCH NEXT FROM option_cursor INTO @QuoteOptionGuid;
            END
            
            CLOSE option_cursor;
            DEALLOCATE option_cursor;
            
            -- Return success
            SELECT 
                'Success' AS Status,
                'Other Fee applied successfully' AS Message,
                @QuoteGuid AS QuoteGuid,
                @Other_Fee AS OtherFeeApplied;
        END
        ELSE
        BEGIN
            -- No other fee to apply
            SELECT 
                'Success' AS Status,
                'No Other Fee to apply' AS Message,
                @QuoteGuid AS QuoteGuid,
                ISNULL(@Other_Fee, 0) AS OtherFee;
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

PRINT 'Stored procedure spApplyTritonOtherFee_WS created successfully';
GO
*/

-- To remove the stored procedure if it exists in the database:
IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'spApplyTritonOtherFee_WS')
BEGIN
    DROP PROCEDURE [dbo].[spApplyTritonOtherFee_WS];
    PRINT 'Stored procedure spApplyTritonOtherFee_WS has been removed';
END
GO