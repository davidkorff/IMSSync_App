-- Add full_payload_json column to tblTritonQuoteData if it doesn't exist
-- This column might be missing if the table was created with an older script

IF NOT EXISTS (SELECT * FROM sys.columns 
               WHERE object_id = OBJECT_ID('dbo.tblTritonQuoteData') 
               AND name = 'full_payload_json')
BEGIN
    ALTER TABLE [dbo].[tblTritonQuoteData]
    ADD [full_payload_json] NVARCHAR(MAX) NULL;
    
    PRINT 'Column full_payload_json added to tblTritonQuoteData';
END
ELSE
BEGIN
    PRINT 'Column full_payload_json already exists in tblTritonQuoteData';
END
GO