# RSG Integration API Documentation

## Overview

The RSG Integration service provides a REST API for receiving and processing insurance transaction data from external systems (primarily Triton). This service processes transactions asynchronously and integrates with the IMS (Insurance Management System) platform.

## Base URLs

| Environment | URL | Purpose |
|-------------|-----|---------|
| Development | `http://localhost:8000` | Local development testing |
| Staging | `https://api-staging.rsgims.com` | Pre-production validation |
| Production | `https://api.rsgims.com` | Production environment |

## Authentication

All API requests require authentication using an API key. There are two types of API keys:

### 1. Standard API Key
- **Header**: `X-API-Key`
- **Default Test Key**: `test_api_key`
- **Usage**: General API endpoints

### 2. Triton-Specific API Key
- **Header**: `X-API-Key`
- **Additional Header**: `X-Client-Id`
- **Default Test Key**: `triton_test_key`
- **Default Client ID**: `triton`
- **Usage**: Triton-specific endpoints

## API Endpoints

### 1. Create New Transaction

**Endpoint**: `POST /api/transaction/new`

Creates a new insurance policy transaction.

**Headers**:
```
Content-Type: application/json
X-API-Key: your-api-key
```

**Request Body**:
```json
{
  "policy_number": "TRI-12345",
  "effective_date": "2025-06-01",
  "expiration_date": "2026-06-01",
  "bound_date": "2025-05-15",
  "program": "Test Program",
  "line_of_business": "General Liability",
  "state": "TX",
  "insured": {
    "name": "Test Company LLC",
    "dba": "Test Co",
    "contact": {
      "name": "John Smith",
      "email": "john@example.com",
      "phone": "555-123-4567",
      "address": "123 Main St",
      "city": "Austin",
      "state": "TX",
      "zip_code": "78701"
    },
    "tax_id": "12-3456789",
    "business_type": "LLC"
  },
  "locations": [
    {
      "address": "123 Main St",
      "city": "Austin",
      "state": "TX",
      "zip_code": "78701",
      "country": "USA",
      "description": "Main Office"
    }
  ],
  "producer": {
    "name": "ABC Insurance Agency",
    "contact": {
      "name": "Jane Doe",
      "email": "jane@example.com",
      "phone": "555-987-6543"
    },
    "commission": 15.0
  },
  "underwriter": "Bob Johnson",
  "coverages": [
    {
      "type": "General Liability",
      "limit": 1000000.0,
      "deductible": 5000.0,
      "premium": 10000.0
    }
  ],
  "premium": 10000.0,
  "billing_type": "Agency Bill",
  "additional_data": {
    "source_system": "triton",
    "source_id": "TRI-12345-1"
  }
}
```

**Response**:
```json
{
  "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "new transaction created successfully and queued for processing"
}
```

### 2. Update Existing Policy

**Endpoint**: `POST /api/transaction/update`

Updates an existing policy.

**Headers**:
```
Content-Type: application/json
X-API-Key: your-api-key
```

**Request Body**:
```json
{
  "policy_number": "TRI-12345",
  "updates": {
    "premium": 12000.0,
    "coverages": [
      {
        "type": "General Liability",
        "limit": 1000000.0,
        "deductible": 5000.0,
        "premium": 12000.0
      }
    ]
  }
}
```

### 3. Check Transaction Status

**Endpoint**: `GET /api/transaction/{transaction_id}`

Retrieves the current status of a transaction.

**Headers**:
```
X-API-Key: your-api-key
```

**Response**:
```json
{
  "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "ims_status": "success",
  "message": "Transaction status: completed"
}
```

### 4. Search Transactions

**Endpoint**: `GET /api/transactions`

Search for transactions based on various criteria.

**Headers**:
```
X-API-Key: your-api-key
```

**Query Parameters**:
- `source`: Filter by source system (e.g., "triton")
- `status`: Filter by transaction status
- `external_id`: Filter by external ID
- `start_date`: Filter by start date (YYYY-MM-DD)
- `end_date`: Filter by end date (YYYY-MM-DD)
- `limit`: Number of results to return (default: 10, max: 100)
- `offset`: Number of results to skip (default: 0)

**Response**:
```json
{
  "total": 25,
  "offset": 0,
  "limit": 10,
  "results": [
    {
      "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
      "external_id": "TRI-12345",
      "type": "new",
      "source": "triton",
      "status": "completed",
      "received_at": "2025-05-29T10:30:00",
      "processed_at": "2025-05-29T10:30:15",
      "ims_status": "success",
      "policy_number": "TRI-12345"
    }
  ]
}
```

### 5. Health Check

