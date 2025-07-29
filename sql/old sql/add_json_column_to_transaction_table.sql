-- Add full_payload_json column to tblTritonTransactionData
-- This stores the complete JSON payload for audit and debugging purposes

PRINT 'Adding full_payload_json column to tblTritonTransactionData...';
PRINT '==========================================================';

-- Check if table exists
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'tblTritonTransactionData')
BEGIN
    PRINT 'ERROR: Table tblTritonTransactionData does not exist. Please create it first.';
    RETURN;
END

-- Add the column if it doesn't already exist
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonTransactionData') AND name = 'full_payload_json')
BEGIN
    ALTER TABLE tblTritonTransactionData 
    ADD full_payload_json NVARCHAR(MAX) NULL;
    
    PRINT 'Successfully added full_payload_json column to tblTritonTransactionData';
END
ELSE
BEGIN
    PRINT 'Column full_payload_json already exists in tblTritonTransactionData';
END

-- Verify the column was added
PRINT '';
PRINT 'Verifying column addition...';
SELECT 
    c.name AS column_name,
    t.name AS data_type,
    c.max_length,
    c.is_nullable
FROM sys.columns c
INNER JOIN sys.types t ON c.user_type_id = t.user_type_id
WHERE c.object_id = OBJECT_ID('tblTritonTransactionData')
AND c.name = 'full_payload_json';

PRINT '';
PRINT 'Column addition complete.';
PRINT 'The full_payload_json column can now store complete transaction payloads for:';
PRINT '  - Audit trail';
PRINT '  - Debugging';
PRINT '  - Transaction replay';
PRINT '  - Historical analysis';

GO