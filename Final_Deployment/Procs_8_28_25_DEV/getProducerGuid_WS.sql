CREATE OR ALTER   PROCEDURE [dbo].[getProducerGuid_WS]
    @producer_email NVARCHAR(100),
    @producer_name NVARCHAR(100) = NULL
AS
BEGIN
    SET NOCOUNT ON;
   
    -- First, try to find by email
    IF EXISTS (SELECT 1 FROM tblproducercontacts WHERE statusid = 1 AND email = @producer_email)
    BEGIN
        SELECT TOP 1
            ProducerContactGUID,
            ProducerLocationGUID
        FROM tblproducercontacts
        WHERE statusid = 1
            AND email = @producer_email
        ORDER BY ProducerContactGUID DESC
    END
    ELSE
    BEGIN
        -- If no email match found, try by name (backward compatibility)
        SELECT TOP 1
            ProducerContactGUID,
            ProducerLocationGUID
        FROM tblproducercontacts
        WHERE LTRIM(RTRIM(fname)) + ' ' + LTRIM(RTRIM(lname)) = @producer_name
        ORDER BY fname, lname
    END
END












