# IMS Integration Field Requirements and Mapping Guide

## Executive Summary

This document provides a comprehensive guide for external systems to integrate with IMS (Insurance Management System). It outlines the **minimum required fields**, **lookup/reconciliation procedures**, and **complete integration workflow** for creating policies in IMS.

## Integration Overview

The IMS integration process follows this sequence:
1. **Insured Management** - Create or find insured entity
2. **Submission Creation** - Link insured to producer/underwriter
3. **Quote Creation** - Set coverage terms and rating
4. **Premium Application** - Apply calculated premiums
5. **Policy Binding** - Convert quote to policy
6. **Policy Issuance** - Finalize policy

---

## 1. MINIMUM REQUIRED FIELDS

### 🏢 **Insured Information** (Required for AddInsured)

| Field | IMS Field | Type | Required | Description |
|-------|-----------|------|----------|-------------|
| **Business Name** | `CorporationName` | string | ✅ **YES** | Legal entity name (for corporations) |
| **Individual Name** | `FirstName`, `LastName` | string | ✅ **YES** | Required for individuals only |
| **Business Type** | `BusinessTypeID` | int | ✅ **YES** | 1=Corporation, 3=Individual, etc. |
| **Tax ID** | `FEIN` (corp) / `SSN` (ind) | string | ⚠️ **Recommended** | Federal tax identifier |

### 📋 **Submission Information** (Required for AddSubmission)

| Field | IMS Field | Type | Required | Description |
|-------|-----------|------|----------|-------------|
| **Insured GUID** | `Insured` | guid | ✅ **YES** | From AddInsured response |
| **Producer GUID** | `ProducerContact` | guid | ✅ **YES** | Must be resolved via lookup |
| **Producer Location GUID** | `ProducerLocation` | guid | ✅ **YES** | Must be resolved via lookup |
| **Underwriter GUID** | `Underwriter` | guid | ✅ **YES** | Must be resolved via lookup |
| **Submission Date** | `SubmissionDate` | date | ✅ **YES** | YYYY-MM-DD format |

### 📄 **Quote Information** (Required for AddQuote)

| Field | IMS Field | Type | Required | Description |
|-------|-----------|------|----------|-------------|
| **Submission GUID** | `Submission` | guid | ✅ **YES** | From AddSubmission response |
| **Line of Business GUID** | `Line` | guid | ✅ **YES** | Must be resolved via lookup |
| **State Code** | `StateID` | string | ✅ **YES** | 2-letter state code |
| **Effective Date** | `Effective` | date | ✅ **YES** | Policy start date |
| **Expiration Date** | `Expiration` | date | ✅ **YES** | Policy end date |
| **Quote Status** | `QuoteStatusID` | int | ✅ **YES** | 1=New, 2=Quoted, etc. |
| **Billing Type** | `BillingTypeID` | int | ✅ **YES** | 1=Agency Bill, 2=Direct Bill |

### 💰 **Premium Information** (Required for AddPremium)

| Field | IMS Field | Type | Required | Description |
|-------|-----------|------|----------|-------------|
| **Quote GUID** | `QuoteGUID` | guid | ✅ **YES** | From AddQuote response |
| **Quote Option ID** | `QuoteOptionID` | int | ✅ **YES** | From AddQuoteOption response |
| **Premium Amount** | `Amount` | decimal | ✅ **YES** | Premium dollar amount |
| **Charge Code** | `ChargeID` | string | ✅ **YES** | Premium type identifier |

---

## 2. LOOKUP/RECONCILIATION PROCEDURES

### 🔍 **Insured Lookup** ✅ **MULTIPLE OPTIONS AVAILABLE**

#### **Option 1: FindInsuredByName** (Best for general matching)
**API:** `FindInsuredByName`
**Purpose:** Find Insured GUID by name and address
**Algorithm:** Uses scoring algorithm to find best match

