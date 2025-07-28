USE [Greyhawk_Test]
GO
/****** Object:  StoredProcedure [VERTAFORE\peterlad].[Ascot_UnbindPolicy_WS]    Script Date: 7/17/2025 10:25:53 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
ALTER   PROCEDURE [VERTAFORE\peterlad].[Ascot_UnbindPolicy_WS]
(
    @QuoteGuid UNIQUEIDENTIFIER,
    @UserGuid UNIQUEIDENTIFIER,
    @KeepPolicyNumbers BIT = 1,
    @KeepAffidavitNumbers BIT = 1
)
AS
BEGIN
    DECLARE
        @UserID INT,
        @err VARCHAR(5000)

    SELECT @UserID = [UserID]
    FROM [dbo].[tblUsers]
    WHERE [UserGUID] = @UserGuid

    IF (@UserID IS NULL)
    BEGIN
        RAISERROR('The provided user could not be found.', 11, 1)
        SELECT 0
        RETURN
    END

    IF NOT EXISTS
    (
        SELECT 1
        FROM [dbo].[tblQuotes]
        WHERE [QuoteGUID] = @QuoteGuid
    )
    BEGIN
        RAISERROR('The provided qutoe could not be found.', 11, 1)
        SELECT 0
        RETURN
    END

    IF NOT EXISTS
    (
        SELECT 1
        FROM [dbo].[tblQuotes]
        WHERE [QuoteGUID] = @QuoteGuid
            AND [DateBound] IS NOT NULL
    )
    BEGIN
        RAISERROR('The provided qutoe is not bound, so it cannot be unbound.', 11, 1)
        SELECT 0
        RETURN
    END

    DECLARE
        @QuoteID INT,
        @ControlNo INT,
        @PolicyNo VARCHAR(50)

    SELECT
        @QuoteID = [QuoteID],
        @ControlNo = [ControlNo],
        @PolicyNo = [PolicyNumber]
    FROM [dbo].[tblQuotes]
    WHERE [QuoteGUID] = @QuoteGuid

    IF NOT EXISTS
    (
        SELECT 1
        FROM [dbo].[tblMaxQuoteIDs]
        WHERE [ControlNo] = @ControlNo
            AND [MaxQuoteID] = @QuoteID
    )
    BEGIN
        RAISERROR('The provided quote does not represent the most recent transaction on this policy, so it cannot be unbound.', 11, 1)
        SELECT 0
        RETURN
    END

    DECLARE
        @NewQuoteStatus TINYINT,
        @CurrentQuoteStatus TINYINT,
        @IsEndorsement BIT

    SELECT
        @CurrentQuoteStatus = [QuoteStatusID],
        @IsEndorsement = IIF([TransactionTypeID] IS NULL, 0, 1)
    FROM [dbo].[tblQuotes]
    WHERE [QuoteGUID] = @QuoteGuid

    -- Mirrors logic from Quote.UnbindTransactionHandler
    IF (@IsEndorsement = 1)
    BEGIN
        IF
        (
            SELECT TOP (1) [OriginalQuoteStatusID]
            FROM [dbo].[tblQuoteStatusChangeLog]
            WHERE [ControlNo] = @ControlNo
            ORDER BY [ID] DESC
        ) = 8 -- Pending Reinstatement
        BEGIN
            SET @NewQuoteStatus = 8 -- Pending Reinstatement
        END
        ELSE IF (@CurrentQuoteStatus = 12) -- Cancelled
        BEGIN
            SET @NewQuoteStatus = 7 -- Pending Cancellation
        END
        ELSE IF (@CurrentQuoteStatus = 17) -- Non-Renewed
        BEGIN
            SET @NewQuoteStatus = 26 -- Unbound Non-Renewal
        END
        ELSE IF (@CurrentQuoteStatus = 28) -- Non-Renewal Rescinded
        BEGIN
            SET @NewQuoteStatus = 27 -- Unbound Non-Renewal Rescinded
        END
        ELSE
        BEGIN
            SET @NewQuoteStatus = 9 -- Unbound Endorsement
        END
    END
    ELSE
    BEGIN
        SET @NewQuoteStatus = 1 -- Submitted
    END

    BEGIN TRANSACTION

    BEGIN TRY
        INSERT INTO [dbo].[tblLog]
        (
            [UserID],
            [Action],
            [IndentifierGuid]
        )
        VALUES
        (
            @UserID,
            'Unbound Policy #' + ISNULL(@PolicyNo, '') + ' - Control #' + CAST(@ControlNo AS VARCHAR) + ' via Ascot_UnbindPolicy_WS',
            @QuoteGuid
        )

        EXEC [dbo].[Greyhawk_spUnbindPolicy]
            @QuoteGuid,
            @UserGuid,
            @NewQuoteStatus,
            @KeepPolicyNumbers,
            @KeepAffidavitNumbers
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION

        SET @err = 'An error occured while attempting to unbind: ' + ISNULL(ERROR_MESSAGE(), 'UNKNOWN ERROR')
        RAISERROR(@err, 11, 1)
        SELECT 0
        RETURN
    END CATCH

    IF (@KeepPolicyNumbers = 0)
    BEGIN
        BEGIN TRY
            EXEC [dbo].[spPolicyNumberingClearUsedTablePolicyNumber] @QuoteGuid
        END TRY
        BEGIN CATCH
            ROLLBACK TRANSACTION

            SET @err = 'An error occured while attempting to clear used policy numbers: ' + ISNULL(ERROR_MESSAGE(), 'UNKNOWN ERROR')
            RAISERROR(@err, 11, 1)
            SELECT 0
            RETURN
        END CATCH
    END

    COMMIT TRANSACTION
    SELECT 1
END

