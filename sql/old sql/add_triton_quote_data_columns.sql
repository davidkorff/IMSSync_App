-- Script to add missing columns to tblTritonQuoteData table
-- Based on the requirements from spProcessTritonPayload_WS stored procedure

-- Check if table exists
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'tblTritonQuoteData')
BEGIN
    -- Create the table if it doesn't exist
    CREATE TABLE [dbo].[tblTritonQuoteData] (
        [TritonQuoteDataID] INT IDENTITY(1,1) PRIMARY KEY,
        [QuoteGuid] UNIQUEIDENTIFIER NOT NULL,
        [created_date] DATETIME DEFAULT GETDATE()
    );
END

-- Add missing columns one by one (checking if they exist first)
-- This approach allows the script to be run multiple times safely

-- QuoteOptionGuid
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'QuoteOptionGuid')
    ALTER TABLE tblTritonQuoteData ADD QuoteOptionGuid UNIQUEIDENTIFIER;

-- UMR fields
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'umr')
    ALTER TABLE tblTritonQuoteData ADD umr NVARCHAR(100) NULL;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'agreement_number')
    ALTER TABLE tblTritonQuoteData ADD agreement_number NVARCHAR(100) NULL;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'section_number')
    ALTER TABLE tblTritonQuoteData ADD section_number NVARCHAR(100) NULL;

-- Business information
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'class_of_business')
    ALTER TABLE tblTritonQuoteData ADD class_of_business NVARCHAR(200);

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'program_name')
    ALTER TABLE tblTritonQuoteData ADD program_name NVARCHAR(200);

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'policy_number')
    ALTER TABLE tblTritonQuoteData ADD policy_number NVARCHAR(50);

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'expiring_policy_number')
    ALTER TABLE tblTritonQuoteData ADD expiring_policy_number NVARCHAR(50) NULL;

-- Personnel
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'underwriter_name')
    ALTER TABLE tblTritonQuoteData ADD underwriter_name NVARCHAR(200);

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'producer_name')
    ALTER TABLE tblTritonQuoteData ADD producer_name NVARCHAR(200);

-- Dates
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'invoice_date')
    ALTER TABLE tblTritonQuoteData ADD invoice_date NVARCHAR(50);

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'effective_date')
    ALTER TABLE tblTritonQuoteData ADD effective_date NVARCHAR(50);

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'expiration_date')
    ALTER TABLE tblTritonQuoteData ADD expiration_date NVARCHAR(50);

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'bound_date')
    ALTER TABLE tblTritonQuoteData ADD bound_date NVARCHAR(50);

-- Fees
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'policy_fee')
    ALTER TABLE tblTritonQuoteData ADD policy_fee DECIMAL(18,2) NULL;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'surplus_lines_tax')
    ALTER TABLE tblTritonQuoteData ADD surplus_lines_tax NVARCHAR(50) NULL;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'stamping_fee')
    ALTER TABLE tblTritonQuoteData ADD stamping_fee NVARCHAR(50) NULL;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'other_fee')
    ALTER TABLE tblTritonQuoteData ADD other_fee NVARCHAR(50) NULL;

-- Insured information
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'insured_name')
    ALTER TABLE tblTritonQuoteData ADD insured_name NVARCHAR(500);

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'insured_state')
    ALTER TABLE tblTritonQuoteData ADD insured_state NVARCHAR(2);

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'insured_zip')
    ALTER TABLE tblTritonQuoteData ADD insured_zip NVARCHAR(10);

-- Business details
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'opportunity_type')
    ALTER TABLE tblTritonQuoteData ADD opportunity_type NVARCHAR(100);

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'business_type')
    ALTER TABLE tblTritonQuoteData ADD business_type NVARCHAR(100);

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'status')
    ALTER TABLE tblTritonQuoteData ADD status NVARCHAR(100);

-- Coverage limits
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'limit_amount')
    ALTER TABLE tblTritonQuoteData ADD limit_amount NVARCHAR(100);

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'limit_prior')
    ALTER TABLE tblTritonQuoteData ADD limit_prior NVARCHAR(100);

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'deductible_amount')
    ALTER TABLE tblTritonQuoteData ADD deductible_amount NVARCHAR(100);

