CREATE or ALTER   PROCEDURE [dbo].[Triton_UnbindPolicy_WS]
(
    @QuoteGuid UNIQUEIDENTIFIER,
    @UserGuid UNIQUEIDENTIFIER,
    @KeepPolicyNumbers BIT = 1,
    @KeepAffidavitNumbers BIT = 1
)
AS
BEGIN
    SET NOCOUNT ON
   
    DECLARE
        @UserID INT,
        @QuoteID INT,
        @ControlNo INT,
        @PolicyNo VARCHAR(50),
        @NewQuoteStatus TINYINT,
        @CurrentQuoteStatus TINYINT,
        @IsEndorsement BIT,
        @err VARCHAR(5000)








    -- Validate User
    SELECT @UserID = [UserID]
    FROM [dbo].[tblUsers]
    WHERE [UserGUID] = @UserGuid








    IF (@UserID IS NULL)
    BEGIN
        -- RAISERROR('The provided user could not be found.', 11, 1)
        SELECT 0 AS Result, 'The provided user could not be found.' AS Message
        RETURN
    END








    -- Validate Quote Exists
    IF NOT EXISTS
    (
        SELECT 1
        FROM [dbo].[tblQuotes]
        WHERE [QuoteGUID] = @QuoteGuid
    )
    BEGIN
        -- RAISERROR('The provided quote could not be found.', 11, 1)
        SELECT 0 AS Result, 'The provided quote could not be found.' AS Message
        RETURN
    END








    -- Validate Quote is Bound
    IF NOT EXISTS
    (
        SELECT 1
        FROM [dbo].[tblQuotes]
        WHERE [QuoteGUID] = @QuoteGuid
            AND [DateBound] IS NOT NULL
    )
    BEGIN
        -- RAISERROR('The provided quote is not bound, so it cannot be unbound.', 11, 1)
        SELECT 0 AS Result, 'The provided quote is not bound, so it cannot be unbound.' AS Message
        RETURN
    END








    -- Get Quote Details
    SELECT
        @QuoteID = [QuoteID],
        @ControlNo = [ControlNo],
        @PolicyNo = [PolicyNumber],
        @CurrentQuoteStatus = [QuoteStatusID],
        @IsEndorsement = IIF([TransactionTypeID] IS NULL, 0, 1)
    FROM [dbo].[tblQuotes]
    WHERE [QuoteGUID] = @QuoteGuid








    -- Validate Most Recent Transaction
    IF NOT EXISTS
    (
        SELECT 1
        FROM [dbo].[tblMaxQuoteIDs]
        WHERE [ControlNo] = @ControlNo
            AND [MaxQuoteID] = @QuoteID
    )
    BEGIN
        -- RAISERROR('The provided quote does not represent the most recent transaction on this policy, so it cannot be unbound.', 11, 1)
        SELECT 0 AS Result, 'The provided quote does not represent the most recent transaction on this policy, so it cannot be unbound.' AS Message
        RETURN
    END








    -- Calculate New Status
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








    -- Begin Transaction
    BEGIN TRANSACTION








    BEGIN TRY
        -- Log the action
        INSERT INTO [dbo].[tblLog]
        (
            [UserID],
            [Action],
            [IndentifierGuid]
        )
        VALUES
        (
            @UserID,
            'Unbound Policy #' + ISNULL(@PolicyNo, '') + ' - Control #' + CAST(@ControlNo AS VARCHAR) + ' via Triton_UnbindPolicy',
            @QuoteGuid
        )








        -- Process Invoice Voids
        DECLARE @invoiceNum INT, @InvoiceDate SMALLDATETIME, @GLCompanyID INT, @InvoiceTypeID VARCHAR(5)
       
        -- Loop through all the invoices that need to be voided
        DECLARE InvoiceCursor CURSOR LOCAL FAST_FORWARD FOR
            SELECT InvoiceNum, PostDate, GLCompanyID, InvoiceTypeID
            FROM tblFin_Invoices I
            INNER JOIN tblQuotes Q ON I.QuoteID = Q.QuoteID
            WHERE Q.QuoteGuid = @QuoteGuid AND I.Failed = 0
       
        OPEN InvoiceCursor
       
        FETCH NEXT FROM InvoiceCursor INTO @invoiceNum, @InvoiceDate, @GLCompanyID, @InvoiceTypeID
       
        WHILE @@FETCH_STATUS = 0
        BEGIN
            -- Check Underwriting Period
            IF (dbo.IsUnderwritingPeriodValid_GlCompany(@InvoiceDate, @GLCompanyID) = 0)
                AND @InvoiceTypeID NOT IN ('PB', 'WP')
            BEGIN
                CLOSE InvoiceCursor
                DEALLOCATE InvoiceCursor
                -- RAISERROR('Cannot unbind transaction - invoice billed in a closed underwriting period month.', 15, 55)
                ROLLBACK TRANSACTION
                SELECT 0 AS Result, 'Cannot unbind transaction - invoice billed in a closed underwriting period month.' AS Message
                RETURN
            END
           
            -- Check Accounting Period
            IF (dbo.IsAccountingPeriodValid_GlCompany(@InvoiceDate, @GLCompanyID) = 0)
                AND @InvoiceTypeID NOT IN ('PB', 'WP')
            BEGIN
                CLOSE InvoiceCursor
                DEALLOCATE InvoiceCursor
                -- RAISERROR('Cannot unbind the transaction - invoice billed in a closed accounting month.', 15, 55)
                ROLLBACK TRANSACTION
                SELECT 0 AS Result, 'Cannot unbind the transaction - invoice billed in a closed accounting month.' AS Message
                RETURN
            END
           
            -- Void the invoice
            EXEC dbo.spFin_VoidInvoice @invoiceNum, @UserGuid
           
            IF @@ERROR > 0
            BEGIN
                CLOSE InvoiceCursor
                DEALLOCATE InvoiceCursor
                -- RAISERROR('Error occurred while voiding invoice.', 15, 55)
                ROLLBACK TRANSACTION
                SELECT 0 AS Result, 'Error occurred while voiding invoice.' AS Message
                RETURN
            END
           
            FETCH NEXT FROM InvoiceCursor INTO @invoiceNum, @InvoiceDate, @GLCompanyID, @InvoiceTypeID
        END
       
        -- Cleanup the cursor      
        CLOSE InvoiceCursor
        DEALLOCATE InvoiceCursor
       
        -- Update the quote status
        UPDATE tblQuotes
        SET QuoteStatusID = @NewQuoteStatus,
            DateIssued = NULL,
            DateBound = NULL
        WHERE QuoteGuid = @QuoteGuid
       
        -- Remove the policy number if requested
        IF (@KeepPolicyNumbers = 0)
        BEGIN
            UPDATE tblQuotes
            SET PolicyNumber = NULL,
                PolicyNumberIndex = NULL
            WHERE QuoteGuid = @QuoteGuid
           
            -- Clear used policy number table
            EXEC [dbo].[spPolicyNumberingClearUsedTablePolicyNumber] @QuoteGuid
        END
       
        -- Remove affidavit numbers if requested
        IF (@KeepAffidavitNumbers = 0)
        BEGIN
            DELETE FROM tblQuoteAffidavitNumbers
            WHERE QuoteID = @QuoteID
        END








        COMMIT TRANSACTION
        SELECT 1 AS Result, 'Policy unbound successfully' AS Message, @QuoteGuid AS QuoteGuid, @PolicyNo AS PolicyNumber
    END TRY
    BEGIN CATCH
        ROLLBACK TRANSACTION








        SET @err = 'An error occurred while attempting to unbind: ' + ISNULL(ERROR_MESSAGE(), 'UNKNOWN ERROR')
        -- RAISERROR(@err, 11, 1)
        SELECT 0 AS Result, @err AS Message
        RETURN
    END CATCH
END
