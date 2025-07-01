# Documentation Contradictions and Corrections

This document identifies contradictions found in the original documentation and provides the correct information based on code analysis.

## 1. API Endpoint Contradictions

### ❌ Incorrect Documentation
Several documents mentioned different endpoint paths:
- `api/triton/api/transactions`
- `/transactions/new`
- `api/transactions/new`

### ✅ Correct Endpoints (from code)
Based on `app/api/source_routes.py` and `app/main.py`:

**Source-Specific Endpoints:**
- `POST /api/triton/transaction/{transaction_type}` - Triton transactions
- `POST /api/xuber/transaction/{transaction_type}` - Xuber transactions

**Generic Endpoints:**
- `POST /api/transaction/{transaction_type}` - Any source via query parameter

Transaction types: `new`, `update`, `cancellation`, `endorsement`, `reinstatement`

## 2. Configuration Contradictions

### ❌ Inconsistent Environment Variables
Different documents showed varying environment variable names and formats.

### ✅ Correct Configuration (from `app/core/config.py`)
- **CORS_ORIGINS**: Must be JSON array format: `'["https://domain.com"]'`
- **API_KEYS**: JSON array format: `'["key1", "key2"]'`
- **DEFAULT_ENVIRONMENT**: Options are `"ims_one"` or `"iscmga_test"`

## 3. Database Requirements

### ❌ Conflicting Information
Some documents mentioned PostgreSQL, others MySQL, some both.

### ✅ Actual Requirements
1. **SQLite**: Used for transaction storage (automatic, no setup needed)
2. **MySQL**: Required only for:
   - Triton database polling (remote)
   - IMS transaction logs (local)
3. **PostgreSQL**: Not used

## 4. Authentication Headers

### ❌ Inconsistent Header Names
Documentation showed various header combinations.

### ✅ Correct Headers (from code)
**Generic Endpoints:**
```
X-API-Key: your-api-key
```

**Triton Webhook:**
```
X-API-Key: triton-specific-key
X-Client-ID: triton (optional)
X-Triton-Version: version (optional)
```

## 5. Transaction Processing Flow

### ❌ Synchronous vs Asynchronous Confusion
Some documents implied synchronous processing.

### ✅ Actual Flow
All transaction processing is **asynchronous**:
1. API accepts transaction → Returns transaction ID immediately
2. Background task processes through IMS workflow
3. Client must poll `/api/transaction/{id}` for status

## 6. Required Software

### ❌ Overly Complex Requirements
Deployment_Requirements.md listed many unnecessary components.

### ✅ Actual Minimum Requirements
**For API Service:**
- Python 3.11
- pip packages from requirements.txt
- SQLite (included with Python)

**For Triton Polling (optional):**
- MySQL client libraries
- Access to Triton MySQL database

**For Production:**
- Reverse proxy (Nginx/Apache)
- SSL certificates

## 7. IMS Integration Steps

### ❌ Conflicting Workflow Orders
Different documents showed different sequences.

### ✅ Correct IMS Workflow (from `ims_workflow_service.py`)
1. **Login** → Get authentication token
2. **Find/Create Insured** → Check existence first
3. **Create Submission** → Link insured to producer
4. **Create Quote** → Policy details
5. **Add Quote Options** → For rating
6. **Apply Premium** → From source or calculate
7. **Bind** → Convert to policy
8. **Issue** → Finalize policy

## 8. Docker vs Direct Deployment

### ❌ Conflicting Recommendations
Some documents strongly recommended Docker, others direct Python.

### ✅ Both Are Valid Options
- **Docker**: Better for isolation, easier deployment
- **Direct Python**: Simpler for debugging, lower overhead
- Choice depends on infrastructure and team expertise

## 9. Field Mapping

### ❌ Incomplete Mapping Information
Field mapping was scattered across documents.

### ✅ Consolidated Mapping
See [Field Mapping Guide](./04_Integration_Guides/04_Field_Mapping.md) for complete reference.

Key corrections:
- Producer lookup returns `ProducerLocationGuid` (use for both contact and location)
- Underwriter lookup requires custom stored procedure
- External ID stored via `UpdateExternalQuoteId`

## 10. Testing Procedures

### ❌ Missing Test Scripts
Documentation referenced test scripts that weren't clearly identified.

### ✅ Available Test Scripts
- `test_ims_login.py` - Verify IMS connectivity
- `test_producer_search.py` - Find producer GUIDs
- `test_triton_integration.py` - Full integration test
- `run_mysql_polling.py` - Triton polling service

## Summary of Key Corrections

1. **Use correct API endpoints** - See API Reference documentation
2. **Follow proper JSON format** for array environment variables
3. **MySQL only needed** for Triton polling and transaction logs
4. **All processing is asynchronous** - Poll for status
5. **Both deployment methods valid** - Choose based on needs
6. **Test scripts included** - Use for validation
7. **Producer search returns location GUID** - Use for both fields
8. **Underwriter lookup needs custom procedure** - Not built-in

## Recommendations

1. Always refer to code for authoritative endpoint definitions
2. Use `.env.example` as template for configuration
3. Test with included scripts before production deployment
4. Follow consolidated documentation in Documentation_Organized folder
5. When in doubt, check the source code for actual implementation