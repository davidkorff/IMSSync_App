-- PSEUDO-CODE for IMS Stored Procedure: GetLatestInvoiceByPolicy_WS
-- This stored procedure would need to be created in the IMS database
-- to support the invoice data retrieval endpoint

CREATE PROCEDURE GetLatestInvoiceByPolicy_WS
    @PolicyNumber NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Get the latest invoice for the policy
    DECLARE @InvoiceID INT;
    DECLARE @PolicyID INT;
    
    -- Get Policy ID from Policy Number
    SELECT @PolicyID = PolicyID 
    FROM Policies 
    WHERE PolicyNumber = @PolicyNumber;
    
    -- Get the latest invoice ID for this policy
    SELECT TOP 1 @InvoiceID = InvoiceID
    FROM Invoices
    WHERE PolicyID = @PolicyID
      AND InvoiceStatus = 'Active'  -- Only active invoices
    ORDER BY InvoiceDate DESC;
    
    -- Return multiple result sets for the DataSet
    
    -- Result Set 1: InvoiceHeader
    SELECT 
        i.InvoiceNumber,
        i.InvoiceDate,
        i.DueDate,
        i.TotalAmount,
        i.Subtotal,
        i.TaxTotal,
        i.Status,
        i.InvoiceID
    FROM Invoices i
    WHERE i.InvoiceID = @InvoiceID;
    
    -- Result Set 2: InvoiceLineItems
    SELECT 
        ili.Description,
        ili.Amount,
        ili.Quantity,
        ili.UnitPrice,
        ili.TaxRate,
        ili.TaxAmount,
        ili.LineItemOrder
    FROM InvoiceLineItems ili
    WHERE ili.InvoiceID = @InvoiceID
    ORDER BY ili.LineItemOrder;
    
    -- Result Set 3: PolicyInfo
    SELECT 
        p.PolicyNumber,
        q.QuoteNumber,
        p.EffectiveDate,
        p.ExpirationDate,
        l.LineName AS CoverageType,
        c.CompanyName AS CarrierName,
        p.LimitPerOccurrence,
        p.LimitAggregate,
        p.Deductible
    FROM Policies p
    LEFT JOIN Quotes q ON p.QuoteID = q.QuoteID
    LEFT JOIN Lines l ON p.LineID = l.LineID
    LEFT JOIN Companies c ON p.CompanyID = c.CompanyID
    WHERE p.PolicyID = @PolicyID;
    
    -- Result Set 4: InsuredInfo
    SELECT 
        i.CorporationName AS InsuredName,
        i.DBAName,
        i.FEIN AS TaxID,
        loc.Address1,
        loc.Address2,
        loc.City,
        loc.State,
        loc.Zip AS ZipCode,
        con.FirstName + ' ' + con.LastName AS ContactName,
        con.Email,
        con.Phone
    FROM Policies p
    INNER JOIN Insureds i ON p.InsuredID = i.InsuredID
    LEFT JOIN InsuredLocations loc ON i.InsuredID = loc.InsuredID AND loc.IsPrimary = 1
    LEFT JOIN InsuredContacts con ON i.InsuredID = con.InsuredID AND con.IsPrimary = 1
    WHERE p.PolicyID = @PolicyID;
    
    -- Result Set 5: BillingInfo (might be different from Insured)
    SELECT 
        CASE 
            WHEN b.BillingName IS NOT NULL THEN b.BillingName
            ELSE i.CorporationName
        END AS BillingName,
        b.AttentionTo,
        COALESCE(b.Address1, loc.Address1) AS Address1,
        COALESCE(b.Address2, loc.Address2) AS Address2,
        COALESCE(b.City, loc.City) AS City,
        COALESCE(b.State, loc.State) AS State,
        COALESCE(b.ZipCode, loc.Zip) AS ZipCode,
        b.ContactName,
        b.Email,
        b.Phone
    FROM Policies p
    LEFT JOIN BillingInfo b ON p.PolicyID = b.PolicyID
    LEFT JOIN Insureds i ON p.InsuredID = i.InsuredID
    LEFT JOIN InsuredLocations loc ON i.InsuredID = loc.InsuredID AND loc.IsPrimary = 1
    WHERE p.PolicyID = @PolicyID;
    
    -- Result Set 6: PaymentInfo
    SELECT 
        pt.PaymentTerms,
        i.DueDate,
        -- ACH Info
        'true' AS ACHEnabled,
        pm.ACHBankName,
        pm.ACHRoutingNumber,
        pm.ACHAccountNumber,
        pm.ACHAccountName,
        -- Wire Info
        'true' AS WireEnabled,
        pm.WireBankName,
        pm.WireSwiftCode,
        pm.WireRoutingNumber,
        pm.WireAccountNumber,
        -- Check Info
        'true' AS CheckEnabled,
        pm.CheckPayableTo,
        pm.CheckMailToName,
        pm.CheckMailToStreet,
        pm.CheckMailToCity,
        pm.CheckMailToState,
        pm.CheckMailToZip,
        -- Online Payment
        pm.OnlinePaymentURL
    FROM Invoices i
    LEFT JOIN PaymentTerms pt ON i.PaymentTermsID = pt.PaymentTermsID
    LEFT JOIN PaymentMethods pm ON i.CompanyID = pm.CompanyID
    WHERE i.InvoiceID = @InvoiceID;
    
    -- Result Set 7: AgentInfo
    SELECT 
        prod.ProducerName AS AgencyName,
        pc.FirstName + ' ' + pc.LastName AS AgentName,
        pc.Email AS AgentEmail,
        pc.Phone AS AgentPhone,
        p.CommissionRate,
        p.CommissionAmount
    FROM Policies p
    INNER JOIN ProducerLocations pl ON p.ProducerLocationID = pl.ProducerLocationID
    INNER JOIN Producers prod ON pl.ProducerID = prod.ProducerID
    LEFT JOIN ProducerContacts pc ON pl.ProducerLocationID = pc.ProducerLocationID AND pc.IsPrimary = 1
    WHERE p.PolicyID = @PolicyID;
    
END

-- Alternative query if you need to find by External Quote ID
CREATE PROCEDURE GetPolicyByExternalQuoteId_WS
    @ExternalQuoteId NVARCHAR(100),
    @ExternalSystemId NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        p.PolicyNumber,
        p.PolicyID,
        q.QuoteNumber,
        q.QuoteID
    FROM ExternalReferences er
    INNER JOIN Quotes q ON er.InternalID = q.QuoteID
    INNER JOIN Policies p ON q.QuoteID = p.QuoteID
    WHERE er.ExternalID = @ExternalQuoteId
      AND er.ExternalSystemID = @ExternalSystemId
      AND er.EntityType = 'Quote';
      
END