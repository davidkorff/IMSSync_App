# RSG Integration Progress Document
Last Updated: 2025-07-15

## Project Overview
Building a service that processes insurance transactions from Triton and transforms them into IMS API calls. The service handles 5 transaction types: Bind, Unbind, Issue, Midterm Endorsement, and Cancellation.

## Current Status: Blocked - Installment billing configuration required

### What We've Accomplished ✅

1. **Project Structure**
   - Created modular FastAPI service with separate IMS service modules
   - Implemented base service pattern for IMS SOAP clients
   - Set up Docker configuration and environment management
   - Created comprehensive test scripts

2. **Authentication**
   - Fixed authentication from `Login` (wrong method) to `LoginIMSUser`
   - Successfully authenticating with IMS using encrypted credentials
   - Token management with auto-refresh

3. **Insured Creation**
   - Successfully creating insureds with proper object structure
   - Fixed BusinessTypeID from 1 to 9 (LLC - Partnership)
   - Insured search working correctly

4. **Submission Creation**
   - Successfully creating submissions with proper object structure
   - Using valid Producer GUID from environment

### Current Issues 🔧

1. ~~**Quote Creation - DateTime Format Error**~~ ✅ FIXED
   - Converted dates from MM/DD/YYYY to YYYY-MM-DD format

2. ~~**Quote Creation - Null Reference Error**~~ ✅ FIXED
   - `AddQuoteWithInsured` method not available in this IMS instance
   - Fixed issues with AddQuote:
     - Changed empty strings to null values in RiskInformation
     - Removed TACSR field from quote object (only valid in submission)
     - AddQuote creates both submission and quote together (not separate calls)
     - Fixed decimal conversion error by converting commission rates from percentage to decimal
   - Current approach: AddInsured + AddQuote (which creates submission and quote)

3. ~~**RaterID Foreign Key Error**~~ ✅ FIXED
   - Changed default RaterID from 1 to 0 to avoid foreign key constraint

4. ~~**BindQuote Method Signature Error**~~ ✅ FIXED
   - BindQuote only accepts quoteGuid parameter, not policyNumber or bindDate
   - Removed extra parameters from the method call

5. ~~**Invalid OptionID Error**~~ ✅ FIXED
   - BindQuote requires a quote option to be added first
   - Implemented AddQuoteOption method to create options before binding
   - Using the line GUID from environment

6. **Installment billing information not found** ❌ BLOCKING
   - Error persists with both BindQuote and BindQuoteWithInstallment (with -1)
   - Tried multiple approaches:
     - BindQuote (original) - fails with "Installment billing information not found"
     - BindQuoteWithInstallment with companyInstallmentID=-1 - same error
     - Both methods internally expect installment billing configuration
   - Possible causes:
     - IMS configuration issue - may require policy number rule setup
     - CompanyLine configuration missing installment billing setup
     - Database configuration issue with installment billing tables
   - Alternative approach attempted:
     - Implemented DataAccess service to query quote options and get the integer ID
     - Created stored procedures and Bind method with quote option ID
     - DataAccess failing with "Parameters must be specified in Key/Value pairs" error
     - Issue appears to be with how Zeep passes array parameters to SOAP service
   - Current status:
     - DataAccess still failing with "Parameters must be specified in Key/Value pairs" error
     - Tried removing @ symbol from parameter names - still getting same error
     - Likely issues:
       1. The stored procedure spGetQuoteOptions_WS probably doesn't exist in the database
       2. DataAccess may have a different parameter format requirement we haven't discovered
       3. The IMS instance may have specific configuration for DataAccess
     - Currently blocked on bind operation due to installment billing requirement

7. **Method Availability**
   - `AddQuoteWithSubmission` doesn't exist in this IMS instance
   - `AddQuoteWithInsured` also not available in this instance
   - Using fallback approach with separate API calls