```xml
<FindInsuredByName>
    <insuredName>ABC Corporation</insuredName>
    <city>Dallas</city>
    <state>TX</state>
    <zip>75201</zip>
    <zipPlus></zipPlus>
</FindInsuredByName>
```

**Returns:** InsuredGUID of highest scoring match (or empty if no match)

#### **Option 2: FindInsuredBySSN** (Best for individuals)
**API:** `FindInsuredBySSN`
**Purpose:** Find Insured GUID by SSN/FEIN

```xml
<FindInsuredBySSN>
    <SSN>123-45-6789</SSN>
</FindInsuredBySSN>
```

**Returns:** InsuredGUID (exact match only)

#### **Option 3: FindInsuredByTaxIDOffice** (Best for corporate entities)
**API:** `FindInsuredByTaxIDOffice`
**Purpose:** Find Insured GUID by Tax ID with optional office filtering

```xml
<FindInsuredByTaxIDOffice>
    <TaxID>12-3456789</TaxID>
    <OfficeGUID>00000000-0000-0000-0000-000000000000</OfficeGUID>
</FindInsuredByTaxIDOffice>
```

**Returns:** InsuredGUID (exact match on Tax ID)

**Recommended Integration Process:**
```python
# 1. Try exact match by Tax ID (if available)
if tax_id:
    insured_guid = FindInsuredByTaxIDOffice(tax_id)
    
# 2. If no match, try by name and address
if not insured_guid:
    insured_guid = FindInsuredByName(name, city, state, zip)
    
# 3. For individuals, also try SSN
if not insured_guid and is_individual:
    insured_guid = FindInsuredBySSN(ssn)
    
# 4. If still no match, create new insured
if not insured_guid:
    insured_guid = AddInsured(insured_data)
```

### 🔍 **Producer Lookup** ✅ **AVAILABLE**

**API:** `ProducerSearch`
**Purpose:** Find Producer GUID by name

```xml
<ProducerSearch>
    <searchString>Producer Name</searchString>
    <startWith>false</startWith>
</ProducerSearch>
```

**Returns:**
- `ProducerLocationGuid` - For ProducerContact field
- `ProducerName` - Matched producer name
- `LocationName` - Producer location details

**Integration Process:**
1. Call `ProducerSearch` with producer name from source system
2. Match exact or closest result
3. Use `ProducerLocationGuid` for both `ProducerContact` and `ProducerLocation` fields

### 🔍 **Underwriter Lookup** ⚠️ **LIMITED**

**Available API:** `GetProducerUnderwriter`
**Limitation:** Requires ProducerEntity GUID + LineGuid (not name-based search)

```xml
<GetProducerUnderwriter>
    <ProducerEntity>guid</ProducerEntity>
    <LineGuid>guid</LineGuid>
</GetProducerUnderwriter>
```

**🚨 RECOMMENDATION:** Create custom stored procedure `FindUnderwriterByName_WS`

**Proposed Implementation:**
```sql
CREATE PROCEDURE [dbo].[FindUnderwriterByName_WS]
    @UnderwriterName NVARCHAR(255),
    @LineGuid UNIQUEIDENTIFIER = NULL
AS
BEGIN
    SELECT 
        UnderwriterGuid,
        FirstName,
        LastName,
        Email,
        Phone,
        Active
    FROM tblUnderwriters 
    WHERE (FirstName + ' ' + LastName LIKE '%' + @UnderwriterName + '%'
           OR Email LIKE '%' + @UnderwriterName + '%')
    AND Active = 1
    ORDER BY 
        CASE WHEN (FirstName + ' ' + LastName) = @UnderwriterName THEN 1 ELSE 2 END,
        LastName, FirstName
END
```

**Usage via DataAccess:**
```xml
<ExecuteDataSet>
    <procedureName>FindUnderwriterByName</procedureName>
    <parameters>
        <string>UnderwriterName</string>
        <string>John Smith</string>
    </parameters>
</ExecuteDataSet>
```

### 🔍 **Other Required Lookups**

