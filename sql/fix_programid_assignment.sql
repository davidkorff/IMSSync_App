-- Fix for ProgramID not being assigned during bind transactions
-- Issue: market_segment_code is extracted but not stored, and ProgramID assignment needs debugging
-- Date: 2025-08-28

-- Step 1: Add market_segment_code column to tblTritonQuoteData if it doesn't exist
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
GO

-- Step 2: Add opportunity_type column if it doesn't exist (also missing from original table)
IF NOT EXISTS (
    SELECT * 
    FROM sys.columns 
    WHERE object_id = OBJECT_ID('tblTritonQuoteData') 
    AND name = 'opportunity_type'
)
BEGIN
    ALTER TABLE tblTritonQuoteData 
    ADD opportunity_type NVARCHAR(100) NULL;
    
    PRINT 'Added opportunity_type column to tblTritonQuoteData';
END
ELSE
BEGIN
    PRINT 'Column opportunity_type already exists in tblTritonQuoteData';
END
GO

-- Step 3: Add commission_percent column if it doesn't exist (missing from table but used in stored proc)
IF NOT EXISTS (
    SELECT * 
    FROM sys.columns 
    WHERE object_id = OBJECT_ID('tblTritonQuoteData') 
    AND name = 'commission_percent'
)
BEGIN
    ALTER TABLE tblTritonQuoteData 
    ADD commission_percent DECIMAL(5,2) NULL;
    
    PRINT 'Added commission_percent column to tblTritonQuoteData';
END
ELSE
BEGIN
    PRINT 'Column commission_percent already exists in tblTritonQuoteData';
END
GO

-- Step 4: Add full_payload_json column if it doesn't exist
IF NOT EXISTS (
    SELECT * 
    FROM sys.columns 
    WHERE object_id = OBJECT_ID('tblTritonQuoteData') 
    AND name = 'full_payload_json'
)
BEGIN
    ALTER TABLE tblTritonQuoteData 
    ADD full_payload_json NVARCHAR(MAX) NULL;
    
    PRINT 'Added full_payload_json column to tblTritonQuoteData';
END
ELSE
BEGIN
    PRINT 'Column full_payload_json already exists in tblTritonQuoteData';
END
GO

PRINT 'Table structure updates completed. Now update the stored procedure spProcessTritonPayload_WS';