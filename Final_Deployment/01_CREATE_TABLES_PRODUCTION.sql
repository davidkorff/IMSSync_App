-- =============================================
-- PRODUCTION TABLE CREATION SCRIPT - VERIFIED AGAINST EXPORT
-- Tables: tblTritonQuoteData, tblTritonTransactionData
-- CRITICAL: Based on actual export from existing tables
-- =============================================

USE [YourDatabaseName]; -- CHANGE THIS TO YOUR DATABASE NAME
GO

-- =============================================
-- WARNING: ONLY uncomment drops if you need to recreate tables!
-- =============================================
-- IF EXISTS (SELECT * FROM sys.tables WHERE name = 'tblTritonQuoteData')
--     DROP TABLE [dbo].[tblTritonQuoteData];
-- IF EXISTS (SELECT * FROM sys.tables WHERE name = 'tblTritonTransactionData')
--     DROP TABLE [dbo].[tblTritonTransactionData];
-- GO

-- =============================================
-- TABLE 1: tblTritonQuoteData (48 columns verified)
-- NOTE: TritonQuoteDataID is the IDENTITY column but wasn't in the export's CREATE statement
-- =============================================

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'tblTritonQuoteData')
BEGIN
    -- IMPORTANT: The export showed the table without TritonQuoteDataID in CREATE but it's needed for the PK
    CREATE TABLE [dbo].[tblTritonQuoteData] (
        [TritonQuoteDataID] INT IDENTITY(1,1) NOT NULL,  -- This column is required for PRIMARY KEY
        [QuoteGuid] UNIQUEIDENTIFIER NOT NULL,
        [QuoteOptionGuid] UNIQUEIDENTIFIER NULL,
        [renewal_of_quote_guid] UNIQUEIDENTIFIER NULL,
        [umr] NVARCHAR(100) NULL,
        [agreement_number] NVARCHAR(100) NULL,
        [section_number] NVARCHAR(100) NULL,
        [class_of_business] NVARCHAR(200) NULL,
        [program_name] NVARCHAR(200) NULL,
        [policy_number] NVARCHAR(50) NULL,
        [expiring_policy_number] NVARCHAR(50) NULL,
        [underwriter_name] NVARCHAR(200) NULL,
        [producer_name] NVARCHAR(200) NULL,
        [effective_date] NVARCHAR(50) NULL,
        [expiration_date] NVARCHAR(50) NULL,
        [bound_date] NVARCHAR(50) NULL,
        [insured_name] NVARCHAR(500) NULL,
        [insured_state] NVARCHAR(2) NULL,
        [insured_zip] NVARCHAR(10) NULL,
        [business_type] NVARCHAR(100) NULL,
        [status] NVARCHAR(100) NULL,
        [limit_amount] NVARCHAR(100) NULL,
        [deductible_amount] NVARCHAR(100) NULL,
        [gross_premium] DECIMAL(18,2) NULL,
        [commission_rate] DECIMAL(5,2) NULL,
        [opportunity_id] INT NULL,
        [midterm_endt_id] INT NULL,
        [midterm_endt_description] NVARCHAR(500) NULL,
        [midterm_endt_effective_from] NVARCHAR(50) NULL,
        [midterm_endt_endorsement_number] NVARCHAR(50) NULL,
        [additional_insured] NVARCHAR(MAX) NULL,
        [address_1] NVARCHAR(200) NULL,
        [address_2] NVARCHAR(200) NULL,
        [city] NVARCHAR(100) NULL,
        [state] NVARCHAR(2) NULL,
        [zip] NVARCHAR(10) NULL,
        [transaction_type] NVARCHAR(100) NULL,
        [transaction_date] NVARCHAR(50) NULL,
        [source_system] NVARCHAR(50) NULL,
        [created_date] DATETIME NOT NULL DEFAULT (GETDATE()),
        [last_updated] DATETIME NOT NULL DEFAULT (GETDATE()),
        [expiring_opportunity_id] INT NULL,
        [opportunity_type] NVARCHAR(100) NULL,
        [full_payload_json] NVARCHAR(MAX) NULL,
        [policy_fee] DECIMAL(18,2) NULL,
        [surplus_lines_tax] NVARCHAR(50) NULL,
        [stamping_fee] NVARCHAR(50) NULL,
        [commission_percent] DECIMAL(5,2) NULL,
        [other_fee] DECIMAL(18,2) NULL,
        [cancellation_id] INT NULL,
        [market_segment_code] NVARCHAR(10) NULL
    );

    -- Add Primary Key
    ALTER TABLE [dbo].[tblTritonQuoteData] 
    ADD CONSTRAINT [PK_tblTritonQuoteData] PRIMARY KEY CLUSTERED ([TritonQuoteDataID] ASC);

    -- Add Unique Constraint
    ALTER TABLE [dbo].[tblTritonQuoteData] 
    ADD CONSTRAINT [UQ_tblTritonQuoteData_QuoteGuid] UNIQUE NONCLUSTERED ([QuoteGuid] ASC);

    -- Create Indexes
    CREATE NONCLUSTERED INDEX [IX_tblTritonQuoteData_QuoteOptionGuid] ON [dbo].[tblTritonQuoteData] ([QuoteOptionGuid] ASC);
    CREATE NONCLUSTERED INDEX [IX_tblTritonQuoteData_policy_number] ON [dbo].[tblTritonQuoteData] ([policy_number] ASC);
    CREATE NONCLUSTERED INDEX [IX_tblTritonQuoteData_opportunity_id] ON [dbo].[tblTritonQuoteData] ([opportunity_id] ASC);
    CREATE NONCLUSTERED INDEX [IX_tblTritonQuoteData_renewal_of_quote_guid] ON [dbo].[tblTritonQuoteData] ([renewal_of_quote_guid] ASC);
    CREATE NONCLUSTERED INDEX [IX_tblTritonQuoteData_transaction_type] ON [dbo].[tblTritonQuoteData] ([transaction_type] ASC);
    CREATE NONCLUSTERED INDEX [IX_tblTritonQuoteData_created_date] ON [dbo].[tblTritonQuoteData] ([created_date] ASC);
    CREATE NONCLUSTERED INDEX [IX_tblTritonQuoteData_expiring_opportunity_id] ON [dbo].[tblTritonQuoteData] ([expiring_opportunity_id] ASC);

    PRINT 'Table tblTritonQuoteData created successfully with all indexes';
