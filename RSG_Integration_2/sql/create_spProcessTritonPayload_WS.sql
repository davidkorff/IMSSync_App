-- Stored procedure to process Triton payload data
-- Inserts into tblTritonQuoteData, updates policy number, and registers premium

CREATE OR ALTER PROCEDURE [dbo].[spProcessTritonPayload_WS]
    -- Quote identifiers
    @QuoteGuid UNIQUEIDENTIFIER,
    @QuoteOptionGuid UNIQUEIDENTIFIER,
    
    -- Payload fields
    @umr NVARCHAR(100) = NULL,
    @agreement_number NVARCHAR(100) = NULL,
    @section_number NVARCHAR(100) = NULL,
    @class_of_business NVARCHAR(200),
    @program_name NVARCHAR(200),
    @policy_number NVARCHAR(50),
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
    @transaction_type NVARCHAR(100),
    @transaction_date NVARCHAR(50),
    @source_system NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        BEGIN TRANSACTION;
        
        -- 1. Insert or update data in tblTritonQuoteData
        -- Check if record exists for this quote
        IF EXISTS (SELECT 1 FROM tblTritonQuoteData WHERE QuoteGuid = @QuoteGuid)
        BEGIN
            -- Update existing record with latest transaction data
            UPDATE tblTritonQuoteData
            SET 
                QuoteOptionGuid = @QuoteOptionGuid,
                umr = @umr,
                agreement_number = @agreement_number,
                section_number = @section_number,
                class_of_business = @class_of_business,
                program_name = @program_name,
                policy_number = @policy_number,
                underwriter_name = @underwriter_name,
                producer_name = @producer_name,
                invoice_date = @invoice_date,
                policy_fee = @policy_fee,
                surplus_lines_tax = @surplus_lines_tax,
                stamping_fee = @stamping_fee,
                other_fee = @other_fee,
                insured_name = @insured_name,
                insured_state = @insured_state,
                insured_zip = @insured_zip,
                effective_date = @effective_date,
                expiration_date = @expiration_date,
                bound_date = @bound_date,
                opportunity_type = @opportunity_type,
                business_type = @business_type,
                status = @status,
                limit_amount = @limit_amount,
                limit_prior = @limit_prior,
                deductible_amount = @deductible_amount,
                gross_premium = @gross_premium,
                commission_rate = @commission_rate,
                commission_percent = @commission_percent,
                commission_amount = @commission_amount,
                net_premium = @net_premium,
                base_premium = @base_premium,
                opportunity_id = @opportunity_id,
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
                transaction_id = @transaction_id,
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
                umr,
                agreement_number,
                section_number,
                class_of_business,
                program_name,
                policy_number,
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
                transaction_id,
                transaction_type,
                transaction_date,
                source_system,
                created_date,
                last_updated
            ) VALUES (
                @QuoteGuid,
                @QuoteOptionGuid,
                @umr,
                @agreement_number,
                @section_number,
                @class_of_business,
                @program_name,
                @policy_number,
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
                @transaction_id,
                @transaction_type,
                @transaction_date,
                @source_system,
                GETDATE(),
                GETDATE()
            );
        END
        
        -- 2. Update policy number in tblquotes
        UPDATE tblquotes 
        SET PolicyNumber = @policy_number 
        WHERE QuoteGuid = @QuoteGuid;
        
        -- 3. Register the premium using UpdatePremiumHistoricV3
        -- This assumes net_premium column exists in tblTritonQuoteData
        EXEC dbo.UpdatePremiumHistoricV3
            @quoteOptionGuid        = @QuoteOptionGuid,
            @RawPremiumHistoryTable = 'tblTritonQuoteData',
            @PremiumField           = 'net_premium';
        
        COMMIT TRANSACTION;
        
        -- Return success
        SELECT 
            'Success' AS Status,
            'Payload processed successfully' AS Message,
            @QuoteGuid AS QuoteGuid,
            @QuoteOptionGuid AS QuoteOptionGuid;
            
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
            
        -- Return error information
        SELECT 
            'Error' AS Status,
            ERROR_MESSAGE() AS Message,
            ERROR_NUMBER() AS ErrorNumber,
            ERROR_LINE() AS ErrorLine;
    END CATCH
END
GO

-- Grant execute permissions
GRANT EXECUTE ON spProcessTritonPayload_WS TO [IMS_User];
GO