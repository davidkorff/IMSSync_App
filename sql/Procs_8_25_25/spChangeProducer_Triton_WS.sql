USE [OneIMS]
GO

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

-- =============================================
-- Author:      Triton Integration
-- Create Date: 2025-08-28
-- Description: Change the producer for a quote during midterm endorsements
--              Called directly from data access service, so needs _WS suffix
-- =============================================

IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[spChangeProducer_Triton_WS]') AND type in (N'P', N'PC'))
    DROP PROCEDURE [dbo].[spChangeProducer_Triton_WS]
GO

CREATE PROCEDURE [dbo].[spChangeProducer_Triton_WS]
    @QuoteGuid uniqueidentifier,
    @NewProducerContactGuid uniqueidentifier
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @ErrorMessage NVARCHAR(4000);
    DECLARE @ErrorSeverity INT;
    DECLARE @ErrorState INT;
    DECLARE @OldProducerContactGuid uniqueidentifier;
    
    BEGIN TRY
        -- Validate that the quote exists
        IF NOT EXISTS (SELECT 1 FROM tblQuotes WHERE QuoteGuid = @QuoteGuid)
        BEGIN
            RAISERROR('Quote not found with QuoteGuid: %s', 16, 1, @QuoteGuid);
            RETURN;
        END
        
        -- Validate that the new producer exists
        IF NOT EXISTS (SELECT 1 FROM tblProducerContacts WHERE ProducerContactGuid = @NewProducerContactGuid)
        BEGIN
            RAISERROR('Producer contact not found with ProducerContactGuid: %s', 16, 1, @NewProducerContactGuid);
            RETURN;
        END
        
        BEGIN TRANSACTION
        
        -- Get the current producer before change
        SELECT @OldProducerContactGuid = ProducerContactGuid
        FROM tblQuotes 
        WHERE QuoteGuid = @QuoteGuid;
        
        -- Update the producer for the quote
        UPDATE tblQuotes
        SET ProducerContactGuid = @NewProducerContactGuid,
            ModifiedDate = GETDATE()
        WHERE QuoteGuid = @QuoteGuid;
        
        -- Also update the producer location if we can determine it from the contact
        DECLARE @NewProducerLocationGuid uniqueidentifier;
        SELECT TOP 1 @NewProducerLocationGuid = pl.ProducerLocationGuid
        FROM tblProducerLocations pl
        INNER JOIN tblProducerContacts pc ON pl.ProducerGuid = pc.ProducerGuid
        WHERE pc.ProducerContactGuid = @NewProducerContactGuid
        ORDER BY pl.IsPrimary DESC, pl.CreatedDate DESC;
        
        IF @NewProducerLocationGuid IS NOT NULL
        BEGIN
            UPDATE tblQuotes
            SET ProducerLocationGuid = @NewProducerLocationGuid
            WHERE QuoteGuid = @QuoteGuid;
        END
        
        -- Update the SubmissionGroup's ProducerLocationGuid if needed
        UPDATE sg
        SET ProducerLocationGuid = @NewProducerLocationGuid
        FROM tblSubmissionGroup sg
        INNER JOIN tblQuotes q ON q.SubmissionGroupGuid = sg.SubmissionGroupGUID
        WHERE q.QuoteGuid = @QuoteGuid
        AND @NewProducerLocationGuid IS NOT NULL;
        
        -- Log the change in an audit table if it exists
        IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[tblProducerChangeAudit]') AND type in (N'U'))
        BEGIN
            INSERT INTO tblProducerChangeAudit (
                QuoteGuid,
                OldProducerContactGuid,
                NewProducerContactGuid,
                ChangeDate,
                ChangedBy
            )
            VALUES (
                @QuoteGuid,
                @OldProducerContactGuid,
                @NewProducerContactGuid,
                GETDATE(),
                'Triton Integration - Midterm Endorsement'
            );
        END
        
        COMMIT TRANSACTION
        
        -- Return success indicator
        SELECT 
            @QuoteGuid as QuoteGuid,
            @OldProducerContactGuid as OldProducerContactGuid,
            @NewProducerContactGuid as NewProducerContactGuid,
            @NewProducerLocationGuid as NewProducerLocationGuid,
            'Success' as Status,
            'Producer changed successfully' as Message;
        
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION
            
        SELECT 
            @ErrorMessage = ERROR_MESSAGE(),
            @ErrorSeverity = ERROR_SEVERITY(),
            @ErrorState = ERROR_STATE();
        
        -- Return error information
        SELECT 
            @QuoteGuid as QuoteGuid,
            NULL as OldProducerContactGuid,
            @NewProducerContactGuid as NewProducerContactGuid,
            NULL as NewProducerLocationGuid,
            'Error' as Status,
            @ErrorMessage as Message;
        
        -- Re-raise the error
        RAISERROR(@ErrorMessage, @ErrorSeverity, @ErrorState);
    END CATCH
END
GO