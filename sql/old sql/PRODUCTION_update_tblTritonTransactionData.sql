-- Production script to create or update tblTritonTransactionData
-- This script will create the table if it doesn't exist, or add missing columns if it does

-- First, create the table if it doesn't exist
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'tblTritonTransactionData')
BEGIN
    CREATE TABLE [dbo].[tblTritonTransactionData] (
        -- Primary identifier
        [TritonTransactionDataID] INT IDENTITY(1,1) NOT NULL,
        [transaction_id] NVARCHAR(100) NOT NULL,
        
        -- Quote identifiers
        [QuoteGuid] UNIQUEIDENTIFIER NOT NULL,
        [QuoteOptionGuid] UNIQUEIDENTIFIER,
        
        -- Full JSON payload for audit trail
        [full_payload_json] NVARCHAR(MAX) NULL,
        
        -- Renewal information
        [renewal_of_quote_guid] UNIQUEIDENTIFIER NULL,
        
        -- UMR fields
        [umr] NVARCHAR(100) NULL,
        [agreement_number] NVARCHAR(100) NULL,
        [section_number] NVARCHAR(100) NULL,
        
        -- Business information
        [class_of_business] NVARCHAR(200),
        [program_name] NVARCHAR(200),
        [policy_number] NVARCHAR(50),
        [expiring_policy_number] NVARCHAR(50) NULL,
        
        -- Personnel
        [underwriter_name] NVARCHAR(200),
        [producer_name] NVARCHAR(200),
        
        -- Dates
        [invoice_date] NVARCHAR(50),
        [effective_date] NVARCHAR(50),
        [expiration_date] NVARCHAR(50),
        [bound_date] NVARCHAR(50),
        
        -- Fees
        [policy_fee] DECIMAL(18,2) NULL,
        [surplus_lines_tax] NVARCHAR(50) NULL,
        [stamping_fee] NVARCHAR(50) NULL,
        [other_fee] NVARCHAR(50) NULL,
        
        -- Insured information
        [insured_name] NVARCHAR(500),
        [insured_state] NVARCHAR(2),
        [insured_zip] NVARCHAR(10),
        
        -- Business details
        [opportunity_type] NVARCHAR(100),
        [business_type] NVARCHAR(100),
        [status] NVARCHAR(100),
        
        -- Coverage limits
        [limit_amount] NVARCHAR(100),
        [limit_prior] NVARCHAR(100),
        [deductible_amount] NVARCHAR(100),
        
        -- Premium information
        [gross_premium] DECIMAL(18,2),
        [commission_rate] DECIMAL(5,2),
        [commission_percent] DECIMAL(5,2) NULL,
        [commission_amount] DECIMAL(18,2) NULL,
        [net_premium] DECIMAL(18,2),
        [base_premium] DECIMAL(18,2),
        
        -- Opportunity information
        [opportunity_id] INT,
        
        -- Midterm endorsement fields
        [midterm_endt_id] INT NULL,
        [midterm_endt_description] NVARCHAR(500) NULL,
        [midterm_endt_effective_from] NVARCHAR(50) NULL,
        [midterm_endt_endorsement_number] NVARCHAR(50) NULL,
        
        -- Additional insured (JSON)
        [additional_insured] NVARCHAR(MAX) NULL,
        
        -- Address information
        [address_1] NVARCHAR(200),
        [address_2] NVARCHAR(200) NULL,
        [city] NVARCHAR(100),
        [state] NVARCHAR(2),
        [zip] NVARCHAR(10),
        
        -- Transaction information
        [prior_transaction_id] NVARCHAR(100) NULL,
        [transaction_type] NVARCHAR(100),
        [transaction_date] NVARCHAR(50),
        [source_system] NVARCHAR(50),
        
        -- Timestamps
        [created_date] DATETIME NOT NULL DEFAULT GETDATE(),
        [last_updated] DATETIME NOT NULL DEFAULT GETDATE(),
        
        -- Constraints
        CONSTRAINT [PK_tblTritonTransactionData] PRIMARY KEY CLUSTERED ([TritonTransactionDataID] ASC),
        CONSTRAINT [UQ_tblTritonTransactionData_transaction_id] UNIQUE NONCLUSTERED ([transaction_id])
    );

    -- Create indexes for better performance
    CREATE INDEX [IX_tblTritonTransactionData_QuoteGuid] ON [dbo].[tblTritonTransactionData] ([QuoteGuid]);
    CREATE INDEX [IX_tblTritonTransactionData_QuoteOptionGuid] ON [dbo].[tblTritonTransactionData] ([QuoteOptionGuid]);
    CREATE INDEX [IX_tblTritonTransactionData_policy_number] ON [dbo].[tblTritonTransactionData] ([policy_number]);
    CREATE INDEX [IX_tblTritonTransactionData_prior_transaction_id] ON [dbo].[tblTritonTransactionData] ([prior_transaction_id]);
    CREATE INDEX [IX_tblTritonTransactionData_renewal_of_quote_guid] ON [dbo].[tblTritonTransactionData] ([renewal_of_quote_guid]);
    CREATE INDEX [IX_tblTritonTransactionData_transaction_type] ON [dbo].[tblTritonTransactionData] ([transaction_type]);
    CREATE INDEX [IX_tblTritonTransactionData_created_date] ON [dbo].[tblTritonTransactionData] ([created_date]);

    -- Grant permissions
    GRANT SELECT, INSERT ON [dbo].[tblTritonTransactionData] TO [IMS_User];

    PRINT 'Table tblTritonTransactionData created successfully';
