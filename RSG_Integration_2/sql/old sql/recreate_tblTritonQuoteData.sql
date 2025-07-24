-- Drop and recreate tblTritonQuoteData with proper constraints

-- Drop the existing table
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'tblTritonQuoteData')
BEGIN
    PRINT 'Dropping existing tblTritonQuoteData table...';
    DROP TABLE tblTritonQuoteData;
END

-- Create the table with all columns and constraints
CREATE TABLE [dbo].[tblTritonQuoteData] (
    -- Primary key
    [TritonQuoteDataID] INT IDENTITY(1,1) NOT NULL,
    
    -- Quote identifiers (QuoteGuid is the main business key)
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
    [transaction_id] NVARCHAR(100) NOT NULL,
    [prior_transaction_id] NVARCHAR(100) NULL,
    [transaction_type] NVARCHAR(100),
    [transaction_date] NVARCHAR(50),
    [source_system] NVARCHAR(50),
    
    -- Timestamps
    [created_date] DATETIME NOT NULL DEFAULT GETDATE(),
    [last_updated] DATETIME NOT NULL DEFAULT GETDATE(),
    
    -- Constraints
    CONSTRAINT [PK_tblTritonQuoteData] PRIMARY KEY CLUSTERED ([TritonQuoteDataID] ASC),
    CONSTRAINT [UQ_tblTritonQuoteData_QuoteGuid] UNIQUE NONCLUSTERED ([QuoteGuid]),
    CONSTRAINT [UQ_tblTritonQuoteData_transaction_id] UNIQUE NONCLUSTERED ([transaction_id])
);

-- Create indexes for better performance
CREATE INDEX [IX_tblTritonQuoteData_QuoteOptionGuid] ON [dbo].[tblTritonQuoteData] ([QuoteOptionGuid]);
CREATE INDEX [IX_tblTritonQuoteData_policy_number] ON [dbo].[tblTritonQuoteData] ([policy_number]);
CREATE INDEX [IX_tblTritonQuoteData_transaction_type] ON [dbo].[tblTritonQuoteData] ([transaction_type]);
CREATE INDEX [IX_tblTritonQuoteData_created_date] ON [dbo].[tblTritonQuoteData] ([created_date]);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON [dbo].[tblTritonQuoteData] TO [IMS_User];

PRINT 'Table tblTritonQuoteData created successfully with unique constraints on QuoteGuid and transaction_id';

-- Show the table structure
SELECT 
    c.name AS column_name,
    t.name AS data_type,
    c.max_length,
    c.is_nullable,
    c.is_identity
FROM sys.columns c
INNER JOIN sys.types t ON c.user_type_id = t.user_type_id
WHERE c.object_id = OBJECT_ID('tblTritonQuoteData')
ORDER BY c.column_id;

-- Show constraints
PRINT '';
PRINT 'Constraints on tblTritonQuoteData:';
SELECT 
    i.name AS constraint_name,
    i.type_desc,
    COL_NAME(ic.object_id, ic.column_id) AS column_name
FROM sys.indexes i
INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
WHERE i.object_id = OBJECT_ID('tblTritonQuoteData')
AND (i.is_unique = 1 OR i.is_unique_constraint = 1 OR i.is_primary_key = 1)
ORDER BY i.name;

GO