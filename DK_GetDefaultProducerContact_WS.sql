SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE OR ALTER PROCEDURE [dbo].[DK_GetDefaultProducerContact_WS]
    @ProducerGUID UNIQUEIDENTIFIER
AS
BEGIN
    SET NOCOUNT ON;

    -- Get the default (primary) contact for a producer entity
    -- This returns the first active contact for the producer
    SELECT TOP 1
        ContactGUID,
        ProducerGUID,
        FName,
        LName,
        Title,
        Email,
        Phone,
        Extension,
        StatusID
    FROM
        tblProducerContacts
    WHERE
        ProducerGUID = @ProducerGUID
        AND StatusID = 1  -- Active status
    ORDER BY
        -- Prioritize primary contacts if there's a flag
        CASE 
            WHEN Title LIKE '%primary%' OR Title LIKE '%main%' THEN 1
            ELSE 2
        END,
        ContactID;  -- Oldest contact first if no primary designation
END