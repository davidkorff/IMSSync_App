CREATE OR ALTER PROCEDURE [dbo].[UpdateBOR_WS]
(
    @EndorsementQuoteGuid UNIQUEIDENTIFIER,
    @NewProducerContactGuid UNIQUEIDENTIFIER
)
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Validate inputs
    IF @EndorsementQuoteGuid IS NULL
    BEGIN
        RAISERROR('EndorsementQuoteGuid cannot be null', 16, 1)
        RETURN
    END
    
    IF @NewProducerContactGuid IS NULL
    BEGIN
        RAISERROR('NewProducerContactGuid cannot be null', 16, 1)
        RETURN
    END
    
    -- Validate the quote exists
    IF NOT EXISTS (SELECT 1 FROM tblQuotes WHERE QuoteGuid = @EndorsementQuoteGuid)
    BEGIN
        RAISERROR('Quote not found', 16, 1)
        RETURN
    END
    
    -- Validate the producer contact exists
    IF NOT EXISTS (SELECT 1 FROM tblProducerContacts WHERE ProducerContactGUID = @NewProducerContactGuid)
    BEGIN
        RAISERROR('Producer contact not found', 16, 1)
        RETURN
    END
    
    BEGIN TRY
        BEGIN TRANSACTION
        
        -- First, update the SubmissionGroup's ProducerLocationGuid to match the new producer contact's location
        -- This must be done BEFORE updating the quote to satisfy the ValidContactID trigger
        UPDATE sg
        SET ProducerLocationGuid = pc.ProducerLocationGuid
        FROM tblSubmissionGroup sg
        JOIN tblQuotes q ON q.SubmissionGroupGuid = sg.SubmissionGroupGUID
        JOIN tblProducerContacts pc ON pc.ProducerContactGUID = @NewProducerContactGuid
        WHERE q.QuoteGuid = @EndorsementQuoteGuid
        
        -- Now update the ProducerContactGuid on the endorsement quote
        UPDATE tblQuotes 
        SET ProducerContactGuid = @NewProducerContactGuid
        WHERE QuoteGuid = @EndorsementQuoteGuid
        
        -- Then update all the denormalized producer fields
        -- This pulls from the new contact's location and producer info
        UPDATE q 
        SET 
            q.ProducerName = p.ProducerName, 
            q.ProducerLocationName = mailloc.Name, 
            q.ProducerAddress1 = mailloc.Address1,
            q.ProducerAddress2 = mailloc.Address2, 
            q.ProducerCity = mailloc.City,
            q.ProducerISOCountryCode = mailloc.ISOCountryCode, 
            q.ProducerRegion = mailloc.Region,
            q.ProducerCounty = mailloc.County, 
            q.ProducerState = mailloc.State, 
            q.ProducerZipCode = mailloc.ZipCode,
            q.ProducerZipPlus = mailloc.ZipPlus, 
            q.ProducerPhone = mailloc.Phone,
            q.ProducerFax = COALESCE(pc.Fax, mailloc.Fax),
            -- Billing address fields
            q.ProducerAddress1_Billing = billloc.Address1,
            q.ProducerAddress2_Billing = billloc.Address2, 
            q.ProducerCity_Billing = billloc.City, 
            q.ProducerState_Billing = billloc.State,
            q.ProducerISOCountryCode_Billing = billloc.ISOCountryCode, 
            q.ProducerRegion_Billing = billloc.Region,
            q.ProducerZipCode_Billing = billloc.ZipCode, 
            q.ProducerZipPlus_Billing = billloc.ZipPlus, 
            q.ProducerPhone_Billing = billloc.Phone, 
            q.ProducerFax_Billing = billloc.Fax,
            q.ProducerCounty_Billing = billloc.County
        FROM 
            dbo.tblQuotes q
            -- Get the producer contact info
            JOIN dbo.tblProducerContacts pc ON pc.ProducerContactGUID = @NewProducerContactGuid
            -- Get the producer location from the contact
            JOIN dbo.tblProducerLocations pl ON pl.ProducerLocationGUID = pc.ProducerLocationGuid
            -- Get the producer info
            JOIN dbo.tblProducers p ON p.ProducerGUID = pl.ProducerGUID
            -- Get mailing location
            LEFT JOIN dbo.tblProducerLocations mailloc ON mailloc.ProducerLocationGUID = 
                ISNULL(pl.MailToProducerLocationGuid, pl.ProducerLocationGUID)
            -- Get billing location
            OUTER APPLY (
                SELECT TOP(1) ProducerLocationGUID 
                FROM dbo.tblProducerLocations prodbill 
                WHERE prodbill.ProducerGUID = p.ProducerGUID 
                AND prodbill.LocationTypeID = 2 
                ORDER BY prodbill.StatusID, prodbill.ProducerLocationID
            ) prodbill
            LEFT JOIN dbo.tblProducerLocations billloc ON billloc.ProducerLocationGUID = 
                ISNULL(pl.BillToProducerLocationGuid, prodbill.ProducerLocationGUID)
        WHERE 
            q.QuoteGuid = @EndorsementQuoteGuid
        
        -- The SubmissionGroup update is already done at the beginning of the transaction
        -- No need to update it again
        
        -- Log the BOR change (optional - create audit table if needed)
        IF OBJECT_ID('tblBOR_AuditLog') IS NOT NULL
        BEGIN
            INSERT INTO tblBOR_AuditLog (
                QuoteGuid,
                OldProducerContactGuid,
                NewProducerContactGuid,
                ChangeDate,
                ChangedBy
            )
            SELECT 
                @EndorsementQuoteGuid,
                ProducerContactGuid,
                @NewProducerContactGuid,
                GETDATE(),
                SYSTEM_USER
            FROM tblQuotes 
            WHERE QuoteGuid = @EndorsementQuoteGuid
        END
        
        COMMIT TRANSACTION
        
        -- Return success
        SELECT 
            'Success' as Result,
            @EndorsementQuoteGuid as QuoteGuid,
            @NewProducerContactGuid as NewProducerContactGuid,
            p.ProducerName,
            pc.LName + ', ' + pc.FName as ContactName
        FROM tblProducerContacts pc
        JOIN tblProducerLocations pl ON pl.ProducerLocationGUID = pc.ProducerLocationGuid
        JOIN tblProducers p ON p.ProducerGUID = pl.ProducerGUID
        WHERE pc.ProducerContactGUID = @NewProducerContactGuid
        
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION
            
        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE()
        DECLARE @ErrorSeverity INT = ERROR_SEVERITY()
        DECLARE @ErrorState INT = ERROR_STATE()
        
        RAISERROR(@ErrorMessage, @ErrorSeverity, @ErrorState)
    END CATCH
END
GO