# Triton Integration Test Guide

## Quick Fix for JSON Loading Issue

The original test script (`test_3_new_business_bind.py`) has an import/environment issue when run with the `--json` parameter. Here are several ways to work around this:

## Solution 1: Use the Fixed Version (Recommended)

```bash
# This version has better error handling and debugging
python3 test_3_new_business_bind_v2.py --json test.json
```

## Solution 2: Use the Test Runner

```bash
# The test runner handles environment setup automatically
python3 test_runner.py --json test.json

# Check environment only
python3 test_runner.py --check-only --json test.json
```

## Solution 3: Test the API Directly

```bash
# Test the actual API endpoint (requires service to be running)
python3 test_api_client.py --json test.json

# Or use default payload
python3 test_api_client.py

# Test against a different URL
python3 test_api_client.py --url http://localhost:8000/api/triton/transaction/new
```

## Setup Environment

If you're still having issues:

```bash
# Run the setup script
./setup_test_env.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Common Issues and Solutions

### Issue: ModuleNotFoundError for 'dotenv'
**Solution**: Install dependencies
```bash
pip install python-dotenv
# or
pip install -r requirements.txt
```

### Issue: Test stops after "Loading payload from test.json"
**Solution**: Use the v2 test script or test_runner.py which handle imports properly

### Issue: Underwriter not found
**Solution**: Update your JSON file with a valid underwriter name that exists in your IMS system

## JSON Payload Format

Your test JSON should include all required fields:

```json
{
  "transaction_id": "unique-id-here",
  "transaction_type": "bind",
  "opportunity_id": 12345,
  "insured_name": "Test Company LLC",
  "underwriter_name": "Valid User Name",
  "producer_name": "Valid Producer Name",
  // ... other required fields
}
```

## Debugging Tips

1. **Check Python path**: The scripts now print debug info about paths and imports
2. **Validate JSON first**: Use `test_runner.py --check-only --json test.json`
3. **Use API client**: Test the service directly without complex imports
4. **Check logs**: The v2 script provides detailed logging of what's happening

## File Descriptions

- `test_3_new_business_bind_v2.py` - Fixed version with better error handling
- `test_runner.py` - Robust test runner that handles environment setup
- `test_api_client.py` - Simple HTTP client to test the API endpoint
- `setup_test_env.sh` - Environment setup script
- `test.json` - Your test payload (update underwriter_name to a valid user)