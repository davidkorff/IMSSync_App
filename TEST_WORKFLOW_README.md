# Full Workflow Test Script

## What It Does

The `test_ims_connection.py` script performs a complete end-to-end test of the Triton → IMS integration:

1. **Loads TEST.json** - Reads your test data file
2. **Connects to IMS** - Uses real credentials from .env
3. **Processes the transaction** - Runs through the entire workflow
4. **Creates real IMS records** - Actually creates data in IMS
5. **Shows detailed logs** - Both on screen and in `test_workflow.log`

## How to Run

```bash
# Basic run (with confirmation prompt)
python test_ims_connection.py

# Skip confirmation
python test_ims_connection.py --skip-confirm

# Use a different test file
python test_ims_connection.py --test-file path/to/test.json
```

## What You'll See

### On Success:
```
================================================================================
FULL TRITON → SERVICE → IMS WORKFLOW TEST
================================================================================

1️⃣ LOADING TEST.JSON
----------------------------------------
  📁 Reading from: TEST.json
  ✅ Loaded successfully
  📋 Policy: GAH-106050-250924
  🏢 Insured: BLC Industries, LLC
  💰 Premium: $3094
  📅 Effective: 2025-09-24

2️⃣ LOADING CONFIGURATION
----------------------------------------
  ⚙️ Environment: ims_one
  🌐 IMS URL: http://10.64.32.234/ims_one
  👤 Username: david.korff
  🔑 Password: ********
  📊 Excel Rating: True

3️⃣ CREATING IMS CLIENT
----------------------------------------
  ✅ IMS client created

4️⃣ AUTHENTICATING WITH IMS
----------------------------------------
  🔐 Attempting login...
  ✅ Successfully authenticated!
  🎫 Token: 12345-ABCDE-67890...

5️⃣ INITIALIZING TRITON PROCESSOR
----------------------------------------
  ✅ Triton processor ready

6️⃣ PROCESSING TRANSACTION
----------------------------------------
  📤 Transaction Type: NEW BUSINESS
  🔄 Processing...

  ✅ TRANSACTION SUCCESSFUL!
  📋 Transaction ID: 5754934b-a66c-4173-8972-ab6c7fe1d384
  📄 Policy Number: POL-2024-001
  🆔 Quote GUID: 12345678-1234-1234-1234-123456789012
  📃 Invoice Number: Not yet available

7️⃣ WORKFLOW STEPS COMPLETED
----------------------------------------
  ✅ 1. Validated Triton data
  ✅ 2. Transformed to IMS format
  ✅ 3. Created/found insured in IMS
  ✅ 4. Created submission
  ✅ 5. Created quote
  ✅ 6. Applied rating/premium
  ✅ 7. Bound policy
  ✅ 8. Linked external ID
```

### On Error:
```
  ❌ WORKFLOW FAILED!
  🚨 Stage: IMS_CALL
  📝 Error: Failed to create insured: Connection timeout
  📋 Details: {
    "operation": "find_or_create_insured",
    "insured_name": "BLC Industries, LLC"
  }

💡 TROUBLESHOOTING TIPS:
  - Check IMS connection is active
  - Verify credentials are correct
  - Ensure GUIDs in config are valid
```

## Log File

The script creates `test_workflow.log` with FULL details:
- Every IMS SOAP call
- Request/response data
- Timing information
- Stack traces for errors
- Debug-level logging

## Error Stages

The script identifies WHERE failures occur:

- **VALIDATION** - Bad input data
- **TRANSFORMATION** - Data mapping issues
- **IMS_CALL** - IMS communication problems
- **BINDING** - Policy creation issues

## Debugging Tips

1. **Check the log file first** - It has all the details
2. **Look at the error stage** - Tells you where it failed
3. **Review the error details** - Shows exactly what was being attempted
4. **Follow the troubleshooting tips** - Specific to each error type

## Testing Other Transactions

Once NEW BUSINESS works, test:
- Cancellations
- Endorsements
- Reinstatements

Just change the `transaction_type` in your test JSON file.