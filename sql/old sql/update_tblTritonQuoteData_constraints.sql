-- Update constraints on tblTritonQuoteData
-- Ensure QuoteGuid is the unique identifier
-- Make transaction_id unique as well

-- First, check if the table exists
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'tblTritonQuoteData')
BEGIN
    PRINT 'ERROR: Table tblTritonQuoteData does not exist. Please create it first.';
    RETURN;
END

-- Check and add unique constraint on QuoteGuid if it doesn't exist
IF NOT EXISTS (
    SELECT * FROM sys.indexes 
    WHERE name = 'UQ_tblTritonQuoteData_QuoteGuid' 
    AND object_id = OBJECT_ID('tblTritonQuoteData')
)
BEGIN
    -- First check if there are any duplicate QuoteGuids
    IF EXISTS (
        SELECT QuoteGuid, COUNT(*) 
        FROM tblTritonQuoteData 
        GROUP BY QuoteGuid 
        HAVING COUNT(*) > 1
    )
    BEGIN
        PRINT 'WARNING: Duplicate QuoteGuid values found in tblTritonQuoteData!';
        PRINT 'Please resolve duplicates before adding unique constraint.';
        
        -- Show the duplicates
        SELECT QuoteGuid, COUNT(*) as DuplicateCount
        FROM tblTritonQuoteData 
        GROUP BY QuoteGuid 
        HAVING COUNT(*) > 1;
    END
    ELSE
    BEGIN
        -- Add unique constraint on QuoteGuid
        ALTER TABLE tblTritonQuoteData 
        ADD CONSTRAINT UQ_tblTritonQuoteData_QuoteGuid UNIQUE (QuoteGuid);
        
        PRINT 'Added unique constraint on QuoteGuid';
    END
END
ELSE
BEGIN
    PRINT 'Unique constraint on QuoteGuid already exists';
END

-- Check and add unique constraint on transaction_id if it doesn't exist
IF NOT EXISTS (
    SELECT * FROM sys.indexes 
    WHERE name = 'UQ_tblTritonQuoteData_transaction_id' 
    AND object_id = OBJECT_ID('tblTritonQuoteData')
)
BEGIN
    -- First check if there are any duplicate transaction_ids
    IF EXISTS (
        SELECT transaction_id, COUNT(*) 
        FROM tblTritonQuoteData 
        WHERE transaction_id IS NOT NULL
        GROUP BY transaction_id 
        HAVING COUNT(*) > 1
    )
    BEGIN
        PRINT 'WARNING: Duplicate transaction_id values found in tblTritonQuoteData!';
        PRINT 'Please resolve duplicates before adding unique constraint.';
        
        -- Show the duplicates
        SELECT transaction_id, COUNT(*) as DuplicateCount
        FROM tblTritonQuoteData 
        WHERE transaction_id IS NOT NULL
        GROUP BY transaction_id 
        HAVING COUNT(*) > 1;
    END
    ELSE
    BEGIN
        -- Add unique constraint on transaction_id
        ALTER TABLE tblTritonQuoteData 
        ADD CONSTRAINT UQ_tblTritonQuoteData_transaction_id UNIQUE (transaction_id);
        
        PRINT 'Added unique constraint on transaction_id';
    END
END
ELSE
BEGIN
    PRINT 'Unique constraint on transaction_id already exists';
END

-- Show current constraints
PRINT '';
PRINT 'Current unique constraints on tblTritonQuoteData:';
SELECT 
    i.name AS constraint_name,
    COL_NAME(ic.object_id, ic.column_id) AS column_name,
    i.is_unique,
    i.is_unique_constraint,
    i.is_primary_key
FROM sys.indexes i
INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
WHERE i.object_id = OBJECT_ID('tblTritonQuoteData')
AND (i.is_unique = 1 OR i.is_unique_constraint = 1 OR i.is_primary_key = 1)
ORDER BY i.name, ic.key_ordinal;

GO