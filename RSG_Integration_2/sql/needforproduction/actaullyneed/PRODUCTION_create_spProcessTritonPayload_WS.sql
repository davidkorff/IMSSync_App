-- Production stored procedure to process Triton payload data
-- Inserts into both tblTritonQuoteData and tblTritonTransactionData
-- Updates policy number and registers premium

IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'spProcessTritonPayload_WS')
BEGIN
    DROP PROCEDURE [dbo].[spProcessTritonPayload_WS];
END
GO

CREATE PROCEDURE [dbo].[spProcessTritonPayload_WS]
    -- Quote identifiers
    @QuoteGuid UNIQUEIDENTIFIER,
    @QuoteOptionGuid UNIQUEIDENTIFIER,
    
    -- Full JSON payload for audit trail
    @full_payload_json NVARCHAR(MAX),
    
    -- Renewal information
    @renewal_of_quote_guid UNIQUEIDENTIFIER = NULL,
    
    -- Payload fields
    @umr NVARCHAR(100) = NULL,
    @agreement_number NVARCHAR(100) = NULL,
    @section_number NVARCHAR(100) = NULL,
    @class_of_business NVARCHAR(200),
    @program_name NVARCHAR(200),
    @policy_number NVARCHAR(50),
    @expiring_policy_number NVARCHAR(50) = NULL,
    @underwriter_name NVARCHAR(200),
    @producer_name NVARCHAR(200),
    @invoice_date NVARCHAR(50),
    @policy_fee DECIMAL(18,2) = NULL,
    @surplus_lines_tax NVARCHAR(50) = NULL,
    @stamping_fee NVARCHAR(50) = NULL,
    @other_fee NVARCHAR(50) = NULL,
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
    @commission_percent DECIMAL(5,2) = NULL,
    @commission_amount DECIMAL(18,2) = NULL,
    @net_premium DECIMAL(18,2),
    @base_premium DECIMAL(18,2),
    @opportunity_id INT,
    @midterm_endt_id INT = NULL,
    @midterm_endt_description NVARCHAR(500) = NULL,
    @midterm_endt_effective_from NVARCHAR(50) = NULL,
    @midterm_endt_endorsement_number NVARCHAR(50) = NULL,
    @additional_insured NVARCHAR(MAX) = NULL,
    @address_1 NVARCHAR(200),
    @address_2 NVARCHAR(200) = NULL,
    @city NVARCHAR(100),
    @state NVARCHAR(2),
    @zip NVARCHAR(10),
    @transaction_id NVARCHAR(100),
    @prior_transaction_id NVARCHAR(100) = NULL,
    @transaction_type NVARCHAR(100),
    @transaction_date NVARCHAR(50),
    @source_system NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        BEGIN TRANSACTION;
        
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

-- Grant execute permissions
GRANT EXECUTE ON [dbo].[spProcessTritonPayload_WS] TO [IMS_User];
GO

PRINT 'Stored procedure spProcessTritonPayload_WS created successfully';
GO