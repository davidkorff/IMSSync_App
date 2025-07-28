USE [Greyhawk_Test]
GO
/****** Object:  StoredProcedure [dbo].[spFin_FlatCancel]    Script Date: 7/17/2025 10:25:23 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
ALTER PROCEDURE [dbo].[spFin_FlatCancel]
(
    @ControlNumber INT,
    @Comments AS VARCHAR(2000) = NULL,
    @PostDate AS DATETIME = NULL,
    @UserGuid AS UNIQUEIDENTIFIER = NULL
)
AS
BEGIN

    IF NOT EXISTS
    (
        SELECT
            1
        FROM
            dbo.tblSystemSettings
        WHERE
              Setting = 'EnableFlatCancel'
          AND SettingValueBool = '1'
    )
        BEGIN
            SELECT 0
            RETURN
        END

    IF @@TRANCOUNT = 0
        BEGIN
            THROW 50000, 'This stored procedure must be used within a transaction.', 1;
        END

    DECLARE @GlCompanyId INT

    SELECT
        @GlCompanyId = GLCompanyID
    FROM
        dbo.tblFin_Invoices
    WHERE
        QuoteControlNum = @ControlNumber

    IF @GlCompanyId IS NULL
        BEGIN
            THROW 50000, 'The GlCompanyId was not found.', 1;
        END

    IF @UserGuid IS NULL
        BEGIN
            SET @UserGuid = (
                                SELECT TOP 1
                                    UserGuid
                                FROM
                                    dbo.tblFin_FlatCancelInvoiceSettings
                                WHERE
                                    GlCompanyId = @GlCompanyId
                            )
        END

    IF @UserGuid IS NULL
        BEGIN
            THROW 50000, 'UserGuid not specified and not found in Flat Cancel Invoice settings.', 1;
        END

    IF @Comments IS NULL
        BEGIN
            SET @Comments = (
                                SELECT TOP 1
                                    Comments
                                FROM
                                    dbo.tblFin_FlatCancelInvoiceSettings
                                WHERE
                                    GlCompanyId = @GlCompanyId
                            )
        END

    IF @PostDate IS NULL
        BEGIN
            SET @PostDate = GETDATE()
        END

    IF OBJECT_ID('tempdb..#FlatCancelRows') IS NOT NULL
        BEGIN
            DROP TABLE #FlatCancelRows
        END

    CREATE TABLE #FlatCancelRows
    (
        LeftRowId INT,
        RightRowId INT,
        GLAcctId INT
    )

    INSERT INTO
        #FlatCancelRows
        (
            LeftRowId,
            RightRowId,
            GLAcctID
        )
    SELECT
        rw1.RowId,
        rw2.RowId,
        fgla.GLAcctID
    FROM
        dbo.tblFin_ReceivableWorking rw1
            JOIN dbo.tblFin_ReceivableWorking rw2
                ON rw2.ControlNumber = rw1.ControlNumber AND rw2.AmtDue = -rw1.AmtDue
                AND rw2.GLCompanyId = rw1.GLCompanyId AND rw2.ChargeCode = rw1.ChargeCode
                AND rw2.CompanyLineGuid = rw1.CompanyLineGuid
            JOIN dbo.tblFin_GLAccounts fgla
                ON fgla.GlCompanyId = rw1.GLCompanyId
            JOIN dbo.tblFin_Invoices fin1
                ON fin1.InvoiceNum = rw1.InvoiceNumber
            JOIN dbo.tblFin_Invoices fin2
                ON fin2.InvoiceNum = rw2.InvoiceNumber
    WHERE
          rw1.ControlNumber = @ControlNumber
      AND fgla.ShortName = 'AR'
      AND fin1.Failed = 0
      AND fin2.Failed = 0
      AND rw1.AmtDue > 0

    IF NOT EXISTS
    (
        SELECT
            1
        FROM
            #FlatCancelRows
    )
        BEGIN
            SELECT 0
            DROP TABLE #FlatCancelRows
            RETURN
        END

    INSERT INTO
        dbo.tblFin_Journal(
                              PostDate,
                              TransDescId,
                              JournalEntryType,
                              Comments,
                              UserGuid
                          )
    VALUES
        (
            @PostDate,
            'R',
            'I',
            @Comments,
            @UserGuid
        )

    DECLARE @TransactionNumber INT = SCOPE_IDENTITY()

    DECLARE @InsertedPostings TABLE
                              (
                                  PostingNum INT,
                                  Amount DECIMAL(18, 2),
                                  InvoiceNumber INT
                              )

    INSERT INTO
        dbo.tblFin_JournalPostings
        (
            TransactNum,
            GLAcctID,
            SourceDocType,
            InvoiceNum,
            ChargeCode,
            CompanyLineGuid,
            Amount,
            EntityGuid,
            CurrencyCode_Amount
        )
    OUTPUT
        inserted.PostingNum,
        inserted.Amount,
        inserted.InvoiceNum INTO @InsertedPostings (PostingNum, Amount, InvoiceNumber)
    SELECT
        @TransactionNumber,
        rows.GLAcctID,
        'I',
        rw.InvoiceNumber,
        rw.ChargeCode,
        rw.CompanyLineGuid,
        -rw.AmtDue,
        rw.EntityGuid,
        rw.CurrencyCode
    FROM
        dbo.tblFin_ReceivableWorking rw
            JOIN #FlatCancelRows rows
                ON rows.LeftRowId = rw.RowId

    INSERT INTO
        dbo.tblFin_CostCenterAllocation(
                                           PostingNum,
                                           CostCenterId,
                                           Amount
                                       )
    SELECT
        ip.PostingNum,
        fi.CostCenterId,
        ip.Amount
    FROM
        @InsertedPostings ip
            JOIN dbo.tblFin_Invoices fi
                ON fi.InvoiceNum = ip.InvoiceNumber

    DELETE
    FROM
        @InsertedPostings

    INSERT INTO
        dbo.tblFin_JournalPostings
        (
            TransactNum,
            GLAcctID,
            SourceDocType,
            InvoiceNum,
            ChargeCode,
            CompanyLineGuid,
            Amount,
            EntityGuid,
            CurrencyCode_Amount
        )
    OUTPUT
        inserted.PostingNum,
        inserted.Amount,
        inserted.InvoiceNum INTO @InsertedPostings (PostingNum, Amount, InvoiceNumber)
    SELECT
        @TransactionNumber,
        rows.GLAcctID,
        'I',
        rw.InvoiceNumber,
        rw.ChargeCode,
        rw.CompanyLineGuid,
        -rw.AmtDue,
        rw.EntityGuid,
        rw.CurrencyCode
    FROM
        dbo.tblFin_ReceivableWorking rw
            JOIN #FlatCancelRows rows
                ON rows.RightRowId = rw.RowId

    INSERT INTO
        dbo.tblFin_CostCenterAllocation(
                                           PostingNum,
                                           CostCenterId,
                                           Amount
                                       )
    SELECT
        ip.PostingNum,
        fi.CostCenterId,
        ip.Amount
    FROM
        @InsertedPostings ip
            JOIN dbo.tblFin_Invoices fi
                ON fi.InvoiceNum = ip.InvoiceNumber

    DROP TABLE #FlatCancelRows

    IF dbo.CheckTransactionBalances(@TransactionNumber) <> 1
        BEGIN
            THROW 50000, 'This transaction will result in the books being out of balance.', 123;
        END

	-- Update working tables
    IF EXISTS
    (
        SELECT
            1
        FROM
            dbo.tblSystemSettings
        WHERE
              Setting = 'IsUpdateWorkingTriggerDisabled'
          AND SettingValueBool = 1
    )
        BEGIN
            EXEC dbo.spFin_UpdateWorking_Transaction @TransactionNumber
        END

    SELECT @TransactionNumber

END