8. **Data Storage Issues (Non-Blocking)**
   - UpdateExternalQuoteId: Missing stored procedure 'dbo.spAddExternalQuoteLink'
     - Error is caught and logged as warning
     - Transaction continues without storing external ID
   - ImportNetRateXml: Expects specific NetRate format, not general XML
     - Error is caught and logged as warning
     - Transaction continues without storing additional data

### Transaction Flow Progress

```
Bind Transaction (CURRENT FLOW):
1. ✅ Authenticate with IMS
2. ✅ Search for existing insured 
3. ✅ Create insured if not found
4. ✅ Create submission and quote with AddQuote (AdditionalInformation working)
5. ⚠️ Update external quote ID (UpdateExternalQuoteId) - Fails but continues (non-blocking)
6. ⚠️ Store additional data (ImportNetRateXml) - Fails but continues (non-blocking)
7. ✅ Add quote option (AddQuoteOption)
8. ❌ Bind quote - "Installment billing information not found" (blocking)
9. ⏸️ Get invoice details
10. ⏸️ Store policy mapping

Legend: ✅ Working | ⚠️ Failing (non-blocking) | ❌ Failing (blocking) | 🔄 Testing | ⏸️ Not implemented
```

### Key Learnings

1. **IMS API Expectations**
   - All methods expect complex objects, not individual parameters
   - Strict type requirements (e.g., BusinessTypeID must exist in DB)
   - Date formats need to be XML-compliant (YYYY-MM-DD)
   - Some documented methods may not be available in all instances
   - AddQuote creates both submission and quote (not just quote)
   - TACSR field belongs in submission, not quote object

2. **Environment-Specific GUIDs**
   - Producer: 895E9291-CFB6-4299-8799-9AF77DF937D6
   - Underwriter: E4391D2A-58FB-4E2D-8B7D-3447D9E18C88
   - Company Location: DF35D4C7-C663-4974-A886-A1E18D3C9618
   - Line: 07564291-CBFE-4BBE-88D1-0548C88ACED4

### Summary of Current Blockers

1. **Installment Billing Error** - Primary blocker
   - BindQuote fails with "Installment billing information not found for quote ID"
   - This appears to be an IMS configuration issue
   
2. **DataAccess Parameter Format** - Secondary issue
   - Still getting "Parameters must be specified in Key/Value pairs" error
   - Prevents using the Bind method with quote option ID workaround
   - Stored procedure spGetQuoteOptions_WS likely needs to be created

### Recent Changes

1. **Implemented AddQuoteWithInsured** (Reverted - method not available)
   - Added new `create_quote_with_insured` method in QuoteService
   - Creates insured, location, submission, and quote in one atomic operation
   - Updated bind transaction flow to use this single-call approach
   - Eliminates null reference errors from multi-step process
   - **UPDATE**: Method doesn't exist in this IMS instance, reverted to multi-step approach

2. **Fixed Multiple Issues in Multi-Step Approach**
   - Fixed null reference error by changing empty strings to null in RiskInformation
   - Removed TACSR field from Quote object (only valid in Submission)
   - Fixed decimal conversion for commission rates (17.5% → 0.175)
   - Fixed RaterID foreign key constraint (changed from 1 to 0)

3. **Fixed BindQuote Method Signature**
   - BindQuote only accepts quoteGuid parameter
   - Removed policyNumber and bindDate parameters that were causing errors
   - Ready for testing

4. **Implemented AddQuoteOption**
   - Added new `add_quote_option` method in QuoteService
   - Calls AddQuoteOption with quote GUID and line GUID
   - Added to bind flow between quote creation and binding
   - This creates the necessary option ID for binding

5. **Implemented Data Storage Solutions**
   - Updated ImportNetRateXml format to try NetRate-specific structure
   - Implemented AdditionalInformation fallback for storing Triton data
   - Added `_build_additional_info` helper method
   - Triton data now stored during quote creation in AdditionalInformation field
   - Each data point stored as "TRITON:key=value" format

