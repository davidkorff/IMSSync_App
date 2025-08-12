-- Add other_fee column to tblTritonQuoteData if it doesn't exist
-- This column stores the "other_fee" value from Triton's JSON payload

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'other_fee')
BEGIN
    ALTER TABLE [dbo].[tblTritonQuoteData]
    ADD [other_fee] DECIMAL(18,2) NULL;
    
    PRINT 'Column other_fee added to tblTritonQuoteData';
END
ELSE
BEGIN
    PRINT 'Column other_fee already exists in tblTritonQuoteData';
END
GO