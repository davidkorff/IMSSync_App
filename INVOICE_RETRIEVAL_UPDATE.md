# Invoice Retrieval Update

## Overview

The RSG Integration Service now automatically retrieves and includes invoice numbers in the response when policies are bound in IMS. This eliminates the need for Triton to make a separate API call to get the invoice number after binding.

## What Changed

### 1. Enhanced Data Model
- Added `invoice_number` and `invoice_retrieved_at` fields to the `IMSPolicy` model
- These fields track when an invoice was successfully retrieved

### 2. Automatic Invoice Retrieval
- After binding a policy, the system automatically attempts to retrieve the invoice number
- Uses a retry mechanism (3 attempts with 2-second intervals) to handle async invoice generation
- If invoice is not immediately available, tries again after policy issuance

### 3. Updated Response Structure
- The `ims_details` section of the response now includes `invoice_number`
- Compatible with existing response structure - just adds one new field

## How It Works

1. **Policy Binding**: When a policy is bound in IMS, we get the policy number
2. **Invoice Retrieval**: System immediately attempts to retrieve the invoice using the policy number
3. **Retry Logic**: If invoice isn't ready, waits 2 seconds and retries (up to 3 times)
4. **Response**: Invoice number is included in the response if available, otherwise returns `null`
5. **Second Chance**: If invoice wasn't available during binding, tries again after issuing

## Response Example

```json
{
  "transaction_id": "12345678-1234-1234-1234-123456789012",
  "status": "completed",
  "ims_status": "issued",
  "message": "Triton new transaction processed: completed",
  "ims_details": {
    "processing_status": "issued",
    "insured_guid": "87654321-4321-4321-4321-098765432109",
    "submission_guid": "11111111-1111-1111-1111-111111111111",
    "quote_guid": "22222222-2222-2222-2222-222222222222",
    "policy_number": "TST-2024-00001",
    "invoice_number": "INV-2024-00001",  // New field
    "error": null
  }
}
```

## Important Notes

1. **Timing**: IMS may generate invoices asynchronously. If the invoice isn't immediately available, the field will be `null`
2. **Synchronous Mode**: Works best with synchronous processing (`sync_mode=true`)
3. **Fallback**: The existing invoice endpoints remain available for manual retrieval if needed

## Testing

Use the provided test script to verify the functionality:

```bash
python test_invoice_in_binding.py
```

This test demonstrates:
- Synchronous binding with invoice retrieval
- Handling of cases where invoice isn't immediately available
- Comparison with async mode behavior

## Configuration

The retry behavior can be adjusted in the `_retrieve_invoice_number` method:
- `max_attempts`: Number of retry attempts (default: 3)
- `wait_seconds`: Seconds between attempts (default: 2)

## Backward Compatibility

This change is fully backward compatible:
- Existing integrations continue to work without modification
- The invoice_number field is optional in the response
- Manual invoice retrieval endpoints remain available