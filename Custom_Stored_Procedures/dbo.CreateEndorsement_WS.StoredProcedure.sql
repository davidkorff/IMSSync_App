USE [InsuranceStrategiesTest]
GO

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

-- =============================================
-- Author:      Custom Integration
-- Create date: 2025-01-07
-- Description: Web Service wrapper for creating policy endorsements
--              Creates new quote as endorsement and handles premium calculations
-- =============================================
CREATE PROCEDURE [dbo].[CreateEndorsement_WS]
(
    @ControlNumber INT,
    @EndorsementEffectiveDate DATETIME,
    @EndorsementComment VARCHAR(250),
    @EndorsementReasonID INT,
    @UserGuid UNIQUEIDENTIFIER,
    @CalculationType CHAR(1) = 'P', -- P=Pro-rata, S=Short-rate, F=Flat
    @CopyExposures BIT = 1,
    @CopyPremiums BIT = 0
)
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        BEGIN TRANSACTION
        
        -- Variables
        DECLARE @OriginalQuoteID INT
        DECLARE @OriginalQuoteGuid UNIQUEIDENTIFIER
        DECLARE @NewQuoteID INT
        DECLARE @NewQuoteGuid UNIQUEIDENTIFIER
        DECLARE @SubmissionGroupGuid UNIQUEIDENTIFIER
        DECLARE @PolicyNumber VARCHAR(50)
        DECLARE @CurrentStatusID INT
        DECLARE @BoundStatusID INT
        DECLARE @SubmittedStatusID INT
        DECLARE @EndorsementNumber INT
        DECLARE @ErrorMessage VARCHAR(4000)
        DECLARE @EffectiveDate DATETIME
        DECLARE @ExpirationDate DATETIME
        DECLARE @ProRataFactor DECIMAL(10,6)
        
        -- Get status IDs
        SELECT @BoundStatusID = QuoteStatusID 
        FROM lstQuoteStatus (NOLOCK) 
        WHERE [Description] = 'Bound'
        
        SELECT @SubmittedStatusID = QuoteStatusID 
        FROM lstQuoteStatus (NOLOCK) 
        WHERE [Description] = 'Submitted'
        
        -- Get current bound policy
        SELECT TOP 1 
            @OriginalQuoteID = q.QuoteID,
            @OriginalQuoteGuid = q.QuoteGuid,
            @CurrentStatusID = q.QuoteStatusID,
            @PolicyNumber = q.PolicyNumber,
            @SubmissionGroupGuid = q.SubmissionGroupGuid,
            @EffectiveDate = q.Effective,
            @ExpirationDate = q.Expiration
        FROM tblQuotes q (NOLOCK)
        WHERE q.ControlNum = @ControlNumber
            AND q.QuoteStatusID = @BoundStatusID
            AND q.IsEndorsement = 0
        ORDER BY q.QuoteID DESC
        
        -- Validate quote exists and is bound
        IF @OriginalQuoteID IS NULL
        BEGIN
            SET @ErrorMessage = 'No bound policy found with control number ' + CAST(@ControlNumber AS VARCHAR(20))
            RAISERROR(@ErrorMessage, 16, 1)
            RETURN
        END
        
        -- Validate endorsement date
        EXEC dbo.spValidateEndorsementEffectiveDate
            @QuoteID = @OriginalQuoteID,
            @EndorsementEffective = @EndorsementEffectiveDate
            
        IF @@ERROR <> 0
        BEGIN
            RAISERROR('Invalid endorsement effective date', 16, 1)
            RETURN
        END
        
        -- Get next endorsement number
        SELECT @EndorsementNumber = ISNULL(MAX(EndorsementNumber), 0) + 1
        FROM tblQuotes (NOLOCK)
        WHERE ControlNum = @ControlNumber
            AND IsEndorsement = 1
        
        -- Create new quote as endorsement
        SET @NewQuoteGuid = NEWID()
        
        -- Copy quote with endorsement flag
        EXEC dbo.spCopyQuote
            @QuoteID = @OriginalQuoteID,
            @NewQuoteGuid = @NewQuoteGuid OUTPUT,
            @UserGuid = @UserGuid,
            @CopyOptions = 1,
            @CopyExposures = @CopyExposures,
            @CopyPremiums = @CopyPremiums
            
        -- Get the new quote ID
        SELECT @NewQuoteID = QuoteID
        FROM tblQuotes (NOLOCK)
        WHERE QuoteGuid = @NewQuoteGuid
        
        -- Update new quote with endorsement information
        UPDATE tblQuotes
        SET
            IsEndorsement = 1,
            EndorsementNumber = @EndorsementNumber,
            EndorsementEffective = @EndorsementEffectiveDate,
            EndorsementComment = @EndorsementComment,
            EndorsementCalculationType = @CalculationType,
            QuoteStatusID = @SubmittedStatusID,
            QuoteStatusReasonID = @EndorsementReasonID,
            ParentQuoteID = @OriginalQuoteID,
            Effective = @EndorsementEffectiveDate, -- Endorsement takes effect on this date
            LastModified = GETDATE(),
            LastModifiedBy = @UserGuid
        WHERE QuoteID = @NewQuoteID
        
        -- Calculate pro-rata factor if needed
        IF @CalculationType = 'P'
        BEGIN
            EXEC dbo.ProRata
                @effective = @EffectiveDate,
                @expiration = @ExpirationDate,
                @endorsementDate = @EndorsementEffectiveDate,
                @ProRataResult = @ProRataFactor OUTPUT
        END
        
        -- Copy all related data
        IF @CopyExposures = 1
        BEGIN
            -- Copy underwriting locations
            EXEC dbo.spCopyUnderwritingLocations
                @SourceQuoteID = @OriginalQuoteID,
                @DestQuoteID = @NewQuoteID
                
            -- Copy additional interests
            EXEC dbo.CopyAdditionalInterests
                @SourceQuoteID = @OriginalQuoteID,
                @DestQuoteID = @NewQuoteID
                
            -- Copy forms, conditions, warranties
            EXEC dbo.CopyFormsConditionsWarranties
                @SourceQuoteID = @OriginalQuoteID,
                @DestQuoteID = @NewQuoteID
        END
        
        -- Update endorsement information
        EXEC dbo.ChangeEndorsementInformation
            @quoteID = @NewQuoteID,
            @endorsementEffective = @EndorsementEffectiveDate,
            @endorsementComment = @EndorsementComment,
            @endorsementCalculationType = @CalculationType,
            @quoteStatusReasonID = @EndorsementReasonID
            
        -- Log the endorsement creation
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
            @NewQuoteID,
            @SubmittedStatusID,
            @EndorsementReasonID,
            GETDATE(),
            @UserGuid,
            'Endorsement created: ' + @EndorsementComment
        )
        
        -- Auto-create quote options if configured
        IF EXISTS (SELECT 1 FROM tblSystemSettings 
                  WHERE Setting = 'AutoCreateEndorsementOptions' 
                  AND SettingValueBool = 1)
        BEGIN
            EXEC dbo.AutoAddQuoteOptions @NewQuoteGuid
        END
        
        -- Generate endorsement documents if automation is configured
        IF EXISTS (SELECT 1 FROM tblDocumentAutomation 
                  WHERE EventName = 'EndorsementCreated' 
                  AND Active = 1)
        BEGIN
            EXEC dbo.GenerateAutomationDocuments 
                @QuoteGuid = @NewQuoteGuid,
                @EventName = 'EndorsementCreated'
        END
        
        COMMIT TRANSACTION
        
        -- Return result
        SELECT 
            @NewQuoteID AS EndorsementQuoteID,
            @NewQuoteGuid AS EndorsementQuoteGuid,
            @PolicyNumber AS PolicyNumber,
            @EndorsementNumber AS EndorsementNumber,
            @ProRataFactor AS ProRataFactor,
            'Endorsement created successfully' AS Message,
            1 AS Success
            
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION
            
        SELECT 
            NULL AS EndorsementQuoteID,
            NULL AS EndorsementQuoteGuid,
            NULL AS PolicyNumber,
            NULL AS EndorsementNumber,
            NULL AS ProRataFactor,
            ERROR_MESSAGE() AS Message,
            0 AS Success
            
        RAISERROR(ERROR_MESSAGE(), 16, 1)
    END CATCH
END
GO