# IMS Integration Field Mapping Guide

This guide provides comprehensive field mapping information for integrating external systems with IMS.

## Table of Contents
1. [Minimum Required Fields](#minimum-required-fields)
2. [Field Mapping Reference](#field-mapping-reference)
3. [Data Type Mappings](#data-type-mappings)
4. [Lookup Procedures](#lookup-procedures)
5. [Validation Rules](#validation-rules)

## Minimum Required Fields

### 🏢 Insured Information
| Field | IMS Field | Type | Required | Description |
|-------|-----------|------|----------|-------------|
| **Business Name** | `CorporationName` | string(100) | ✅ YES* | For corporations |
| **Individual Name** | `FirstName`, `LastName` | string(50) | ✅ YES* | For individuals |
| **Business Type** | `BusinessTypeID` | int | ✅ YES | See business type table |
| **Tax ID** | `FEIN` / `SSN` | string | ⚠️ Recommended | Federal tax identifier |
| **Name on Policy** | `NameOnPolicy` | string(200) | ✅ YES | How name appears on policy |

*Either Business Name OR Individual Name required

### 📋 Submission Information
| Field | IMS Field | Type | Required | Description |
|-------|-----------|------|----------|-------------|
| **Insured GUID** | `Insured` | guid | ✅ YES | From AddInsured response |
| **Producer GUID** | `ProducerContact` | guid | ✅ YES | From ProducerSearch |
| **Producer Location** | `ProducerLocation` | guid | ✅ YES | From ProducerSearch |
| **Underwriter GUID** | `Underwriter` | guid | ✅ YES | From lookup/config |
| **Submission Date** | `SubmissionDate` | date | ✅ YES | YYYY-MM-DD format |

### 📄 Quote Information
| Field | IMS Field | Type | Required | Description |
|-------|-----------|------|----------|-------------|
| **Submission GUID** | `Submission` | guid | ✅ YES | From AddSubmission |
| **Line GUID** | `Line` | guid | ✅ YES | Line of business |
| **State Code** | `StateID` | string(2) | ✅ YES | 2-letter state code |
| **Effective Date** | `Effective` | date | ✅ YES | Policy start date |
| **Expiration Date** | `Expiration` | date | ✅ YES | Policy end date |
| **Quote Status** | `QuoteStatusID` | int | ✅ YES | 1=New, 2=Quoted |
| **Billing Type** | `BillingTypeID` | int | ✅ YES | 1=Agency, 2=Direct |

### 💰 Premium Information
| Field | IMS Field | Type | Required | Description |
|-------|-----------|------|----------|-------------|
| **Quote GUID** | `QuoteGUID` | guid | ✅ YES | From AddQuote |
| **Quote Option ID** | `QuoteOptionID` | int | ✅ YES | From AddQuoteOption |
| **Premium Amount** | `Amount` | decimal | ✅ YES | Premium dollars |
| **Charge Code** | `ChargeID` | string | ✅ YES | Premium type |

## Field Mapping Reference

### Triton → IMS Mapping
| Triton Field | IMS API | IMS Field | Transformation |
|--------------|---------|-----------|----------------|
| `account.name` | AddInsured | CorporationName | Direct |
| `account.id` | AddInsured | RiskId | Direct (optional) |
| `tax_id` | AddInsured | FEIN | Direct |
| `producer.name` | ProducerSearch | searchString | Lookup required |
| `program.name` | DataAccess | Line GUID | Lookup required |
| `policy_number` | AddQuote | ExternalQuoteId | Store for reference |
| `effective_date` | AddQuote | Effective | ISO to date |
| `expiration_date` | AddQuote | Expiration | ISO to date |
| `premium.annual_premium` | AddPremium | Amount | Direct |

### Xuber → IMS Mapping
| Xuber Field | IMS API | IMS Field | Transformation |
|-------------|---------|-----------|----------------|
| `insured_name` | AddInsured | CorporationName | Direct |
| `insured_address` | AddInsuredLocation | Address1 | Parse components |
| `producer_code` | ProducerSearch | searchString | Lookup by code |
| `coverage_type` | DataAccess | Line GUID | Map to line |
| `policy_term` | AddQuote | Effective/Expiration | Calculate dates |
| `total_premium` | AddPremium | Amount | Direct |

## Data Type Mappings

### Business Types
| ID | Type | Use For |
|----|------|---------|
| 1 | Corporation | Most businesses |
| 2 | Partnership | Partnerships |
| 3 | Individual | Personal policies |
| 4 | Sole Proprietor | Individual businesses |
| 9 | LLC/LLP | Limited liability |

### Quote Status
| ID | Status | Description |
|----|--------|-------------|
| 1 | New | Initial submission |
| 2 | Quoted | Premium calculated |
| 3 | Bound | Policy active |
| 4 | Declined | Not proceeding |
| 5 | Lost | Business lost |

### Billing Types
| ID | Type | Description |
|----|------|-------------|
| 1 | Agency Bill | Producer collects |
| 2 | Direct Bill (MGA) | MGA bills insured |
| 3 | Direct Bill (Company) | Carrier bills |

### Policy Types
| ID | Type | When to Use |
|----|------|-------------|
| 1 | New | First time policy |
| 2 | Renewal | Renewal transaction |
| 3 | Rewrite | Rewritten policy |

## Lookup Procedures

### Finding Insureds
```xml
<!-- Option 1: By Name and Address -->
<FindInsuredByName>
    <insuredName>ABC Corporation</insuredName>
    <city>Dallas</city>
    <state>TX</state>
    <zip>75201</zip>
</FindInsuredByName>

<!-- Option 2: By Tax ID -->
<FindInsuredByTaxIDOffice>
    <TaxID>12-3456789</TaxID>
    <OfficeGUID>00000000-0000-0000-0000-000000000000</OfficeGUID>
</FindInsuredByTaxIDOffice>

<!-- Option 3: By SSN (individuals) -->
<FindInsuredBySSN>
    <SSN>123-45-6789</SSN>
</FindInsuredBySSN>
```

### Finding Producers
```xml
<ProducerSearch>
    <searchString>Smith Insurance</searchString>
    <startWith>false</startWith>
</ProducerSearch>
```

Returns:
- `ProducerLocationGuid` - Use for both ProducerContact and ProducerLocation
- `ProducerName` - Matched name
- `LocationName` - Office location

### Finding Underwriters
Currently requires custom stored procedure:
```sql
-- Recommended: Create this procedure
CREATE PROCEDURE [dbo].[FindUnderwriterByName_WS]
    @UnderwriterName NVARCHAR(255),
    @LineGuid UNIQUEIDENTIFIER = NULL
AS
BEGIN
    SELECT UnderwriterGuid, FirstName, LastName, Email
    FROM tblUnderwriters 
    WHERE (FirstName + ' ' + LastName LIKE '%' + @UnderwriterName + '%')
    AND Active = 1
END
```

## Validation Rules

### Required Field Validation
1. **Insured Name**: Either CorporationName OR (FirstName + LastName)
2. **Dates**: Effective < Expiration
3. **State**: Valid 2-letter code
4. **GUIDs**: Valid format (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)

### Business Rules
1. **New Business**: PolicyTypeID = 1
2. **Renewals**: Requires RenewalOfQuoteGuid
3. **Premium**: Must be > 0 for binding
4. **Producer**: Must have valid license for state

### Common Validation Errors
| Error | Cause | Solution |
|-------|-------|----------|
| "Invalid GUID format" | Malformed GUID | Use proper GUID format |
| "Producer not found" | Invalid producer GUID | Use ProducerSearch first |
| "Line not available" | Invalid line/state combo | Verify line configuration |
| "Duplicate insured" | Insured already exists | Use Find functions first |

## Integration Workflow

### Recommended Field Resolution Order
1. **Resolve Producer** → Get GUID via ProducerSearch
2. **Check Insured** → Use Find functions, create if needed
3. **Validate Line** → Ensure line/state combination valid
4. **Create Submission** → Link insured to producer
5. **Create Quote** → Add all required fields
6. **Add Premium** → Apply source system premium

### Field Storage for Additional Data

For fields not in IMS, use these options:

1. **External Quote ID**:
```xml
<UpdateExternalQuoteId>
    <quoteGuid>ims-quote-guid</quoteGuid>
    <externalQuoteId>source-system-id</externalQuoteId>
    <externalSystemId>Triton</externalSystemId>
</UpdateExternalQuoteId>
```

2. **Custom Tables** (via stored procedures):
```sql
EXEC StoreSourceSystemData_WS 
    @QuoteGUID = 'quote-guid',
    @SourceData = '{"custom_field": "value"}'
```

3. **Document Storage**:
```xml
<InsertStandardDocument>
    <file>
        <Name>additional_data.json</Name>
        <Data>base64-encoded-json</Data>
    </file>
</InsertStandardDocument>
```

## Field Mapping Template

Use this template for new integrations:

```json
{
  "source_to_ims_mapping": {
    "insured": {
      "source_field": "ims_field",
      "company_name": "CorporationName",
      "tax_id": "FEIN"
    },
    "location": {
      "address_line_1": "Address1",
      "city": "City",
      "state": "State",
      "zip": "Zip"
    },
    "policy": {
      "policy_number": "ExternalQuoteId",
      "start_date": "Effective",
      "end_date": "Expiration"
    }
  },
  "lookups_required": [
    "producer_guid",
    "underwriter_guid",
    "line_guid"
  ],
  "custom_fields": [
    "field_not_in_ims"
  ]
}
```

## Next Steps

1. Review your source system fields
2. Map to IMS required fields
3. Identify lookup requirements
4. Plan custom field storage
5. Test with sample data