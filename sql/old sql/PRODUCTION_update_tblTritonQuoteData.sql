-- Production script to create or update tblTritonQuoteData
-- This script will create the table if it doesn't exist, or add missing columns if it does

-- First, create the table if it doesn't exist
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'tblTritonQuoteData')
BEGIN
    CREATE TABLE [dbo].[tblTritonQuoteData] (
        -- Primary key
        [TritonQuoteDataID] INT IDENTITY(1,1) NOT NULL,
        
        -- Quote identifiers (QuoteGuid is the main business key)
        [QuoteGuid] UNIQUEIDENTIFIER NOT NULL,
        [QuoteOptionGuid] UNIQUEIDENTIFIER,
        
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
        [effective_date] NVARCHAR(50),
        [expiration_date] NVARCHAR(50),
        [bound_date] NVARCHAR(50),
        
        -- Insured information
        [insured_name] NVARCHAR(500),
        [insured_state] NVARCHAR(2),
        [insured_zip] NVARCHAR(10),
        
        -- Business details
        [business_type] NVARCHAR(100),
        [status] NVARCHAR(100),
        
        -- Coverage limits
        [limit_amount] NVARCHAR(100),
        [deductible_amount] NVARCHAR(100),
        
        -- Premium information
        [gross_premium] DECIMAL(18,2),
        [commission_rate] DECIMAL(5,2),
        
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
        [transaction_type] NVARCHAR(100),
        [transaction_date] NVARCHAR(50),
        [source_system] NVARCHAR(50),
        
        -- Timestamps
        [created_date] DATETIME NOT NULL DEFAULT GETDATE(),
        [last_updated] DATETIME NOT NULL DEFAULT GETDATE(),
        
        -- Constraints
        CONSTRAINT [PK_tblTritonQuoteData] PRIMARY KEY CLUSTERED ([TritonQuoteDataID] ASC),
        CONSTRAINT [UQ_tblTritonQuoteData_QuoteGuid] UNIQUE NONCLUSTERED ([QuoteGuid])
    );

    -- Create indexes for better performance
    CREATE INDEX [IX_tblTritonQuoteData_QuoteOptionGuid] ON [dbo].[tblTritonQuoteData] ([QuoteOptionGuid]);
    CREATE INDEX [IX_tblTritonQuoteData_policy_number] ON [dbo].[tblTritonQuoteData] ([policy_number]);
    CREATE INDEX [IX_tblTritonQuoteData_renewal_of_quote_guid] ON [dbo].[tblTritonQuoteData] ([renewal_of_quote_guid]);
    CREATE INDEX [IX_tblTritonQuoteData_transaction_type] ON [dbo].[tblTritonQuoteData] ([transaction_type]);
    CREATE INDEX [IX_tblTritonQuoteData_created_date] ON [dbo].[tblTritonQuoteData] ([created_date]);

    -- Grant permissions
    GRANT SELECT, INSERT, UPDATE, DELETE ON [dbo].[tblTritonQuoteData] TO [IMS_User];

    PRINT 'Table tblTritonQuoteData created successfully';