END
ELSE
BEGIN
    PRINT 'Table tblTritonTransactionData already exists - checking for missing columns';
    
    -- Add any missing columns
    -- transaction_id
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'transaction_id')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [transaction_id] NVARCHAR(100) NOT NULL DEFAULT '';
        PRINT 'Added column: transaction_id';
    END
    
    -- QuoteGuid
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'QuoteGuid')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [QuoteGuid] UNIQUEIDENTIFIER NOT NULL;
        PRINT 'Added column: QuoteGuid';
    END
    
    -- QuoteOptionGuid
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'QuoteOptionGuid')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [QuoteOptionGuid] UNIQUEIDENTIFIER NULL;
        PRINT 'Added column: QuoteOptionGuid';
    END
    
    -- full_payload_json
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'full_payload_json')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [full_payload_json] NVARCHAR(MAX) NULL;
        PRINT 'Added column: full_payload_json';
    END
    
    -- renewal_of_quote_guid
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'renewal_of_quote_guid')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [renewal_of_quote_guid] UNIQUEIDENTIFIER NULL;
        PRINT 'Added column: renewal_of_quote_guid';
    END
    
    -- umr
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'umr')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [umr] NVARCHAR(100) NULL;
        PRINT 'Added column: umr';
    END
    
    -- agreement_number
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'agreement_number')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [agreement_number] NVARCHAR(100) NULL;
        PRINT 'Added column: agreement_number';
    END
    
    -- section_number
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'section_number')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [section_number] NVARCHAR(100) NULL;
        PRINT 'Added column: section_number';
    END
    
    -- class_of_business
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'class_of_business')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [class_of_business] NVARCHAR(200) NULL;
        PRINT 'Added column: class_of_business';
    END
    
    -- program_name
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'program_name')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [program_name] NVARCHAR(200) NULL;
        PRINT 'Added column: program_name';
    END
    
    -- policy_number
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'policy_number')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [policy_number] NVARCHAR(50) NULL;
        PRINT 'Added column: policy_number';
    END
    
    -- expiring_policy_number
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'expiring_policy_number')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [expiring_policy_number] NVARCHAR(50) NULL;
        PRINT 'Added column: expiring_policy_number';
    END
    
    -- underwriter_name
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'underwriter_name')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [underwriter_name] NVARCHAR(200) NULL;
        PRINT 'Added column: underwriter_name';
    END
    
    -- producer_name
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'producer_name')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [producer_name] NVARCHAR(200) NULL;
        PRINT 'Added column: producer_name';
    END
    
    -- invoice_date
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'invoice_date')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [invoice_date] NVARCHAR(50) NULL;
        PRINT 'Added column: invoice_date';
    END
    
    -- effective_date
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'effective_date')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [effective_date] NVARCHAR(50) NULL;
        PRINT 'Added column: effective_date';
    END
    
    -- expiration_date
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'expiration_date')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [expiration_date] NVARCHAR(50) NULL;
        PRINT 'Added column: expiration_date';
    END
    
    -- bound_date
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'bound_date')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [bound_date] NVARCHAR(50) NULL;
        PRINT 'Added column: bound_date';
    END
    
    -- policy_fee
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'policy_fee')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [policy_fee] DECIMAL(18,2) NULL;
        PRINT 'Added column: policy_fee';
    END
    
    -- surplus_lines_tax
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'surplus_lines_tax')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [surplus_lines_tax] NVARCHAR(50) NULL;
        PRINT 'Added column: surplus_lines_tax';
    END
    
    -- stamping_fee
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'stamping_fee')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [stamping_fee] NVARCHAR(50) NULL;
        PRINT 'Added column: stamping_fee';
    END
    
    -- other_fee
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'other_fee')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [other_fee] NVARCHAR(50) NULL;
        PRINT 'Added column: other_fee';
    END
    
    -- insured_name
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'insured_name')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [insured_name] NVARCHAR(500) NULL;
        PRINT 'Added column: insured_name';
    END
    
    -- insured_state
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'insured_state')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [insured_state] NVARCHAR(2) NULL;
        PRINT 'Added column: insured_state';
    END
    
    -- insured_zip
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'insured_zip')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [insured_zip] NVARCHAR(10) NULL;
        PRINT 'Added column: insured_zip';
    END
    
    -- opportunity_type
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'opportunity_type')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [opportunity_type] NVARCHAR(100) NULL;
        PRINT 'Added column: opportunity_type';
    END
    
    -- business_type
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'business_type')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [business_type] NVARCHAR(100) NULL;
        PRINT 'Added column: business_type';
    END
    
    -- status
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'status')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [status] NVARCHAR(100) NULL;
        PRINT 'Added column: status';
    END
    
    -- limit_amount
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'limit_amount')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [limit_amount] NVARCHAR(100) NULL;
        PRINT 'Added column: limit_amount';
    END
    
    -- limit_prior
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'limit_prior')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [limit_prior] NVARCHAR(100) NULL;
        PRINT 'Added column: limit_prior';
    END
    
    -- deductible_amount
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'deductible_amount')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [deductible_amount] NVARCHAR(100) NULL;
        PRINT 'Added column: deductible_amount';
    END
    
    -- gross_premium
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'gross_premium')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [gross_premium] DECIMAL(18,2) NULL;
        PRINT 'Added column: gross_premium';
    END
    
    -- commission_rate
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'commission_rate')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [commission_rate] DECIMAL(5,2) NULL;
        PRINT 'Added column: commission_rate';
    END
    
    -- commission_percent
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'commission_percent')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [commission_percent] DECIMAL(5,2) NULL;
        PRINT 'Added column: commission_percent';
    END
    
    -- commission_amount
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'commission_amount')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [commission_amount] DECIMAL(18,2) NULL;
        PRINT 'Added column: commission_amount';
    END
    
    -- net_premium
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'net_premium')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [net_premium] DECIMAL(18,2) NULL;
        PRINT 'Added column: net_premium';
    END
    
    -- base_premium
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'base_premium')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [base_premium] DECIMAL(18,2) NULL;
        PRINT 'Added column: base_premium';
    END
    
    -- opportunity_id
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'opportunity_id')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [opportunity_id] INT NULL;
        PRINT 'Added column: opportunity_id';
    END
    
    -- midterm_endt_id
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'midterm_endt_id')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [midterm_endt_id] INT NULL;
        PRINT 'Added column: midterm_endt_id';
    END
    
    -- midterm_endt_description
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'midterm_endt_description')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [midterm_endt_description] NVARCHAR(500) NULL;
        PRINT 'Added column: midterm_endt_description';
    END
    
    -- midterm_endt_effective_from
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'midterm_endt_effective_from')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [midterm_endt_effective_from] NVARCHAR(50) NULL;
        PRINT 'Added column: midterm_endt_effective_from';
    END
    
    -- midterm_endt_endorsement_number
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'midterm_endt_endorsement_number')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [midterm_endt_endorsement_number] NVARCHAR(50) NULL;
        PRINT 'Added column: midterm_endt_endorsement_number';
    END
    
    -- additional_insured
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'additional_insured')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [additional_insured] NVARCHAR(MAX) NULL;
        PRINT 'Added column: additional_insured';
    END
    
    -- address_1
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'address_1')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [address_1] NVARCHAR(200) NULL;
        PRINT 'Added column: address_1';
    END
    
    -- address_2
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'address_2')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [address_2] NVARCHAR(200) NULL;
        PRINT 'Added column: address_2';
    END
    
    -- city
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'city')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [city] NVARCHAR(100) NULL;
        PRINT 'Added column: city';
    END
    
    -- state
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'state')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [state] NVARCHAR(2) NULL;
        PRINT 'Added column: state';
    END
    
    -- zip
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'zip')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [zip] NVARCHAR(10) NULL;
        PRINT 'Added column: zip';
    END
    
    -- prior_transaction_id
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'prior_transaction_id')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [prior_transaction_id] NVARCHAR(100) NULL;
        PRINT 'Added column: prior_transaction_id';
    END
    
    -- transaction_type
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'transaction_type')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [transaction_type] NVARCHAR(100) NULL;
        PRINT 'Added column: transaction_type';
    END
    
    -- transaction_date
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'transaction_date')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [transaction_date] NVARCHAR(50) NULL;
        PRINT 'Added column: transaction_date';
    END
    
    -- source_system
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'source_system')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [source_system] NVARCHAR(50) NULL;
        PRINT 'Added column: source_system';
    END
    
    -- created_date
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'created_date')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [created_date] DATETIME NOT NULL DEFAULT GETDATE();
        PRINT 'Added column: created_date';
    END
    
    -- last_updated
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonTransactionData') AND name = 'last_updated')
    BEGIN
        ALTER TABLE [dbo].[tblTritonTransactionData] ADD [last_updated] DATETIME NOT NULL DEFAULT GETDATE();
        PRINT 'Added column: last_updated';
    END
    
    -- Add indexes if they don't exist
    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_tblTritonTransactionData_QuoteGuid')
    BEGIN
        CREATE INDEX [IX_tblTritonTransactionData_QuoteGuid] ON [dbo].[tblTritonTransactionData] ([QuoteGuid]);
        PRINT 'Added index: IX_tblTritonTransactionData_QuoteGuid';
    END
    
    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_tblTritonTransactionData_renewal_of_quote_guid')
    BEGIN
        CREATE INDEX [IX_tblTritonTransactionData_renewal_of_quote_guid] ON [dbo].[tblTritonTransactionData] ([renewal_of_quote_guid]);
        PRINT 'Added index: IX_tblTritonTransactionData_renewal_of_quote_guid';
    END
    
    -- Grant permissions
    GRANT SELECT, INSERT ON [dbo].[tblTritonTransactionData] TO [IMS_User];
    
    PRINT 'Table tblTritonTransactionData update complete';
END
GO