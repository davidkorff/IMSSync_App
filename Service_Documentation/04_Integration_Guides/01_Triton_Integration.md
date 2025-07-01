# Triton Integration Guide

This guide provides complete instructions for integrating Triton with the RSG Integration Service.

## Overview

The Triton integration supports two methods of data ingestion:
1. **Database Polling**: Automatically polls Triton MySQL database for new transactions
2. **Webhook/API**: Receives transactions via HTTP POST

## Integration Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Triton MySQL   │────▶│  Polling Service │────▶│             │
└─────────────────┘     └──────────────────┘     │             │
                                                  │   RSG API   │────▶ IMS
┌─────────────────┐     ┌──────────────────┐     │             │
│ Triton Webhook  │────▶│  API Endpoints   │────▶│             │
└─────────────────┘     └──────────────────┘     └─────────────┘
```

## Configuration

### Required Environment Variables

Add these to your `.env` file:

```env
# Triton API Keys
TRITON_API_KEYS='["your-triton-api-key-here"]'
TRITON_CLIENT_IDS='["triton"]'

# Triton Database (for polling)
TRITON_MYSQL_HOST="triton-staging.ctfcgagzmyca.us-east-1.rds.amazonaws.com"
TRITON_MYSQL_PORT="3306"
TRITON_MYSQL_DATABASE="triton_staging"
TRITON_MYSQL_USER="your_mysql_user"
TRITON_MYSQL_PASSWORD="your_mysql_password"

# IMS Configuration for Triton
TRITON_DEFAULT_PRODUCER_GUID="12345678-1234-1234-1234-123456789012"
TRITON_PRIMARY_LINE_GUID="23456789-2345-2345-2345-234567890123"
TRITON_EXCESS_LINE_GUID="34567890-3456-3456-3456-345678901234"

# Rater Configuration
TRITON_PRIMARY_RATER_ID=101
TRITON_PRIMARY_FACTOR_SET_GUID="45678901-4567-4567-4567-456789012345"
TRITON_EXCESS_RATER_ID=102
TRITON_EXCESS_FACTOR_SET_GUID="56789012-5678-5678-5678-567890123456"

# Polling Settings
ENABLE_TRITON_POLLING="true"
POLL_INTERVAL_SECONDS=60
POLL_BATCH_SIZE=10
```

### Getting Required GUIDs

1. **Producer GUID**:
   ```bash
   python test_producer_search.py
   # Search for your Triton producer
   # Note the ProducerLocationGuid
   ```

2. **Line GUIDs**:
   ```sql
   -- Query IMS database
   SELECT LineGuid, LineName 
   FROM tblLines 
   WHERE LineName LIKE '%Allied Healthcare%';
   ```

3. **Rater Configuration**:
   - Contact IMS administrator for rater IDs
   - Request factor set GUIDs for your program

## Method 1: Database Polling

### Setup

1. **Configure Database Access**:
   ```bash
   # Test connection
   mysql -h $TRITON_MYSQL_HOST -P $TRITON_MYSQL_PORT \
         -u $TRITON_MYSQL_USER -p$TRITON_MYSQL_PASSWORD \
         -D $TRITON_MYSQL_DATABASE -e "SELECT 1"
   ```

2. **Using AWS SSM Tunnel** (if direct access not available):
   ```bash
   # Set in .env
   USE_SSM_TUNNEL="true"
   SSM_INSTANCE_ID="i-xxxxxxxxxxxxxxxxx"
   SSM_LOCAL_PORT=13306
   
   # Update MySQL host for tunnel
   TRITON_MYSQL_HOST="localhost"
   TRITON_MYSQL_PORT="13306"
   ```

3. **Start Polling Service**:
   ```bash
   python run_mysql_polling.py
   ```

### How Polling Works

1. Service polls Triton database every 60 seconds
2. Queries for new policies since last check
3. Transforms Triton data to IMS format
4. Processes through IMS workflow
5. Updates status in tracking table

### Monitoring Polling

```bash
# Watch polling logs
tail -f ims_integration.log | grep "Polling"

# Check processing status
mysql -e "SELECT * FROM ims_transaction_logs WHERE source_system='triton' ORDER BY created_at DESC LIMIT 10"
```

## Method 2: Webhook/API Integration

### Endpoint Configuration

Triton can send transactions to these endpoints:

1. **Source-Specific Endpoint**:
   ```
   POST /api/triton/transaction/{transaction_type}
   Headers:
     X-API-Key: your-triton-api-key
     Content-Type: application/json
   ```

2. **Generic Endpoint**:
   ```
   POST /api/transaction/{transaction_type}?source=triton
   Headers:
     X-API-Key: your-api-key
     Content-Type: application/json
   ```

### Transaction Types

- `binding` - New policy or renewal
- `midterm_endorsement` - Policy changes
- `cancellation` - Policy cancellation

### Sample Requests

#### Binding Transaction
```bash
curl -X POST https://api.rsgims.com/api/triton/transaction/new \
  -H "X-API-Key: your-triton-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_type": "binding",
    "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
    "transaction_date": "2025-01-23T10:00:00Z",
    "policy_number": "AHC-12345",
    "effective_date": "2025-02-01T00:00:00Z",
    "expiration_date": "2026-02-01T00:00:00Z",
    "is_renewal": false,
    "account": {
      "id": "TRITON-ACCT-001",
      "name": "Healthcare Clinic LLC",
      "street_1": "123 Medical Center Dr",
      "city": "Dallas",
      "state": "TX",
      "zip": "75201"
    },
    "producer": {
      "name": "Smith Insurance Agency",
      "agency": {
        "id": "AGENCY-001",
        "name": "Smith Insurance Agency"
      }
    },
    "program": {
      "id": "AHC-PRIMARY",
      "name": "Allied Healthcare Primary"
    },
    "premium": {
      "annual_premium": 10000.00,
      "policy_fee": 250.00,
      "grand_total": 10250.00
    }
  }'
