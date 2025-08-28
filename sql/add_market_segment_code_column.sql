-- Add market_segment_code column to tblTritonQuoteData
-- This column is needed for the ProgramID assignment logic

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
    
    -- Update existing records by extracting from JSON
    UPDATE tblTritonQuoteData
    SET market_segment_code = JSON_VALUE(full_payload_json, '$.market_segment_code')
    WHERE full_payload_json IS NOT NULL
      AND market_segment_code IS NULL;
    
    PRINT 'Updated existing records with market_segment_code from JSON';
END
ELSE
BEGIN
    PRINT 'Column market_segment_code already exists in tblTritonQuoteData';
END
GO