# Sync Mode Update - Default Behavior Change

## Overview

As of this update, the RSG Integration Service now defaults to **synchronous processing** for all transaction endpoints. This means the API will wait for complete IMS processing before returning a response, providing immediate feedback about success or failure.

## What Changed

### Previous Behavior (Async by Default)
```json
// Request
POST /api/transaction/new

// Immediate Response (doesn't wait for IMS)
{
  "transaction_id": "abc123",
  "status": "received",
  "message": "transaction created successfully and queued for processing"
}
```

### New Behavior (Sync by Default)
```json
// Request
POST /api/transaction/new

// Response after IMS processing completes
{
  "transaction_id": "abc123",
  "status": "completed",  // or "failed"
  "ims_status": "issued",  // or "error"
  "message": "new transaction processed: completed",
  "ims_details": {
    "processing_status": "issued",
    "policy_number": "POL-12345",
    "insured_guid": "def456",
    "quote_guid": "ghi789",
    "error": null  // or error message if failed
  }
}
```

## Affected Endpoints

All transaction endpoints now default to sync mode:
- `POST /api/transaction/{type}`
- `POST /api/triton/transaction/{type}`
- `POST /api/xuber/transaction/{type}`

## How to Use Async Mode

If you need the old behavior (immediate response without waiting for IMS):

```bash
# Add sync_mode=false parameter
POST /api/transaction/new?sync_mode=false
```

## Benefits of Sync Mode Default

1. **Immediate Error Detection**: Know right away if IMS processing failed
2. **Complete Transaction Status**: Get policy numbers, GUIDs, and full details
3. **Simplified Integration**: No need to poll for status updates
4. **Better Debugging**: Error messages returned directly in response

## Response Time Considerations

- **Sync Mode**: 5-30 seconds (depends on IMS processing)
- **Async Mode**: < 1 second (just queuing time)

Use async mode if:
- You have timeout constraints
- You're processing large batches
- You have a separate status polling mechanism

## Example: Handling Both Modes

```python
# Python example
response = requests.post(
    "http://api/transaction/new",
    params={"sync_mode": True},  # Optional, now default
    json=transaction_data
)

if response.json()["status"] == "completed":
    policy_number = response.json()["ims_details"]["policy_number"]
    print(f"Policy created: {policy_number}")
elif response.json()["status"] == "failed":
    error = response.json()["ims_details"]["error"]
    print(f"IMS Error: {error}")
```

## Migration Notes

- No changes required for existing integrations expecting full transaction flow
- Integrations relying on immediate response should add `sync_mode=false`
- Monitor timeout settings - may need adjustment for sync processing