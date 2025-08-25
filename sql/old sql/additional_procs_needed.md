# Additional Stored Procedures Needed for Complete Workflow

## 1. Quote Option Management
- **spGetQuoteOptions_WS** - Already exists
- **spGetQuoteOptionID_WS** - Already exists

## 2. Transaction History Query
```sql
-- Get all transactions for a specific quote
CREATE PROCEDURE spGetQuoteTransactionHistory_WS
    @QuoteGuid UNIQUEIDENTIFIER
AS
BEGIN
    SELECT 
        transaction_id,
        transaction_type,
        transaction_date,
        policy_number,
        net_premium,
        status,
        created_date
    FROM tblTritonTransactionData
    WHERE QuoteGuid = @QuoteGuid
    ORDER BY created_date DESC;
END
```

## 3. Get Latest Transaction for Quote
```sql
-- Get the most recent transaction for a quote
CREATE PROCEDURE spGetLatestQuoteTransaction_WS
    @QuoteGuid UNIQUEIDENTIFIER
AS
BEGIN
    SELECT TOP 1 *
    FROM tblTritonTransactionData
    WHERE QuoteGuid = @QuoteGuid
    ORDER BY created_date DESC;
END
```

## 4. Handle Unbind Transaction
```sql
-- Process unbind transaction
CREATE PROCEDURE spProcessUnbindTransaction_WS
    @QuoteGuid UNIQUEIDENTIFIER,
    @TransactionId NVARCHAR(100)
AS
BEGIN
    -- Update quote status
    UPDATE tblquotes 
    SET QuoteStatusID = (SELECT ID FROM tblQuoteStatus WHERE Name = 'Quote')
    WHERE QuoteGuid = @QuoteGuid;
    
    -- Clear policy number
    UPDATE tblquotes 
    SET PolicyNumber = NULL
    WHERE QuoteGuid = @QuoteGuid;
    
    -- Update tblTritonQuoteData status
    UPDATE tblTritonQuoteData
    SET status = 'unbound',
        last_updated = GETDATE()
    WHERE QuoteGuid = @QuoteGuid;
END
```

## 5. Get Policy by Number
```sql
-- Find quote/policy by policy number
CREATE PROCEDURE spGetQuoteByPolicyNumber_WS
    @PolicyNumber NVARCHAR(50)
AS
BEGIN
    SELECT 
        q.QuoteGuid,
        q.PolicyNumber,
        td.insured_name,
        td.status,
        td.effective_date,
        td.expiration_date
    FROM tblquotes q
    INNER JOIN tblTritonQuoteData td ON q.QuoteGuid = td.QuoteGuid
    WHERE q.PolicyNumber = @PolicyNumber;
END
```

## 6. Midterm Endorsement Handler
```sql
-- Process midterm endorsement
CREATE PROCEDURE spProcessMidtermEndorsement_WS
    @QuoteGuid UNIQUEIDENTIFIER,
    @EndorsementNumber NVARCHAR(50),
    @EffectiveDate DATETIME,
    @Description NVARCHAR(500),
    @PremiumChange DECIMAL(18,2)
AS
BEGIN
    -- Implementation for handling endorsements
    -- Would update both transaction and quote data tables
END
```

## 7. Cancellation Handler
```sql
-- Process policy cancellation
CREATE PROCEDURE spProcessCancellation_WS
    @QuoteGuid UNIQUEIDENTIFIER,
    @CancellationDate DATETIME,
    @Reason NVARCHAR(500),
    @ReturnPremium DECIMAL(18,2)
AS
BEGIN
    -- Update quote status to cancelled
    -- Calculate return premium
    -- Update both tables
END
```

## Notes:
- You already have the core procedures needed for basic bind/issue
- The above additions would handle the full policy lifecycle
- Consider adding error handling and transaction management to all procedures
- Add appropriate permissions (GRANT EXECUTE TO [IMS_User])