END
ELSE
BEGIN
    PRINT 'Table tblTritonQuoteData already exists';
END
GO

-- =============================================
-- TABLE 2: tblTritonTransactionData
-- =============================================

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'tblTritonTransactionData')
BEGIN
    CREATE TABLE [dbo].[tblTritonTransactionData] (
        [TritonTransactionDataID] INT IDENTITY(1,1) NOT NULL,
        [transaction_id] NVARCHAR(100) NOT NULL,
        [full_payload_json] NVARCHAR(MAX) NULL,
        [opportunity_id] INT NULL,
        [policy_number] NVARCHAR(50) NULL,
        [insured_name] NVARCHAR(500) NULL,
        [transaction_type] NVARCHAR(100) NULL,
        [transaction_date] NVARCHAR(50) NULL,
        [source_system] NVARCHAR(50) NULL,
        [date_created] DATETIME NOT NULL DEFAULT (GETDATE()),
        [ProcessedFlag] BIT NULL DEFAULT ((0)),
        [ProcessedDate] DATETIME NULL,
        [ErrorMessage] NVARCHAR(500) NULL
    );

    -- Add Primary Key
    ALTER TABLE [dbo].[tblTritonTransactionData] 
    ADD CONSTRAINT [PK_tblTritonTransactionData] PRIMARY KEY CLUSTERED ([TritonTransactionDataID] ASC);

    -- Add Unique Constraint
    ALTER TABLE [dbo].[tblTritonTransactionData] 
    ADD CONSTRAINT [UQ_tblTritonTransactionData_transaction_id] UNIQUE NONCLUSTERED ([transaction_id] ASC);

    -- Create Indexes
    CREATE NONCLUSTERED INDEX [IX_tblTritonTransactionData_transaction_type] ON [dbo].[tblTritonTransactionData] ([transaction_type] ASC);
    CREATE NONCLUSTERED INDEX [IX_tblTritonTransactionData_date_created] ON [dbo].[tblTritonTransactionData] ([date_created] ASC);
    CREATE NONCLUSTERED INDEX [IX_tblTritonTransactionData_opportunity_id] ON [dbo].[tblTritonTransactionData] ([opportunity_id] ASC);
    CREATE NONCLUSTERED INDEX [IX_tblTritonTransactionData_policy_number] ON [dbo].[tblTritonTransactionData] ([policy_number] ASC);

    PRINT 'Table tblTritonTransactionData created successfully with all indexes';
END
ELSE
BEGIN
    PRINT 'Table tblTritonTransactionData already exists';
END
GO

-- =============================================
-- VERIFICATION
-- =============================================

PRINT '';
PRINT '==========================================';
PRINT 'VERIFICATION RESULTS:';
PRINT '==========================================';

-- Check tables exist
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'tblTritonQuoteData')
    PRINT '✓ tblTritonQuoteData created successfully'
ELSE
    PRINT '✗ ERROR: tblTritonQuoteData not found!'

IF EXISTS (SELECT * FROM sys.tables WHERE name = 'tblTritonTransactionData')
    PRINT '✓ tblTritonTransactionData created successfully'
ELSE
    PRINT '✗ ERROR: tblTritonTransactionData not found!'

-- Count indexes
DECLARE @QuoteIndexCount INT, @TransactionIndexCount INT;

SELECT @QuoteIndexCount = COUNT(*) 
FROM sys.indexes i
JOIN sys.tables t ON i.object_id = t.object_id
WHERE t.name = 'tblTritonQuoteData';

SELECT @TransactionIndexCount = COUNT(*) 
FROM sys.indexes i
JOIN sys.tables t ON i.object_id = t.object_id
WHERE t.name = 'tblTritonTransactionData';

PRINT '';
PRINT 'Index counts:';
PRINT '  tblTritonQuoteData: ' + CAST(@QuoteIndexCount AS VARCHAR(10)) + ' indexes (expected: 9)';
PRINT '  tblTritonTransactionData: ' + CAST(@TransactionIndexCount AS VARCHAR(10)) + ' indexes (expected: 6)';

PRINT '';
PRINT 'Run 02_VERIFY_TABLES.sql for detailed verification';
PRINT '==========================================';