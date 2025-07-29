-- Production stored procedure to process Triton payload data
-- Inserts into both tblTritonQuoteData and tblTritonTransactionData
-- Updates policy number and registers premium
-- Uses JSON parsing to extract values from the payload

IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'spProcessTritonPayload_WS')
BEGIN
    DROP PROCEDURE [dbo].[spProcessTritonPayload_WS];
END
GO

CREATE PROCEDURE [dbo].[spProcessTritonPayload_WS]
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
                @other_fee NVARCHAR(50),
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
                @source_system NVARCHAR(50);
        
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
        SET @other_fee = JSON_VALUE(@full_payload_json, '$.other_fee');
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
        
        -- Handle empty strings as NULL for certain fields
        IF @surplus_lines_tax = '' SET @surplus_lines_tax = NULL;
        IF @stamping_fee = '' SET @stamping_fee = NULL;
        IF @other_fee = '' SET @other_fee = NULL;
        IF @address_2 = '' SET @address_2 = NULL;
        IF @midterm_endt_effective_from = '' SET @midterm_endt_effective_from = NULL;
        
        -- 1. ALWAYS insert into tblTritonTransactionData (keeps full history)
        INSERT INTO tblTritonTransactionData (
            transaction_id,
            QuoteGuid,
            QuoteOptionGuid,
            full_payload_json,
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
            invoice_date,
            policy_fee,
            surplus_lines_tax,
            stamping_fee,
            other_fee,
            insured_name,
            insured_state,
            insured_zip,
            effective_date,
            expiration_date,
            bound_date,
            opportunity_type,
            business_type,
            status,
            limit_amount,
            limit_prior,
            deductible_amount,
            gross_premium,
            commission_rate,
            commission_percent,
            commission_amount,
            net_premium,
            base_premium,
            opportunity_id,
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
            prior_transaction_id,
            transaction_type,
            transaction_date,
            source_system,
            created_date,
            last_updated
        ) VALUES (
            @transaction_id,
            @QuoteGuid,
            @QuoteOptionGuid,
            @full_payload_json,
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
            @invoice_date,
            @policy_fee,
            @surplus_lines_tax,
            @stamping_fee,
            @other_fee,
            @insured_name,
            @insured_state,
            @insured_zip,
            @effective_date,
            @expiration_date,
            @bound_date,
            @opportunity_type,
            @business_type,
            @status,
            @limit_amount,
            @limit_prior,
            @deductible_amount,
            @gross_premium,
            @commission_rate,
            @commission_percent,
            @commission_amount,
            @net_premium,
            @base_premium,
            @opportunity_id,
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
            @prior_transaction_id,
            @transaction_type,
            @transaction_date,
            @source_system,
            GETDATE(),
            GETDATE()
        );
        
        -- 2. Insert or update data in tblTritonQuoteData
        -- Check if record exists for this quote
        IF EXISTS (SELECT 1 FROM tblTritonQuoteData WHERE QuoteGuid = @QuoteGuid)
        BEGIN
            -- Update existing record with latest transaction data
            UPDATE tblTritonQuoteData
            SET 
                QuoteOptionGuid = @QuoteOptionGuid,
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
                business_type = @business_type,
                status = @status,
                limit_amount = @limit_amount,
                deductible_amount = @deductible_amount,
                gross_premium = @gross_premium,
                commission_rate = @commission_rate,
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
                last_updated = GETDATE()
            WHERE QuoteGuid = @QuoteGuid;
        END
        ELSE
        BEGIN
            -- Insert new record
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
                transaction_type,
                transaction_date,
                source_system,
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
                @transaction_type,
                @transaction_date,
                @source_system,
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
        
        -- 4. Register the premium using UpdatePremiumHistoricV3
        -- Check if the stored procedure exists before calling
        IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'UpdatePremiumHistoricV3')
        BEGIN
            EXEC dbo.UpdatePremiumHistoricV3
                @quoteOptionGuid        = @QuoteOptionGuid,
                @RawPremiumHistoryTable = 'tblTritonQuoteData',
                @PremiumField           = 'gross_premium';
        END
        
        COMMIT TRANSACTION;
        
        -- Return success
        SELECT 
            'Success' AS Status,
            'Payload processed successfully' AS Message,
            @QuoteGuid AS QuoteGuid,
            @QuoteOptionGuid AS QuoteOptionGuid,
            @transaction_id AS TransactionId;
            
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
GO


GO

PRINT 'Stored procedure spProcessTritonPayload_WS created successfully';
GO