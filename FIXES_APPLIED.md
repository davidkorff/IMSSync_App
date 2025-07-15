# IMS Integration Fixes Applied

## Summary of Changes

### 1. Business Type Fix
- **Issue**: Business type was being passed as "individual" which wasn't valid
- **Fix**: Hardcoded business type to 9 (LLC/LLP) everywhere per user requirements
- **Files Changed**: 
  - `app/services/triton_processor.py` (both transform methods)
  - `app/services/ims_client.py` (create_quote method)

### 2. AddQuote NullReferenceException Fix
- **Issue**: AddQuote was throwing NullReferenceException mentioning "CreateSubmission" at line 63
- **Root Causes**:
  1. Missing required fields in quote object
  2. Incorrect parameter passing to AddQuote
  3. Missing RiskInformation structure
  
- **Fixes Applied**:
  1. Added all missing fields to quote object:
     - AccountNumber
     - AdditionalInformation
     - ProgramCode (at root level)
     - ProgramID (at root level)
     - RiskInformation (complete structure)
  
  2. Changed AddQuote call from named parameter to direct object:
     ```python
     # Before:
     result = service.AddQuote(quote=quote, _soapheaders=self._get_header())
     
     # After:
     result = service.AddQuote(quote, _soapheaders=self._get_header())
     ```
  
  3. Added RiskInformation with all required fields:
     ```python
     'RiskInformation': {
         'PolicyName': quote_data.get('insured_name', ''),
         'CorporationName': quote_data.get('insured_name', ''),
         'DBA': quote_data.get('insured_dba', ''),
         'FEIN': quote_data.get('tax_id', ''),
         'Address1': quote_data.get('address', ''),
         'City': quote_data.get('city', ''),
         'State': quote_data.get('state', ''),
         'ZipCode': quote_data.get('zip', ''),
         'Phone': quote_data.get('phone', ''),
         'BusinessType': 9  # LLC/LLP
         # ... other fields
     }
     ```

### 3. Data Flow Improvements
- **Issue**: Quote creation was missing insured information needed for RiskInformation
- **Fix**: Updated triton_processor.py to pass insured details in quote_data:
  ```python
  quote_data = {
      # ... existing fields ...
      'insured_name': ims_data['insured']['name'],
      'insured_dba': ims_data['insured'].get('dba', ''),
      'tax_id': ims_data['insured'].get('tax_id', ''),
      'address': ims_data['insured'].get('address', ''),
      'city': ims_data['insured'].get('city', ''),
      'zip': ims_data['insured'].get('zip', ''),
      'phone': ims_data['insured'].get('phone', '')
  }
  ```

### 4. Transform Method Updates
- Added phone and dba fields to both transform methods:
  - `_transform_binding_data` (nested structure)
  - `_transform_flat_binding_data` (flat structure like TEST.json)

## Next Steps

1. Run the test again to verify the NullReferenceException is resolved
2. If successful, the quote should be created and we can proceed with binding
3. If still failing, check the IMS logs for more specific error details

## Test Command

```bash
python3 test_triton_integration.py TEST.json
```