USE [Greyhawk_Prod]
GO

/****** Object:  StoredProcedure [dbo].[Triton_UnbindPolicy_WS]    Script Date: [Current Date] ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE OR ALTER PROCEDURE [dbo].[Triton_UnbindPolicy]
(
    @QuoteGuid UNIQUEIDENTIFIER,
    @UserGuid UNIQUEIDENTIFIER,
    @KeepPolicyNumbers BIT = 1,
    @KeepAffidavitNumbers BIT = 1
)
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE 
        @QuoteID INT,
        @ControlNo INT,
        @PolicyNumber VARCHAR(50),
        @UserID INT,
        @ErrorMessage NVARCHAR(4000),
        @ResultStatus INT = 0,
        @NewQuoteStatus TINYINT,
        @CurrentQuoteStatus TINYINT,
        @IsEndorsement BIT,
        @InvoiceNum INT,
        @InvoiceDate SMALLDATETIME,
        @GLCompanyID INT,
        @InvoiceTypeID VARCHAR(5);

    BEGIN TRY
        -- Start transaction
        BEGIN TRANSACTION;

        -- Validate and get UserID
        SELECT @UserID = [UserID]
        FROM [dbo].[tblUsers]
        WHERE [UserGUID] = @UserGuid;

        IF @UserID IS NULL
        BEGIN
            -- RAISERROR('The provided user could not be found.', 16, 1);
            SELECT 0 AS Result, 'The provided user could not be found.' AS Message;
            ROLLBACK TRANSACTION;
            RETURN;
        END

        -- Get quote info from QuoteGuid
        SELECT
            @QuoteID = q.QuoteID,
            @ControlNo = q.ControlNo,
            @PolicyNumber = q.PolicyNumber,
            @CurrentQuoteStatus = q.QuoteStatusID,
            @IsEndorsement = IIF(q.TransactionTypeID IS NULL, 0, 1)
        FROM [dbo].[tblQuotes] q
        WHERE q.QuoteGUID = @QuoteGuid;

        -- Validate quote was found
        IF @QuoteID IS NULL
        BEGIN
            -- RAISERROR('No quote found for the provided QuoteGuid: %s', 16, 1, @QuoteGuid);
            SELECT 0 AS Result, 'No quote found for the provided QuoteGuid' AS Message;
            ROLLBACK TRANSACTION;
            RETURN;
        END

        -- Check if quote is bound
        IF NOT EXISTS (
            SELECT 1 
            FROM [dbo].[tblQuotes] 
            WHERE [QuoteGUID] = @QuoteGuid 
                AND [DateBound] IS NOT NULL
        )
        BEGIN
            -- RAISERROR('The quote is not bound, so it cannot be unbound. QuoteGuid: %s', 16, 1, @QuoteGuid);
            SELECT 0 AS Result, 'The quote is not bound, so it cannot be unbound.' AS Message;
            ROLLBACK TRANSACTION;
            RETURN;
        END

        -- Check if this is the most recent transaction
        IF NOT EXISTS (
            SELECT 1
            FROM [dbo].[tblMaxQuoteIDs]
            WHERE [ControlNo] = @ControlNo
                AND [MaxQuoteID] = @QuoteID
        )
        BEGIN
            -- RAISERROR('The quote does not represent the most recent transaction on this policy.', 16, 1);
            SELECT 0 AS Result, 'The quote does not represent the most recent transaction on this policy.' AS Message;
            ROLLBACK TRANSACTION;
            RETURN;
        END

        -- Determine new quote status based on current status and transaction type
        IF @IsEndorsement = 1
        BEGIN
            IF (
                SELECT TOP (1) [OriginalQuoteStatusID]
                FROM [dbo].[tblQuoteStatusChangeLog]
                WHERE [ControlNo] = @ControlNo
                ORDER BY [ID] DESC
            ) = 8 -- Pending Reinstatement
            BEGIN
                SET @NewQuoteStatus = 8; -- Pending Reinstatement
            END
            ELSE IF @CurrentQuoteStatus = 12 -- Cancelled
            BEGIN
                SET @NewQuoteStatus = 7; -- Pending Cancellation
            END
            ELSE IF @CurrentQuoteStatus = 17 -- Non-Renewed
            BEGIN
                SET @NewQuoteStatus = 26; -- Unbound Non-Renewal
            END
            ELSE IF @CurrentQuoteStatus = 28 -- Non-Renewal Rescinded
            BEGIN
                SET @NewQuoteStatus = 27; -- Unbound Non-Renewal Rescinded
            END
            ELSE
            BEGIN
                SET @NewQuoteStatus = 9; -- Unbound Endorsement
            END
        END
        ELSE
        BEGIN
            SET @NewQuoteStatus = 1; -- Submitted
        END

        -- Log the unbind action
        INSERT INTO [dbo].[tblLog] (
            [UserID],
            [Action],
            [IndentifierGuid]
        )
        VALUES (
            @UserID,
            'Unbound Policy #' + ISNULL(@PolicyNumber, '') + ' - Control #' + CAST(@ControlNo AS VARCHAR) + ' via Triton_UnbindPolicy',
            @QuoteGuid
        );

        -- Process invoice voids
        DECLARE InvoiceCursor CURSOR LOCAL FAST_FORWARD FOR
            SELECT InvoiceNum, PostDate, GLCompanyID, InvoiceTypeID
            FROM [dbo].[tblFin_Invoices] I
            INNER JOIN [dbo].[tblQuotes] Q ON I.QuoteID = Q.QuoteID
            WHERE Q.QuoteGuid = @QuoteGuid AND I.Failed = 0;

        OPEN InvoiceCursor;
        
        FETCH NEXT FROM InvoiceCursor INTO @InvoiceNum, @InvoiceDate, @GLCompanyID, @InvoiceTypeID;
        
        WHILE @@FETCH_STATUS = 0
        BEGIN
            -- Check underwriting period
            IF (dbo.IsUnderwritingPeriodValid_GlCompany(@InvoiceDate, @GLCompanyID) = 0) AND @InvoiceTypeID NOT IN ('PB', 'WP')
            BEGIN
                CLOSE InvoiceCursor;
                DEALLOCATE InvoiceCursor;
                -- RAISERROR('Cannot unbind transaction - invoice billed in a closed underwriting period month.', 16, 55);
                SELECT 0 AS Result, 'Cannot unbind transaction - invoice billed in a closed underwriting period month.' AS Message;
                ROLLBACK TRANSACTION;
                RETURN;
            END

            -- Check accounting period
            IF (dbo.IsAccountingPeriodValid_GlCompany(@InvoiceDate, @GLCompanyID) = 0) AND @InvoiceTypeID NOT IN ('PB', 'WP')
            BEGIN
                CLOSE InvoiceCursor;
                DEALLOCATE InvoiceCursor;
                -- RAISERROR('Cannot unbind transaction - invoice billed in a closed accounting month.', 16, 55);
                SELECT 0 AS Result, 'Cannot unbind transaction - invoice billed in a closed accounting month.' AS Message;
                ROLLBACK TRANSACTION;
                RETURN;
            END

            -- Void the invoice
            EXEC dbo.Greyhawk_spFin_VoidInvoice @InvoiceNum, @UserGuid;
            
            IF @@ERROR > 0
            BEGIN
                CLOSE InvoiceCursor;
                DEALLOCATE InvoiceCursor;
                -- RAISERROR('Error voiding invoice %d', 16, 1, @InvoiceNum);
                SELECT 0 AS Result, 'Error voiding invoice' AS Message;
                ROLLBACK TRANSACTION;
                RETURN;
            END

            FETCH NEXT FROM InvoiceCursor INTO @InvoiceNum, @InvoiceDate, @GLCompanyID, @InvoiceTypeID;
        END

        -- Cleanup cursor
        CLOSE InvoiceCursor;
        DEALLOCATE InvoiceCursor;

        -- Update quote status and clear bound/issued dates
        UPDATE [dbo].[tblQuotes] 
        SET 
            QuoteStatusID = @NewQuoteStatus,
            DateIssued = NULL,
            DateBound = NULL
        WHERE QuoteGuid = @QuoteGuid;

        -- Remove policy number if requested
        IF @KeepPolicyNumbers = 0
        BEGIN
            UPDATE [dbo].[tblQuotes] 
            SET 
                PolicyNumber = NULL,
                PolicyNumberIndex = NULL
            WHERE QuoteGuid = @QuoteGuid;

            -- Clear used policy numbers
            EXEC [dbo].[spPolicyNumberingClearUsedTablePolicyNumber] @QuoteGuid;
        END

        -- Remove affidavit numbers if requested
        IF @KeepAffidavitNumbers = 0
        BEGIN
            DELETE FROM [dbo].[tblQuoteAffidavitNumbers] 
            WHERE QuoteID = @QuoteID;
        END

        -- Update audit trail
        INSERT INTO [dbo].[tblAuditLog] (
            [TableName], 
            [Action], 
            [RecordID], 
            [UserID], 
            [AuditDate], 
            [Details]
        )
        VALUES (
            'tblQuotes',
            'Unbind',
            @QuoteGuid,
            @UserID,
            GETDATE(),
            'Unbind via Triton integration. PolicyNumber: ' + ISNULL(@PolicyNumber, 'NULL') + 
            ', NewStatus: ' + CAST(@NewQuoteStatus AS VARCHAR(3))
        );

        -- Commit transaction
        COMMIT TRANSACTION;

        -- Return success
        SET @ResultStatus = 1;
        
        SELECT 
            @ResultStatus AS Result, 
            'Policy unbound successfully' AS Message,
            @QuoteGuid AS QuoteGuid,
            @PolicyNumber AS PolicyNumber,
            @NewQuoteStatus AS NewQuoteStatusID;

    END TRY
    BEGIN CATCH
        -- Rollback transaction on error
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        SET @ErrorMessage = ERROR_MESSAGE();
        SET @ResultStatus = 0;
        
        -- Log the error
        INSERT INTO [dbo].[tblErrorLog] (
            [ErrorDate],
            [ErrorMessage],
            [ErrorProcedure],
            [ErrorLine],
            [UserID]
        )
        VALUES (
            GETDATE(),
            @ErrorMessage,
            'Triton_UnbindPolicy',
            ERROR_LINE(),
            @UserID
        );

        -- Return error result
        SELECT 
            @ResultStatus AS Result, 
            @ErrorMessage AS Message,
            NULL AS QuoteGuid,
            NULL AS PolicyNumber,
            NULL AS NewQuoteStatusID;
            
        -- Re-throw the error
        THROW;
    END CATCH
END
GO

-- Grant permissions
GRANT EXECUTE ON [dbo].[Triton_UnbindPolicy] TO [TritonWebUser];
GO