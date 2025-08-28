-- Script to add market_segment_code column to tblTritonQuoteData
-- This column is required for ProgramID assignment based on market segment (RT/WL)
-- Date: 2025-08-28

-- Step 1: Add market_segment_code column if it doesn't exist
IF NOT EXISTS (
    SELECT * 
    FROM sys.columns 
    WHERE object_id = OBJECT_ID('tblTritonQuoteData') 
    AND name = 'market_segment_code'
)
BEGIN
    ALTER TABLE tblTritonQuoteData 
    ADD market_segment_code NVARCHAR(10) NULL;
    
    PRINT 'Added market_segment_code column to tblTritonQuoteData';
    
    -- Update existing records by extracting from JSON if full_payload_json exists
    IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'full_payload_json')
    BEGIN
        UPDATE tblTritonQuoteData
        SET market_segment_code = JSON_VALUE(full_payload_json, '$.market_segment_code')
        WHERE full_payload_json IS NOT NULL
          AND market_segment_code IS NULL
          AND JSON_VALUE(full_payload_json, '$.market_segment_code') IS NOT NULL;
        
        PRINT 'Updated existing records with market_segment_code from JSON';
    END
END
ELSE
BEGIN
    PRINT 'Column market_segment_code already exists in tblTritonQuoteData';
    
    -- Check if any existing records need to be updated
    IF EXISTS (
        SELECT 1 
        FROM tblTritonQuoteData 
        WHERE market_segment_code IS NULL 
          AND full_payload_json IS NOT NULL
          AND JSON_VALUE(full_payload_json, '$.market_segment_code') IS NOT NULL
    )
    BEGIN
        UPDATE tblTritonQuoteData
        SET market_segment_code = JSON_VALUE(full_payload_json, '$.market_segment_code')
        WHERE market_segment_code IS NULL
          AND full_payload_json IS NOT NULL
          AND JSON_VALUE(full_payload_json, '$.market_segment_code') IS NOT NULL;
        
        PRINT 'Updated NULL market_segment_code values from JSON';
    END
END
GO

-- Verify the column was added
SELECT 
    c.name AS ColumnName,
    t.name AS DataType,
    c.max_length AS MaxLength,
    c.is_nullable AS IsNullable,
    'Added/Verified' AS Status
FROM sys.columns c
INNER JOIN sys.types t ON c.user_type_id = t.user_type_id
WHERE c.object_id = OBJECT_ID('tblTritonQuoteData')
  AND c.name = 'market_segment_code';

-- Show sample of data with market_segment_code
SELECT TOP 5
    QuoteGuid,
    policy_number,
    market_segment_code,
    transaction_type,
    JSON_VALUE(full_payload_json, '$.market_segment_code') AS market_segment_from_json,
    created_date
FROM tblTritonQuoteData
WHERE transaction_type IN ('bind', 'midterm_endorsement')
ORDER BY created_date DESC;

PRINT 'Column addition/verification complete';