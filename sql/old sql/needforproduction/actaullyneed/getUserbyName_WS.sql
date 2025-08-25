CREATE OR ALTER PROCEDURE [dbo].[getUserbyName_WS] 
	@fullname NVARCHAR(100) 
AS 
BEGIN 
	SET NOCOUNT ON; 
	
	SELECT TOP 1 UserGUID
	FROM tblusers 
	WHERE LTRIM(RTRIM(firstname)) + ' ' + LTRIM(RTRIM(lastname)) = @fullname 
	ORDER BY firstname, lastname 
	
END
