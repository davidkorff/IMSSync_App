# IMS Integration Business Type Error Analysis

## Error Description

The error message indicates a foreign key constraint violation:
```
The INSERT statement conflicted with the FOREIGN KEY constraint 'FK_tblInsureds_lstBusinessTypes'. 
The conflict occurred in database 'IMS_DEV', table 'dbo.lstBusinessTypes', column 'BusinessTypeID'.
```

Log message shows:
```
Unknown business type 'Renewal', defaulting to Corporation (13)
```

## Root Cause

The error is caused by **inconsistent business type ID mappings** across different files in the codebase.

### Business Type ID Mappings Found

#### 1. flat_transformer.py (lines 259-287)
```python
business_type_map = {
    'partnership': 2,
    'limited liability partnership': 3,
    'llp': 3,
    'individual': 4,
    'other': 5,
    'limited liability corporation': 9,
    'llc': 9,
    'joint venture': 10,
    'trust': 11,
    'corporation': 13,  # <-- PROBLEMATIC!
    'corp': 13,         # <-- PROBLEMATIC!
    'inc': 13           # <-- PROBLEMATIC!
}
```

#### 2. insured_service.py (lines 297-308)
```python
type_mapping = {
    "corporation": 1,  # <-- CORRECT
    "corp": 1,         # <-- CORRECT
    "inc": 1,          # <-- CORRECT
    "partnership": 2,
    "individual": 3,
    "person": 3,
    "sole proprietor": 4,
    "sole prop": 4,
    "llc": 5,
    "limited liability": 5
}
```

#### 3. field_mappings.py (lines 62-69)
```python
transform_func=lambda x: {
    "LLC": 5,
    "CORP": 1,         # <-- CORRECT
    "CORPORATION": 1,  # <-- CORRECT
    "PARTNERSHIP": 2,
    "INDIVIDUAL": 3,
    "SOLE PROP": 4
}.get(x.upper() if x else "", 1)  # Default to Corporation (1)
```

## The Problem

1. **flat_transformer.py** is using BusinessTypeID **13** for Corporation
2. **insured_service.py** and **field_mappings.py** use BusinessTypeID **1** for Corporation
3. BusinessTypeID **13 does not exist** in the IMS database's lstBusinessTypes table
4. When the business type is "Renewal" (not a valid business entity type), the code defaults to Corporation with ID 13, causing the foreign key constraint error

## Solution

Update the `flat_transformer.py` file to use the correct business type IDs that match the IMS database:

```python
# In flat_transformer.py, update the _get_business_type_id method:
business_type_map = {
    'partnership': 2,
    'limited liability partnership': 3,
    'llp': 3,
    'individual': 4,
    'sole proprietor': 4,
    'sole prop': 4,
    'other': 5,
    'limited liability corporation': 5,  # Changed from 9 to 5
    'llc': 5,                            # Changed from 9 to 5
    'corporation': 1,                    # Changed from 13 to 1
    'corp': 1,                           # Changed from 13 to 1
    'inc': 1                             # Changed from 13 to 1
}
```

Also update the default return value:
```python
# Default to Corporation if not found
logger.warning(f"Unknown business type '{business_type}', defaulting to Corporation (1)")
return 1  # Changed from 13 to 1
```

## Additional Recommendations

1. **Query Valid Business Types**: Use the `GetInsuredBusinessTypes` IMS API or run the SQL query:
   ```sql
   SELECT BusinessTypeID, BusinessTypeName FROM lstBusinessTypes ORDER BY BusinessTypeID
   ```

2. **Handle "Renewal" Properly**: "Renewal" is not a business entity type, it's a transaction type. The code should:
   - Not treat "Renewal" as a business type
   - Look for the actual business entity type in the data
   - Default to Corporation (ID 1) only for actual entity types

3. **Standardize Mappings**: Create a single source of truth for business type mappings that all modules can import:
   ```python
   # app/services/ims/constants.py
   BUSINESS_TYPE_MAPPING = {
       "corporation": 1,
       "partnership": 2,
       "individual": 3,
       "sole proprietor": 4,
       "llc": 5,
       # ... etc
   }
   ```

4. **Add Validation**: Before inserting, validate that the business type ID exists in the database.

## Files to Update

1. `/app/integrations/triton/flat_transformer.py` - Lines 259-287
2. Consider creating a shared constants file for business type mappings

## Testing

After making changes:
1. Test with data containing "Renewal" as business type
2. Test with valid business entity types (Corporation, LLC, etc.)
3. Verify no foreign key constraint errors occur