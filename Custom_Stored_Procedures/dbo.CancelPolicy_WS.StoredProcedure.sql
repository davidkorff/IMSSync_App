USE [InsuranceStrategiesTest]
GO

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

-- =============================================
-- Author:      Custom Integration
-- Create date: 2025-01-07
-- Description: Web Service wrapper for policy cancellation
--              Handles status updates and invoice processing
-- =============================================
CREATE PROCEDURE [dbo].[CancelPolicy_WS]
(
    @ControlNumber INT,
    @CancellationDate DATETIME,
    @CancellationReasonID INT,
    @Comments VARCHAR(2000) = NULL,
    @UserGuid UNIQUEIDENTIFIER = NULL,
    @ReturnPremium BIT = 1, -- Whether to calculate return premium
    @FlatCancel BIT = 0     -- If 1, no return premium calculated
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
        DECLARE @PolicyNumber VARCHAR(50)
        DECLARE @TransactNum INT
        DECLARE @ErrorMessage VARCHAR(4000)
        
        -- Get status IDs
        SELECT @CancelledStatusID = QuoteStatusID 
        FROM lstQuoteStatus (NOLOCK) 
        WHERE [Description] = 'Cancelled'
        
        SELECT @BoundStatusID = QuoteStatusID 
        FROM lstQuoteStatus (NOLOCK) 
        WHERE [Description] = 'Bound'
        
        -- Get current quote information
        SELECT TOP 1 
            @QuoteID = q.QuoteID,
            @QuoteGuid = q.QuoteGuid,
            @CurrentStatusID = q.QuoteStatusID,
            @PolicyNumber = q.PolicyNumber
        FROM tblQuotes q (NOLOCK)
        WHERE q.ControlNum = @ControlNumber
            AND q.QuoteStatusID = @BoundStatusID
        ORDER BY q.QuoteID DESC
        
        -- Validate quote exists and is bound
        IF @QuoteID IS NULL
        BEGIN
            SET @ErrorMessage = 'No bound policy found with control number ' + CAST(@ControlNumber AS VARCHAR(20))
            RAISERROR(@ErrorMessage, 16, 1)
            RETURN
        END
        
        -- Validate cancellation date
        DECLARE @EffectiveDate DATETIME, @ExpirationDate DATETIME
        SELECT 
            @EffectiveDate = Effective,
            @ExpirationDate = Expiration
        FROM tblQuotes (NOLOCK)
        WHERE QuoteID = @QuoteID
        
        IF @CancellationDate < @EffectiveDate
        BEGIN
            SET @ErrorMessage = 'Cancellation date cannot be before policy effective date'
            RAISERROR(@ErrorMessage, 16, 1)
            RETURN
        END
        
        IF @CancellationDate > @ExpirationDate
        BEGIN
            SET @ErrorMessage = 'Cancellation date cannot be after policy expiration date'
            RAISERROR(@ErrorMessage, 16, 1)
            RETURN
        END
        
        -- Update quote status to cancelled
        UPDATE tblQuotes 
        SET 
            QuoteStatusID = @CancelledStatusID,
            QuoteStatusReasonID = @CancellationReasonID,
            CancellationDate = @CancellationDate,
            LastModified = GETDATE(),
            LastModifiedBy = ISNULL(@UserGuid, LastModifiedBy)
        WHERE QuoteID = @QuoteID
        
        -- Log the cancellation
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
            @CancelledStatusID,
            @CancellationReasonID,
            GETDATE(),
            @UserGuid,
            @Comments
        )
        
        -- Handle financial transactions if not flat cancel
        IF @FlatCancel = 0 AND @ReturnPremium = 1
        BEGIN
            -- Check if financial module is enabled
            IF EXISTS (SELECT 1 FROM tblSystemSettings 
                      WHERE Setting IN ('PolicyCancelWashFlat', 'PolicyCancelWashAll') 
                      AND SettingValueBool = 1)
            BEGIN
                -- Call the internal cancellation procedure
                EXEC dbo.spFin_CancelPolicy 
                    @ControlNumber = @ControlNumber,
                    @Comments = @Comments,
                    @PostDate = @CancellationDate,
                    @UserGuid = @UserGuid,
                    @CheckNumber = NULL
                    
                SET @TransactNum = @@IDENTITY
            END
        END
        
        -- Generate cancellation documents if automation is configured
        IF EXISTS (SELECT 1 FROM tblDocumentAutomation 
                  WHERE EventName = 'PolicyCancellation' 
                  AND Active = 1)
        BEGIN
            -- This would trigger document generation
            -- Implementation depends on client's document automation setup
            EXEC dbo.GenerateAutomationDocuments 
                @QuoteGuid = @QuoteGuid,
                @EventName = 'PolicyCancellation'
        END
        
        COMMIT TRANSACTION
        
        -- Return result
        SELECT 
            @QuoteID AS QuoteID,
            @PolicyNumber AS PolicyNumber,
            @CancelledStatusID AS NewStatusID,
            @TransactNum AS TransactionNumber,
            'Policy cancelled successfully' AS Message,
            1 AS Success
            
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION
            
        SELECT 
            NULL AS QuoteID,
            NULL AS PolicyNumber,
            NULL AS NewStatusID,
            NULL AS TransactionNumber,
            ERROR_MESSAGE() AS Message,
            0 AS Success
            
        RAISERROR(ERROR_MESSAGE(), 16, 1)
    END CATCH
END
GO