6. **Attempted to Fix BindQuote Installment Billing Error**
   - Tried multiple approaches:
     - Changed from BindQuote to BindQuoteWithInstallment with companyInstallmentID=-1
     - Reverted back to simple BindQuote method
   - Error persists: "Installment billing information not found"
   - Appears to be an IMS configuration issue requiring administrator intervention

7. **Added DataAccess Stored Procedure Approach**
   - Documented as Option 7 for data storage
   - Provides most flexible and scalable solution
   - Includes SQL scripts for table and stored procedure creation
   - Recommended for long-term production use

### Data Storage Options for Extra Policy Details

**Option 1: AdditionalInformation Field (Currently Implemented)**
- **Method**: Store data in the AdditionalInformation array field during quote creation
- **Pros**: 
  - No additional API calls needed
  - Guaranteed to work (part of quote object)
  - Simple key-value storage
  - No database changes required
- **Cons**: 
  - Limited to string array format
  - Not easily queryable
  - May have size limitations
- **Implementation**: Store as "TRITON:key=value" strings

**Option 2: UpdateExternalQuoteId**
- **Method**: Use dedicated method to link external system IDs
- **Pros**: 
  - Purpose-built for external system integration
  - Clean separation of concerns
  - Potentially queryable
- **Cons**: 
  - Requires stored procedure 'dbo.spAddExternalQuoteLink' (currently missing)
  - Only stores external ID, not full data set
  - Additional API call required
- **Status**: Currently failing due to missing stored procedure

**Option 3: ImportNetRateXml**
- **Method**: Store XML data associated with quote
- **Pros**: 
  - Can store structured XML data
  - Designed for rating data storage
  - May support large data sets
- **Cons**: 
  - Expects specific NetRate XML format
  - May have side effects on rating
  - Additional API call required
  - Currently failing with format errors
- **Status**: Attempting with NetRate-specific format

**Option 4: ImportExcelRater**
- **Method**: Import Excel file with data as base64Binary
- **Pros**: 
  - Can store any data encoded in Excel format
  - Supports complex data structures
  - Returns premium calculations
- **Cons**: 
  - Requires creating Excel file format
  - May trigger rating calculations
  - Additional API call required
  - Overhead of Excel file creation
- **Parameters**: QuoteGuid, FileBytes (base64), FileName, RaterID, FactorSetGuid, ApplyFees

**Option 5: Custom XML Table with IMS Stored Procedure**
- **Method**: Create custom database table and stored procedure
- **Pros**: 
  - Full control over data structure
  - Highly queryable
  - Can store complex relationships
  - Scalable solution
- **Cons**: 
  - Requires database modifications
  - Requires custom stored procedure development
  - May need IMS vendor support
  - Most complex implementation
- **Implementation**: 
  - Create table (e.g., tblTritonQuoteData)
  - Create stored procedure (e.g., spAddTritonQuoteData_WS)
  - Use ExecuteCommand from DataAccess service
- **DataAccess Details**:
  - Service: `/dataaccess.asmx`
  - Method: `ExecuteCommand` for single results
  - Method: `ExecuteDataSet` for multiple rows
  - Auto-appends '_WS' to procedure names
  - Parameters passed as name-value pairs

**Option 6: Quote Notes/Comments**
- **Method**: Store data as notes attached to quote (if available)
- **Pros**: 
  - Human-readable
  - May be visible in IMS UI
  - Simple text storage
- **Cons**: 
  - May not be structured
  - Depends on notes functionality availability
  - Not easily queryable

**Current Implementation Strategy:**
1. **Primary**: AdditionalInformation field (implemented and working)
2. **Secondary**: Continue attempting UpdateExternalQuoteId and ImportNetRateXml
3. **Future**: Consider ImportExcelRater or custom table if more robust solution needed

