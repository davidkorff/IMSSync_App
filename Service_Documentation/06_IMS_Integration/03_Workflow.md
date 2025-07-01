# IMS Integration Workflow

This document details the complete workflow for creating policies in IMS through the integration service.

## Workflow Overview

The IMS integration follows a specific sequence of operations to create a policy:

```
1. Authenticate → 2. Insured → 3. Submission → 4. Quote → 5. Rating → 6. Bind → 7. Issue
```

## Detailed Workflow Steps

### Step 1: Authentication

**Purpose**: Obtain a session token for all subsequent API calls

**API Call**: `LoginIMSUser`
```xml
<LoginIMSUser>
    <username>your_username</username>
    <password>encrypted_password</password>
</LoginIMSUser>
```

**Response**: Authentication token (GUID)
- Token valid for 8 hours
- Must be included in SOAP header for all calls
- Token tied to originating IP address

### Step 2: Insured Management

**Purpose**: Find existing or create new insured entity

#### 2.1 Search for Existing Insured
```xml
<!-- Option 1: Search by name -->
<FindInsuredByName>
    <insuredName>ABC Corporation</insuredName>
    <city>Dallas</city>
    <state>TX</state>
    <zip>75201</zip>
</FindInsuredByName>

<!-- Option 2: Search by Tax ID -->
<FindInsuredByTaxIDOffice>
    <TaxID>12-3456789</TaxID>
    <OfficeGUID>00000000-0000-0000-0000-000000000000</OfficeGUID>
</FindInsuredByTaxIDOffice>
```

#### 2.2 Create New Insured (if not found)
```xml
<AddInsuredWithLocation>
    <insured>
        <BusinessTypeID>1</BusinessTypeID>  <!-- 1=Corporation -->
        <CorporationName>ABC Corporation</CorporationName>
        <NameOnPolicy>ABC Corporation</NameOnPolicy>
        <FEIN>123456789</FEIN>
    </insured>
    <location>
        <LocationName>Primary Location</LocationName>
        <Address1>123 Main Street</Address1>
        <City>Dallas</City>
        <State>TX</State>
        <Zip>75201</Zip>
        <LocationTypeID>1</LocationTypeID>  <!-- 1=Primary -->
        <DeliveryMethodID>1</DeliveryMethodID>  <!-- 1=Mail -->
    </location>
</AddInsuredWithLocation>
```

**Key Points**:
- Always search before creating to avoid duplicates
- Store InsuredGUID for future use
- Location is required for searchability

### Step 3: Submission Creation

**Purpose**: Create submission linking insured to producer/underwriter

**API Call**: `AddSubmission`
```xml
<AddSubmission>
    <submission>
        <Insured>insured-guid-from-step-2</Insured>
        <ProducerContact>producer-guid</ProducerContact>
        <ProducerLocation>producer-location-guid</ProducerLocation>
        <Underwriter>underwriter-guid</Underwriter>
        <SubmissionDate>2025-01-23</SubmissionDate>
    </submission>
</AddSubmission>
```

**Response**: SubmissionGroupGUID
- Links insured to producer
- Groups related quotes
- Required for quote creation

### Step 4: Quote Creation

**Purpose**: Create the policy quote with coverage details

**API Call**: `AddQuoteWithAutocalculateDetails`
```xml
<AddQuoteWithAutocalculateDetails>
    <quote>
        <Submission>submission-guid-from-step-3</Submission>
        <QuotingLocation>office-guid</QuotingLocation>
        <IssuingLocation>office-guid</IssuingLocation>
        <CompanyLocation>company-location-guid</CompanyLocation>
        <Line>line-of-business-guid</Line>
        <StateID>TX</StateID>
        <ProducerContact>producer-guid</ProducerContact>
        <QuoteStatusID>1</QuoteStatusID>  <!-- 1=New -->
        <Effective>2025-02-01</Effective>
        <Expiration>2026-02-01</Expiration>
        <BillingTypeID>1</BillingTypeID>  <!-- 1=Agency Bill -->
        <Underwriter>underwriter-guid</Underwriter>
        <PolicyTypeID>1</PolicyTypeID>  <!-- 1=New Business -->
    </quote>
</AddQuoteWithAutocalculateDetails>
```

**Response**: QuoteGUID
- Represents the policy record
- Used for all subsequent operations

### Step 5: Quote Options & Rating

**Purpose**: Add coverage options and apply premium

#### 5.1 Create Quote Options
```xml
<AutoAddQuoteOptions>
    <quoteGuid>quote-guid-from-step-4</quoteGuid>
</AutoAddQuoteOptions>
```

**Response**: QuoteOptionIDs for each coverage line

#### 5.2 Apply Premium (Direct Pass-Through)
```xml
<AddPremium>
    <quoteGuid>quote-guid</quoteGuid>
    <quoteOptionId>option-id</quoteOptionId>
    <amount>5000.00</amount>
    <description>Annual Premium</description>
    <chargeCode>PREMIUM_TX</chargeCode>
</AddPremium>
```

