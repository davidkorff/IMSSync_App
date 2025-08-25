USE [IMS_DEV]
GO

/****** Object:  StoredProcedure [dbo].[ryan_rptInvoice_WS]    Script Date: 7/30/2025 2:14:21 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

ALTER PROC [dbo].[ryan_rptInvoice_WS]
    @InvoiceNum INT = NULL,
    @QuoteGuid UNIQUEIDENTIFIER = NULL,
    @PolicyNumber VARCHAR(50) = NULL,
    @OpportunityID VARCHAR(50) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @FinalInvoiceNum INT;
    DECLARE @QuoteID INT;
    DECLARE @IntermediateQuoteGuid UNIQUEIDENTIFIER;
    
    -- Validation: Ensure at least one parameter is provided
    IF @InvoiceNum IS NULL AND @QuoteGuid IS NULL AND @PolicyNumber IS NULL AND @OpportunityID IS NULL
    BEGIN
        RAISERROR('At least one parameter must be provided: @InvoiceNum, @QuoteGuid, @PolicyNumber, or @OpportunityID', 16, 1);
        RETURN;
    END
    
    -- Case 1: InvoiceNum is provided directly - use it
    IF @InvoiceNum IS NOT NULL
    BEGIN
        SET @FinalInvoiceNum = @InvoiceNum;
    END
    
    -- Case 2: QuoteGuid is provided - find InvoiceNum through QuoteID
    ELSE IF @QuoteGuid IS NOT NULL
    BEGIN
        -- Get QuoteID from tblQuotes using QuoteGuid
        SELECT @QuoteID = QuoteID 
        FROM tblQuotes 
        WHERE QuoteGuid = @QuoteGuid;
        
        IF @QuoteID IS NULL
        BEGIN
            RAISERROR('No quote found with the provided QuoteGuid', 16, 1);
            RETURN;
        END
        
        -- Get InvoiceNum from tblFin_Invoices using QuoteID
        SELECT TOP 1 @FinalInvoiceNum = InvoiceNum
        FROM tblFin_Invoices
        WHERE QuoteID = @QuoteID
        ORDER BY InvoiceNum DESC; -- Get the latest invoice if multiple exist
        
        IF @FinalInvoiceNum IS NULL
        BEGIN
            RAISERROR('No invoice found for the provided QuoteGuid', 16, 1);
            RETURN;
        END
    END
    
    -- Case 3: PolicyNumber is provided - find InvoiceNum through QuoteGuid
    ELSE IF @PolicyNumber IS NOT NULL
    BEGIN
        -- Get the latest QuoteGuid from tblTritonQuoteData for this PolicyNumber
        SELECT TOP 1 @IntermediateQuoteGuid = QuoteGuid
        FROM tblTritonQuoteData
        WHERE PolicyNumber = @PolicyNumber
        ORDER BY Created_Date DESC;
        
        IF @IntermediateQuoteGuid IS NULL
        BEGIN
            RAISERROR('No quote data found for the provided PolicyNumber', 16, 1);
            RETURN;
        END
        
        -- Get QuoteID from tblQuotes using the QuoteGuid
        SELECT @QuoteID = QuoteID 
        FROM tblQuotes 
        WHERE QuoteGuid = @IntermediateQuoteGuid;
        
        IF @QuoteID IS NULL
        BEGIN
            RAISERROR('No quote found for the PolicyNumber', 16, 1);
            RETURN;
        END
        
        -- Get InvoiceNum from tblFin_Invoices using QuoteID
        SELECT TOP 1 @FinalInvoiceNum = InvoiceNum
        FROM tblFin_Invoices
        WHERE QuoteID = @QuoteID
        ORDER BY InvoiceNum DESC;
        
        IF @FinalInvoiceNum IS NULL
        BEGIN
            RAISERROR('No invoice found for the provided PolicyNumber', 16, 1);
            RETURN;
        END
    END
    
    -- Case 4: OpportunityID is provided - find InvoiceNum through QuoteGuid
    ELSE IF @OpportunityID IS NOT NULL
    BEGIN
        -- Get the latest QuoteGuid from tblTritonQuoteData for this OpportunityID
        SELECT TOP 1 @IntermediateQuoteGuid = QuoteGuid
        FROM tblTritonQuoteData
        WHERE Opportunity_ID = @OpportunityID
        ORDER BY Created_Date DESC;
        
        IF @IntermediateQuoteGuid IS NULL
        BEGIN
            RAISERROR('No quote data found for the provided OpportunityID', 16, 1);
            RETURN;
        END
        
        -- Get QuoteID from tblQuotes using the QuoteGuid
        SELECT @QuoteID = QuoteID 
        FROM tblQuotes 
        WHERE QuoteGuid = @IntermediateQuoteGuid;
        
        IF @QuoteID IS NULL
        BEGIN
            RAISERROR('No quote found for the OpportunityID', 16, 1);
            RETURN;
        END
        
        -- Get InvoiceNum from tblFin_Invoices using QuoteID
        SELECT TOP 1 @FinalInvoiceNum = InvoiceNum
        FROM tblFin_Invoices
        WHERE QuoteID = @QuoteID
        ORDER BY InvoiceNum DESC;
        
        IF @FinalInvoiceNum IS NULL
        BEGIN
            RAISERROR('No invoice found for the provided OpportunityID', 16, 1);
            RETURN;
        END
    END
    
    -- Execute the original stored procedure with the found InvoiceNum
    EXEC Ryan_rptInvoice @InvoiceNum = @FinalInvoiceNum;
    
END