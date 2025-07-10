# Triton-IMS Integration Tests

## Quick Start

### Test with TEST.json
The simplest way to test the integration:

```bash
cd tests
python test_with_test_json.py
```

This will:
1. Load the actual TEST.json file
2. Send it to `/api/triton/transaction/new`
3. Show the response
4. Test both sync and async modes

## Test Structure

```
tests/
├── README.md                          # This file
├── test_with_test_json.py            # Simple standalone test
├── data/
│   └── TEST.json                     # Test data
├── integration/
│   └── test_triton_binding.py        # Full integration tests
└── unit/
    └── (unit tests will go here)
```

## Running Different Tests

### 1. Quick Test (Recommended)
```bash
python test_with_test_json.py
```

### 2. Integration Tests with pytest
```bash
pytest integration/test_triton_binding.py -v
```

### 3. Manual cURL Test
```bash
# Ensure transaction_type is set to "binding"
curl -X POST http://localhost:8000/api/triton/transaction/new \
  -H "Content-Type: application/json" \
  -H "X-API-Key: triton_test_key" \
  -d @data/TEST.json
```

## What TEST.json Contains

- **Policy**: GAH-106050-250924
- **Insured**: BLC Industries, LLC (Michigan)
- **Premium**: $3,094
- **Transaction Type**: "NEW BUSINESS" (converted to "binding" by tests)

## Common Issues

### Server Not Running
```
ERROR: Cannot connect to server
```
**Solution**: Start the server first:
```bash
cd ..
uvicorn app.main:app --reload
```

### Invalid Transaction Type
TEST.json has `"transaction_type": "NEW BUSINESS"` which needs to be normalized to `"binding"`.
The test scripts handle this automatically.

### Missing API Key
Ensure your API key matches what's configured. Default: `triton_test_key`

## Test Results

Successful output looks like:
```
✅ SUCCESS!
  Transaction ID: 5754934b-a66c-4173-8972-ab6c7fe1d384
  Policy Number: POL-2024-001
  Quote GUID: 12345678-1234-1234-1234-123456789012
  Invoice Number: Not yet available
```

Error output shows:
```
❌ FAILED!
  Stage: BINDING
  Message: Failed to create insured
  Details: {...}
```