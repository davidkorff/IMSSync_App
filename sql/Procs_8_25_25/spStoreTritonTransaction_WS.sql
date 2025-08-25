CREATE OR ALTER PROCEDURE [dbo].[spStoreTritonTransaction_WS]
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
                date_created
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
            date_created
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
            GETDATE() AS date_created;
            
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