**Endpoint**: `GET /api/health`

Check if the service is healthy and running.

**Response**:
```json
{
  "status": "healthy"
}
```

## Triton-Specific Endpoints

### 1. Triton Transaction Submission

**Endpoint**: `POST /api/triton/transaction/{transaction_type}`

Process a Triton-specific transaction.

**Transaction Types**:
- `new`: New policy binding
- `endorsement`: Policy endorsement
- `cancellation`: Policy cancellation

**Headers**:
```
Content-Type: application/json
X-API-Key: triton_test_key
X-External-ID: TRI-12345 (optional)
```


## Transaction Processing

### Transaction States

1. **pending**: Transaction received and queued
2. **processing**: Currently being processed
3. **completed**: Successfully processed
4. **failed**: Processing failed

### Processing Flow

1. Transaction is received via API
2. Assigned unique transaction ID
3. Queued for asynchronous processing
4. Data transformed to IMS format
5. Submitted to IMS via SOAP API
6. Status updated based on IMS response

## Error Handling

### HTTP Status Codes

- `200`: Success
- `201`: Created
- `400`: Bad Request (invalid data)
- `401`: Unauthorized (invalid API key)
- `404`: Not Found
- `500`: Internal Server Error

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

## Rate Limits

- **Default**: 60 requests per minute per API key
- **Triton**: 100 requests per minute per API key

## Data Formats

### Supported Content Types

- `application/json`: JSON format (recommended)
- `application/xml`: XML format
- `text/xml`: XML format

### Date Format

All dates should be in ISO 8601 format: `YYYY-MM-DD`

## Testing

### Example Using cURL

**Create New Transaction**:
```bash
curl -X POST http://localhost:8000/api/transaction/new \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test_api_key" \
  -d '{
    "policy_number": "TEST-001",
    "effective_date": "2025-06-01",
    "expiration_date": "2026-06-01",
    "bound_date": "2025-05-29",
    "insured": {
      "name": "Test Company",
      "contact": {
        "email": "test@example.com"
      }
    },
    "premium": 5000.0
  }'
```

**Check Status**:
```bash
curl -X GET http://localhost:8000/api/transaction/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-API-Key: test_api_key"
```

### Example Using Python

See `test_client.py` for a complete Python example:

```python
import requests
import json

# Configuration
API_URL = "http://localhost:8000"
API_KEY = "test_api_key"

# Create transaction
headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

policy_data = {
    "policy_number": "TEST-001",
    # ... rest of policy data
}

response = requests.post(
    f"{API_URL}/api/transaction/new",
    headers=headers,
    json=policy_data
)

print(response.json())
```

## Configuration

### Environment Variables

The service uses the following environment variables:

```bash
# API Keys
API_KEYS=["test_api_key", "prod_key_1"]
TRITON_API_KEYS=["triton_test_key"]
TRITON_CLIENT_IDS=["triton"]

# IMS Credentials
IMS_ONE_USERNAME=username
IMS_ONE_PASSWORD=encrypted_password
ISCMGA_TEST_USERNAME=username
ISCMGA_TEST_PASSWORD=encrypted_password

# Triton Configuration
TRITON_DEFAULT_PRODUCER_GUID=00000000-0000-0000-0000-000000000000
TRITON_PRIMARY_LINE_GUID=00000000-0000-0000-0000-000000000000
TRITON_EXCESS_LINE_GUID=00000000-0000-0000-0000-000000000000
```

### Default Credentials

**Development Environment**:
- API Key: `test_api_key`
- Triton API Key: `triton_test_key`
- IMS Username: `dkorff`
- IMS Password: `kCeTLc2bxqOmG72ZBvMFkA==` (encrypted)

## Monitoring

### Transaction Logs

All transactions are logged with:
- Transaction ID
- External ID (if provided)
- Source system
- Status changes
- Processing errors

### Database

Transactions are stored in SQLite database (`transactions.db`) with full audit trail.

## Support

For technical support or questions:

**Integration Technical Lead**: David Korff  
**Email**: dkorff@rsg.com  

## Appendix

### Required Fields for New Policy

Minimum required fields:
- `policy_number`
- `effective_date`
- `expiration_date`
- `insured.name`
- `insured.contact.email`
- `premium`

### IMS Integration Details

The service integrates with IMS using:
- SOAP Web Services
- Triple DES encrypted passwords
- Environment-specific endpoints
- Asynchronous processing

### Transaction Volume Expectations

- New policies: 50-100 per day
- Endorsements: 20-50 per day
- Cancellations: 5-10 per day

Processing SLA: 5 minutes per transaction