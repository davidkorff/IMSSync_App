USE [Greyhawk_Test]
GO
/****** Object:  StoredProcedure [dbo].[spFin_CancelPolicy]    Script Date: 7/17/2025 10:25:03 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
ALTER PROCEDURE [dbo].[spFin_CancelPolicy]
(
    @ControlNumber INT,
    @Comments AS VARCHAR(2000) = NULL,
    @PostDate AS DATETIME = NULL,
    @UserGuid AS UNIQUEIDENTIFIER = NULL,
    @CheckNumber AS VARCHAR(100) = NULL
)
AS
BEGIN
    IF (@@TRANCOUNT = 0)
    BEGIN
        RAISERROR('This procedure must be called within a transaction.', 11, 1)
        RETURN
    END

    IF NOT EXISTS
    (
        SELECT 1
        FROM [dbo].[tblSystemSettings]
        WHERE
            (
                [Setting] = 'PolicyCancelWashFlat'
                OR [Setting] = 'PolicyCancelWashAll'
                OR [Setting] = 'PolicyEndorsementWashAll'
            )
            AND [SettingValueBool] = 1
    )
    BEGIN
        RETURN
    END

    DECLARE @CancelQuoteId INT
    DECLARE @CancelPostDate DATETIME
    DECLARE @GlCompanyId INT

    SELECT TOP (1)
        @CancelQuoteId = [QuoteID],
        @CancelPostDate = [PostDate],
        @GlCompanyId = [GLCompanyID]
    FROM [dbo].[tblFin_Invoices]
    WHERE [QuoteControlNum] = @ControlNumber
        AND [Failed] = 0
        AND [InvoiceTypeID] = 'IN'
    ORDER BY [InvoiceNum] DESC

    IF (@@ROWCOUNT = 0)
    BEGIN
        RAISERROR('No invoices found for this policy.', 11, 1)
        RETURN
    END

    IF
    (
        SELECT -SUM(RW.[AmtDue])
        FROM [dbo].[tblFin_ReceivableWorking] RW
        JOIN [dbo].[tblFin_Invoices] I
            ON I.[InvoiceNum] = RW.[InvoiceNumber]
            AND I.[Failed] = 0
        WHERE RW.[QuoteId] = @CancelQuoteId
    ) <= 0
    BEGIN
        RAISERROR('Most recent quote does not refund money.', 11, 1)
        RETURN
    END

    DECLARE @RemitterGuid UNIQUEIDENTIFIER

    SELECT TOP (1)
        @RemitterGuid = RW.[RemitterGuid]
    FROM [dbo].[tblFin_ReceivableWorking] RW
    JOIN [dbo].[tblFin_Invoices] I
        ON I.[InvoiceNum] = RW.[InvoiceNumber]
        AND I.[Failed] = 0
    WHERE RW.[QuoteId] = @CancelQuoteId

    IF (@UserGuid IS NULL OR EXISTS (
        SELECT 1
        FROM [dbo].[tblFin_FlatCancelInvoiceSettings]
        WHERE [GlCompanyId] = @GlCompanyId
            AND [UseCancellingUser] = 0
    ))
    BEGIN
        SET @UserGuid =
        (
            SELECT TOP (1) [UserGuid]
            FROM [dbo].[tblFin_FlatCancelInvoiceSettings]
            WHERE [GlCompanyId] = @GlCompanyId
        )
    END

    IF (@UserGuid IS NULL)
    BEGIN
        RAISERROR('No user was specified in the flat cancel invoice settings.', 11, 1)
    END

    IF (@Comments IS NULL)
    BEGIN
        SET @Comments =
        (
            SELECT TOP (1) [Comments]
            FROM [dbo].[tblFin_FlatCancelInvoiceSettings]
            WHERE [GlCompanyId] = @GlCompanyId
        )
    END

    IF (@CheckNumber IS NULL)
    BEGIN
        SET @CheckNumber =
        (
            SELECT TOP (1) [CheckNumber]
            FROM [dbo].[tblFin_FlatCancelInvoiceSettings]
            WHERE [GlCompanyId] = @GlCompanyId
        )
    END

    IF (@PostDate IS NOT NULL AND DATEDIFF(d, @CancelPostDate, @PostDate) > 0)
    BEGIN
        SET @CancelPostDate = @PostDate
    END

    DECLARE @TransactNum INT

    DECLARE @CancelGlAcctId INT, @CancelInvoiceNum INT, @CancelChargeCode INT, @CancelCompanyLineGuid UNIQUEIDENTIFIER,
        @CancelCurrencyCode VARCHAR(10), @CancelEntityGuid UNIQUEIDENTIFIER, @CancelAmount MONEY,
        @CancelCostCenterId INT

    DECLARE @PostingNum INT, @RowId INT, @GlAcctId INT, @InvoiceNum INT, @ChargeCode INT, @CompanyLineGuid UNIQUEIDENTIFIER,
        @EntityGuid UNIQUEIDENTIFIER, @Amount MONEY, @CostCenterId INT

    DECLARE [cancel_lines] CURSOR LOCAL FAST_FORWARD FOR
    SELECT
        GL.[GLAcctID],
        RW.[InvoiceNumber],
        RW.[ChargeCode],
        RW.[CompanyLineGuid],
        RW.[CurrencyCode],
        RW.[EntityGuid],
        -RW.[AmtDue],
        RW.[CostCenterId]
    FROM [dbo].[tblFin_ReceivableWorking] RW
    JOIN [dbo].[tblFin_GLAccounts] GL
        ON GL.[GlCompanyId] = RW.[GLCompanyId]
        AND GL.[ShortName] = 'AR'
    JOIN [dbo].[tblFin_Invoices] I
        ON I.[InvoiceNum] = RW.[InvoiceNumber]
        AND I.[Failed] = 0
    LEFT JOIN [dbo].[tblFin_PolicyCharges] PC
        ON PC.[ChargeCode] = RW.[ChargeCode]
    WHERE RW.[ControlNumber] = @ControlNumber
        AND RW.[GLCompanyID] = @GlCompanyId
        AND RW.[QuoteId] = @CancelQuoteId
        AND DATEDIFF(d, I.[PostDate], @CancelPostDate) >= 0
        AND RW.[AmtDue] < 0
    ORDER BY
        I.[PostDate] DESC,
        ( CASE WHEN PC.[ChargeType] = 'P' THEN 1 ELSE 0 END ) DESC,
        I.[InvoiceNum] DESC

    OPEN [cancel_lines]
    FETCH NEXT FROM [cancel_lines]
    INTO @CancelGlAcctId, @CancelInvoiceNum, @CancelChargeCode, @CancelCompanyLineGuid, @CancelCurrencyCode,
        @CancelEntityGuid, @CancelAmount, @CancelCostCenterId

    WHILE (@@FETCH_STATUS = 0)
    BEGIN
        DECLARE [receivable_lines] CURSOR LOCAL FAST_FORWARD FOR
        SELECT
            RW.[RowId],
            GL.[GLAcctID],
            RW.[InvoiceNumber],
            RW.[ChargeCode],
            RW.[CompanyLineGuid],
            RW.[EntityGuid],
            RW.[AmtDue],
            RW.[CostCenterId]
        FROM [dbo].[tblFin_ReceivableWorking] RW
        JOIN [dbo].[tblFin_GLAccounts] GL
            ON GL.[GlCompanyId] = RW.[GLCompanyId]
            AND GL.[ShortName] = 'AR'
        JOIN [dbo].[tblFin_Invoices] I
            ON I.[InvoiceNum] = RW.[InvoiceNumber]
            AND I.[Failed] = 0
        WHERE RW.[ControlNumber] = @ControlNumber
            AND RW.[GLCompanyID] = @GlCompanyId
            AND RW.[QuoteId] <> @CancelQuoteId
            AND RW.[CurrencyCode] = @CancelCurrencyCode
            AND DATEDIFF(d, I.[PostDate], @CancelPostDate) >= 0
            AND RW.[ChargeCode] = @CancelChargeCode
            AND RW.[CompanyLineGuid] = @CancelCompanyLineGuid
            AND RW.[AmtDue] > 0
        ORDER BY
            I.[PostDate] DESC,
            RW.[InvoiceNumber] DESC

        OPEN [receivable_lines]
        FETCH NEXT FROM [receivable_lines]
        INTO @RowId, @GlAcctId, @InvoiceNum, @ChargeCode, @CompanyLineGuid,
            @EntityGuid, @Amount, @CostCenterId

        WHILE (@@FETCH_STATUS = 0)
        BEGIN
            IF (@Amount > @CancelAmount)
            BEGIN
                SET @Amount = @CancelAmount
            END

            IF (@Amount > 0)
            BEGIN
                SET @CancelAmount -= @Amount

                IF (@TransactNum IS NULL)
                BEGIN
                    INSERT INTO [dbo].[tblFin_Journal]
                    (
                        [PostDate],
                        [TransDescID],
                        [JournalEntryType],
                        [Comments],
                        [UserGUID]
                    )
                    VALUES
                    (
                        @CancelPostDate,
                        'R',
                        'I',
                        @Comments,
                        @UserGuid
                    )

                    SET @TransactNum = SCOPE_IDENTITY()
                END

                INSERT INTO [dbo].[tblFin_JournalPostings]
                (
                    [TransactNum],
                    [GLAcctID],
                    [SourceDocType],
                    [InvoiceNum],
                    [ChargeCode],
                    [CompanyLineGuid],
                    [CurrencyCode_Amount],
                    [EntityGuid],
                    [Amount]
                )
                VALUES
                (
                    @TransactNum,
                    @GlAcctID,
                    'I',
                    @InvoiceNum,
                    @ChargeCode,
                    @CompanyLineGuid,
                    @CancelCurrencyCode,
                    @EntityGuid,
                    -@Amount
                )

                SET @PostingNum = SCOPE_IDENTITY()

                INSERT INTO [dbo].[tblFin_CostCenterAllocation]
                (
                    [PostingNum],
                    [CostCenterId],
                    [Amount]
                )
                VALUES
                (
                    @PostingNum,
                    @CostCenterId,
                    -@Amount
                )

                INSERT INTO [dbo].[tblFin_JournalPostings]
                (
                    [TransactNum],
                    [GLAcctID],
                    [SourceDocType],
                    [InvoiceNum],
                    [ChargeCode],
                    [CompanyLineGuid],
                    [CurrencyCode_Amount],
                    [EntityGuid],
                    [Amount]
                )
                VALUES
                (
                    @TransactNum,
                    @CancelGlAcctId,
                    'I',
                    @CancelInvoiceNum,
                    @CancelChargeCode,
                    @CancelCompanyLineGuid,
                    @CancelCurrencyCode,
                    @CancelEntityGuid,
                    @Amount
                )

                SET @PostingNum = SCOPE_IDENTITY()

                INSERT INTO [dbo].[tblFin_CostCenterAllocation]
                (
                    [PostingNum],
                    [CostCenterId],
                    [Amount]
                )
                VALUES
                (
                    @PostingNum,
                    @CancelCostCenterId,
                    @Amount
                )

                IF (@CancelAmount <= 0)
                BEGIN
                    BREAK
                END
            END

            FETCH NEXT FROM [receivable_lines]
            INTO @RowId, @GlAcctId, @InvoiceNum, @ChargeCode, @CompanyLineGuid,
                @EntityGuid, @Amount, @CostCenterId
        END

        CLOSE [receivable_lines]
        DEALLOCATE [receivable_lines]

        IF (@CancelAmount <= 0)
        BEGIN
            FETCH NEXT FROM [cancel_lines]
            INTO @CancelGlAcctId, @CancelInvoiceNum, @CancelChargeCode, @CancelCompanyLineGuid, @CancelCurrencyCode,
                @CancelEntityGuid, @CancelAmount, @CancelCostCenterId
            CONTINUE
        END

        DECLARE [receivable_lines] CURSOR LOCAL FAST_FORWARD FOR
        SELECT
            RW.[RowId],
            GL.[GLAcctID],
            RW.[InvoiceNumber],
            RW.[ChargeCode],
            RW.[CompanyLineGuid],
            RW.[EntityGuid],
            RW.[AmtDue],
            RW.[CostCenterId]
        FROM [dbo].[tblFin_ReceivableWorking] RW
        JOIN [dbo].[tblFin_GLAccounts] GL
            ON GL.[GlCompanyId] = RW.[GLCompanyId]
            AND GL.[ShortName] = 'AR'
        JOIN [dbo].[tblFin_Invoices] I
            ON I.[InvoiceNum] = RW.[InvoiceNumber]
            AND I.[Failed] = 0
        LEFT JOIN [dbo].[tblFin_PolicyCharges] PC
            ON PC.[ChargeCode] = RW.[ChargeCode]
        WHERE RW.[ControlNumber] = @ControlNumber
            AND RW.[GLCompanyID] = @GlCompanyId
            AND RW.[QuoteId] <> @CancelQuoteId
            AND RW.[CurrencyCode] = @CancelCurrencyCode
            AND DATEDIFF(d, I.[PostDate], @CancelPostDate) >= 0
            AND RW.[AmtDue] > 0
        ORDER BY
            I.[PostDate] DESC,
            RW.[InvoiceNumber] DESC,
            ( CASE WHEN PC.[ChargeType] = 'P' THEN 1 ELSE 0 END ) DESC

        OPEN [receivable_lines]
        FETCH NEXT FROM [receivable_lines]
        INTO @RowId, @GlAcctId, @InvoiceNum, @ChargeCode, @CompanyLineGuid,
            @EntityGuid, @Amount, @CostCenterId

        WHILE (@@FETCH_STATUS = 0)
        BEGIN
            IF (@Amount > @CancelAmount)
            BEGIN
                SET @Amount = @CancelAmount
            END
            
            IF (@Amount > 0)
            BEGIN
                SET @CancelAmount -= @Amount

                IF (@TransactNum IS NULL)
                BEGIN
                    INSERT INTO [dbo].[tblFin_Journal]
                    (
                        [PostDate],
                        [TransDescID],
                        [JournalEntryType],
                        [Comments],
                        [UserGUID]
                    )
                    VALUES
                    (
                        @CancelPostDate,
                        'R',
                        'I',
                        @Comments,
                        @UserGuid
                    )

                    SET @TransactNum = SCOPE_IDENTITY()
                END

                INSERT INTO [dbo].[tblFin_JournalPostings]
                (
                    [TransactNum],
                    [GLAcctID],
                    [SourceDocType],
                    [InvoiceNum],
                    [ChargeCode],
                    [CompanyLineGuid],
                    [CurrencyCode_Amount],
                    [EntityGuid],
                    [Amount]
                )
                VALUES
                (
                    @TransactNum,
                    @GlAcctID,
                    'I',
                    @InvoiceNum,
                    @ChargeCode,
                    @CompanyLineGuid,
                    @CancelCurrencyCode,
                    @EntityGuid,
                    -@Amount
                )

                SET @PostingNum = SCOPE_IDENTITY()

                INSERT INTO [dbo].[tblFin_CostCenterAllocation]
                (
                    [PostingNum],
                    [CostCenterId],
                    [Amount]
                )
                VALUES
                (
                    @PostingNum,
                    @CostCenterId,
                    -@Amount
                )

                INSERT INTO [dbo].[tblFin_JournalPostings]
                (
                    [TransactNum],
                    [GLAcctID],
                    [SourceDocType],
                    [InvoiceNum],
                    [ChargeCode],
                    [CompanyLineGuid],
                    [CurrencyCode_Amount],
                    [EntityGuid],
                    [Amount]
                )
                VALUES
                (
                    @TransactNum,
                    @CancelGlAcctId,
                    'I',
                    @CancelInvoiceNum,
                    @CancelChargeCode,
                    @CancelCompanyLineGuid,
                    @CancelCurrencyCode,
                    @CancelEntityGuid,
                    @Amount
                )

                SET @PostingNum = SCOPE_IDENTITY()

                INSERT INTO [dbo].[tblFin_CostCenterAllocation]
                (
                    [PostingNum],
                    [CostCenterId],
                    [Amount]
                )
                VALUES
                (
                    @PostingNum,
                    @CancelCostCenterId,
                    @Amount
                )

                IF (@CancelAmount <= 0)
                BEGIN
                    BREAK
                END
            END

            FETCH NEXT FROM [receivable_lines]
            INTO @RowId, @GlAcctId, @InvoiceNum, @ChargeCode, @CompanyLineGuid,
                @EntityGuid, @Amount, @CostCenterId
        END

        CLOSE [receivable_lines]
        DEALLOCATE [receivable_lines]

        FETCH NEXT FROM [cancel_lines]
        INTO @CancelGlAcctId, @CancelInvoiceNum, @CancelChargeCode, @CancelCompanyLineGuid, @CancelCurrencyCode,
            @CancelEntityGuid, @CancelAmount, @CancelCostCenterId
    END

    CLOSE [cancel_lines]
    DEALLOCATE [cancel_lines]

    IF (@TransactNum IS NULL)
    BEGIN
        -- Nothing posted, but nothing failed. No transaction created.
        RETURN
    END

    INSERT INTO [dbo].[tblFin_RemitterJournal]
    (
        [TransactNum],
        [RemitterGUID],
        [ReceivedDate],
        [DepositDate],
        [CheckNumber],
        [Amount],
        [Comments],
        [Reconciled],
        [RemittedByGuid],
        [CheckBounced],
        [BouncedTransactNum],
        [isCreditCard]
    )
    VALUES
    (
        @TransactNum,
        @RemitterGuid,
        @CancelPostDate,
        @CancelPostDate,
        @CheckNumber,
        0,
        @Comments,
        0,
        NULL,
        NULL,
        NULL,
        0
    )

    IF ([dbo].[CheckTransactionBalances](@TransactNum) <> 1)
    BEGIN
        RAISERROR('This transaction will result in the books being out of balance.', 11, 1)
        RETURN
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
            EXEC dbo.spFin_UpdateWorking_Transaction @TransactNum
        END

    SELECT @TransactNum
END


