-- Script to remove specified columns from tblTritonQuoteData
-- This removes columns that should only exist in tblTritonTransactionData

PRINT 'Removing columns from tblTritonQuoteData...';
PRINT '==========================================';

-- Check if table exists
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'tblTritonQuoteData')
BEGIN
    PRINT 'ERROR: Table tblTritonQuoteData does not exist.';
    RETURN;
END

-- First, drop any indexes or constraints on the columns we want to remove
PRINT '';
PRINT 'Dropping indexes and constraints...';

-- Drop index on transaction_id if it exists
IF EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_tblTritonQuoteData_transaction_id' AND object_id = OBJECT_ID('tblTritonQuoteData'))
BEGIN
    DROP INDEX IX_tblTritonQuoteData_transaction_id ON tblTritonQuoteData;
    PRINT 'Dropped index: IX_tblTritonQuoteData_transaction_id';
END

-- Drop unique constraint on transaction_id if it exists
IF EXISTS (SELECT * FROM sys.indexes WHERE name = 'UQ_tblTritonQuoteData_transaction_id' AND object_id = OBJECT_ID('tblTritonQuoteData'))
BEGIN
    ALTER TABLE tblTritonQuoteData DROP CONSTRAINT UQ_tblTritonQuoteData_transaction_id;
    PRINT 'Dropped constraint: UQ_tblTritonQuoteData_transaction_id';
END

PRINT '';
PRINT 'Dropping columns...';

-- Drop columns one by one (checking if they exist first)
-- This approach allows the script to be run multiple times safely

-- Transaction columns
IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'transaction_id')
BEGIN
    ALTER TABLE tblTritonQuoteData DROP COLUMN transaction_id;
    PRINT 'Dropped column: transaction_id';
END

IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'prior_transaction_id')
BEGIN
    ALTER TABLE tblTritonQuoteData DROP COLUMN prior_transaction_id;
    PRINT 'Dropped column: prior_transaction_id';
END

-- Opportunity columns
IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'opportunity_id')
BEGIN
    ALTER TABLE tblTritonQuoteData DROP COLUMN opportunity_id;
    PRINT 'Dropped column: opportunity_id';
END

IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'opportunity_type')
BEGIN
    ALTER TABLE tblTritonQuoteData DROP COLUMN opportunity_type;
    PRINT 'Dropped column: opportunity_type';
END

-- Fee columns
IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'policy_fee')
BEGIN
    ALTER TABLE tblTritonQuoteData DROP COLUMN policy_fee;
    PRINT 'Dropped column: policy_fee';
END

IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'surplus_lines_tax')
BEGIN
    ALTER TABLE tblTritonQuoteData DROP COLUMN surplus_lines_tax;
    PRINT 'Dropped column: surplus_lines_tax';
END

IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'stamping_fee')
BEGIN
    ALTER TABLE tblTritonQuoteData DROP COLUMN stamping_fee;
    PRINT 'Dropped column: stamping_fee';
END

IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'other_fee')
BEGIN
    ALTER TABLE tblTritonQuoteData DROP COLUMN other_fee;
    PRINT 'Dropped column: other_fee';
END

-- Commission columns
IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'commission_percent')
BEGIN
    ALTER TABLE tblTritonQuoteData DROP COLUMN commission_percent;
    PRINT 'Dropped column: commission_percent';
END

IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'commission_amount')
BEGIN
    ALTER TABLE tblTritonQuoteData DROP COLUMN commission_amount;
    PRINT 'Dropped column: commission_amount';
END

-- Premium columns
IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'net_premium')
BEGIN
    ALTER TABLE tblTritonQuoteData DROP COLUMN net_premium;
    PRINT 'Dropped column: net_premium';
END

IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'base_premium')
BEGIN
    ALTER TABLE tblTritonQuoteData DROP COLUMN base_premium;
    PRINT 'Dropped column: base_premium';
END

-- Limit column
IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'limit_prior')
BEGIN
    ALTER TABLE tblTritonQuoteData DROP COLUMN limit_prior;
    PRINT 'Dropped column: limit_prior';
END

-- Date column
IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'invoice_date')
BEGIN
    ALTER TABLE tblTritonQuoteData DROP COLUMN invoice_date;
    PRINT 'Dropped column: invoice_date';
END

PRINT '';
PRINT 'Column removal complete.';
PRINT '';

-- Show remaining columns
PRINT 'Remaining columns in tblTritonQuoteData:';
SELECT 
    c.name AS column_name,
    t.name AS data_type,
    c.max_length,
    c.is_nullable
FROM sys.columns c
INNER JOIN sys.types t ON c.user_type_id = t.user_type_id
WHERE c.object_id = OBJECT_ID('tblTritonQuoteData')
ORDER BY c.column_id;

GO