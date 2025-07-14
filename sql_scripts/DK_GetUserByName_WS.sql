SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE OR ALTER PROCEDURE [dbo].[DK_GetUserByName_WS]
    @UserName NVARCHAR(255)
AS
BEGIN
    SET NOCOUNT ON;

    -- Return user information by searching name
    -- Searches in FirstName, LastName, Name_FirstLast, Name_LastFirst, and UserName fields
    SELECT TOP 1
        UserGUID,
        UserID,
        OfficeGUID,
        UserName,
        FirstName,
        LastName,
        Title,
        Name_FirstLast,
        Name_LastFirst,
        EmailAddress
    FROM
        tblUsers
    WHERE
        (FirstName LIKE '%' + @UserName + '%'
        OR LastName LIKE '%' + @UserName + '%'
        OR Name_FirstLast LIKE '%' + @UserName + '%'
        OR Name_LastFirst LIKE '%' + @UserName + '%'
        OR UserName LIKE '%' + @UserName + '%')
    ORDER BY
        -- Prioritize exact matches
        CASE 
            WHEN Name_FirstLast = @UserName THEN 1
            WHEN Name_LastFirst = @UserName THEN 2
            WHEN UserName = @UserName THEN 3
            WHEN FirstName + ' ' + LastName = @UserName THEN 4
            WHEN LastName + ', ' + FirstName = @UserName THEN 5
            ELSE 6
        END,
        UserID DESC;  -- If multiple matches, get the most recent user
END