END
ELSE
BEGIN
    PRINT 'Table tblTritonQuoteData already exists - checking for missing columns';
    
    -- Add any missing columns
    -- QuoteGuid
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'QuoteGuid')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [QuoteGuid] UNIQUEIDENTIFIER NOT NULL;
        PRINT 'Added column: QuoteGuid';
    END
    
    -- QuoteOptionGuid
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'QuoteOptionGuid')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [QuoteOptionGuid] UNIQUEIDENTIFIER NULL;
        PRINT 'Added column: QuoteOptionGuid';
    END
    
    -- renewal_of_quote_guid
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'renewal_of_quote_guid')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [renewal_of_quote_guid] UNIQUEIDENTIFIER NULL;
        PRINT 'Added column: renewal_of_quote_guid';
    END
    
    -- umr
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'umr')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [umr] NVARCHAR(100) NULL;
        PRINT 'Added column: umr';
    END
    
    -- agreement_number
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'agreement_number')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [agreement_number] NVARCHAR(100) NULL;
        PRINT 'Added column: agreement_number';
    END
    
    -- section_number
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'section_number')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [section_number] NVARCHAR(100) NULL;
        PRINT 'Added column: section_number';
    END
    
    -- class_of_business
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'class_of_business')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [class_of_business] NVARCHAR(200) NULL;
        PRINT 'Added column: class_of_business';
    END
    
    -- program_name
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'program_name')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [program_name] NVARCHAR(200) NULL;
        PRINT 'Added column: program_name';
    END
    
    -- policy_number
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'policy_number')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [policy_number] NVARCHAR(50) NULL;
        PRINT 'Added column: policy_number';
    END
    
    -- expiring_policy_number
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'expiring_policy_number')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [expiring_policy_number] NVARCHAR(50) NULL;
        PRINT 'Added column: expiring_policy_number';
    END
    
    -- underwriter_name
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'underwriter_name')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [underwriter_name] NVARCHAR(200) NULL;
        PRINT 'Added column: underwriter_name';
    END
    
    -- producer_name
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'producer_name')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [producer_name] NVARCHAR(200) NULL;
        PRINT 'Added column: producer_name';
    END
    
    -- effective_date
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'effective_date')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [effective_date] NVARCHAR(50) NULL;
        PRINT 'Added column: effective_date';
    END
    
    -- expiration_date
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'expiration_date')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [expiration_date] NVARCHAR(50) NULL;
        PRINT 'Added column: expiration_date';
    END
    
    -- bound_date
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'bound_date')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [bound_date] NVARCHAR(50) NULL;
        PRINT 'Added column: bound_date';
    END
    
    -- insured_name
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'insured_name')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [insured_name] NVARCHAR(500) NULL;
        PRINT 'Added column: insured_name';
    END
    
    -- insured_state
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'insured_state')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [insured_state] NVARCHAR(2) NULL;
        PRINT 'Added column: insured_state';
    END
    
    -- insured_zip
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'insured_zip')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [insured_zip] NVARCHAR(10) NULL;
        PRINT 'Added column: insured_zip';
    END
    
    -- business_type
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'business_type')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [business_type] NVARCHAR(100) NULL;
        PRINT 'Added column: business_type';
    END
    
    -- status
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'status')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [status] NVARCHAR(100) NULL;
        PRINT 'Added column: status';
    END
    
    -- limit_amount
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'limit_amount')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [limit_amount] NVARCHAR(100) NULL;
        PRINT 'Added column: limit_amount';
    END
    
    -- deductible_amount
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'deductible_amount')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [deductible_amount] NVARCHAR(100) NULL;
        PRINT 'Added column: deductible_amount';
    END
    
    -- gross_premium
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'gross_premium')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [gross_premium] DECIMAL(18,2) NULL;
        PRINT 'Added column: gross_premium';
    END
    
    -- commission_rate
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'commission_rate')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [commission_rate] DECIMAL(5,2) NULL;
        PRINT 'Added column: commission_rate';
    END
    
    -- midterm_endt_id
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'midterm_endt_id')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [midterm_endt_id] INT NULL;
        PRINT 'Added column: midterm_endt_id';
    END
    
    -- midterm_endt_description
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'midterm_endt_description')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [midterm_endt_description] NVARCHAR(500) NULL;
        PRINT 'Added column: midterm_endt_description';
    END
    
    -- midterm_endt_effective_from
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'midterm_endt_effective_from')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [midterm_endt_effective_from] NVARCHAR(50) NULL;
        PRINT 'Added column: midterm_endt_effective_from';
    END
    
    -- midterm_endt_endorsement_number
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'midterm_endt_endorsement_number')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [midterm_endt_endorsement_number] NVARCHAR(50) NULL;
        PRINT 'Added column: midterm_endt_endorsement_number';
    END
    
    -- additional_insured
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'additional_insured')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [additional_insured] NVARCHAR(MAX) NULL;
        PRINT 'Added column: additional_insured';
    END
    
    -- address_1
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'address_1')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [address_1] NVARCHAR(200) NULL;
        PRINT 'Added column: address_1';
    END
    
    -- address_2
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'address_2')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [address_2] NVARCHAR(200) NULL;
        PRINT 'Added column: address_2';
    END
    
    -- city
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'city')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [city] NVARCHAR(100) NULL;
        PRINT 'Added column: city';
    END
    
    -- state
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'state')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [state] NVARCHAR(2) NULL;
        PRINT 'Added column: state';
    END
    
    -- zip
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'zip')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [zip] NVARCHAR(10) NULL;
        PRINT 'Added column: zip';
    END
    
    -- transaction_type
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'transaction_type')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [transaction_type] NVARCHAR(100) NULL;
        PRINT 'Added column: transaction_type';
    END
    
    -- transaction_date
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'transaction_date')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [transaction_date] NVARCHAR(50) NULL;
        PRINT 'Added column: transaction_date';
    END
    
    -- source_system
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'source_system')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [source_system] NVARCHAR(50) NULL;
        PRINT 'Added column: source_system';
    END
    
    -- created_date
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'created_date')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [created_date] DATETIME NOT NULL DEFAULT GETDATE();
        PRINT 'Added column: created_date';
    END
    
    -- last_updated
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') AND name = 'last_updated')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [last_updated] DATETIME NOT NULL DEFAULT GETDATE();
        PRINT 'Added column: last_updated';
    END
    
    -- Add indexes if they don't exist
    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_tblTritonQuoteData_QuoteOptionGuid')
    BEGIN
        CREATE INDEX [IX_tblTritonQuoteData_QuoteOptionGuid] ON [dbo].[tblTritonQuoteData] ([QuoteOptionGuid]);
        PRINT 'Added index: IX_tblTritonQuoteData_QuoteOptionGuid';
    END
    
    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_tblTritonQuoteData_renewal_of_quote_guid')
    BEGIN
        CREATE INDEX [IX_tblTritonQuoteData_renewal_of_quote_guid] ON [dbo].[tblTritonQuoteData] ([renewal_of_quote_guid]);
        PRINT 'Added index: IX_tblTritonQuoteData_renewal_of_quote_guid';
    END
    
    -- Grant permissions
    GRANT SELECT, INSERT, UPDATE, DELETE ON [dbo].[tblTritonQuoteData] TO [IMS_User];
    
    PRINT 'Table tblTritonQuoteData update complete';
END
GO