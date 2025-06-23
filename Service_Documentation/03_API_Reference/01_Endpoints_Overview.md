# API Endpoints Overview

This document provides a comprehensive overview of all available endpoints in the RSG Integration API.

## Base URL

The API is typically deployed at:
- **Production**: `https://api.rsgims.com`
- **Staging**: `https://api-staging.rsgims.com`
- **Development**: `http://localhost:8000`

## Authentication

All endpoints (except `/api/health`) require API key authentication:

```http
X-API-Key: your-api-key-here
```

For source-specific endpoints, additional headers may be required:
```http
X-API-Key: source-specific-key
X-Client-ID: source-identifier
```

## Endpoint Categories

### 1. Health & Monitoring

#### Health Check
```http
GET /api/health
```
- **Authentication**: Not required
- **Purpose**: Check service status and version
- **Response**: Service health information

### 2. Generic Transaction Endpoints

These endpoints accept transactions from any configured source system.

#### Create Transaction
```http
POST /api/transaction/{transaction_type}
```
- **Path Parameters**:
  - `transaction_type`: `new`, `update`, `cancellation`, `endorsement`, `reinstatement`
- **Query Parameters**:
  - `source`: Source system identifier (default: "triton")
  - `external_id`: Optional external reference ID
  - `sync_mode`: Process synchronously and wait for IMS result (default: true)
- **Body**: JSON or XML transaction data
- **Response**: Transaction ID and status

#### Get Transaction Status
```http
GET /api/transaction/{transaction_id}
```
- **Path Parameters**:
  - `transaction_id`: UUID of the transaction
- **Response**: Detailed transaction status and processing information, including:
  - Transaction status
  - IMS processing status
  - IMS details (when available): policy number, GUIDs, processing logs
  - Error messages

#### Search Transactions
```http
GET /api/transactions
```
- **Query Parameters**:
  - `source`: Filter by source system
  - `status`: Filter by status
  - `transaction_type`: Filter by type
  - `start_date`: Filter by date range (ISO format)
  - `end_date`: Filter by date range (ISO format)
  - `external_id`: Filter by external reference
  - `limit`: Maximum results (default: 100)
  - `offset`: Pagination offset
- **Response**: List of transactions matching criteria

### 3. Source-Specific Endpoints

#### Triton Endpoints

##### Create Triton Transaction
```http
POST /api/triton/transaction/{transaction_type}
```
- **Path Parameters**:
  - `transaction_type`: `new`, `update`, `cancellation`, `endorsement`, `reinstatement`
- **Query Parameters**:
  - `sync_mode`: Process synchronously and wait for IMS result (default: true)
- **Headers**:
  - `X-API-Key`: Triton-specific API key
  - `X-Client-ID`: "triton" (optional)
- **Body**: Triton-formatted JSON/XML data
- **Response**: Transaction ID and complete IMS processing result (when sync_mode=true)


#### Xuber Endpoints

##### Create Xuber Transaction
```http
POST /api/xuber/transaction/{transaction_type}
```
- **Path Parameters**:
  - `transaction_type`: `new`, `update`, `cancellation`
- **Headers**:
  - `X-API-Key`: Xuber-specific API key
- **Body**: Xuber-formatted JSON data
- **Response**: Transaction ID and status

## Request/Response Examples

### Example: Create New Policy (Generic)
```bash
curl -X POST https://api.rsgims.com/api/transaction/new?source=triton \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "policy_number": "TEST-001",
    "insured": {
      "name": "Test Company LLC",
      "address": "123 Main St",
      "city": "Dallas",
      "state": "TX",
      "zip": "75201"
    },
    "effective_date": "2025-01-01",
    "expiration_date": "2026-01-01",
    "premium": 5000.00
  }'
```

**Response:**
```json
{
  "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "received",
  "message": "Transaction created and queued for processing"
}
```

### Example: Create New Policy with Synchronous Processing
```bash
curl -X POST "https://api.rsgims.com/api/transaction/new?source=triton&sync_mode=true" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "policy": {
      "policy_number": "TEST-001",
      "insured_name": "Test Company LLC",
      "insured_address": "123 Main St",
      "insured_city": "Dallas",
      "insured_state": "TX",
      "insured_zip": "75201",
      "effective_date": "2025-01-01",
      "expiration_date": "2026-01-01",
      "gross_premium": 5000.00
    }
  }'
```

