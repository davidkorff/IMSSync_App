USE [IMS_DEV]
GO
/****** Object:  StoredProcedure [dbo].[spProcessTritonPayload_WS]    Script Date: 8/18/2025 6:26:07 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
















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
                @market_segment_code NVARCHAR(10);
       
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
        SET @market_segment_code = JSON_VALUE(@full_payload_json, '$.market_segment_code');
       
        -- Handle empty strings as NULL for certain fields
        IF @surplus_lines_tax = '' SET @surplus_lines_tax = NULL;
        IF @stamping_fee = '' SET @stamping_fee = NULL;
        -- other_fee is already decimal, no need to check for empty string
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
       
        -- 2. Insert or update tblTritonQuoteData with fee and tax fields
        -- Check if quote already exists
        IF EXISTS (SELECT 1 FROM tblTritonQuoteData WHERE QuoteGuid = @QuoteGuid)
        BEGIN
            -- Update existing record with latest data (including fees and taxes)
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
                transaction_type = @transaction_type,
                transaction_date = @transaction_date,
                source_system = @source_system,
                full_payload_json = @full_payload_json,
                last_updated = GETDATE()
            WHERE QuoteGuid = @QuoteGuid;
        END
        ELSE
        BEGIN
            -- Insert new record (including fees and taxes)
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
                @transaction_type,
                @transaction_date,
                @source_system,
                @full_payload_json,
                GETDATE(),
                GETDATE()
            );
        END
       
        -- 3. Update policy number in tblquotes
        IF EXISTS (SELECT 1 FROM tblquotes WHERE QuoteGuid = @QuoteGuid)
        BEGIN
            UPDATE tblquotes
            SET PolicyNumber = @policy_number
            WHERE QuoteGuid = @QuoteGuid;
        END
       
        -- 4. Update commission rates in tblQuoteDetails
        -- Convert whole number percentages to decimals (20 -> 0.20) if needed
        IF EXISTS (SELECT 1 FROM tblQuoteDetails WHERE QuoteGuid = @QuoteGuid)
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
        -- This must happen before binding
        -- Market segment codes: RT (Retail) or WL (Wholesale)
        DECLARE @CompanyLineGuid UNIQUEIDENTIFIER;
       
        -- Get the CompanyLineGuid from tblQuotes
        SELECT @CompanyLineGuid = CompanyLineGuid
        FROM tblQuotes
        WHERE QuoteGuid = @QuoteGuid;
       
        -- Set ProgramID based on market segment and line combinations
        IF EXISTS (SELECT 1 FROM tblQuoteDetails WHERE QuoteGuid = @QuoteGuid)
        BEGIN
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
                PRINT 'Warning: No matching ProgramID rule for market_segment_code ''' + ISNULL(@market_segment_code, 'NULL') + ''' and LineGuid ''' + CAST(ISNULL(@CompanyLineGuid, '00000000-0000-0000-0000-000000000000') AS NVARCHAR(50)) + '''';
            END
        END
       
        -- 6. Register the premium using UpdatePremiumHistoricV3
        -- Check if the stored procedure exists before calling
        IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'UpdatePremiumHistoricV3')
        BEGIN
            EXEC dbo.UpdatePremiumHistoricV3
                @quoteOptionGuid        = @QuoteOptionGuid,
                @RawPremiumHistoryTable = 'tblTritonQuoteData',
                @PremiumField           = 'gross_premium';
        END
       
        -- 7. Auto apply fees ONLY if stamping_fee OR surplus_lines_tax have values
        -- If Triton provides ANY fee values, we use auto-apply to calculate the rest
        -- If all fees are blank/null, skip auto-apply (Triton has no fees for this policy)
        IF (@stamping_fee IS NOT NULL AND @stamping_fee != '') OR (@surplus_lines_tax IS NOT NULL AND @surplus_lines_tax != '')
        BEGIN
            -- Check if the stored procedure exists before calling
            IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'spAutoApplyFees')
            BEGIN
                EXEC dbo.spAutoApplyFees
                    @quoteOptionGuid = @QuoteOptionGuid;
                   
                PRINT 'Auto-applied fees because stamping_fee or surplus_lines_tax were provided';
            END
        END
        ELSE
        BEGIN
            PRINT 'Skipped auto-apply fees because stamping_fee and surplus_lines_tax were both blank/null';
        END
       
        -- 8. Apply Policy Fee from Triton if present
        -- This applies the policy_fee to all quote options using charge code 12374
        IF @policy_fee IS NOT NULL AND @policy_fee > 0
        BEGIN
            -- Check if the stored procedure exists before calling
            IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'spApplyTritonPolicyFee_WS')
            BEGIN
                EXEC dbo.spApplyTritonPolicyFee_WS
                    @QuoteGuid = @QuoteGuid;
                   
                PRINT 'Applied Triton Policy Fee of $' + CAST(@policy_fee AS VARCHAR(20));
            END
        END
       
        -- 9. Other Fee from Triton is stored but NOT applied
        -- The other_fee value is captured in tblTritonQuoteData for reference only
        IF @other_fee IS NOT NULL AND @other_fee > 0
        BEGIN
            PRINT 'Other Fee of $' + CAST(@other_fee AS VARCHAR(20)) + ' received from Triton (stored but not applied)';
        END
       
        COMMIT TRANSACTION;
       
        -- Return success
        SELECT
            'Success' AS Status,
            'Payload processed successfully' AS Message,
            @QuoteGuid AS QuoteGuid,
            @QuoteOptionGuid AS QuoteOptionGuid,
            @transaction_id AS TransactionId,
            CASE
                WHEN (@stamping_fee IS NULL OR @stamping_fee = '') AND (@surplus_lines_tax IS NULL OR @surplus_lines_tax = '')
                THEN 'Fees auto-applied by IMS'
                ELSE 'Fees provided by Triton'
            END AS FeeSource;
           
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
           
        -- Return error information
        SELECT
            'Error' AS Status,
            ERROR_MESSAGE() AS Message,
            ERROR_NUMBER() AS ErrorNumber,
            ERROR_LINE() AS ErrorLine,
            ERROR_PROCEDURE() AS ErrorProcedure;
    END CATCH
END