#### **Line of Business GUID**
- **Method:** Custom stored procedure or DataAccess query
- **Input:** Line name (e.g., "General Liability", "Professional Liability")
- **Output:** Line GUID

#### **Program/Rater Information**
- **Method:** DataAccess query on program tables
- **Input:** Program name, state, line of business
- **Output:** ProgramID, RaterID, FactorSetGuid

#### **Business Type ID**
- **Method:** Static mapping or DataAccess lookup
- **Common Values:**
  - 1 = Corporation
  - 2 = Partnership  
  - 3 = Individual
  - 4 = Sole Proprietor

---

## 3. INTEGRATION WORKFLOW

### **Phase 1: Data Preparation**
```
1. Validate all required fields present
2. Resolve Producer GUID via ProducerSearch
3. Resolve Underwriter GUID via FindUnderwriterByName_WS
4. Resolve Line GUID via lookup table
5. Map business types and other reference data
```

### **Phase 2: IMS Entity Creation**
```
1. LoginIMSUser → Get authentication token
2. FindInsuredByName → Check if insured exists
3. AddInsured → Create insured if not found
4. AddSubmission → Create submission record
5. AddQuote → Create quote with all details
6. AddQuoteOption → Create quote option for rating
```

### **Phase 3: Rating and Premium**
```
7. ImportExcelRater → Calculate premiums (if using Excel rater)
   OR
   AddPremium → Apply manual premium amounts
8. Validate rating results
```

### **Phase 4: Policy Creation**
```
9. Bind → Convert quote to policy
10. IssuePolicy → Finalize policy issuance
11. UpdateExternalQuoteId → Link back to source system
```

---

## 4. FIELD MAPPING EXAMPLES

### **Source System → IMS Mapping**

| Source Field | IMS API | IMS Field | Transformation Required |
|--------------|---------|-----------|------------------------|
| Company Name | AddInsured | CorporationName | Direct mapping |
| Tax ID | AddInsured | FEIN | Direct mapping |
| Producer Name | ProducerSearch | searchString | **Lookup required** |
| Underwriter Name | FindUnderwriterByName_WS | UnderwriterName | **Custom proc required** |
| Line of Business | DataAccess lookup | Line GUID | **Lookup required** |
| State | AddQuote | StateID | Direct mapping |
| Policy Start | AddQuote | Effective | Date format: YYYY-MM-DD |
| Policy End | AddQuote | Expiration | Date format: YYYY-MM-DD |
| Total Premium | AddPremium | Amount | Direct mapping |

### **Required Static/Default Values**

| IMS Field | Recommended Default | Notes |
|-----------|-------------------|-------|
| QuoteStatusID | 1 (New) | Standard for new submissions |
| BillingTypeID | 1 (Agency Bill) | Most common billing type |
| QuotingLocation | Default company GUID | Set per environment |
| IssuingLocation | Default company GUID | Set per environment |
| CompanyLocation | Default company GUID | Set per environment |

---

## 5. DATA STORAGE OPTIONS FOR ADDITIONAL FIELDS

### **Option 1: Dynamic Data Tables** ⭐ **RECOMMENDED**
```sql
-- Create custom rater entry
INSERT INTO tblExcelRating_Raters (
    RaterName = 'Source System Data Import',
    DatabaseTableName = 'dynamic_data_source_system'
)

-- Store additional data via ExecuteCommand
EXEC StoreSourceSystemData_WS 
    @QuoteOptionGUID = 'quote-guid',
    @SourceSystemData = '{"field1": "value1", "field2": "value2"}'
```

### **Option 2: Document Storage**
```xml
<InsertStandardDocument>
    <file>
        <Name>source_system_data.json</Name>
        <Data>base64-encoded-json</Data>
        <Description>Complete source system data</Description>
        <MetaXml><metadata><source>SourceSystem</source></metadata></MetaXml>
    </file>
</InsertStandardDocument>
```