-- Premium information
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'gross_premium')
    ALTER TABLE tblTritonQuoteData ADD gross_premium DECIMAL(18,2);

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'commission_rate')
    ALTER TABLE tblTritonQuoteData ADD commission_rate DECIMAL(5,2);

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'commission_percent')
    ALTER TABLE tblTritonQuoteData ADD commission_percent DECIMAL(5,2) NULL;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'commission_amount')
    ALTER TABLE tblTritonQuoteData ADD commission_amount DECIMAL(18,2) NULL;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'net_premium')
    ALTER TABLE tblTritonQuoteData ADD net_premium DECIMAL(18,2);

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'base_premium')
    ALTER TABLE tblTritonQuoteData ADD base_premium DECIMAL(18,2);

-- Opportunity information
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'opportunity_id')
    ALTER TABLE tblTritonQuoteData ADD opportunity_id INT;

-- Midterm endorsement fields
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'midterm_endt_id')
    ALTER TABLE tblTritonQuoteData ADD midterm_endt_id INT NULL;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'midterm_endt_description')
    ALTER TABLE tblTritonQuoteData ADD midterm_endt_description NVARCHAR(500) NULL;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'midterm_endt_effective_from')
    ALTER TABLE tblTritonQuoteData ADD midterm_endt_effective_from NVARCHAR(50) NULL;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'midterm_endt_endorsement_number')
    ALTER TABLE tblTritonQuoteData ADD midterm_endt_endorsement_number NVARCHAR(50) NULL;

-- Additional insured (JSON)
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'additional_insured')
    ALTER TABLE tblTritonQuoteData ADD additional_insured NVARCHAR(MAX) NULL;

-- Address information
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'address_1')
    ALTER TABLE tblTritonQuoteData ADD address_1 NVARCHAR(200);

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'address_2')
    ALTER TABLE tblTritonQuoteData ADD address_2 NVARCHAR(200) NULL;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'city')
    ALTER TABLE tblTritonQuoteData ADD city NVARCHAR(100);

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'state')
    ALTER TABLE tblTritonQuoteData ADD state NVARCHAR(2);

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'zip')
    ALTER TABLE tblTritonQuoteData ADD zip NVARCHAR(10);

-- Transaction information
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'transaction_id')
    ALTER TABLE tblTritonQuoteData ADD transaction_id NVARCHAR(100);

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'prior_transaction_id')
    ALTER TABLE tblTritonQuoteData ADD prior_transaction_id NVARCHAR(100) NULL;

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'transaction_type')
    ALTER TABLE tblTritonQuoteData ADD transaction_type NVARCHAR(100);

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'transaction_date')
    ALTER TABLE tblTritonQuoteData ADD transaction_date NVARCHAR(50);

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'source_system')
    ALTER TABLE tblTritonQuoteData ADD source_system NVARCHAR(50);

-- Renewal information
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'renewal_of_quote_guid')
    ALTER TABLE tblTritonQuoteData ADD renewal_of_quote_guid UNIQUEIDENTIFIER NULL;

-- Timestamps
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'created_date')
    ALTER TABLE tblTritonQuoteData ADD created_date DATETIME DEFAULT GETDATE();

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'last_updated')
    ALTER TABLE tblTritonQuoteData ADD last_updated DATETIME DEFAULT GETDATE();

-- Create index on QuoteGuid for better performance
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_tblTritonQuoteData_QuoteGuid')
    CREATE INDEX IX_tblTritonQuoteData_QuoteGuid ON tblTritonQuoteData(QuoteGuid);

-- Create index on QuoteOptionGuid for better performance
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_tblTritonQuoteData_QuoteOptionGuid')
    CREATE INDEX IX_tblTritonQuoteData_QuoteOptionGuid ON tblTritonQuoteData(QuoteOptionGuid);

-- Create index on transaction_id for better performance
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_tblTritonQuoteData_transaction_id')
    CREATE INDEX IX_tblTritonQuoteData_transaction_id ON tblTritonQuoteData(transaction_id);

PRINT 'All columns have been added successfully to tblTritonQuoteData';
GO