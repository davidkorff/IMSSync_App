-- Rollback script to remove the extra columns that were added by mistake
-- Only run this if you need to remove: other_fee, commission_amount, net_premium, base_premium

-- Drop other_fee column if it exists
IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'other_fee')
BEGIN
    ALTER TABLE [dbo].[tblTritonQuoteData]
    DROP COLUMN [other_fee];
    
    PRINT 'Column other_fee removed from tblTritonQuoteData';
END
GO

-- Drop commission_amount column if it exists
IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'commission_amount')
BEGIN
    ALTER TABLE [dbo].[tblTritonQuoteData]
    DROP COLUMN [commission_amount];
    
    PRINT 'Column commission_amount removed from tblTritonQuoteData';
END
GO

-- Drop net_premium column if it exists
IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'net_premium')
BEGIN
    ALTER TABLE [dbo].[tblTritonQuoteData]
    DROP COLUMN [net_premium];
    
    PRINT 'Column net_premium removed from tblTritonQuoteData';
END
GO

-- Drop base_premium column if it exists
IF EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('tblTritonQuoteData') AND name = 'base_premium')
BEGIN
    ALTER TABLE [dbo].[tblTritonQuoteData]
    DROP COLUMN [base_premium];
    
    PRINT 'Column base_premium removed from tblTritonQuoteData';
END
GO

PRINT 'Rollback completed - removed extra columns';
GO