USE [InsuranceStrategiesTest]
GO

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

-- =============================================
-- Author:      Custom Integration
-- Create date: 2025-01-07
-- Description: Web Service wrapper for policy reinstatement
--              Handles status updates and invoice regeneration
-- =============================================
CREATE PROCEDURE [dbo].[ReinstatePolicy_WS]
(
    @ControlNumber INT,
    @ReinstatementDate DATETIME,
    @ReinstatementReasonID INT = NULL,
    @Comments VARCHAR(2000) = NULL,
    @UserGuid UNIQUEIDENTIFIER = NULL,
    @GenerateInvoice BIT = 1,
    @PaymentReceived MONEY = NULL,
    @CheckNumber VARCHAR(100) = NULL
)
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        BEGIN TRANSACTION
        
        -- Variables
        DECLARE @QuoteID INT
        DECLARE @QuoteGuid UNIQUEIDENTIFIER
        DECLARE @CurrentStatusID INT
        DECLARE @CancelledStatusID INT
        DECLARE @BoundStatusID INT
        DECLARE @ReinstateReasonID INT
        DECLARE @PolicyNumber VARCHAR(50)
        DECLARE @CancellationDate DATETIME
        DECLARE @OriginalExpiration DATETIME
        DECLARE @ErrorMessage VARCHAR(4000)
        DECLARE @InvoiceNum INT
        DECLARE @AmountDue MONEY
        
        -- Get status IDs
        SELECT @CancelledStatusID = QuoteStatusID 
        FROM lstQuoteStatus (NOLOCK) 
        WHERE [Description] = 'Cancelled'
        
        SELECT @BoundStatusID = QuoteStatusID 
        FROM lstQuoteStatus (NOLOCK) 
        WHERE [Description] = 'Bound'
        
        -- Get reinstatement reason if not provided
        IF @ReinstatementReasonID IS NULL
        BEGIN
            SELECT @ReinstateReasonID = [ID] 
            FROM lstQuoteStatusReasons (NOLOCK) 
            WHERE AutomationID = 'REINST'
        END
        ELSE
        BEGIN
            SET @ReinstateReasonID = @ReinstatementReasonID
        END
        
        -- Get cancelled policy information
        SELECT TOP 1 
            @QuoteID = q.QuoteID,
            @QuoteGuid = q.QuoteGuid,
            @CurrentStatusID = q.QuoteStatusID,
            @PolicyNumber = q.PolicyNumber,
            @CancellationDate = q.CancellationDate,
            @OriginalExpiration = q.Expiration
        FROM tblQuotes q (NOLOCK)
        WHERE q.ControlNum = @ControlNumber
            AND q.QuoteStatusID = @CancelledStatusID
        ORDER BY q.QuoteID DESC
        
        -- Validate quote exists and is cancelled
        IF @QuoteID IS NULL
        BEGIN
            SET @ErrorMessage = 'No cancelled policy found with control number ' + CAST(@ControlNumber AS VARCHAR(20))
            RAISERROR(@ErrorMessage, 16, 1)
            RETURN
        END
        
        -- Validate reinstatement date
        IF @ReinstatementDate < @CancellationDate
        BEGIN
            SET @ErrorMessage = 'Reinstatement date cannot be before cancellation date'
            RAISERROR(@ErrorMessage, 16, 1)
            RETURN
        END
        
        IF @ReinstatementDate > @OriginalExpiration
        BEGIN
            SET @ErrorMessage = 'Reinstatement date cannot be after original policy expiration date'
            RAISERROR(@ErrorMessage, 16, 1)
            RETURN
        END
        
        -- Get the current bound quote ID (for financial calculations)
        SET @QuoteID = dbo.GetCurrentBoundQuoteId(@QuoteID)
        
        -- Update quote status to bound/reinstated
        UPDATE tblQuotes 
        SET 
            QuoteStatusID = @BoundStatusID,
            QuoteStatusReasonID = @ReinstateReasonID,
            CancellationDate = NULL, -- Clear cancellation date
            ReinstatementDate = @ReinstatementDate,
            LastModified = GETDATE(),
            LastModifiedBy = ISNULL(@UserGuid, LastModifiedBy)
        WHERE QuoteID = @QuoteID
        
        -- Log the reinstatement
        INSERT INTO tblQuoteStatusLog
        (
            QuoteID,
            QuoteStatusID,
            QuoteStatusReasonID,
            StatusDate,
            UserGuid,
            Comments
        )
        VALUES
        (
            @QuoteID,
            @BoundStatusID,
            @ReinstateReasonID,
            GETDATE(),
            @UserGuid,
            @Comments
        )
        
        -- Handle financial reinstatement
        IF @GenerateInvoice = 1
        BEGIN
            -- Calculate amount due for reinstatement period
            DECLARE @DaysLapsed INT
            DECLARE @TotalDays INT
            DECLARE @ProRataFactor DECIMAL(10,6)
            
            SET @DaysLapsed = DATEDIFF(DAY, @CancellationDate, @ReinstatementDate)
            SET @TotalDays = DATEDIFF(DAY, @CancellationDate, @OriginalExpiration)
            
            IF @TotalDays > 0
            BEGIN
                SET @ProRataFactor = CAST(@DaysLapsed AS DECIMAL(10,6)) / CAST(@TotalDays AS DECIMAL(10,6))
            END
            ELSE
            BEGIN
                SET @ProRataFactor = 0
            END
            
            -- Get total premium that was returned
            SELECT @AmountDue = ISNULL(SUM(AmtDue), 0)
            FROM tblFin_ReceivableWorking rw
            INNER JOIN tblFin_Invoices i ON i.InvoiceNum = rw.InvoiceNumber
            WHERE rw.ControlNumber = @ControlNumber
                AND rw.QuoteId = @QuoteID
                AND i.Failed = 0
                AND rw.AmtDue < 0 -- Credits from cancellation
            
            -- Calculate reinstatement amount (portion of returned premium)
            SET @AmountDue = ABS(@AmountDue) * @ProRataFactor
            
            -- Log policy reinstatement for financial tracking
            EXEC dbo.spFin_LogPolicyReinstatement
                @QuoteID = @QuoteID,
                @ReinstatementDate = @ReinstatementDate,
                @AmountDue = @AmountDue,
                @UserGuid = @UserGuid
                
            -- If payment was received, apply it
            IF @PaymentReceived IS NOT NULL AND @PaymentReceived > 0
            BEGIN
                -- This would create payment application records
                -- Implementation depends on client's payment processing
                INSERT INTO tblFin_PaymentLog
                (
                    QuoteID,
                    PaymentAmount,
                    PaymentDate,
                    CheckNumber,
                    PaymentType,
                    UserGuid,
                    Comments
                )
                VALUES
                (
                    @QuoteID,
                    @PaymentReceived,
                    GETDATE(),
                    @CheckNumber,
                    'Reinstatement',
                    @UserGuid,
                    'Reinstatement payment for policy ' + @PolicyNumber
                )
            END
        END
        
        -- Update expiration date if needed (some states require this)
        IF EXISTS (SELECT 1 FROM tblSystemSettings 
                  WHERE Setting = 'UpdateExpirationOnReinstatement' 
                  AND SettingValueBool = 1)
        BEGIN
            EXEC dbo.SetExpDateOnReInstatedPolicy @QuoteID
        END
        
        -- Generate reinstatement documents if automation is configured
        IF EXISTS (SELECT 1 FROM tblDocumentAutomation 
                  WHERE EventName = 'PolicyReinstatement' 
                  AND Active = 1)
        BEGIN
            EXEC dbo.GenerateAutomationDocuments 
                @QuoteGuid = @QuoteGuid,
                @EventName = 'PolicyReinstatement'
        END
        
        COMMIT TRANSACTION
        
        -- Return result
        SELECT 
            @QuoteID AS QuoteID,
            @PolicyNumber AS PolicyNumber,
            @BoundStatusID AS NewStatusID,
            @AmountDue AS ReinstatementAmount,
            @InvoiceNum AS InvoiceNumber,
            'Policy reinstated successfully' AS Message,
            1 AS Success
            
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION
            
        SELECT 
            NULL AS QuoteID,
            NULL AS PolicyNumber,
            NULL AS NewStatusID,
            NULL AS ReinstatementAmount,
            NULL AS InvoiceNumber,
            ERROR_MESSAGE() AS Message,
            0 AS Success
            
        RAISERROR(ERROR_MESSAGE(), 16, 1)
    END CATCH
END
GO