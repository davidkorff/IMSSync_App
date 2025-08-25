-- =============================================
-- Update Script: tblTritonQuoteData
-- Description: Updates existing tblTritonQuoteData table with new columns
-- Purpose: Add missing columns for rebind and renewal detection
-- =============================================

-- Check if table exists
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'tblTritonQuoteData')
BEGIN
    PRINT 'Updating tblTritonQuoteData schema...';
    
    -- Add opportunity_id column if it doesn't exist
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'opportunity_id')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [opportunity_id] INT NULL;
        CREATE INDEX [IX_tblTritonQuoteData_opportunity_id] ON [dbo].[tblTritonQuoteData] ([opportunity_id]);
        PRINT 'Added opportunity_id column to tblTritonQuoteData';
    END
    ELSE
    BEGIN
        PRINT 'Column opportunity_id already exists';
    END
    
    -- Add expiring_opportunity_id column if it doesn't exist
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'expiring_opportunity_id')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [expiring_opportunity_id] INT NULL;
        CREATE INDEX [IX_tblTritonQuoteData_expiring_opportunity_id] ON [dbo].[tblTritonQuoteData] ([expiring_opportunity_id]);
        PRINT 'Added expiring_opportunity_id column to tblTritonQuoteData';
    END
    ELSE
    BEGIN
        PRINT 'Column expiring_opportunity_id already exists';
    END
    
    -- Add opportunity_type column if it doesn't exist
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'opportunity_type')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [opportunity_type] NVARCHAR(100) NULL;
        PRINT 'Added opportunity_type column to tblTritonQuoteData';
    END
    ELSE
    BEGIN
        PRINT 'Column opportunity_type already exists';
    END
    
    -- Add full_payload_json column if it doesn't exist
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'full_payload_json')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [full_payload_json] NVARCHAR(MAX) NULL;
        PRINT 'Added full_payload_json column to tblTritonQuoteData';
    END
    ELSE
    BEGIN
        PRINT 'Column full_payload_json already exists';
    END
    
    -- Add renewal_of_quote_guid column if it doesn't exist
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'renewal_of_quote_guid')
    BEGIN
        ALTER TABLE [dbo].[tblTritonQuoteData] ADD [renewal_of_quote_guid] UNIQUEIDENTIFIER NULL;
        CREATE INDEX [IX_tblTritonQuoteData_renewal_of_quote_guid] ON [dbo].[tblTritonQuoteData] ([renewal_of_quote_guid]);
        PRINT 'Added renewal_of_quote_guid column to tblTritonQuoteData';
    END
    ELSE
    BEGIN
        PRINT 'Column renewal_of_quote_guid already exists';
    END
    
    PRINT 'tblTritonQuoteData schema update completed';
END
ELSE
BEGIN
    -- If table doesn't exist, provide instructions
    PRINT 'ERROR: Table tblTritonQuoteData does not exist.';
    PRINT 'Please run the following script first:';
    PRINT '  sql/needforproduction/actaullyneed/PRODUCTION_create_tblTritonQuoteData.sql';
END
GO

-- Display the current schema
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'tblTritonQuoteData')
BEGIN
    PRINT '';
    PRINT 'Current tblTritonQuoteData columns:';
    SELECT 
        c.name AS ColumnName,
        t.name AS DataType,
        c.max_length,
        c.is_nullable
    FROM sys.columns c
    INNER JOIN sys.types t ON c.user_type_id = t.user_type_id
    WHERE c.object_id = OBJECT_ID('tblTritonQuoteData')
    ORDER BY c.column_id;
END
GO