**Option 7: DataAccess Stored Procedure (RECOMMENDED LONG-TERM)**
- **Method**: Use IMS DataAccess service to execute custom stored procedures
- **Pros**: 
  - Most flexible and scalable solution
  - Direct database access with full control
  - Can store complex relationships and data structures
  - Highly queryable with SQL
  - Can retrieve data in multiple formats
  - Standard IMS approach for custom data
- **Cons**: 
  - Requires database modifications
  - Requires stored procedure development
  - More complex initial setup
- **Implementation Steps**:
  1. Create custom database table:
     ```sql
     CREATE TABLE tblTritonQuoteData (
         QuoteGuid UNIQUEIDENTIFIER NOT NULL,
         TransactionID VARCHAR(50),
         PriorTransactionID VARCHAR(50),
         OpportunityID VARCHAR(50),
         OpportunityType VARCHAR(50),
         PolicyFee DECIMAL(10,2),
         SurplusLinesTax DECIMAL(10,2),
         StampingFee DECIMAL(10,2),
         OtherFee DECIMAL(10,2),
         CommissionPercent DECIMAL(5,2),
         CommissionAmount DECIMAL(10,2),
         NetPremium DECIMAL(10,2),
         BasePremium DECIMAL(10,2),
         Status VARCHAR(50),
         LimitPrior VARCHAR(50),
         InvoiceDate DATE,
         CreatedDate DATETIME DEFAULT GETDATE(),
         CONSTRAINT FK_TritonQuoteData_Quote FOREIGN KEY (QuoteGuid) 
             REFERENCES tblQuotes(QuoteGuid)
     )
     ```
  2. Create stored procedure with _WS suffix:
     ```sql
     CREATE PROCEDURE spAddTritonQuoteData_WS
         @QuoteGuid UNIQUEIDENTIFIER,
         @TransactionID VARCHAR(50),
         @PriorTransactionID VARCHAR(50) = NULL,
         @OpportunityID VARCHAR(50) = NULL,
         @OpportunityType VARCHAR(50) = NULL,
         @PolicyFee DECIMAL(10,2) = NULL,
         @SurplusLinesTax DECIMAL(10,2) = NULL,
         @StampingFee DECIMAL(10,2) = NULL,
         @OtherFee DECIMAL(10,2) = NULL,
         @CommissionPercent DECIMAL(5,2) = NULL,
         @CommissionAmount DECIMAL(10,2) = NULL,
         @NetPremium DECIMAL(10,2) = NULL,
         @BasePremium DECIMAL(10,2) = NULL,
         @Status VARCHAR(50) = NULL,
         @LimitPrior VARCHAR(50) = NULL,
         @InvoiceDate DATE = NULL
     AS
     BEGIN
         INSERT INTO tblTritonQuoteData (
             QuoteGuid, TransactionID, PriorTransactionID, OpportunityID,
             OpportunityType, PolicyFee, SurplusLinesTax, StampingFee,
             OtherFee, CommissionPercent, CommissionAmount, NetPremium,
             BasePremium, Status, LimitPrior, InvoiceDate
         )
         VALUES (
             @QuoteGuid, @TransactionID, @PriorTransactionID, @OpportunityID,
             @OpportunityType, @PolicyFee, @SurplusLinesTax, @StampingFee,
             @OtherFee, @CommissionPercent, @CommissionAmount, @NetPremium,
             @BasePremium, @Status, @LimitPrior, @InvoiceDate
         )
         
         SELECT 'Success' as Result
     END
     ```
  3. Call from code using DataAccess service:
     ```python
     # In data_access_service.py
     def store_triton_data(self, quote_guid: UUID, data: Dict[str, Any]):
         params = {
             "QuoteGuid": str(quote_guid),
             "TransactionID": data.get("transaction_id"),
             "PriorTransactionID": data.get("prior_transaction_id"),
             # ... other parameters
         }
         
         # Note: _WS suffix is added automatically by ExecuteCommand
         response = self.client.service.ExecuteCommand(
             procedureName="spAddTritonQuoteData",
             namedParameters=params,
             _soapheaders=self.get_header(token)
         )
     ```
  4. Create retrieval stored procedure:
     ```sql
     CREATE PROCEDURE spGetTritonQuoteData_WS
         @QuoteGuid UNIQUEIDENTIFIER
     AS
     BEGIN
         SELECT * FROM tblTritonQuoteData
         WHERE QuoteGuid = @QuoteGuid
     END
     ```

