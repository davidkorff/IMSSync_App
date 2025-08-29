CREATE OR ALTER PROCEDURE [dbo].[spChangeProducer_Triton]
(
    @QuoteGuid UNIQUEIDENTIFIER,
    @NewProducerContactGuid UNIQUEIDENTIFIER
)
AS
BEGIN
    SET NOCOUNT ON;
    SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
    
    -- Validate inputs
    IF @QuoteGuid IS NULL
    BEGIN
        RAISERROR('QuoteGuid cannot be null', 16, 1)
        RETURN
    END
    
    IF @NewProducerContactGuid IS NULL
    BEGIN
        RAISERROR('NewProducerContactGuid cannot be null', 16, 1)
        RETURN
    END
    
    -- Check if quote exists
    IF NOT EXISTS (SELECT 1 FROM tblQuotes WHERE QuoteGuid = @QuoteGuid)
    BEGIN
        RAISERROR('Quote not found', 16, 1)
        RETURN
    END
    
    -- Check if quote is bound
    IF dbo.IsQuoteBound(@QuoteGuid) = 1
    BEGIN
        RAISERROR('Cannot change producer on a bound quote', 16, 1)
        RETURN
    END
    
    -- Validate producer contact exists
    IF NOT EXISTS (SELECT 1 FROM tblProducerContacts WHERE ProducerContactGUID = @NewProducerContactGuid)
    BEGIN
        RAISERROR('Producer contact not found', 16, 1)
        RETURN
    END
    
    -- Declare variables
    DECLARE 
        @SubmissionGroupGuid UNIQUEIDENTIFIER,
        @ControlNo INT,
        @NewProducerLocationGuid UNIQUEIDENTIFIER,
        @NewProducerContactID INT,
        @NewProducerLocationID INT,
        @OldProducerContactGuid UNIQUEIDENTIFIER
    
    -- Get current quote info
    SELECT 
        @SubmissionGroupGuid = q.SubmissionGroupGuid,
        @ControlNo = q.ControlNo,
        @OldProducerContactGuid = q.ProducerContactGuid
    FROM tblQuotes q
    WHERE q.QuoteGuid = @QuoteGuid
    
    -- Get new producer info
    SELECT 
        @NewProducerContactID = pc.ProducerContactID,
        @NewProducerLocationGuid = pc.ProducerLocationGuid,
        @NewProducerLocationID = pl.ProducerLocationID
    FROM tblProducerContacts pc
    JOIN tblProducerLocations pl ON pl.ProducerLocationGUID = pc.ProducerLocationGuid
    WHERE pc.ProducerContactGUID = @NewProducerContactGuid
    
    IF @NewProducerLocationGuid IS NULL
    BEGIN
        RAISERROR('Producer location not found for the contact', 16, 1)
        RETURN
    END
    
    -- Declare transaction count variable before TRY block
    DECLARE @TranCount INT = @@TRANCOUNT
    
    BEGIN TRY
        -- Start transaction if not already in one
        IF @TranCount = 0
            BEGIN TRANSACTION
        
        -- Step 1: Update SubmissionGroup with new producer location and contact
        -- This must be done FIRST to maintain referential integrity
        UPDATE sg
        SET 
            ProducerLocationGuid = @NewProducerLocationGuid,
            ProducerContactID = @NewProducerContactID
        FROM tblSubmissionGroup sg
        WHERE sg.SubmissionGroupGUID = @SubmissionGroupGuid
        
        -- Step 2: Update all quotes in the control stack
        -- Set ProducerAddress1 = NULL to trigger the CopyHistoricalInfo trigger
        UPDATE q
        SET 
            ProducerContactGuid = @NewProducerContactGuid,
            ProducerLocationID = @NewProducerLocationID,
            -- Clear secondary producer if from different location
            SecProducerContactGuid = CASE 
                WHEN secpc.ProducerLocationGUID = @NewProducerLocationGuid 
                THEN q.SecProducerContactGuid 
                ELSE NULL 
            END,
            -- Set to NULL to trigger producer info refresh
            ProducerAddress1 = NULL
        FROM tblQuotes q
        CROSS APPLY (
            SELECT mq.ControlNo 
            FROM tblMaxQuoteIDs mq 
            WHERE mq.MaxQuoteID = q.QuoteID
        ) mq
        LEFT JOIN tblProducerContacts secpc 
            ON q.SecProducerContactGuid = secpc.ProducerContactGUID
        WHERE q.SubmissionGroupGuid = @SubmissionGroupGuid
            AND mq.ControlNo = @ControlNo
        
        -- Step 3: Force update of producer info if trigger didn't fire
        -- This ensures all denormalized fields are updated
        UPDATE q
        SET 
            q.ProducerName = p.ProducerName,
            q.ProducerLocationName = ISNULL(mailloc.Name, pl.Name),
            q.ProducerAddress1 = ISNULL(mailloc.Address1, pl.Address1),
            q.ProducerAddress2 = ISNULL(mailloc.Address2, pl.Address2),
            q.ProducerCity = ISNULL(mailloc.City, pl.City),
            q.ProducerState = ISNULL(mailloc.State, pl.State),
            q.ProducerZipCode = ISNULL(mailloc.ZipCode, pl.ZipCode),
            q.ProducerZipPlus = ISNULL(mailloc.ZipPlus, pl.ZipPlus),
            q.ProducerPhone = ISNULL(mailloc.Phone, pl.Phone),
            q.ProducerFax = COALESCE(pc.Fax, mailloc.Fax, pl.Fax),
            q.ProducerCounty = ISNULL(mailloc.County, pl.County),
            q.ProducerISOCountryCode = ISNULL(mailloc.ISOCountryCode, pl.ISOCountryCode),
            q.ProducerRegion = ISNULL(mailloc.Region, pl.Region),
            -- Billing address
            q.ProducerAddress1_Billing = ISNULL(billloc.Address1, pl.Address1),
            q.ProducerAddress2_Billing = ISNULL(billloc.Address2, pl.Address2),
            q.ProducerCity_Billing = ISNULL(billloc.City, pl.City),
            q.ProducerState_Billing = ISNULL(billloc.State, pl.State),
            q.ProducerZipCode_Billing = ISNULL(billloc.ZipCode, pl.ZipCode),
            q.ProducerZipPlus_Billing = ISNULL(billloc.ZipPlus, pl.ZipPlus),
            q.ProducerPhone_Billing = ISNULL(billloc.Phone, pl.Phone),
            q.ProducerFax_Billing = ISNULL(billloc.Fax, pl.Fax),
            q.ProducerCounty_Billing = ISNULL(billloc.County, pl.County),
            q.ProducerISOCountryCode_Billing = ISNULL(billloc.ISOCountryCode, pl.ISOCountryCode),
            q.ProducerRegion_Billing = ISNULL(billloc.Region, pl.Region)
        FROM tblQuotes q
        JOIN tblProducerContacts pc ON pc.ProducerContactGUID = @NewProducerContactGuid
        JOIN tblProducerLocations pl ON pl.ProducerLocationGUID = pc.ProducerLocationGuid
        JOIN tblProducers p ON p.ProducerGUID = pl.ProducerGUID
        -- Mailing location
        LEFT JOIN tblProducerLocations mailloc 
            ON mailloc.ProducerLocationGUID = ISNULL(pl.MailToProducerLocationGuid, pl.ProducerLocationGUID)
        -- Billing location
        OUTER APPLY (
            SELECT TOP(1) ProducerLocationGUID 
            FROM tblProducerLocations prodbill 
            WHERE prodbill.ProducerGUID = p.ProducerGUID 
                AND prodbill.LocationTypeID = 2  -- Billing location type
            ORDER BY prodbill.StatusID, prodbill.ProducerLocationID
        ) prodbill
        LEFT JOIN tblProducerLocations billloc 
            ON billloc.ProducerLocationGUID = ISNULL(pl.BillToProducerLocationGuid, prodbill.ProducerLocationGUID)
        WHERE q.QuoteGuid = @QuoteGuid
        
        -- Step 4: Update commissions if AutoUpdateQuoteDetails exists
        IF EXISTS (SELECT 1 FROM sys.objects WHERE name = 'AutoUpdateQuoteDetails' AND type = 'P')
        BEGIN
            EXEC dbo.AutoUpdateQuoteDetails
                @quoteGuid = @QuoteGuid,
                @recalcCommissions = 1
        END
        
        -- Step 5: Log the change for audit purposes (if audit table exists)
        -- Commented out since tblNotes doesn't exist
        -- You can create your own audit table or use existing logging mechanism
        
        -- Commit if we started the transaction
        IF @TranCount = 0
            COMMIT TRANSACTION
        
        -- Return success with producer info
        SELECT 
            'Success' as Result,
            @QuoteGuid as QuoteGuid,
            @NewProducerContactGuid as NewProducerContactGuid,
            p.ProducerName,
            pl.Name as ProducerLocationName,
            pc.LName + ', ' + pc.FName as ContactName,
            q.ControlNo,
            q.PolicyNumber,
            'BOR change completed successfully' as Message
        FROM tblQuotes q
        JOIN tblProducerContacts pc ON pc.ProducerContactGUID = q.ProducerContactGuid
        JOIN tblProducerLocations pl ON pl.ProducerLocationGUID = pc.ProducerLocationGuid
        JOIN tblProducers p ON p.ProducerGUID = pl.ProducerGUID
        WHERE q.QuoteGuid = @QuoteGuid
        
    END TRY
    BEGIN CATCH
        -- Rollback if we started the transaction
        IF @TranCount = 0 AND @@TRANCOUNT > 0
            ROLLBACK TRANSACTION
        
        DECLARE @ErrorMessage NVARCHAR(4000) = ERROR_MESSAGE()
        DECLARE @ErrorSeverity INT = ERROR_SEVERITY()
        DECLARE @ErrorState INT = ERROR_STATE()
        DECLARE @ErrorLine INT = ERROR_LINE()
        DECLARE @ErrorProc NVARCHAR(128) = ERROR_PROCEDURE()
        
        -- Build detailed error message
        SET @ErrorMessage = 'Error in ' + ISNULL(@ErrorProc, 'spChangeProducer_Triton') + 
                           ' at line ' + CAST(@ErrorLine AS VARCHAR(10)) + ': ' + @ErrorMessage
        
        RAISERROR(@ErrorMessage, @ErrorSeverity, @ErrorState)
    END CATCH
END
GO

/*
-- Usage:
EXEC spChangeProducer_Triton 
    @QuoteGuid = 'DD845045-DC49-488C-8FC3-7303D5FE942E',
    @NewProducerContactGuid = '42C38BD7-1277-48E8-AEC0-BD4403C77BD9'
*/