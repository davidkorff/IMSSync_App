# Triton-IMS Integration Routes Documentation

## Overview

This document outlines two integration routes for sending insurance policy data from Triton to IMS (Insurance Management System) via the RSG Integration service.

## Route 1: Push Integration (Triton → RSG Service → IMS)

### How It Works
1. **Trigger**: When specific events occur in Triton (policy binding, endorsement, cancellation)
2. **Data Collection**: Triton's `ImsTransactionService` gathers all policy data
3. **API Call**: Triton sends JSON payload to RSG Integration API
4. **Processing**: RSG Service transforms data and pushes to IMS via SOAP
5. **Response**: IMS returns policy number, RSG updates Triton

### Key Files & Code

#### Triton Side:
- `/greenhill/services/ims/transaction_service.rb` - Collects policy data
- `/greenhill/services/ims/ims_api_client.rb` - HTTP client for API calls
- `/greenhill/services/ims/integration_patches.rb` - Hooks into Triton workflows
- `/app/jobs/ims_transaction_job.rb` - Background job processor
- `/app/models/ims_transaction_log.rb` - Transaction tracking model
- `/config/initializers/ims_integration.rb` - Configuration

#### RSG Integration Side:
- `/app/api/routes.py` - API endpoints
- `/app/api/source_routes.py` - Triton-specific endpoints
- `/app/integrations/triton/transformer.py` - Data transformation
- `/app/services/ims_workflow_service.py` - IMS integration logic

### Current Status
- ✅ Triton push code complete
- ✅ RSG API endpoints ready
- ⏸️ Not active (migration not run, env vars not configured)
- ❌ IMS workflow incomplete

### Work Required
1. **Triton Team**:
   - Run migration: `rails db:migrate`
   - Configure environment variables:
     ```
     IMS_API_ENDPOINT=https://rsg-integration.example.com
     IMS_API_KEY=your-api-key
     ```
   - Enable integration feature flag

2. **RSG Integration Team**:
   - Complete IMS workflow implementation
   - Add producer/underwriter GUID resolution
   - Implement document generation
   - Add clearance checks
   - Handle BDX additional fields

---

## Route 2: Pull Integration (MySQL → RSG Service → IMS)

### How It Works
1. **Polling**: RSG Service polls Triton MySQL database
2. **Query**: Fetch pending transactions from `ims_transaction_logs` table
3. **Data Extraction**: Pull complete policy data from related tables
4. **Processing**: Transform data and push to IMS via SOAP
5. **Status Update**: Update transaction status in database

### Key Files & Code

#### RSG Integration Side:
- `/app/services/mysql_extractor.py` - Database extraction logic
- `/app/services/mysql_polling_service.py` - Polling service
- `/app/services/ims_workflow_service.py` - IMS integration logic
- `/app/services/transaction_processor.py` - Transaction processing

### Current Status
- ✅ MySQL connection working (via SSM tunnel)
- ✅ Data extraction tested and working
- ✅ Polling service code complete
- ❌ Blocked: `ims_transaction_logs` table doesn't exist
- ❌ IMS workflow incomplete

### Work Required
1. **Triton Team**:
   - Run migration to create `ims_transaction_logs` table
   - OR provide alternative trigger mechanism

2. **RSG Integration Team**:
   - Complete IMS workflow implementation (same as Route 1)
   - Map BDX fields to database tables:
     - UMR, Agreement No, Section No
     - Invoice details
     - Tax and fee breakdowns
   - Add producer/underwriter GUID resolution
   - Implement document generation

---

## Alternative: Direct Database Pull (No Logs Table)

### How It Works
1. **Direct Query**: Query opportunities table for bound policies
2. **Date Range**: Process policies within specified date range
3. **Manual Tracking**: Track processed policies locally
4. **Processing**: Same as other routes

### Implementation
- Modify polling service to query opportunities directly
- Filter by status='bound' and date range
- Maintain local tracking of processed policies

---

## Common Components (Both Routes)

### IMS Workflow Implementation
Location: `/app/services/ims_workflow_service.py`

**Current State**:
- ✅ Authentication (login)
- ✅ Find/Add Insured
- ✅ Add Submission
- ✅ Add Quote
- ✅ Add Premium
- ✅ Bind Policy
- ✅ Issue Policy

**Missing**:
- ❌ Producer GUID lookup (currently hardcoded)
- ❌ Underwriter GUID lookup (currently hardcoded)
- ❌ Document generation after binding
- ❌ Clearance checks before creating insureds
- ❌ Excel rater file generation
- ❌ Error recovery and retry logic

### Data Mapping

**Core Fields** (Available):
- Policy number, dates, status
- Insured name and address
- Producer and agency info
- Premium amounts
- Coverage limits and deductibles

**BDX Fields** (Need Mapping):
- UMR (Unique Market Reference)
- Agreement No / Section No
- Parent Broker
- Invoice Number & Date
- Commission breakdown
- Tax details (Surplus Lines, Stamping)
- Other fees

### Database Tables Used
- `opportunities` - Main policy record
- `accounts` - Insured information
- `producers` - Producer details
- `agencies` - Agency information
- `quotes` - Premium information
- `exposures` - Coverage details
- `program_classes` - Coverage types
- `territories` - State/location info
- `limits` - Coverage limits
- `deductibles` - Deductible amounts
- `quote_taxes_and_fees` - Tax breakdown
- `adjustments` - Fee information

