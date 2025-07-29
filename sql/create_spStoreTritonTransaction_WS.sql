-- =============================================
-- Stored Procedure: spStoreTritonTransaction_WS
-- Description: Stores transaction data from Triton payload
-- Purpose: Store transaction history without quote associations
-- =============================================

IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[spStoreTritonTransaction_WS]') AND type in (N'P', N'PC'))
    DROP PROCEDURE [dbo].[spStoreTritonTransaction_WS]
GO

CREATE PROCEDURE [dbo].[spStoreTritonTransaction_WS]
    @transaction_id NVARCHAR(100),
    @full_payload_json NVARCHAR(MAX),
    @opportunity_id INT = NULL,
    @policy_number NVARCHAR(50) = NULL,
    @insured_name NVARCHAR(500) = NULL,
    @transaction_type NVARCHAR(100),
    @transaction_date NVARCHAR(50),
    @source_system NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        -- Check if transaction already exists
        IF EXISTS (SELECT 1 FROM tblTritonTransactionData WHERE transaction_id = @transaction_id)
        BEGIN
            -- Return existing transaction info
            SELECT 
                'Warning' AS Status,
                'Transaction already exists' AS Message,
                transaction_id,
                created_date
            FROM tblTritonTransactionData
            WHERE transaction_id = @transaction_id;
            
            RETURN;
        END
        
        -- Insert new transaction
        INSERT INTO tblTritonTransactionData (
            transaction_id,
            full_payload_json,
            opportunity_id,
            policy_number,
            insured_name,
            transaction_type,
            transaction_date,
            source_system,
            created_date
        )
        VALUES (
            @transaction_id,
            @full_payload_json,
            @opportunity_id,
            @policy_number,
            @insured_name,
            @transaction_type,
            @transaction_date,
            @source_system,
            GETDATE()
        );
        
        -- Return success
        SELECT 
            'Success' AS Status,
            'Transaction stored successfully' AS Message,
            @transaction_id AS transaction_id,
            SCOPE_IDENTITY() AS TritonTransactionDataID,
            GETDATE() AS created_date;
            
    END TRY
    BEGIN CATCH
        -- Return error
        SELECT 
            'Error' AS Status,
            ERROR_MESSAGE() AS Message,
            ERROR_NUMBER() AS ErrorNumber,
            ERROR_LINE() AS ErrorLine;
    END CATCH
END
GO

-- Grant execute permission to IMS user
GRANT EXECUTE ON [dbo].[spStoreTritonTransaction_WS] TO [IMS_User]
GO

PRINT 'Stored procedure spStoreTritonTransaction_WS created successfully';