CREATE OR ALTER PROCEDURE [dbo].[getProducerbyName_WS]
    @fullname NVARCHAR(100)
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT TOP 1 ProducerContactGUID, ProducerLocationGUID 
    FROM tblproducercontacts 
    WHERE LTRIM(RTRIM(fname)) + ' ' + LTRIM(RTRIM(lname)) = @fullname
    ORDER BY fname, lname

END