---

## Testing Strategy

### Route 1 Testing
1. Send test JSON payload to API endpoint
2. Verify data transformation
3. Test IMS workflow with test data
4. Verify response handling

### Route 2 Testing
1. Extract sample opportunities from database
2. Transform to IMS format
3. Test IMS workflow
4. Verify status updates

### Current Testing Focus
- Using Route 2 alternative (direct pull)
- Extracting last 10 bound policies
- Testing data transformation
- Preparing for IMS workflow testing

---

## Next Steps

1. **Immediate**: Pull and analyze last 10 transactions
2. **Short-term**: Complete IMS workflow implementation
3. **Medium-term**: Add BDX field mapping
4. **Long-term**: Enable chosen route in production

---

## Report Generation Files in Triton

### Bordereaux Reports
- **Controller**: `/api/app/controllers/accounting_controller.rb`
- **Main Logic**: `/api/greenhill/accounting/generate_bordereaux_interactor.rb`
- **Data Presenter**: `/api/greenhill/accounting/opportunity_bordereaux_presenter.rb`
- **Endpoint**: `GET /accounting/export-bordereaux`
- **Features**:
  - Generates CSV with 200+ data fields
  - Supports date filtering and column selection
  - Includes midterm endorsements and claims
  - BDX fields come from `slips` table (UMR, Agreement No, Section No)

### CSV Export Files
- **Opportunities**: `/api/greenhill/http/presenters/opportunities/export_csv_presenter.rb`
- **Accounts**: `/api/greenhill/http/presenters/accounts/export_csv_presenter.rb`
- **Agencies**: `/api/greenhill/http/presenters/agencies/export_csv_presenter.rb`
- **Producers**: `/api/greenhill/http/presenters/producers/export_csv_presenter.rb`

### Claims/Loss Runs
- **Generator**: `/api/greenhill/claims/loss_runs_generator.rb`
- **Exporter**: `/api/greenhill/claims/export_loss_runs_interactor.rb`
- **Excel Parser**: `/api/greenhill/claims/claims_parser.rb` (uses `roo` gem)

### Key Data Models
- **Slip**: Contains BDX fields (UMR, agreement_no, section_no, coverholder_name)
- **Opportunity**: Core policy/submission model
- **Quote**: Premium and financial details
- **Claim**: Claims information
- **BrokerInformation**: Surplus lines broker data

### BDX Field Sources
The `slips` table contains the key BDX fields needed for bordereaux reporting:
- `unique_market_reference` (UMR)
- `agreement_no` (Agreement Number)
- `section_no` (Section Number)
- `coverholder_name`
- `commission_percent`

Slips are linked to programs and filtered by opportunity effective date and section number.

---

## Current Implementation Status (Updated)

### Database Access
- ✅ **Triton-Dev Database**: Connected via AWS SSM tunnel (localhost:13307)
- ✅ **MySQL Extraction**: Complete BDX data extraction working
- ✅ **All Tables Accessible**: opportunities, accounts, producers, agencies, quotes, slips, etc.

### Transaction Type Detection
Triton determines transaction types based on opportunity status and relationships:

**Transaction Types:**
- **NEW BUSINESS (BINDER)**: `status = 'Bound'` + `previous_opportunity_id = NULL`
- **RENEWAL**: `status = 'Bound'` + `previous_opportunity_id` exists
- **CANCELLATION**: `status = 'Cancelled'` OR `cancelled_date` is set
- **MIDTERM ENDORSEMENT**: Records in `opportunity_midterm_endorsements` table
- **DECLINED/LOST**: `status = 'Declined'` or `status = 'Lost'`

### Complete BDX Field Mapping
Successfully extracted all bordereaux fields from triton-dev:

**✅ Available Fields:**
- Policy information (numbers, dates, status, business type)
- Complete insured details (name, address, DBA, business class)
- Producer/agency information (including parent agency)
- Financial data (premiums, fees, taxes, commissions)
- Coverage details (limits, deductibles, territories, rating units)
- Underwriter assignments (primary + assistant)
- Surplus lines broker information
- BDX fields from slips table (UMR, Agreement No, Section No, Coverholder)
- Territory factors for tax calculations
- Endorsement and claims counts
- Policy lifecycle tracking (bound, paid, sent dates)

**❌ Missing/Needs Calculation:**
- Commission amounts (need to calculate: premium × commission_percent)
- Net premium (gross_premium - commission_amount)
- Some slip data not populated for all programs
- Producer/Underwriter GUIDs for IMS (need lookup logic)

### Data Quality Observations
- **Test Data**: Some bound dates show 2062 (likely test records)
- **Commission Rates**: Many showing 0% (may need program-specific lookup)
- **Territory Data**: Mixed availability across different policies
- **Invoice Data**: Recent policies have complete invoice information
- **BDX Fields**: Available in slips table but not all programs have slips configured

### Next Implementation Steps
1. **Complete IMS Workflow**: Finish binding transaction processing
2. **Add GUID Resolution**: Producer/underwriter lookup from IMS
3. **Handle Transaction Types**: Different workflows for binders vs endorsements vs cancellations
4. **BDX Field Joining**: Properly join opportunities with slips table for UMR/Agreement data
5. **Commission Calculation**: Implement proper commission amount calculations
6. **Error Handling**: Add retry logic and error recovery
7. **Testing**: End-to-end testing with actual triton-dev data