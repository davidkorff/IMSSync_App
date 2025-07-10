# Running the IMS Integration Service

## Quick Start

### 1. Fix the Import Error First
The service currently has an import error. Run:
```bash
# This is already fixed in the code
```

### 2. Start the Service

**Option A: Using the helper script (recommended)**
```bash
python start_service.py
```

If port 8000 is in use:
```bash
python start_service.py --port 8001
```

**Option B: Using uvicorn directly**
```bash
# Basic start
python -m uvicorn app.main:app

# With auto-reload (for development)
python -m uvicorn app.main:app --reload

# On a different port
python -m uvicorn app.main:app --port 8001

# If you get "Address already in use" error
python -m uvicorn app.main:app --port 8001 --reload
```

**Option C: Using run_service.py (if it exists)**
```bash
python run_service.py
```

### 3. Test the Service

Once running, test it:
```bash
# Test with default settings (uses localhost:8000)
python test_api_workflow.py

# Test with different port
python test_api_workflow.py --url http://localhost:8001

# Skip confirmation prompt
python test_api_workflow.py --skip-confirm
```

## Troubleshooting

### "Address already in use" Error

1. **Find what's using port 8000:**
   ```bash
   # Linux/Mac
   lsof -i :8000
   
   # Or
   netstat -tlpn | grep :8000
   ```

2. **Kill the process:**
   ```bash
   # If you find a PID from above
   kill -9 <PID>
   ```

3. **Or just use a different port:**
   ```bash
   python start_service.py --port 8001
   ```

### Import Errors

If you get import errors like `ImportError: cannot import name 'IMSInvoiceService'`:

1. The code has been refactored but some imports weren't updated
2. The fix has been applied to `workflow_orchestrator.py`
3. If you get other import errors, check the actual class names in the files

### Service Won't Start

1. **Check Python version:**
   ```bash
   python --version  # Should be 3.8+
   ```

2. **Check dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Check .env file exists:**
   ```bash
   ls -la .env
   ```

## Testing Workflow

### Full Test Process:

1. **Start the service:**
   ```bash
   python start_service.py
   ```

2. **In another terminal, run the test:**
   ```bash
   python test_api_workflow.py
   ```

3. **Check the logs:**
   - Console output shows real-time progress
   - `test_api_workflow.log` has detailed request/response
   - Service logs show IMS communication

### What the Test Does:

1. Loads TEST.json
2. Sends it to your service via HTTP POST
3. Service authenticates with IMS (using .env credentials)
4. Service creates the policy in IMS
5. Returns success/error response
6. Test script displays everything clearly

## Service Endpoints

Once running, you can access:

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Main Endpoint**: POST http://localhost:8000/api/triton/transaction/new

## Expected Output

### Successful Test:
```
✅ TRANSACTION SUCCESSFUL!
📋 Transaction ID: 5754934b-a66c-4173-8972-ab6c7fe1d384
📄 Policy Number: POL-2024-001
🆔 Quote GUID: 12345678-1234-1234-1234-123456789012
```

### Failed Test:
```
❌ WORKFLOW FAILED!
🚨 Stage: IMS_CALL
📝 Error: Failed to authenticate with IMS
💡 TROUBLESHOOTING:
  - Check IMS credentials in .env
  - Verify IMS endpoint is reachable
```