-- Production script to create tblTritonQuoteData
-- This table stores the current state of each quote

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
        
        -- Opportunity information
        [opportunity_id] INT NULL,
        
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
    CREATE INDEX [IX_tblTritonQuoteData_opportunity_id] ON [dbo].[tblTritonQuoteData] ([opportunity_id]);
    CREATE INDEX [IX_tblTritonQuoteData_renewal_of_quote_guid] ON [dbo].[tblTritonQuoteData] ([renewal_of_quote_guid]);
    CREATE INDEX [IX_tblTritonQuoteData_transaction_type] ON [dbo].[tblTritonQuoteData] ([transaction_type]);
    CREATE INDEX [IX_tblTritonQuoteData_created_date] ON [dbo].[tblTritonQuoteData] ([created_date]);

    -- Grant permissions
    GRANT SELECT, INSERT, UPDATE, DELETE ON [dbo].[tblTritonQuoteData] TO [IMS_User];

    PRINT 'Table tblTritonQuoteData created successfully';
END
ELSE
BEGIN
    PRINT 'Table tblTritonQuoteData already exists';
END
GO