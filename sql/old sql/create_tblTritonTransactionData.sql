-- Create tblTritonTransactionData to store all transaction history
-- This table keeps a permanent record of every transaction payload
-- Transaction_id is the primary unique identifier

IF EXISTS (SELECT * FROM sys.tables WHERE name = 'tblTritonTransactionData')
BEGIN
    PRINT 'Table tblTritonTransactionData already exists. Dropping and recreating...'
    DROP TABLE tblTritonTransactionData;
END

CREATE TABLE [dbo].[tblTritonTransactionData] (
    -- Primary identifier
    [TritonTransactionDataID] INT IDENTITY(1,1) NOT NULL,
    [transaction_id] NVARCHAR(100) NOT NULL,
    
    -- Quote identifiers
    [QuoteGuid] UNIQUEIDENTIFIER NOT NULL,
    [QuoteOptionGuid] UNIQUEIDENTIFIER,
    
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
    
    -- Full JSON payload for audit trail
    [full_payload_json] NVARCHAR(MAX) NULL,
    
    -- Renewal information
    [renewal_of_quote_guid] UNIQUEIDENTIFIER NULL,
    
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
CREATE INDEX [IX_tblTritonTransactionData_transaction_type] ON [dbo].[tblTritonTransactionData] ([transaction_type]);
CREATE INDEX [IX_tblTritonTransactionData_created_date] ON [dbo].[tblTritonTransactionData] ([created_date]);



PRINT 'Table tblTritonTransactionData created successfully with transaction_id as unique identifier';
GO