**Recommendation for Production:**
- **Short-term**: Use AdditionalInformation (already working)
- **Medium-term**: Fix UpdateExternalQuoteId stored procedure for cleaner integration
- **Long-term**: Implement DataAccess stored procedure (Option 7) for full queryability and scalability
- **Alternative**: If Excel-based workflows exist, consider ImportExcelRater

### Next Steps

1. **Test Current Implementation**
   - Run bind transaction with BindQuoteWithInstallment fix
   - Verify bind completes successfully
   - Check that AdditionalInformation data is stored correctly
   - Monitor for any new errors

2. **Complete Bind Flow**
   - ✅ Create insured/quote 
   - ✅ Update external ID (non-blocking failure)
   - ✅ Store additional data (AdditionalInformation working)
   - ✅ Add quote option
   - ✅ Bind the quote (fixed with BindQuoteWithInstallment)
   - ⏸️ Get invoice details
   - ⏸️ Store policy mappings

3. **Implement DataAccess Solution (Future)**
   - Create data_access_service.py
   - Implement store_triton_data method
   - Create SQL scripts for database setup
   - Test stored procedure integration

4. **Update Other Transactions**
   - Apply same bind method fix to other transaction types
   - Ensure consistent data storage approach across all flows
   - Test all 5 transaction types

### Technical Debt

1. Need proper policy lookup mechanism (currently using file-based storage)
2. Error handling could be more specific
3. Need to implement retry logic for transient failures
4. Should add request/response logging for debugging

### Questions to Resolve

1. ~~Should we use `AddQuoteWithInsured` instead of separate calls?~~ - Method not available
2. ~~What's the correct date format for IMS?~~ - YYYY-MM-DD format required
3. Are there other required fields we're missing?
4. How do we handle policy lookups for existing policies?

### Current Work Status

**Implemented AddQuoteOption:**
- Added `add_quote_option` method to QuoteService
- Integrated into bind flow after quote creation
- Uses line GUID from environment
- Should fix the "Invalid OptionID specified" error

**Latest Test Results:**
- ✅ Insured created successfully
- ✅ Quote created successfully with AdditionalInformation data
- ⚠️ UpdateExternalQuoteId failed (missing stored procedure) - Non-blocking
- ⚠️ ImportNetRateXml failed (wrong format expected) - Non-blocking
- ✅ AddQuoteOption successful
- ❌ BindQuote failed with "Installment billing information not found" - tried both BindQuote and BindQuoteWithInstallment

**New Field Added:**
- `prior_transaction_id` added to TEST.json to track policy changes/renewals

**Next Steps:**
1. Test bind flow with BindQuoteWithInstallment fix
2. Expect bind to succeed now that installment billing error is resolved
3. Complete invoice retrieval after successful bind
4. Implement remaining transaction flows
5. Begin DataAccess stored procedure implementation for production

## File Structure
```
app/
├── api/
│   ├── triton.py - Main transaction endpoint
│   └── ims.py - Direct IMS endpoints
├── services/
│   ├── ims/
│   │   ├── auth_service.py - IMS authentication
│   │   ├── insured_service.py - Insured operations
│   │   ├── quote_service.py - Quote/submission operations
│   │   └── invoice_service.py - Invoice operations
│   └── triton_processor.py - Transaction orchestration
├── models/
│   ├── triton_models.py - Triton payload models
│   └── ims_models.py - IMS data models
└── utils/
    └── policy_store.py - Policy GUID storage
```