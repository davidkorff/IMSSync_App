USE [Greyhawk_Test]
GO
/****** Object:  StoredProcedure [dbo].[Greyhawk_spUnbindPolicy]    Script Date: 7/17/2025 10:26:33 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
ALTER PROC [dbo].[Greyhawk_spUnbindPolicy]
(
       @quoteGuid uniqueidentifier,
       @userGuid uniqueidentifier,
       @newQuoteStatusID tinyint,
       @keepPolicyNumber bit,
       @keepExistingAffidavitNumbers bit
)

AS

       IF (@@TRANCOUNT = 0)
              BEGIN
                     RAISERROR('Transaction required when calling spUnbindPolicy',15,1)
                     RETURN
              END
              
       SET NOCOUNT ON
       
       DECLARE @invoiceNum int, @quoteID int, @InvoiceDate smalldatetime, @GLCompanyID int, @InvoiceTypeID varchar(5)
       
       SELECT @quoteID=QuoteID FROM tblQuotes WITH (NOLOCK) WHERE QuoteGuid=@quoteGuid
       

       -- Loop through all the invoices that need to be voided
       DECLARE InvoiceCursor CURSOR LOCAL FAST_FORWARD FOR
              SELECT InvoiceNum, PostDate, GLCompanyID, InvoiceTypeID
              FROM tblFin_Invoices I
              INNER JOIN tblQuotes Q ON I.QuoteID=Q.QuoteID
              WHERE Q.QuoteGuid=@quoteGuid AND I.Failed=0
       
       OPEN InvoiceCursor
       
       FETCH NEXT FROM InvoiceCursor INTO @invoiceNum, @InvoiceDate, @GLCompanyID, @InvoiceTypeID
       
       WHILE @@FETCH_STATUS = 0
              BEGIN
              
                     --TFS 40350. Underwriting date takes precedence here
                     IF (dbo.IsUnderwritingPeriodValid_GlCompany(@InvoiceDate, @GLCompanyID) = 0) AND @InvoiceTypeID NOT IN ('PB', 'WP')
                           BEGIN
                                  CLOSE InvoiceCursor
                                  DEALLOCATE InvoiceCursor
                                  RAISERROR('Cannot unbind transaction - invoice billed in a closed underwriting period month.',15,55)
                           END

                     -- IMS05494
                     -- Unbinding - Block if billing being voided was billed in a closed Accounting Month
                     -- janderson 1-22-2013: but allow if invoice is purchase book
                     IF (dbo.IsAccountingPeriodValid_GlCompany(@InvoiceDate, @GLCompanyID) = 0) AND @InvoiceTypeID NOT IN ('PB', 'WP')
                            BEGIN
                                  CLOSE InvoiceCursor
                                  DEALLOCATE InvoiceCursor
                                  RAISERROR('Can not unbind the transaction - invoice billed in a closed accounting month.',15,55)
                           END

              
                     EXEC dbo.Greyhawk_spFin_VoidInvoice @invoiceNum, @userGuid
                     
                     IF @@ERROR > 0
                          BEGIN
                                  CLOSE InvoiceCursor
                                  DEALLOCATE InvoiceCursor
                                  RETURN
                           END
              
                     FETCH NEXT FROM InvoiceCursor INTO @invoiceNum, @InvoiceDate, @GLCompanyID, @InvoiceTypeID
              END
       
       -- Cleanup the cursor      
       CLOSE InvoiceCursor
       DEALLOCATE InvoiceCursor                 

       -- Mark any options as unbound    
       --UPDATE tblQuoteOptions SET Bound=0 WHERE QuoteGuid=@quoteGuid
       
       -- Update the quote status
       UPDATE tblQuotes SET QuoteStatusID=@newQuoteStatusID, DateIssued = NULL,DateBound = NULL WHERE QuoteGuid=@quoteGuid
       
       
       -- Remove the policy number
       IF (@keepPolicyNumber = 0)
              UPDATE tblQuotes SET PolicyNumber=null, PolicyNumberIndex=null WHERE QuoteGuid = @quoteGuid
              
       IF (@keepExistingAffidavitNumbers = 0)
              DELETE FROM tblQuoteAffidavitNumbers WHERE QuoteID = @quoteID

       RETURN


