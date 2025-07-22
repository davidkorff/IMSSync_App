# Underwriter Lookup Process

## Overview
The underwriter service retrieves underwriter information from IMS by executing the `getUserbyName_WS` stored procedure through the DataAccess ExecuteDataSet method.

## Service Details

### Endpoint
- **URL**: `POST http://10.64.32.234/ims_one/dataaccess.asmx`
- **SOAPAction**: `http://tempuri.org/IMSWebServices/DataAccess/ExecuteDataSet`

### Request Structure
```xml
<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
               xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Header>
    <TokenHeader xmlns="http://tempuri.org/IMSWebServices/DataAccess">
      <Token>{authentication_token}</Token>
      <Context>RSG_Integration</Context>
    </TokenHeader>
  </soap:Header>
  <soap:Body>
    <ExecuteDataSet xmlns="http://tempuri.org/IMSWebServices/DataAccess">
      <procedureName>getUserbyName</procedureName>
      <parameters>
        <string>fullname</string>
        <string>{underwriter_name}</string>
      </parameters>
    </ExecuteDataSet>
  </soap:Body>
</soap:Envelope>
```

### Response Format
```xml
<ExecuteDataSetResponse xmlns="http://tempuri.org/IMSWebServices/DataAccess">
    <ExecuteDataSetResult>
        &lt;Results&gt;
          &lt;Table&gt;
            &lt;UserGUID&gt;ae8000e6-a437-4990-b867-7925d7f1e4b4&lt;/UserGUID&gt;
          &lt;/Table&gt;
        &lt;/Results&gt;
    </ExecuteDataSetResult>
</ExecuteDataSetResponse>
```

## Stored Procedure
The `getUserbyName_WS` stored procedure:
- Takes a full name parameter
- Searches for users by concatenating first and last name
- Returns UserGUID (used as the underwriter GUID)
- Note: IMS automatically appends '_WS' to the procedure name

## Usage

### Import and Initialize
```python
from app.services.ims.underwriter_service import get_underwriter_service

# Get singleton instance
underwriter_service = get_underwriter_service()
```

### Look Up Underwriter
```python
# Look up by name
success, underwriter_guid, message = underwriter_service.get_underwriter_by_name("Christina Rentas")

if success and underwriter_guid:
    print(f"Underwriter GUID: {underwriter_guid}")
else:
    print(f"Lookup failed: {message}")
```

### Process from Payload
```python
# Extract underwriter from Triton payload
payload = {
    "underwriter_name": "Haley Crocombe",
    # ... other fields
}

success, underwriter_guid, message = underwriter_service.process_underwriter_from_payload(payload)

if success:
    print(f"Underwriter GUID: {underwriter_guid}")
    # Use this GUID for quote creation
```

## Key Points

1. **Service Independence**: The underwriter service is separate from the producer service
2. **GUID Extraction**: Extracts UserGUID as the underwriter identifier
3. **XML Handling**: Automatically handles escaped XML in responses
4. **Error Handling**: Manages authentication, network, and parsing errors

## Testing
Run the underwriter service test:
```bash
python3 test_underwriter_lookup.py
```

## Integration with Policy Lifecycle
The underwriter GUID will be used in subsequent operations:
- Creating quotes with underwriter assignment
- Tracking underwriter performance
- Workflow management and approvals
- Policy documentation and compliance

## Error Scenarios
The service handles:
- Missing underwriter name in payload
- Underwriter not found in IMS
- Authentication failures
- Network timeouts
- XML parsing errors
- Special characters in names