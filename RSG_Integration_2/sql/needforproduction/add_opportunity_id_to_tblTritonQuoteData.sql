-- Add opportunity_id column to tblTritonQuoteData
-- This column is needed to look up quotes by opportunity_id for issue/unbind operations

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[tblTritonQuoteData]') AND name = 'opportunity_id')
BEGIN
    ALTER TABLE [dbo].[tblTritonQuoteData]
    ADD [opportunity_id] INT NULL;
    
    -- Create index for better performance
    CREATE INDEX [IX_tblTritonQuoteData_opportunity_id] ON [dbo].[tblTritonQuoteData] ([opportunity_id]);
    
    PRINT 'Column opportunity_id added to tblTritonQuoteData successfully';
END
ELSE
BEGIN
    PRINT 'Column opportunity_id already exists in tblTritonQuoteData';
END
GO