### **Option 3: External Reference**
```xml
<UpdateExternalQuoteId>
    <quoteGuid>ims-quote-guid</quoteGuid>
    <externalQuoteId>source-system-id</externalQuoteId>
    <externalSystemId>SourceSystemName</externalSystemId>
</UpdateExternalQuoteId>
```

---

## 6. IMPLEMENTATION CHECKLIST

### **Pre-Integration Setup**
- [ ] Obtain IMS environment access and credentials
- [ ] Create/verify FindUnderwriterByName_WS stored procedure
- [ ] Establish lookup tables for Line GUIDs, Program IDs
- [ ] Configure producer mapping strategy
- [ ] Set up default location GUIDs

### **Integration Development**
- [ ] Implement ProducerSearch integration
- [ ] Implement underwriter lookup (custom procedure)
- [ ] Build field validation and mapping logic
- [ ] Create error handling and retry mechanisms
- [ ] Implement complete workflow (Insured → Quote → Bind → Issue)

### **Testing & Validation**
- [ ] Test with sample producer names (verify ProducerSearch)
- [ ] Test with sample underwriter names (verify custom lookup)
- [ ] Validate complete policy creation workflow
- [ ] Test error scenarios and edge cases
- [ ] Performance testing with volume data

---

## 7. TECHNICAL SPECIFICATIONS

### **Authentication**
- **Method:** SOAP Header with Token
- **Endpoint:** `LoginIMSUser`
- **Token Lifespan:** Typically 8 hours
- **Renewal:** Call LoginIMSUser again

### **Error Handling**
- **SOAP Faults:** Check for fault messages in responses
- **Business Logic Errors:** Validate field requirements
- **Retry Strategy:** Implement exponential backoff for transient failures

### **Performance Considerations**
- **Batch Processing:** Process multiple policies in sequence
- **Connection Reuse:** Maintain SOAP client connections
- **Lookup Caching:** Cache producer/underwriter lookups
- **Monitoring:** Track success/failure rates

---

## 8. LOOKUP API SUMMARY

### **Available Lookups in IMS:**

| Entity | API Method | Input | Output | Status |
|--------|------------|-------|--------|--------|
| **Insured** | `FindInsuredByName` | Name, City, State, Zip | InsuredGUID | ✅ Available |
| **Insured** | `FindInsuredBySSN` | SSN | InsuredGUID | ✅ Available |
| **Insured** | `FindInsuredByTaxIDOffice` | TaxID, OfficeGUID | InsuredGUID | ✅ Available |
| **Producer** | `ProducerSearch` | Name (partial/full) | ProducerLocationGuid | ✅ Available |
| **Underwriter** | `GetProducerUnderwriter` | ProducerGUID + LineGUID | UnderwriterGUID | ⚠️ Limited |
| **Underwriter** | `FindUnderwriterByName_WS` | Name | UnderwriterGUID | ❌ Needs Creation |

### **Recommended Lookup Order:**

1. **Insured:** Tax ID → Name/Address → SSN → Create New
2. **Producer:** Name Search → Manual Selection → Default
3. **Underwriter:** Custom Procedure → Producer Default → Manual Assignment

## 9. SUPPORT CONTACTS

- **IMS API Documentation:** [IMS Web Services Documentation]
- **Custom Stored Procedures:** Database team for FindUnderwriterByName_WS creation
- **Producer/Underwriter Data:** Business users for validation
- **Integration Support:** Technical team for implementation assistance

---

## Appendix A: Complete Minimal Example

```json
{
  "insured": {
    "name": "ABC Corporation",
    "tax_id": "12-3456789",
    "business_type": "Corporation"
  },
  "producer": {
    "name": "Smith Insurance Agency"
  },
  "underwriter": {
    "name": "John Underwriter"
  },
  "quote": {
    "line_of_business": "General Liability",
    "state": "TX",
    "effective_date": "2024-01-01",
    "expiration_date": "2024-12-31",
    "premium": 5000.00
  }
}
```

This represents the **absolute minimum** data required for successful IMS policy creation.