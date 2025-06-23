# Quick Start Guide

Get the RSG Integration Service up and running in minutes with this quick start guide.

## Prerequisites

Before starting, ensure you have:
- Python 3.11 installed
- Access to IMS credentials
- API keys for authentication
- Network access to IMS servers

## Step 1: Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd "RSG Integration"

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure Environment

```bash
# For TEST environments: .env may already exist in the repo
# For PRODUCTION: Copy from example and configure
cp .env.example .env  # Skip if .env already exists

# Edit .env with your configuration
# At minimum, set these values:
```

> **Note**: In test environments, the `.env` file may be committed to the repository for convenience. 
> For production deployments, always use proper secret management and never commit credentials.

Edit `.env` with these essential values:
```env
# IMS Environment
DEFAULT_ENVIRONMENT=iscmga_test
ISCMGA_TEST_USERNAME=your_username
ISCMGA_TEST_PASSWORD=your_encrypted_password

# API Security
API_KEYS='["your-secure-api-key"]'
TRITON_API_KEYS='["triton-api-key"]'

# Required GUIDs (use test values initially)
TRITON_DEFAULT_PRODUCER_GUID=12345678-1234-1234-1234-123456789012
TRITON_PRIMARY_LINE_GUID=12345678-1234-1234-1234-123456789012
```

## Step 3: Test IMS Connection

```bash
# Test IMS login
python test_ims_login.py

# Expected output:
# Testing IMS login...
# Login successful! Token: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

## Step 4: Find Required GUIDs

```bash
# Search for producers
python test_producer_search.py

# Enter producer name when prompted
# Note the ProducerLocationGuid for your .env file
```

## Step 5: Start the Service

### Option A: API Service Only
```bash
# Start the API service
python -m app.main

# Service will start on http://localhost:8000
# Check health: http://localhost:8000/api/health
```

### Option B: With Triton Polling
```bash
# Configure Triton database in .env first
TRITON_MYSQL_HOST=your-triton-host
TRITON_MYSQL_USER=your-user
TRITON_MYSQL_PASSWORD=your-password

# Run polling service
python run_mysql_polling.py
```

## Step 6: Test Transaction Submission

### Test with CSV Loader
```bash
# Load CSV file with default async mode (fast, no IMS feedback)
python load_csv_to_ims.py 1

# Load CSV with synchronous mode (waits for IMS processing)
python load_csv_to_ims.py 1 --sync

# Load CSV with status polling (submits async, then polls)
python load_csv_to_ims.py 1 --poll

# Examples:
# - Select file #2 with sync mode:
python load_csv_to_ims.py 2 --sync

# - Use custom API URL and key:
python load_csv_to_ims.py 1 http://localhost:8001 my-api-key --sync
```

#### CSV Loader Modes:
- **Default (Async)**: Fast submission, check status later
- **--sync**: Waits for IMS processing, shows immediate results/errors
- **--poll**: Submits async, then polls for status updates

### Test with cURL
```bash
# Submit test transaction (async mode)
curl -X POST http://localhost:8000/api/transaction/new?source=triton \
  -H "X-API-Key: your-secure-api-key" \
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
    "effective_date": "2025-02-01",
    "expiration_date": "2026-02-01",
    "premium": 5000.00
  }'

# Submit with sync mode (wait for IMS processing)
curl -X POST "http://localhost:8000/api/transaction/new?source=triton&sync_mode=true" \
  -H "X-API-Key: your-secure-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "policy": {
      "policy_number": "TEST-001",
      "insured_name": "Test Company LLC",
      "insured_address": "123 Main St",
      "insured_city": "Dallas",
      "insured_state": "TX",
      "insured_zip": "75201",
      "effective_date": "2025-02-01",
      "expiration_date": "2026-02-01",
      "gross_premium": 5000.00
    }
  }'

# Check status
curl http://localhost:8000/api/transaction/{transaction_id} \
  -H "X-API-Key: your-secure-api-key"
```

### Test with Python
```python
import requests

# Submit transaction
response = requests.post(
    "http://localhost:8000/api/transaction/new",
    params={"source": "triton"},
    headers={"X-API-Key": "your-secure-api-key"},
    json={
        "policy_number": "TEST-001",
        "insured": {"name": "Test Company LLC"},
        "effective_date": "2025-02-01",
        "expiration_date": "2026-02-01",
        "premium": 5000.00
    }
)

transaction_id = response.json()["transaction_id"]
print(f"Transaction ID: {transaction_id}")
```

## Common Issues and Solutions

### Issue: "Authentication failed"
**Solution**: Verify IMS credentials in .env are correct and encrypted properly

### Issue: "Producer not found"
**Solution**: Run `test_producer_search.py` to find valid producer GUIDs

### Issue: "Connection refused"
**Solution**: Check firewall rules and network connectivity to IMS servers

### Issue: "Invalid API key"
**Solution**: Ensure API key in request matches one in API_KEYS environment variable

## Next Steps

1. **Configure Production GUIDs**: Replace test GUIDs with real values
2. **Set Up Monitoring**: Configure health check monitoring
3. **Enable HTTPS**: Set up reverse proxy with SSL
4. **Configure Logging**: Adjust log levels and rotation
5. **Test All Transaction Types**: Verify new, update, and cancellation flows

## Quick Command Reference

```bash
# Start API service
python -m app.main

# Run tests
python test_ims_login.py
python test_producer_search.py
python test_triton_integration.py

# Check service health
curl http://localhost:8000/api/health

# View logs
tail -f ims_integration.log

# Stop service
# Ctrl+C in terminal or:
pkill -f "python -m app.main"
```

## Getting Help

- Check [Troubleshooting Guide](../07_Operations/03_Troubleshooting.md)
- Review [API Reference](../03_API_Reference/01_Endpoints_Overview.md)
- See [Configuration Guide](../02_Configuration/01_Environment_Variables.md)

## Ready for Production?

Once everything is working locally:
1. Review [Production Checklist](../05_Deployment/05_Production_Checklist.md)
2. Choose deployment method: [Docker](../05_Deployment/02_Docker_Deployment.md) or [Direct](../05_Deployment/03_Direct_Deployment.md)
3. Configure monitoring and backups
4. Deploy to production server