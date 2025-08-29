CREATE OR ALTER   PROCEDURE [dbo].[spGetPolicyPremiumTotal_WS]
    @ControlNo INT
AS
BEGIN
    SET NOCOUNT ON;
   
    -- Calculate total premium from all invoices for this policy
    SELECT
        @ControlNo as ControlNo,
        ISNULL(SUM(AnnualPremium), 0) as TotalPremium,
        COUNT(*) as InvoiceCount,
        MIN(InvoiceDate) as FirstInvoiceDate,
        MAX(InvoiceDate) as LastInvoiceDate,
        'Success' as Status
    FROM tblFin_Invoices
    WHERE QuoteControlNum = @ControlNo
    GROUP BY QuoteControlNum
   
    UNION ALL
   
    -- Return zero if no invoices found
    SELECT
        @ControlNo as ControlNo,
        0 as TotalPremium,
        0 as InvoiceCount,
        NULL as FirstInvoiceDate,
        NULL as LastInvoiceDate,
        'No invoices found' as Status
    WHERE NOT EXISTS (
        SELECT 1
        FROM tblFin_Invoices
        WHERE QuoteControlNum = @ControlNo
    );
   
END






