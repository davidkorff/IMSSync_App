-- Add ONLY the 4 required columns to tblTritonQuoteData

-- Add commission_percent column if it doesn't exist
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'commission_percent')
BEGIN
    ALTER TABLE [dbo].[tblTritonQuoteData]
    ADD [commission_percent] DECIMAL(5,2) NULL;
    
    PRINT 'Column commission_percent added to tblTritonQuoteData';
END
ELSE
BEGIN
    PRINT 'Column commission_percent already exists in tblTritonQuoteData';
END
GO

-- Add policy_fee column if it doesn't exist
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'policy_fee')
BEGIN
    ALTER TABLE [dbo].[tblTritonQuoteData]
    ADD [policy_fee] DECIMAL(18,2) NULL;
    
    PRINT 'Column policy_fee added to tblTritonQuoteData';
END
ELSE
BEGIN
    PRINT 'Column policy_fee already exists in tblTritonQuoteData';
END
GO

-- Add stamping_fee column if it doesn't exist
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'stamping_fee')
BEGIN
    ALTER TABLE [dbo].[tblTritonQuoteData]
    ADD [stamping_fee] NVARCHAR(50) NULL;
    
    PRINT 'Column stamping_fee added to tblTritonQuoteData';
END
ELSE
BEGIN
    PRINT 'Column stamping_fee already exists in tblTritonQuoteData';
END
GO

-- Add surplus_lines_tax column if it doesn't exist  
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'surplus_lines_tax')
BEGIN
    ALTER TABLE [dbo].[tblTritonQuoteData]
    ADD [surplus_lines_tax] NVARCHAR(50) NULL;
    
    PRINT 'Column surplus_lines_tax added to tblTritonQuoteData';
END
ELSE
BEGIN
    PRINT 'Column surplus_lines_tax already exists in tblTritonQuoteData';
END
GO

PRINT 'tblTritonQuoteData update completed - added 4 required columns only';
GO