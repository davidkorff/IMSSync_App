-- Update spProcessTritonPayload_WS to include market_segment_code in INSERT and UPDATE
-- This fixes the issue where market_segment_code is extracted but not stored

ALTER PROCEDURE [dbo].[spProcessTritonPayload_WS]
    -- Quote identifiers
    @QuoteGuid UNIQUEIDENTIFIER,
    @QuoteOptionGuid UNIQUEIDENTIFIER,
   
    -- Full JSON payload for processing and audit trail
    @full_payload_json NVARCHAR(MAX),
   
    -- Optional renewal information
    @renewal_of_quote_guid UNIQUEIDENTIFIER = NULL
AS
BEGIN
    SET NOCOUNT ON;
   
    BEGIN TRY
        BEGIN TRANSACTION;
       
        -- Declare variables to hold parsed JSON values
        DECLARE @transaction_id NVARCHAR(100),
                @umr NVARCHAR(100),
                @agreement_number NVARCHAR(100),
                @section_number NVARCHAR(100),
                @class_of_business NVARCHAR(200),
                @program_name NVARCHAR(200),
                @policy_number NVARCHAR(50),
                @expiring_policy_number NVARCHAR(50),
                @underwriter_name NVARCHAR(200),
                @producer_name NVARCHAR(200),
                @invoice_date NVARCHAR(50),
                @policy_fee DECIMAL(18,2),
                @surplus_lines_tax NVARCHAR(50),
                @stamping_fee NVARCHAR(50),
                @other_fee DECIMAL(18,2),
                @insured_name NVARCHAR(500),
                @insured_state NVARCHAR(2),
                @insured_zip NVARCHAR(10),
                @effective_date NVARCHAR(50),
                @expiration_date NVARCHAR(50),
                @bound_date NVARCHAR(50),
                @opportunity_type NVARCHAR(100),
                @business_type NVARCHAR(100),
                @status NVARCHAR(100),
                @limit_amount NVARCHAR(100),
                @limit_prior NVARCHAR(100),
                @deductible_amount NVARCHAR(100),
                @gross_premium DECIMAL(18,2),
                @commission_rate DECIMAL(5,2),
                @commission_percent DECIMAL(5,2),
                @commission_amount DECIMAL(18,2),
                @net_premium DECIMAL(18,2),
                @base_premium DECIMAL(18,2),
                @opportunity_id INT,
                @midterm_endt_id INT,
                @midterm_endt_description NVARCHAR(500),
                @midterm_endt_effective_from NVARCHAR(50),
                @midterm_endt_endorsement_number NVARCHAR(50),
                @additional_insured NVARCHAR(MAX),
                @address_1 NVARCHAR(200),
                @address_2 NVARCHAR(200),
                @city NVARCHAR(100),
                @state NVARCHAR(2),
                @zip NVARCHAR(10),
                @prior_transaction_id NVARCHAR(100),
                @transaction_type NVARCHAR(100),
                @transaction_date NVARCHAR(50),
                @source_system NVARCHAR(50),
                @market_segment_code NVARCHAR(10);  -- IMPORTANT: This variable exists
       
        -- Parse JSON values
        SET @transaction_id = JSON_VALUE(@full_payload_json, '$.transaction_id');
        SET @umr = JSON_VALUE(@full_payload_json, '$.umr');
        SET @agreement_number = JSON_VALUE(@full_payload_json, '$.agreement_number');
        SET @section_number = JSON_VALUE(@full_payload_json, '$.section_number');
        SET @class_of_business = JSON_VALUE(@full_payload_json, '$.class_of_business');
        SET @program_name = JSON_VALUE(@full_payload_json, '$.program_name');
        SET @policy_number = JSON_VALUE(@full_payload_json, '$.policy_number');
        SET @expiring_policy_number = JSON_VALUE(@full_payload_json, '$.expiring_policy_number');
        SET @underwriter_name = JSON_VALUE(@full_payload_json, '$.underwriter_name');
        SET @producer_name = JSON_VALUE(@full_payload_json, '$.producer_name');
        SET @invoice_date = JSON_VALUE(@full_payload_json, '$.invoice_date');
        SET @policy_fee = TRY_CAST(JSON_VALUE(@full_payload_json, '$.policy_fee') AS DECIMAL(18,2));
        SET @surplus_lines_tax = JSON_VALUE(@full_payload_json, '$.surplus_lines_tax');
        SET @stamping_fee = JSON_VALUE(@full_payload_json, '$.stamping_fee');
        SET @other_fee = TRY_CAST(JSON_VALUE(@full_payload_json, '$.other_fee') AS DECIMAL(18,2));
        SET @insured_name = JSON_VALUE(@full_payload_json, '$.insured_name');
        SET @insured_state = JSON_VALUE(@full_payload_json, '$.insured_state');
        SET @insured_zip = JSON_VALUE(@full_payload_json, '$.insured_zip');
        SET @effective_date = JSON_VALUE(@full_payload_json, '$.effective_date');
        SET @expiration_date = JSON_VALUE(@full_payload_json, '$.expiration_date');
        SET @bound_date = JSON_VALUE(@full_payload_json, '$.bound_date');
        SET @opportunity_type = JSON_VALUE(@full_payload_json, '$.opportunity_type');
        SET @business_type = JSON_VALUE(@full_payload_json, '$.business_type');
        SET @status = JSON_VALUE(@full_payload_json, '$.status');
        SET @limit_amount = JSON_VALUE(@full_payload_json, '$.limit_amount');
        SET @limit_prior = JSON_VALUE(@full_payload_json, '$.limit_prior');
        SET @deductible_amount = JSON_VALUE(@full_payload_json, '$.deductible_amount');
        SET @gross_premium = TRY_CAST(JSON_VALUE(@full_payload_json, '$.gross_premium') AS DECIMAL(18,2));
        SET @commission_rate = TRY_CAST(JSON_VALUE(@full_payload_json, '$.commission_rate') AS DECIMAL(5,2));
        SET @commission_percent = TRY_CAST(JSON_VALUE(@full_payload_json, '$.commission_percent') AS DECIMAL(5,2));
        SET @commission_amount = TRY_CAST(JSON_VALUE(@full_payload_json, '$.commission_amount') AS DECIMAL(18,2));
        SET @net_premium = TRY_CAST(JSON_VALUE(@full_payload_json, '$.net_premium') AS DECIMAL(18,2));
        SET @base_premium = TRY_CAST(JSON_VALUE(@full_payload_json, '$.base_premium') AS DECIMAL(18,2));
        SET @opportunity_id = TRY_CAST(JSON_VALUE(@full_payload_json, '$.opportunity_id') AS INT);
        SET @midterm_endt_id = TRY_CAST(JSON_VALUE(@full_payload_json, '$.midterm_endt_id') AS INT);
        SET @midterm_endt_description = JSON_VALUE(@full_payload_json, '$.midterm_endt_description');
        SET @midterm_endt_effective_from = JSON_VALUE(@full_payload_json, '$.midterm_endt_effective_from');
        SET @midterm_endt_endorsement_number = JSON_VALUE(@full_payload_json, '$.midterm_endt_endorsement_number');
       
        -- Handle additional_insured as array (convert to string representation)
        SET @additional_insured = JSON_QUERY(@full_payload_json, '$.additional_insured');
       
        SET @address_1 = JSON_VALUE(@full_payload_json, '$.address_1');
        SET @address_2 = JSON_VALUE(@full_payload_json, '$.address_2');
        SET @city = JSON_VALUE(@full_payload_json, '$.city');
        SET @state = JSON_VALUE(@full_payload_json, '$.state');
        SET @zip = JSON_VALUE(@full_payload_json, '$.zip');
        SET @prior_transaction_id = JSON_VALUE(@full_payload_json, '$.prior_transaction_id');
        SET @transaction_type = JSON_VALUE(@full_payload_json, '$.transaction_type');
        SET @transaction_date = JSON_VALUE(@full_payload_json, '$.transaction_date');
        SET @source_system = JSON_VALUE(@full_payload_json, '$.source_system');
        SET @market_segment_code = JSON_VALUE(@full_payload_json, '$.market_segment_code');  -- EXTRACTED FROM JSON
        
        -- DEBUG: Log the market_segment_code
        PRINT 'DEBUG: Extracted market_segment_code = ' + ISNULL(@market_segment_code, 'NULL');
        PRINT 'DEBUG: Transaction type = ' + ISNULL(@transaction_type, 'NULL');
       
        -- Handle empty strings as NULL for certain fields
        IF @surplus_lines_tax = '' SET @surplus_lines_tax = NULL;
        IF @stamping_fee = '' SET @stamping_fee = NULL;
        IF @address_2 = '' SET @address_2 = NULL;
        IF @midterm_endt_effective_from = '' SET @midterm_endt_effective_from = NULL;
       
        -- 1. Insert into simplified tblTritonTransactionData (matching actual schema)
        -- Check if transaction already exists
        IF NOT EXISTS (SELECT 1 FROM tblTritonTransactionData WHERE transaction_id = @transaction_id)
        BEGIN
            INSERT INTO tblTritonTransactionData (
                transaction_id,
                full_payload_json,
                opportunity_id,
                policy_number,
                insured_name,
                transaction_type,
                transaction_date,
                source_system
            ) VALUES (
                @transaction_id,
                @full_payload_json,
                @opportunity_id,
                @policy_number,
                @insured_name,
                @transaction_type,
                @transaction_date,
                @source_system
            );
        END
       
        -- 2. Insert or update tblTritonQuoteData with market_segment_code
        -- Check if quote already exists
        IF EXISTS (SELECT 1 FROM tblTritonQuoteData WHERE QuoteGuid = @QuoteGuid)
        BEGIN
            -- Update existing record - NOW INCLUDING market_segment_code
            UPDATE tblTritonQuoteData
            SET QuoteOptionGuid = @QuoteOptionGuid,
                renewal_of_quote_guid = @renewal_of_quote_guid,
                umr = @umr,
                agreement_number = @agreement_number,
                section_number = @section_number,
                class_of_business = @class_of_business,
                program_name = @program_name,
                policy_number = @policy_number,
                expiring_policy_number = @expiring_policy_number,
                underwriter_name = @underwriter_name,
                producer_name = @producer_name,
                effective_date = @effective_date,
                expiration_date = @expiration_date,
                bound_date = @bound_date,
                insured_name = @insured_name,
                insured_state = @insured_state,
                insured_zip = @insured_zip,
                business_type = @business_type,
                status = @status,
                limit_amount = @limit_amount,
                deductible_amount = @deductible_amount,
                gross_premium = @gross_premium,
                commission_rate = @commission_rate,
                commission_percent = @commission_percent,
                policy_fee = @policy_fee,
                other_fee = @other_fee,
                surplus_lines_tax = @surplus_lines_tax,
                stamping_fee = @stamping_fee,
                midterm_endt_id = @midterm_endt_id,
                midterm_endt_description = @midterm_endt_description,
                midterm_endt_effective_from = @midterm_endt_effective_from,
                midterm_endt_endorsement_number = @midterm_endt_endorsement_number,
                additional_insured = @additional_insured,
                address_1 = @address_1,
                address_2 = @address_2,
                city = @city,
                state = @state,
                zip = @zip,
                opportunity_id = @opportunity_id,
                opportunity_type = @opportunity_type,
                market_segment_code = @market_segment_code,  -- NOW INCLUDED!
                transaction_type = @transaction_type,
                transaction_date = @transaction_date,
                source_system = @source_system,
                full_payload_json = @full_payload_json,
                last_updated = GETDATE()
            WHERE QuoteGuid = @QuoteGuid;
            
            PRINT 'DEBUG: Updated tblTritonQuoteData with market_segment_code = ' + ISNULL(@market_segment_code, 'NULL');
        END
        ELSE
        BEGIN
            -- Insert new record - NOW INCLUDING market_segment_code
            INSERT INTO tblTritonQuoteData (
                QuoteGuid,
                QuoteOptionGuid,
                renewal_of_quote_guid,
                umr,
                agreement_number,
                section_number,
                class_of_business,
                program_name,
                policy_number,
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
                status,
                limit_amount,
                deductible_amount,
                gross_premium,
                commission_rate,
                commission_percent,
                policy_fee,
                other_fee,
                surplus_lines_tax,
                stamping_fee,
                midterm_endt_id,
                midterm_endt_description,
                midterm_endt_effective_from,
                midterm_endt_endorsement_number,
                additional_insured,
                address_1,
                address_2,
                city,
                state,
                zip,
                opportunity_id,
                opportunity_type,
                market_segment_code,  -- NOW INCLUDED!
                transaction_type,
                transaction_date,
                source_system,
                full_payload_json,
                created_date,
                last_updated
            ) VALUES (
                @QuoteGuid,
                @QuoteOptionGuid,
                @renewal_of_quote_guid,
                @umr,
                @agreement_number,
                @section_number,
                @class_of_business,
                @program_name,
                @policy_number,
                @expiring_policy_number,
                @underwriter_name,
                @producer_name,
                @effective_date,
                @expiration_date,
                @bound_date,
                @insured_name,
                @insured_state,
                @insured_zip,
                @business_type,
                @status,
                @limit_amount,
                @deductible_amount,
                @gross_premium,
                @commission_rate,
                @commission_percent,
                @policy_fee,
                @other_fee,
                @surplus_lines_tax,
                @stamping_fee,
                @midterm_endt_id,
                @midterm_endt_description,
                @midterm_endt_effective_from,
                @midterm_endt_endorsement_number,
                @additional_insured,
                @address_1,
                @address_2,
                @city,
                @state,
                @zip,
                @opportunity_id,
                @opportunity_type,
                @market_segment_code,  -- NOW INCLUDED!
                @transaction_type,
                @transaction_date,
                @source_system,
                @full_payload_json,
                GETDATE(),
                GETDATE()
            );
            
            PRINT 'DEBUG: Inserted into tblTritonQuoteData with market_segment_code = ' + ISNULL(@market_segment_code, 'NULL');
        END
       
        -- 3. Update Policy Number in tblQuotes
        IF @policy_number IS NOT NULL AND @policy_number != ''
        BEGIN
            UPDATE tblQuotes
            SET PolicyNumber = @policy_number,
                AccountNumber = @policy_number  -- Also update AccountNumber for consistency
            WHERE QuoteGuid = @QuoteGuid;
           
            PRINT 'Updated PolicyNumber to: ' + @policy_number;
        END
       
        -- 4. Update commission rates if provided
        IF (@commission_rate IS NOT NULL OR @commission_percent IS NOT NULL) 
            AND EXISTS (SELECT 1 FROM tblQuoteDetails WHERE QuoteGuid = @QuoteGuid)
        BEGIN
            UPDATE tblQuoteDetails
            SET ProducerCommission = CASE
                    WHEN @commission_rate > 1 THEN @commission_rate / 100.0
                    ELSE @commission_rate
                END,
                CompanyCommission = CASE
                    WHEN @commission_percent > 1 THEN @commission_percent / 100.0
                    ELSE @commission_percent
                END
            WHERE QuoteGuid = @QuoteGuid;
           
            PRINT 'Updated commission rates in tblQuoteDetails';
        END
       
        -- 5. Set ProgramID based on market_segment_code and CompanyLineGuid
        -- This must happen before binding/processing
        -- Market segment codes: RT (Retail) or WL (Wholesale)
        -- Apply for bind, midterm_endorsement, cancellation, and reinstatement
        IF @transaction_type IN ('bind', 'midterm_endorsement', 'cancellation', 'reinstatement')
        BEGIN
            DECLARE @CompanyLineGuid UNIQUEIDENTIFIER;
           
            -- Get the CompanyLineGuid from tblQuotes
            SELECT @CompanyLineGuid = CompanyLineGuid
            FROM tblQuotes
            WHERE QuoteGuid = @QuoteGuid;
            
            PRINT 'DEBUG: CompanyLineGuid from tblQuotes = ' + ISNULL(CAST(@CompanyLineGuid AS NVARCHAR(50)), 'NULL');
            PRINT 'DEBUG: Checking ProgramID assignment for market_segment_code = ' + ISNULL(@market_segment_code, 'NULL');
           
            -- Set ProgramID based on market segment and line combinations
            IF EXISTS (SELECT 1 FROM tblQuoteDetails WHERE QuoteGuid = @QuoteGuid)
            BEGIN
                DECLARE @CurrentProgramID INT;
                SELECT @CurrentProgramID = ProgramID FROM tblQuoteDetails WHERE QuoteGuid = @QuoteGuid;
                PRINT 'DEBUG: Current ProgramID = ' + ISNULL(CAST(@CurrentProgramID AS NVARCHAR(10)), 'NULL');
                
                -- RT + LineGuid 07564291-CBFE-4BBE-88D1-0548C88ACED4 -> ProgramID = 11615
                IF @market_segment_code = 'RT' AND @CompanyLineGuid = '07564291-CBFE-4BBE-88D1-0548C88ACED4'
                BEGIN
                    UPDATE tblQuoteDetails
                    SET ProgramID = 11615
                    WHERE QuoteGuid = @QuoteGuid;
                    PRINT 'Set ProgramID to 11615 (RT market segment, LineGuid 07564291)';
                END
                -- WL + LineGuid 07564291-CBFE-4BBE-88D1-0548C88ACED4 -> ProgramID = 11613
                ELSE IF @market_segment_code = 'WL' AND @CompanyLineGuid = '07564291-CBFE-4BBE-88D1-0548C88ACED4'
                BEGIN
                    UPDATE tblQuoteDetails
                    SET ProgramID = 11613
                    WHERE QuoteGuid = @QuoteGuid;
                    PRINT 'Set ProgramID to 11613 (WL market segment, LineGuid 07564291)';
                END
                -- RT + LineGuid 08798559-321C-4FC0-98ED-A61B92215F31 -> ProgramID = 11612
                ELSE IF @market_segment_code = 'RT' AND @CompanyLineGuid = '08798559-321C-4FC0-98ED-A61B92215F31'
                BEGIN
                    UPDATE tblQuoteDetails
                    SET ProgramID = 11612
                    WHERE QuoteGuid = @QuoteGuid;
                    PRINT 'Set ProgramID to 11612 (RT market segment, LineGuid 08798559)';
                END
                -- WL + LineGuid 08798559-321C-4FC0-98ED-A61B92215F31 -> ProgramID = 11614
                ELSE IF @market_segment_code = 'WL' AND @CompanyLineGuid = '08798559-321C-4FC0-98ED-A61B92215F31'
                BEGIN
                    UPDATE tblQuoteDetails
                    SET ProgramID = 11614
                    WHERE QuoteGuid = @QuoteGuid;
                    PRINT 'Set ProgramID to 11614 (WL market segment, LineGuid 08798559)';
                END
                ELSE
                BEGIN
                    PRINT 'Warning: No matching ProgramID rule for market_segment_code ''' + ISNULL(@market_segment_code, 'NULL') + 
                          ''' and LineGuid ''' + ISNULL(CAST(@CompanyLineGuid AS NVARCHAR(50)), 'NULL') + '''';
                END
                
                -- Verify the update
                SELECT @CurrentProgramID = ProgramID FROM tblQuoteDetails WHERE QuoteGuid = @QuoteGuid;
                PRINT 'DEBUG: Final ProgramID = ' + ISNULL(CAST(@CurrentProgramID AS NVARCHAR(10)), 'NULL');
            END
            ELSE
            BEGIN
                PRINT 'Warning: tblQuoteDetails record does not exist for QuoteGuid ' + CAST(@QuoteGuid AS NVARCHAR(50));
            END
        END
       
        -- 6. SKIP UpdatePremiumHistoricV3 for endorsements and cancellations
        -- This procedure tries to insert into tblQuoteRatingDetail which fails for these transaction types
        -- Only run for bind transactions where rating data exists
        IF @transaction_type = 'bind' AND EXISTS (SELECT * FROM sys.procedures WHERE name = 'UpdatePremiumHistoricV3')
        BEGIN
            PRINT 'Processing premium for bind transaction';
            EXEC dbo.UpdatePremiumHistoricV3
                @quoteOptionGuid        = @QuoteOptionGuid,
                @RawPremiumHistoryTable = 'tblTritonQuoteData',
                @PremiumField           = 'gross_premium';
        END
        ELSE IF @transaction_type IN ('midterm_endorsement', 'cancellation', 'reinstatement')
        BEGIN
            PRINT 'Skipping UpdatePremiumHistoricV3 for ' + @transaction_type + ' (rating already handled by transaction-specific procedures)';
        END
       
        -- 7. Auto apply fees based on market_segment_code
        -- RT (Retail) = Auto-apply fees
        -- WL (Wholesale) = Do NOT auto-apply fees
        -- Apply for bind, midterm_endorsement, and reinstatement (NOT cancellation - already bound)
       
        -- Debug variables for auto-fee tracking
        DECLARE @AutoFeeStatus NVARCHAR(100) = 'Not Attempted';
        DECLARE @AutoFeeDetails NVARCHAR(500) = '';
       
        -- Build debug details
        SET @AutoFeeDetails = 'QuoteOptionGuid: ' + ISNULL(CAST(@QuoteOptionGuid AS VARCHAR(50)), 'NULL') +
                             ', Market: ' + ISNULL(@market_segment_code, 'NULL') +
                             ', Transaction: ' + ISNULL(@transaction_type, 'NULL');
       
        IF @transaction_type IN ('bind', 'midterm_endorsement', 'reinstatement')
            AND @market_segment_code = 'RT'
        BEGIN
            SET @AutoFeeStatus = 'Attempting RT Auto-Apply';
            PRINT 'Auto-applying fees for RT market segment...';
            PRINT @AutoFeeDetails;
           
            -- Check if auto apply fee procedure exists
            IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'spAutoApplyFee')
            BEGIN
                BEGIN TRY
                    EXEC spAutoApplyFee @quoteOptionGuid = @QuoteOptionGuid;
                    SET @AutoFeeStatus = 'RT Auto-Apply Success';
                    PRINT 'Successfully auto-applied fees for RT market segment';
                END TRY
                BEGIN CATCH
                    SET @AutoFeeStatus = 'RT Auto-Apply Failed: ' + ERROR_MESSAGE();
                    PRINT 'Warning: Failed to auto-apply fees - ' + ERROR_MESSAGE();
                    -- Don't fail the transaction, just log the warning
                END CATCH
            END
            ELSE
            BEGIN
                SET @AutoFeeStatus = 'RT Auto-Apply Skipped: Procedure not found';
                PRINT 'Warning: spAutoApplyFee procedure not found - skipping fee application';
            END
        END
        ELSE IF @transaction_type IN ('bind', 'midterm_endorsement', 'reinstatement')
            AND @market_segment_code = 'WL'
        BEGIN
            SET @AutoFeeStatus = 'WL - No Auto-Apply';
            PRINT 'NOT auto-applying fees for WL (wholesale) market segment';
            PRINT @AutoFeeDetails;
        END
        ELSE IF @transaction_type = 'cancellation'
        BEGIN
            SET @AutoFeeStatus = 'Cancellation - Skip Auto-Apply';
            PRINT 'Skipping auto-apply fees for cancellation (already bound)';
        END
        ELSE
        BEGIN
            SET @AutoFeeStatus = 'No Auto-Apply: ' + ISNULL(@transaction_type, 'NULL') + '/' + ISNULL(@market_segment_code, 'NULL');
            PRINT 'Auto-apply fee conditions not met';
            PRINT @AutoFeeDetails;
        END
       
        -- Log the auto-fee status
        PRINT 'Auto-Fee Status: ' + @AutoFeeStatus;
       
        -- Return success result
        SELECT 
            'Success' AS Status,
            'Payload processed successfully' AS Message,
            @QuoteGuid AS QuoteGuid,
            @QuoteOptionGuid AS QuoteOptionGuid,
            @policy_number AS PolicyNumber,
            @market_segment_code AS MarketSegmentCode,
            @AutoFeeStatus AS AutoFeeStatus;
       
        COMMIT TRANSACTION;
       
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
       
        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE();
        DECLARE @ErrorSeverity INT = ERROR_SEVERITY();
        DECLARE @ErrorState INT = ERROR_STATE();
       
        -- Return error result
        SELECT 
            'Error' AS Status,
            @ErrorMessage AS Message,
            @QuoteGuid AS QuoteGuid,
            @QuoteOptionGuid AS QuoteOptionGuid;
       
        -- Re-throw the error
        RAISERROR (@ErrorMessage, @ErrorSeverity, @ErrorState);
    END CATCH
END
GO

-- Grant execute permissions
GRANT EXECUTE ON spProcessTritonPayload_WS TO [IMS_User];
GO