**Response (with sync_mode=true):**
```json
{
  "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "ims_status": "issued",
  "message": "Transaction successfully processed in IMS. Policy number: TEST-001",
  "ims_details": {
    "processing_status": "issued",
    "policy_number": "TEST-001",
    "insured_guid": "abc123-def456-ghi789",
    "submission_guid": "jkl012-mno345-pqr678",
    "quote_guid": "stu901-vwx234-yza567",
    "error": null,
    "processing_logs": [
      "[2025-01-23T10:30:00] Processing insured data",
      "[2025-01-23T10:30:01] Created insured with GUID: abc123-def456-ghi789",
      "[2025-01-23T10:30:02] Created submission with GUID: jkl012-mno345-pqr678",
      "[2025-01-23T10:30:03] Created quote with GUID: stu901-vwx234-yza567",
      "[2025-01-23T10:30:04] Policy issued: TEST-001"
    ]
  }
}
```

### Example: Triton-Specific Endpoint
```bash
curl -X POST https://api.rsgims.com/api/triton/transaction/new \
  -H "X-API-Key: triton-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_type": "binding",
    "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
    "policy_number": "AHC-12345",
    "account": {
      "name": "Healthcare Provider LLC"
    },
    "effective_date": "2025-01-01",
    "premium": {
      "annual_premium": 10000.00
    }
  }'
```

### Example: Check Transaction Status
```bash
curl https://api.rsgims.com/api/transaction/550e8400-e29b-41d4-a716-446655440000 \
  -H "X-API-Key: your-api-key"
```

**Response:**
```json
{
  "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "source": "triton",
  "type": "new",
  "status": "completed",
  "external_id": "TRITON-12345",
  "created_at": "2025-01-23T10:30:00Z",
  "updated_at": "2025-01-23T10:35:00Z",
  "ims_processing": {
    "status": "issued",
    "insured": {
      "guid": "abc123...",
      "created_at": "2025-01-23T10:31:00Z"
    },
    "quote": {
      "guid": "def456...",
      "policy_number": "AHC-12345",
      "created_at": "2025-01-23T10:32:00Z"
    }
  },
  "errors": []
}
```

### Example: Search Transactions
```bash
curl "https://api.rsgims.com/api/transactions?source=triton&status=completed&start_date=2025-01-01" \
  -H "X-API-Key: your-api-key"
```

## Status Codes

### Success Codes
- `200 OK`: Request processed successfully
- `201 Created`: Transaction created successfully
- `202 Accepted`: Transaction accepted for processing

### Client Error Codes
- `400 Bad Request`: Invalid request format or data
- `401 Unauthorized`: Invalid or missing API key
- `403 Forbidden`: Valid API key but insufficient permissions
- `404 Not Found`: Transaction or resource not found
- `422 Unprocessable Entity`: Valid format but business logic error

### Server Error Codes
- `500 Internal Server Error`: Server-side processing error
- `502 Bad Gateway`: IMS connection error
- `503 Service Unavailable`: Service temporarily unavailable
- `504 Gateway Timeout`: IMS request timeout

## Rate Limiting

- **Default Rate Limit**: 1000 requests per hour per API key
- **Burst Limit**: 100 requests per minute
- **Headers Returned**:
  - `X-RateLimit-Limit`: Total allowed requests
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Unix timestamp when limit resets

## Error Response Format

All error responses follow this format:
```json
{
  "status_code": 400,
  "detail": "Invalid transaction data",
  "errors": [
    {
      "field": "insured.name",
      "message": "Required field missing"
    },
    {
      "field": "effective_date",
      "message": "Date must be in future"
    }
  ]
}
```

## Best Practices

1. **Always include API key** in request headers
2. **Use appropriate content-type** header (application/json or application/xml)
3. **Include external_id** for easier transaction tracking
4. **Implement retry logic** for transient errors (5xx codes)
5. **Check transaction status** asynchronously after submission
6. **Log transaction IDs** for troubleshooting
7. **Validate data** before submission to avoid 400 errors

## Webhook Configuration

For push-based integrations, configure your system to send to:
- **Triton**: `/api/triton/transaction/{type}`
- **Xuber**: `/api/xuber/transaction/{type}`
- **Generic**: `/api/transaction/{type}?source={your_source}`

## Testing

Use these endpoints for integration testing:
1. Start with `/api/health` to verify connectivity
2. Submit a test transaction to validate authentication
3. Check status to verify processing
4. Search transactions to verify data flow