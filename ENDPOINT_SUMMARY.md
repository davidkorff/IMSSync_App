# Triton-IMS Integration Endpoints

## 🎯 Main Endpoints (Use These!)

### 1. **Triton Transaction Endpoint** 
```
POST /api/triton/transaction/new
```

**Purpose**: Process ALL Triton transactions (binding, cancellation, endorsement, reinstatement)
**Note**: The transaction type is determined by the `transaction_type` field in the JSON payload

**Headers**:
- `Content-Type: application/json`
- `X-API-Key: {your_api_key}`

**Query Parameters**:
- `sync_mode` (optional): `true` (default) or `false` for async processing

**Supports both structures**:

#### Nested Structure (Modern)
```json
{
  "transaction_type": "binding",
  "transaction_id": "TRN-12345",
  "policy_number": "POL-2024-001",
  "account": {
    "name": "ABC Company",
    "street_1": "123 Main St",
    "city": "Dallas",
    "state": "TX",
    "zip": "75201"
  },
  "producer": {
    "name": "XYZ Agency"
  },
  "premium": {
    "annual_premium": 50000
  }
}
```

#### Flat Structure (TEST.json style)
```json
{
  "transaction_type": "binding",
  "transaction_id": "5754934b-a66c-4173-8972-ab6c7fe1d384",
  "policy_number": "GAH-106050-250924",
  "insured_name": "BLC Industries, LLC",
  "insured_state": "MI",
  "producer_name": "Mike Woodworth",
  "gross_premium": 3094,
  "effective_date": "09/24/2025",
  "expiration_date": "09/24/2026"
}
```

### 2. **Invoice Retrieval**
```
GET /api/v1/invoice/policy/{policy_number}/latest
```

**Purpose**: Get latest invoice data for a policy from IMS

**Headers**:
- `X-API-Key: {your_api_key}`

**Query Parameters**:
- `include_payment_info`: `true` (default) or `false`
- `format_currency`: `true` (default) or `false`

**Response**:
```json
{
  "success": true,
  "invoice_data": {
    "invoice_number": "INV-2024-001",
    "policy_number": "POL-2024-001",
    "amount": 50000,
    // ... more invoice details
  }
}
```

## 📝 How It Works

The `/api/triton/transaction/new` endpoint handles ALL transaction types. The actual transaction type is determined by the `transaction_type` field in the JSON payload:

- `"transaction_type": "binding"` or `"new"` → Creates a new policy
- `"transaction_type": "cancellation"` → Cancels a policy
- `"transaction_type": "endorsement"` or `"midterm_endorsement"` → Creates an endorsement
- `"transaction_type": "reinstatement"` → Reinstates a cancelled policy

## 📋 Testing with TEST.json

### Option 1: Use the test script
```bash
python test_with_real_data.py
```

### Option 2: Direct cURL with TEST.json data
```bash
# First, transform TEST.json to webhook format
python -c "
import json
with open('TEST.json') as f:
    data = json.load(f)
    
webhook_data = {
    'transaction_type': 'binding',
    'transaction_id': data['transaction_id'],
    'policy_number': data['policy_number'],
    'insured_name': data['insured_name'],
    'insured_state': data['state'],
    'producer_name': data['producer_name'],
    'gross_premium': data['gross_premium'],
    'effective_date': data['effective_date'],
    'expiration_date': data['expiration_date'],
    'address_1': data['address_1'],
    'city': data['city'],
    'state': data['state'],
    'zip': data['zip']
}

with open('webhook_payload.json', 'w') as f:
    json.dump(webhook_data, f, indent=2)
"

# Send to endpoint
curl -X POST http://localhost:8000/api/triton/transaction/new \
  -H "Content-Type: application/json" \
  -H "X-API-Key: triton_test_key" \
  -d @webhook_payload.json
```

### Option 3: Direct flat structure support
The endpoint automatically detects flat structure (like TEST.json) vs nested structure, so you can send TEST.json data directly with minimal modifications:

```bash
# Just add transaction_type if missing
jq '. + {"transaction_type": "binding"}' TEST.json | \
curl -X POST http://localhost:8000/api/triton/transaction/new \
  -H "Content-Type: application/json" \
  -H "X-API-Key: triton_test_key" \
  -d @-
```

## 🔍 Health Check

```
GET /api/health
```

Check if the service is running.

## 📊 Monitoring

- All transactions are logged with structured logging
- Check `ims_integration.log` for detailed processing information
- Each transaction has a unique ID for tracing

## 🚀 Quick Start

1. **Start the service**:
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Test with sample data**:
   ```bash
   python test_with_real_data.py
   ```

3. **Check logs**:
   ```bash
   tail -f ims_integration.log
   ```