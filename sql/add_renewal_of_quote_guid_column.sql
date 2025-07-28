-- Add renewal_of_quote_guid column to both Triton tables
-- This column links renewal quotes to their original quotes

PRINT 'Adding renewal_of_quote_guid column to Triton tables...';
PRINT '===================================================';

-- Add to tblTritonQuoteData
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'tblTritonQuoteData')
BEGIN
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'renewal_of_quote_guid')
    BEGIN
        ALTER TABLE tblTritonQuoteData 
        ADD renewal_of_quote_guid UNIQUEIDENTIFIER NULL;
        
        PRINT 'Successfully added renewal_of_quote_guid column to tblTritonQuoteData';
    END
    ELSE
    BEGIN
        PRINT 'Column renewal_of_quote_guid already exists in tblTritonQuoteData';
    END
END
ELSE
BEGIN
    PRINT 'Table tblTritonQuoteData does not exist';
END

PRINT '';

-- Add to tblTritonTransactionData
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'tblTritonTransactionData')
BEGIN
    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonTransactionData') AND name = 'renewal_of_quote_guid')
    BEGIN
        ALTER TABLE tblTritonTransactionData 
        ADD renewal_of_quote_guid UNIQUEIDENTIFIER NULL;
        
        PRINT 'Successfully added renewal_of_quote_guid column to tblTritonTransactionData';
    END
    ELSE
    BEGIN
        PRINT 'Column renewal_of_quote_guid already exists in tblTritonTransactionData';
    END
END
ELSE
BEGIN
    PRINT 'Table tblTritonTransactionData does not exist';
END

-- Create index on renewal_of_quote_guid for better performance
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'tblTritonQuoteData')
BEGIN
    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_tblTritonQuoteData_renewal_of_quote_guid')
    BEGIN
        CREATE INDEX IX_tblTritonQuoteData_renewal_of_quote_guid 
        ON tblTritonQuoteData(renewal_of_quote_guid);
        PRINT 'Created index IX_tblTritonQuoteData_renewal_of_quote_guid';
    END
END

IF EXISTS (SELECT * FROM sys.tables WHERE name = 'tblTritonTransactionData')
BEGIN
    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_tblTritonTransactionData_renewal_of_quote_guid')
    BEGIN
        CREATE INDEX IX_tblTritonTransactionData_renewal_of_quote_guid 
        ON tblTritonTransactionData(renewal_of_quote_guid);
        PRINT 'Created index IX_tblTritonTransactionData_renewal_of_quote_guid';
    END
END

PRINT '';
PRINT 'Column addition complete.';
PRINT 'The renewal_of_quote_guid column can now be used to:';
PRINT '  - Link renewal quotes to their original quotes';
PRINT '  - Track renewal chains';
PRINT '  - Analyze renewal patterns';

GO