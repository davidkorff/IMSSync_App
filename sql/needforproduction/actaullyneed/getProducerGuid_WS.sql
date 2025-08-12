CREATE OR ALTER PROCEDURE [dbo].[getProducerGuid_WS]
    @producer_email NVARCHAR(100)
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT TOP 1 
        ProducerContactGUID, 
        ProducerLocationGUID 
    FROM tblproducercontacts 
    WHERE statusid = 1 
        AND email = @producer_email
    ORDER BY ProducerContactGUID DESC
END