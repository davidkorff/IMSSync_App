-- =============================================
-- Add cancellation_id column to tblTritonQuoteData
-- Similar to midterm_endt_id for tracking cancellations
-- =============================================

USE [IMS_DEV]
GO

-- Check if column exists before adding
IF NOT EXISTS (
    SELECT * 
    FROM sys.columns 
    WHERE object_id = OBJECT_ID(N'[dbo].[tblTritonQuoteData]') 
    AND name = 'cancellation_id'
)
BEGIN
    ALTER TABLE [dbo].[tblTritonQuoteData]
    ADD cancellation_id INT NULL
    
    PRINT 'Column cancellation_id added to tblTritonQuoteData'
END
ELSE
BEGIN
    PRINT 'Column cancellation_id already exists in tblTritonQuoteData'
END
GO