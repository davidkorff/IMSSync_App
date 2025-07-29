-- =============================================
-- Update Script: tblTritonTransactionData
-- Description: Drops and recreates the transaction data table with simplified schema
-- Purpose: Store only transaction history data (no quote associations)
-- =============================================

-- Drop existing table if it exists
IF EXISTS (SELECT * FROM sys.tables WHERE name = 'tblTritonTransactionData')
BEGIN
    -- Drop all indexes first
    DROP INDEX IF EXISTS [IX_tblTritonTransactionData_QuoteGuid] ON [dbo].[tblTritonTransactionData];
    DROP INDEX IF EXISTS [IX_tblTritonTransactionData_QuoteOptionGuid] ON [dbo].[tblTritonTransactionData];
    DROP INDEX IF EXISTS [IX_tblTritonTransactionData_policy_number] ON [dbo].[tblTritonTransactionData];
    DROP INDEX IF EXISTS [IX_tblTritonTransactionData_prior_transaction_id] ON [dbo].[tblTritonTransactionData];
    DROP INDEX IF EXISTS [IX_tblTritonTransactionData_renewal_of_quote_guid] ON [dbo].[tblTritonTransactionData];
    DROP INDEX IF EXISTS [IX_tblTritonTransactionData_transaction_type] ON [dbo].[tblTritonTransactionData];
    DROP INDEX IF EXISTS [IX_tblTritonTransactionData_created_date] ON [dbo].[tblTritonTransactionData];
    DROP INDEX IF EXISTS [IX_tblTritonTransactionData_opportunity_id] ON [dbo].[tblTritonTransactionData];
    
    -- Drop the table
    DROP TABLE [dbo].[tblTritonTransactionData];
    PRINT 'Dropped existing tblTritonTransactionData table';
END

-- Create the table with new simplified schema
CREATE TABLE [dbo].[tblTritonTransactionData] (
    -- Primary identifier
    [TritonTransactionDataID] INT IDENTITY(1,1) NOT NULL,
    [transaction_id] NVARCHAR(100) NOT NULL,
    
    -- Full JSON payload for audit trail
    [full_payload_json] NVARCHAR(MAX) NULL,
    
    -- Key transaction fields for quick lookup
    [opportunity_id] INT NULL,
    [policy_number] NVARCHAR(50) NULL,
    [insured_name] NVARCHAR(500) NULL,
    
    -- Transaction information
    [transaction_type] NVARCHAR(100),
    [transaction_date] NVARCHAR(50),
    [source_system] NVARCHAR(50),
    
    -- Timestamps
    [date_created] DATETIME NOT NULL DEFAULT GETDATE(),
    
    -- Constraints
    CONSTRAINT [PK_tblTritonTransactionData] PRIMARY KEY CLUSTERED ([TritonTransactionDataID] ASC),
    CONSTRAINT [UQ_tblTritonTransactionData_transaction_id] UNIQUE NONCLUSTERED ([transaction_id])
);

-- Create indexes for performance
CREATE INDEX [IX_tblTritonTransactionData_transaction_type] ON [dbo].[tblTritonTransactionData] ([transaction_type]);
CREATE INDEX [IX_tblTritonTransactionData_date_created] ON [dbo].[tblTritonTransactionData] ([date_created]);
CREATE INDEX [IX_tblTritonTransactionData_opportunity_id] ON [dbo].[tblTritonTransactionData] ([opportunity_id]);
CREATE INDEX [IX_tblTritonTransactionData_policy_number] ON [dbo].[tblTritonTransactionData] ([policy_number]);

-- Grant permissions
GRANT SELECT, INSERT ON [dbo].[tblTritonTransactionData] TO [IMS_User];

PRINT 'Table tblTritonTransactionData created successfully with simplified schema';
GO