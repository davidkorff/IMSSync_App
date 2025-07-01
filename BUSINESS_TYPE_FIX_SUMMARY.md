# Business Type Foreign Key Error - Fix Summary

## Problem Fixed
The IMS integration was failing with a foreign key constraint error because the code was using BusinessTypeID 13 for corporations, but this ID doesn't exist in the IMS database.

## Changes Made

### File: `/app/integrations/triton/flat_transformer.py`

Updated the `_get_business_type_id` method to:

1. **Use correct BusinessTypeIDs that exist in IMS database:**
   - Corporation: 1 (was 13)
   - Partnership: 2
   - Limited Liability Partnership: 3
   - Individual: 3
   - Sole Proprietor: 4
   - LLC: 5

2. **Handle transaction types properly:**
   - Added logic to recognize "Renewal", "New Business", "Endorsement", etc. as transaction types, not business entity types
   - These now default to Corporation (ID 1) with an appropriate warning

3. **Improved matching logic:**
   - Added exact match checking first
   - Ordered mappings to check longer strings before shorter ones (e.g., "limited liability partnership" before "partnership")
   - This prevents incorrect partial matches

## Test Results
All test cases now pass:
- Corporation types correctly map to ID 1
- Transaction types are handled appropriately
- All business entity types map to valid IMS IDs

## Impact
This fix resolves the foreign key constraint error that was preventing insured records from being created in IMS when the business type was "Renewal" or when corporations were being processed.

## Next Steps
1. Deploy the updated code
2. Reprocess any failed transactions
3. Monitor logs to ensure no more foreign key errors occur

## Additional Recommendations
1. Consider querying IMS for valid business types on startup to ensure mappings stay in sync
2. Add validation before attempting to insert to catch any future mapping issues
3. Create a shared constants file for business type mappings to ensure consistency across all modules