```

#### Response
```json
{
  "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "received",
  "message": "Triton new transaction processed: completed",
  "ims_status": "issued",
  "ims_details": {
    "policy_number": "AHC-12345",
    "insured_guid": "abc123-def456-ghi789"
  }
}
```

## Data Mapping

### Triton to IMS Field Mapping

| Triton Field | IMS Field | Notes |
|--------------|-----------|-------|
| `account.name` | `CorporationName` | Business name |
| `account.street_1` | `Address1` | Primary address |
| `account.city` | `City` | |
| `account.state` | `State` | 2-letter code |
| `account.zip` | `Zip` | 5 digits |
| `policy_number` | `ExternalQuoteId` | Stored for reference |
| `effective_date` | `Effective` | ISO to date format |
| `expiration_date` | `Expiration` | ISO to date format |
| `premium.annual_premium` | `Amount` | Direct pass-through |
| `producer.name` | Used for lookup | ProducerSearch |
| `program.name` | Used for line selection | Maps to Line GUID |

### Special Handling

1. **Producer Resolution**:
   - System searches by producer name
   - Falls back to default if not found
   - Configure default in environment

2. **Premium Pass-Through**:
   - Premium amounts from Triton used directly
   - No calculation in IMS
   - Supports multiple premium components

3. **Program Mapping**:
   - "Allied Healthcare Primary" → Primary Line GUID
   - "Allied Healthcare Excess" → Excess Line GUID

## Testing Triton Integration

### 1. Test Database Connection
```bash
python test_triton_db_connection.py
```

### 2. Test Single Transaction
```python
# test_triton_transaction.py
import requests

transaction = {
    "transaction_type": "binding",
    "policy_number": "TEST-001",
    "account": {"name": "Test Clinic"},
    "effective_date": "2025-02-01",
    "premium": {"annual_premium": 5000}
}

response = requests.post(
    "http://localhost:8000/api/triton/transaction/new",
    headers={"X-API-Key": "your-triton-api-key"},
    json=transaction
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

### 3. Test Polling Service
```bash
# Set test mode in .env
POLL_INTERVAL_SECONDS=10  # Faster for testing

# Run service
python run_mysql_polling.py

# Check logs
tail -f ims_integration.log | grep -E "(Polling|Processing|Completed)"
```

## Monitoring & Troubleshooting

### Common Issues

1. **Database Connection Failed**:
   - Check network connectivity
   - Verify credentials
   - Test firewall rules
   - Try SSM tunnel if needed

2. **Producer Not Found**:
   - Run producer search
   - Update default GUID
   - Check producer name spelling

3. **Invalid Premium**:
   - Ensure premium > 0
   - Check decimal format
   - Verify charge codes

### Monitoring Commands

```bash
# Check recent Triton transactions
curl "http://localhost:8000/api/transactions?source=triton&limit=10" \
  -H "X-API-Key: your-api-key"

# View specific transaction
curl "http://localhost:8000/api/transaction/{id}" \
  -H "X-API-Key: your-api-key"

# Database monitoring (if using polling)
mysql -e "
  SELECT COUNT(*) as pending 
  FROM triton_policies 
  WHERE processed = 0 
  AND created_at > DATE_SUB(NOW(), INTERVAL 1 DAY)
"
```

## Production Deployment

### Checklist
- [ ] Production database credentials configured
- [ ] SSL/TLS enabled for API endpoints
- [ ] Monitoring alerts configured
- [ ] Backup procedures in place
- [ ] Error notification setup

### Performance Tuning

1. **Polling Optimization**:
   ```env
   POLL_BATCH_SIZE=50  # Increase for higher volume
   POLL_INTERVAL_SECONDS=300  # Adjust based on volume
   ```

2. **Connection Pooling**:
   ```python
   # Automatically handled, but can tune:
   MYSQL_POOL_SIZE=5
   MYSQL_POOL_TIMEOUT=30
   ```

3. **API Rate Limiting**:
   - Default: 1000 requests/hour per API key
   - Contact support for increases

## Support

For Triton-specific issues:
1. Check [Troubleshooting Guide](../07_Operations/03_Troubleshooting.md)
2. Review transaction logs
3. Contact integration support

## Next Steps

1. Configure all required GUIDs
2. Test with sample transactions
3. Set up monitoring
4. Plan production rollout
5. Document any custom mappings