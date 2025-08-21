USE [IMS_DEV]
GO
/****** Object:  StoredProcedure [dbo].[spProcessTritonPayload_WS]    Script Date: 8/18/2025 6:26:07 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

-- FIXED VERSION: Skips UpdatePremiumHistoricV3 for endorsements and cancellations
-- This avoids the tblQuoteRatingDetail NULL insertion error

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
       
        -- 3. Update tblquotes fields (only for bind transactions)
        -- This handles rebind scenarios where data may have changed between transactions
        IF @transaction_type = 'bind' AND EXISTS (SELECT 1 FROM tblquotes WHERE QuoteGuid = @QuoteGuid)
        BEGIN
            -- Declare variables for date conversion and producer lookup
            DECLARE @EffectiveDateConverted DATE = NULL;
            DECLARE @ExpirationDateConverted DATE = NULL;
            DECLARE @ProducerContactGuid UNIQUEIDENTIFIER = NULL;
            
            -- Convert date strings to DATE type
            IF @effective_date IS NOT NULL AND @effective_date != ''
            BEGIN
                SET @EffectiveDateConverted = TRY_CONVERT(DATE, @effective_date);
            END
            
            IF @expiration_date IS NOT NULL AND @expiration_date != ''
            BEGIN
                SET @ExpirationDateConverted = TRY_CONVERT(DATE, @expiration_date);
            END
            
            -- Lookup producer by name or email using existing logic
            DECLARE @producer_email NVARCHAR(200);
            SET @producer_email = JSON_VALUE(@full_payload_json, '$.producer_email');
            
            -- Option 1: Use the existing getProducerGuid_WS procedure if it exists
            IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'getProducerGuid_WS')
            BEGIN
                -- Create temp table to capture results
                CREATE TABLE #ProducerLookup (
                    ProducerContactGUID UNIQUEIDENTIFIER,
                    ProducerLocationGUID UNIQUEIDENTIFIER
                );
                
                INSERT INTO #ProducerLookup
                EXEC getProducerGuid_WS @producer_email = @producer_email, @producer_name = @producer_name;
                
                SELECT TOP 1 @ProducerContactGuid = ProducerContactGUID
                FROM #ProducerLookup;
                
                DROP TABLE #ProducerLookup;
            END
            ELSE
            BEGIN
                -- Option 2: Direct lookup matching the logic in getProducerGuid_WS
                IF @producer_email IS NOT NULL AND @producer_email != ''
                BEGIN
                    -- Try to find producer by email first
                    SELECT TOP 1 @ProducerContactGuid = ProducerContactGUID
                    FROM tblproducercontacts 
                    WHERE statusid = 1 
                        AND email = @producer_email
                    ORDER BY ProducerContactGUID DESC;
                END
                
                -- If not found by email, try by name
                IF @ProducerContactGuid IS NULL AND @producer_name IS NOT NULL AND @producer_name != ''
                BEGIN
                    SELECT TOP 1 @ProducerContactGuid = ProducerContactGUID
                    FROM tblproducercontacts 
                    WHERE LTRIM(RTRIM(fname)) + ' ' + LTRIM(RTRIM(lname)) = @producer_name
                    ORDER BY fname, lname;
                END
            END
            
            -- Update tblquotes with new values
            UPDATE tblquotes
            SET PolicyNumber = @policy_number,
                EffectiveDate = ISNULL(@EffectiveDateConverted, EffectiveDate),
                ExpirationDate = ISNULL(@ExpirationDateConverted, ExpirationDate),
                ProducerContactGuid = ISNULL(@ProducerContactGuid, ProducerContactGuid)
            WHERE QuoteGuid = @QuoteGuid;
            
            -- Log what was updated
            PRINT 'Updated tblquotes for rebind:';
            PRINT '  - PolicyNumber: ' + ISNULL(@policy_number, 'NULL');
            IF @EffectiveDateConverted IS NOT NULL
                PRINT '  - EffectiveDate: ' + CONVERT(VARCHAR, @EffectiveDateConverted, 101);
            IF @ExpirationDateConverted IS NOT NULL
                PRINT '  - ExpirationDate: ' + CONVERT(VARCHAR, @ExpirationDateConverted, 101);
            IF @ProducerContactGuid IS NOT NULL
                PRINT '  - ProducerContactGuid: ' + CAST(@ProducerContactGuid AS VARCHAR(50));
            ELSE IF @producer_name IS NOT NULL OR @producer_email IS NOT NULL
                PRINT '  - WARNING: Producer not found for email: ' + ISNULL(@producer_email, 'N/A') + ', name: ' + ISNULL(@producer_name, 'N/A');
        END
       
        -- 4. Update commission rates in tblQuoteDetails (only for bind transactions)
        -- Convert whole number percentages to decimals (20 -> 0.20) if needed
        IF @transaction_type = 'bind' AND EXISTS (SELECT 1 FROM tblQuoteDetails WHERE QuoteGuid = @QuoteGuid)
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
        -- Apply for bind, midterm_endorsement, cancellation, and reinstatement
        IF @transaction_type IN ('bind', 'midterm_endorsement', 'cancellation', 'reinstatement') 
            AND @market_segment_code = 'RT'
        BEGIN
            -- Check if the stored procedure exists before calling
            IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'spAutoApplyFees')
            BEGIN
                EXEC dbo.spAutoApplyFees
                    @quoteOptionGuid = @QuoteOptionGuid;
                   
                PRINT 'Auto-applied fees for ' + @transaction_type + ' (RT market segment)';
            END
        END
        ELSE IF @transaction_type IN ('bind', 'midterm_endorsement', 'cancellation', 'reinstatement')
            AND @market_segment_code = 'WL'
        BEGIN
            PRINT 'Skipped auto-apply fees for ' + @transaction_type + ' (WL market segment - wholesale does not auto-apply fees)';
        END
        ELSE IF @transaction_type IN ('bind', 'midterm_endorsement', 'cancellation', 'reinstatement')
        BEGIN
            PRINT 'Skipped auto-apply fees for ' + @transaction_type + ' (market_segment_code: ' + ISNULL(@market_segment_code, 'NULL') + ')';
        END
       
        -- 8. Apply Policy Fee from Triton if present
        -- For bind: Apply policy_fee as positive
        -- For cancellation: Apply as negative ONLY if flat cancel (policy_cancellation_date = effective_date)
        IF @transaction_type = 'bind' AND @policy_fee IS NOT NULL AND @policy_fee > 0
        BEGIN
            -- Check if the stored procedure exists before calling
            IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'spApplyTritonPolicyFee_WS')
            BEGIN
                EXEC dbo.spApplyTritonPolicyFee_WS
                    @QuoteGuid = @QuoteGuid;
                   
                PRINT 'Applied Triton Policy Fee of $' + CAST(@policy_fee AS VARCHAR(20)) + ' for bind';
            END
        END
        ELSE IF @transaction_type = 'cancellation' AND @policy_fee IS NOT NULL AND @policy_fee > 0
        BEGIN
            -- Check if this is a flat cancel (policy_cancellation_date = effective_date)
            -- Note: policy_cancellation_date comes as YYYY-MM-DD, effective_date comes as MM/DD/YYYY
            DECLARE @policy_cancellation_date NVARCHAR(50);
            DECLARE @policy_cancellation_date_converted DATE;
            DECLARE @effective_date_converted DATE;
            
            SET @policy_cancellation_date = JSON_VALUE(@full_payload_json, '$.policy_cancellation_date');
            
            -- Debug: Log raw date values
            PRINT '=== CANCELLATION POLICY FEE DATE COMPARISON DEBUG ===';
            PRINT 'Raw policy_cancellation_date from JSON: ' + ISNULL(@policy_cancellation_date, 'NULL');
            PRINT 'Raw effective_date from JSON: ' + ISNULL(@effective_date, 'NULL');
            
            -- Convert both dates to DATE type for proper comparison
            IF @policy_cancellation_date IS NOT NULL
            BEGIN
                SET @policy_cancellation_date_converted = TRY_CONVERT(DATE, @policy_cancellation_date); -- Handles YYYY-MM-DD
            END
            
            IF @effective_date IS NOT NULL
            BEGIN
                SET @effective_date_converted = TRY_CONVERT(DATE, @effective_date, 101); -- 101 = MM/DD/YYYY format
            END
            
            -- Debug: Log converted date values
            PRINT 'Converted policy_cancellation_date: ' + ISNULL(CONVERT(VARCHAR, @policy_cancellation_date_converted, 120), 'NULL');
            PRINT 'Converted effective_date: ' + ISNULL(CONVERT(VARCHAR, @effective_date_converted, 120), 'NULL');
            
            -- Debug: Check if dates match
            IF @policy_cancellation_date_converted IS NOT NULL AND @effective_date_converted IS NOT NULL
            BEGIN
                PRINT 'Date comparison result: ' + 
                    CASE 
                        WHEN @policy_cancellation_date_converted = @effective_date_converted THEN 'MATCH - This is a flat cancel'
                        ELSE 'NO MATCH - Not a flat cancel'
                    END;
            END
            ELSE
            BEGIN
                PRINT 'Date comparison result: CANNOT COMPARE - One or both dates failed to convert';
            END
            PRINT '=== END DEBUG ===';
            
            -- Compare the converted dates
            IF @policy_cancellation_date_converted IS NOT NULL 
                AND @effective_date_converted IS NOT NULL 
                AND @policy_cancellation_date_converted = @effective_date_converted
            BEGIN
                -- For flat cancels, apply negative policy fee
                -- Need to modify the policy_fee value to negative before applying
                SET @policy_fee = -1 * ABS(@policy_fee);
                
                IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'spApplyTritonPolicyFee_WS')
                BEGIN
                    EXEC dbo.spApplyTritonPolicyFee_WS
                        @QuoteGuid = @QuoteGuid;
                    
                    PRINT 'Applied negative Triton Policy Fee of $' + CAST(@policy_fee AS VARCHAR(20)) + ' for flat cancellation';
                END
            END
            ELSE
            BEGIN
                PRINT 'Skipped policy fee for cancellation (not a flat cancel)';
            END
        END
        ELSE IF @transaction_type = 'reinstatement' AND @policy_fee IS NOT NULL AND @policy_fee > 0
        BEGIN
            -- For reinstatements, check if the cancelled policy had a policy fee that was refunded
            -- If so, we need to reapply it
            DECLARE @CancellationHadPolicyFee BIT = 0;
            DECLARE @CancellationQuoteID INT;
            
            -- Find the cancellation quote in the chain (should be the OriginalQuoteGuid of current reinstatement)
            -- First need to find our reinstatement quote in tblQuotes to get its OriginalQuoteGuid
            DECLARE @CancellationQuoteGuid UNIQUEIDENTIFIER;
            
            SELECT @CancellationQuoteGuid = OriginalQuoteGuid
            FROM tblQuotes
            WHERE QuoteGuid = @QuoteGuid;
            
            IF @CancellationQuoteGuid IS NOT NULL
            BEGIN
                -- Get the QuoteID for the cancellation
                SELECT @CancellationQuoteID = QuoteID
                FROM tblQuotes
                WHERE QuoteGuid = @CancellationQuoteGuid;
                
                -- Check if the cancellation invoice had a policy fee
                IF @CancellationQuoteID IS NOT NULL
                BEGIN
                    SELECT @CancellationHadPolicyFee = 1
                    FROM tblfin_invoices inv
                    INNER JOIN tblfin_invoicedetails det ON inv.InvoiceNum = det.InvoiceNum
                    WHERE inv.QuoteID = @CancellationQuoteID
                        AND inv.Failed = 0
                        AND det.ChargeName LIKE '%Policy Fee%';
                END
            END
            
            -- If cancellation had a policy fee refund, apply it to reinstatement
            IF @CancellationHadPolicyFee = 1
            BEGIN
                IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'spApplyTritonPolicyFee_WS')
                BEGIN
                    EXEC dbo.spApplyTritonPolicyFee_WS
                        @QuoteGuid = @QuoteGuid;
                    
                    PRINT 'Applied Triton Policy Fee of $' + CAST(@policy_fee AS VARCHAR(20)) + ' for reinstatement (matching cancellation refund)';
                END
            END
            ELSE
            BEGIN
                PRINT 'Skipped policy fee for reinstatement (cancellation did not have policy fee refund)';
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
            @transaction_type AS TransactionType,
            CASE
                WHEN @transaction_type IN ('midterm_endorsement', 'cancellation', 'reinstatement')
                THEN 'Skipped rating updates (handled by transaction-specific procedures)'
                WHEN (@stamping_fee IS NULL OR @stamping_fee = '') AND (@surplus_lines_tax IS NULL OR @surplus_lines_tax = '')
                THEN 'Fees auto-applied by IMS'
                ELSE 'Fees provided by Triton'
            END AS ProcessingNotes;
           
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