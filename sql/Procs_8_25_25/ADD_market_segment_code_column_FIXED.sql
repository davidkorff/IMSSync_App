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
END
ELSE
BEGIN
    PRINT 'Column market_segment_code already exists in tblTritonQuoteData';
END
GO  -- This GO statement creates a new batch so the column exists for the next statements

-- Step 2: Update existing records by extracting from JSON (in a separate batch)
IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'full_payload_json')
   AND EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'market_segment_code')
BEGIN
    -- Update records where market_segment_code is null but exists in JSON
    UPDATE tblTritonQuoteData
    SET market_segment_code = JSON_VALUE(full_payload_json, '$.market_segment_code')
    WHERE full_payload_json IS NOT NULL
      AND market_segment_code IS NULL
      AND JSON_VALUE(full_payload_json, '$.market_segment_code') IS NOT NULL;
    
    DECLARE @RowsUpdated INT = @@ROWCOUNT;
    PRINT 'Updated ' + CAST(@RowsUpdated AS VARCHAR(10)) + ' existing records with market_segment_code from JSON';
END
GO

-- Step 3: Verify the column was added and show statistics
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

-- Show statistics about market_segment_code values
SELECT 
    'Statistics' AS [Check],
    COUNT(*) AS TotalRecords,
    COUNT(market_segment_code) AS RecordsWithMarketSegment,
    COUNT(CASE WHEN market_segment_code = 'RT' THEN 1 END) AS RT_Count,
    COUNT(CASE WHEN market_segment_code = 'WL' THEN 1 END) AS WL_Count,
    COUNT(CASE WHEN market_segment_code IS NULL THEN 1 END) AS NULL_Count
FROM tblTritonQuoteData
WHERE transaction_type IN ('bind', 'midterm_endorsement');

-- Show sample of data with market_segment_code
SELECT TOP 10
    QuoteGuid,
    policy_number,
    market_segment_code,
    transaction_type,
    CASE 
        WHEN full_payload_json IS NOT NULL 
        THEN JSON_VALUE(full_payload_json, '$.market_segment_code')
        ELSE NULL
    END AS market_segment_from_json,
    created_date
FROM tblTritonQuoteData
WHERE transaction_type IN ('bind', 'midterm_endorsement')
ORDER BY created_date DESC;

PRINT '';
PRINT 'Column addition/verification complete';
PRINT 'Next step: Run the updated spProcessTritonPayload_WS.sql';