#### 5.3 Alternative: Excel Rating
```xml
<ImportExcelRater>
    <quoteguid>quote-guid</quoteguid>
    <quoteDetailIds>
        <int>detail-id</int>
    </quoteDetailIds>
    <excelXml>base64-encoded-excel-data</excelXml>
    <saveRatingSheet>true</saveRatingSheet>
</ImportExcelRater>
```

### Step 6: Bind Policy

**Purpose**: Convert quote to active policy

**API Call**: `BindQuote`
```xml
<BindQuote>
    <quoteGuid>quote-guid</quoteGuid>
</BindQuote>
```

**Alternative with Payment Plan**:
```xml
<BindQuoteWithInstallment>
    <quoteGuid>quote-guid</quoteGuid>
    <companyInstallmentId>installment-plan-id</companyInstallmentId>
</BindQuoteWithInstallment>
```

**Response**: Policy Number
- Policy is now active
- Generates binder documents
- Creates billing records

### Step 7: Issue Policy

**Purpose**: Finalize policy issuance

**API Call**: `IssuePolicy`
```xml
<IssuePolicy>
    <quoteGuid>quote-guid</quoteGuid>
</IssuePolicy>
```

**Results**:
- Policy fully issued
- Policy documents generated
- Commissions calculated

### Step 8: Link External Reference

**Purpose**: Store source system reference

**API Call**: `UpdateExternalQuoteId`
```xml
<UpdateExternalQuoteId>
    <quoteGuid>quote-guid</quoteGuid>
    <externalQuoteId>TRITON-12345</externalQuoteId>
    <externalSystemId>Triton</externalSystemId>
</UpdateExternalQuoteId>
```

## Workflow Variations

### Renewal Workflow
1. Find existing policy
2. Create renewal quote with `RenewalOfQuoteGuid`
3. Update effective/expiration dates
4. Follow standard workflow from Step 5

### Endorsement Workflow
1. Find active policy by external ID
2. Create endorsement transaction
3. Apply premium changes
4. Process through workflow

### Cancellation Workflow
1. Find active policy
2. Call cancellation API with date
3. Calculate return premium
4. Update policy status

## Error Handling

### Retry Strategy
```python
def process_with_retry(transaction, max_retries=3):
    for attempt in range(max_retries):
        try:
            # Process transaction
            result = process_transaction(transaction)
            return result
        except IMSTemporaryError:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            raise
        except IMSPermanentError:
            # Don't retry permanent errors
            raise
```

### Common Workflow Errors

| Step | Error | Solution |
|------|-------|----------|
| Authentication | Invalid credentials | Verify username/password |
| Insured | Duplicate found | Use existing GUID |
| Submission | Invalid producer | Verify producer GUID |
| Quote | Missing required field | Check field mapping |
| Rating | No rater configured | Set rater ID |
| Bind | No premium | Add premium first |
| Issue | Policy not bound | Complete bind step |

## Best Practices

### 1. Transaction Management
- Store all GUIDs for audit trail
- Log each step completion
- Implement idempotency checks

### 2. Error Recovery
- Save transaction state after each step
- Allow resuming from last successful step
- Don't create duplicate entities

### 3. Performance
- Cache authentication tokens
- Reuse insured/producer lookups
- Batch similar operations

### 4. Data Validation
- Validate all data before starting workflow
- Check required fields early
- Verify GUIDs are valid format

## Workflow State Tracking

Track progress through IMS workflow:

```python
class IMSWorkflowState:
    STARTED = "started"
    AUTHENTICATED = "authenticated"
    INSURED_CREATED = "insured_created"
    SUBMISSION_CREATED = "submission_created"
    QUOTE_CREATED = "quote_created"
    RATED = "rated"
    BOUND = "bound"
    ISSUED = "issued"
    COMPLETED = "completed"
    FAILED = "failed"
```

## Testing the Workflow

### Test Each Step Individually
```bash
# Test authentication
python test_ims_login.py

# Test insured search
python test_insured_search.py

# Test full workflow
python test_full_workflow.py
```

### Verify Results in IMS
1. Check insured was created correctly
2. Verify quote appears in system
3. Confirm policy number generated
4. Validate premium amounts

## Monitoring Workflow Progress

### Log Analysis
```bash
# Track specific transaction
grep "transaction_id" ims_integration.log | grep -E "(INSURED_CREATED|QUOTE_CREATED|BOUND|ISSUED)"

# Check workflow timing
grep "transaction_id" ims_integration.log | grep "Processing time"
```

### Status Endpoints
```bash
# Check transaction status
curl http://localhost:8000/api/transaction/{id} \
  -H "X-API-Key: your-key"
```

## Next Steps

- Review [Field Mapping](../04_Integration_Guides/04_Field_Mapping.md) for data requirements
- See [IMS Functions Reference](./04_Functions_Reference.md) for detailed API documentation
- Check [Troubleshooting](../07_Operations/03_Troubleshooting.md) for common issues