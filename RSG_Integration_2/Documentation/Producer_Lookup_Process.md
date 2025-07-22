# Producer Lookup Process

## Overview
The data access service uses the IMS DataAccess ExecuteDataSet method to retrieve producer information by executing stored procedures.

## Service Details

### ExecuteDataSet
- **URL**: `POST http://10.64.32.234/ims_one/dataaccess.asmx`
- **SOAPAction**: `http://tempuri.org/IMSWebServices/DataAccess/ExecuteDataSet`
- **Purpose**: Execute stored procedures and return results as XML

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
      <procedureName>getProducerbyName</procedureName>
      <parameters>
        <string>fullname</string>
        <string>{producer_name}</string>
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
            &lt;ProducerContactGUID&gt;77742f00-97b9-49e5-b01a-0292e972d43d&lt;/ProducerContactGUID&gt;
            &lt;ProducerLocationGUID&gt;b37422f1-7dc7-4d15-8d59-d717803fa160&lt;/ProducerLocationGUID&gt;
          &lt;/Table&gt;
        &lt;/Results&gt;
    </ExecuteDataSetResult>
</ExecuteDataSetResponse>
```

## Stored Procedure
The `getProducerbyName_WS` stored procedure:
- Takes a full name parameter
- Searches for producer by concatenating first and last name
- Returns ProducerContactGUID and ProducerLocationGUID
- Note: IMS automatically appends '_WS' to the procedure name

## Usage

### Import and Initialize
```python
from app.services.ims.data_access_service import get_data_access_service

# Get singleton instance
data_service = get_data_access_service()
```

### Look Up Producer
```python
# Look up by name
success, producer_info, message = data_service.get_producer_by_name("Mike Woodworth")

if success and producer_info:
    contact_guid = producer_info['ProducerContactGUID']
    location_guid = producer_info['ProducerLocationGUID']
    print(f"Producer Contact GUID: {contact_guid}")
    print(f"Producer Location GUID: {location_guid}")
```

### Process from Payload
```python
# Extract producer from Triton payload
payload = {
    "producer_name": "Dan Mulligan",
    # ... other fields
}

success, producer_info, message = data_service.process_producer_from_payload(payload)
if success:
    contact_guid = producer_info['ProducerContactGUID']
    location_guid = producer_info['ProducerLocationGUID']
```

### Direct ExecuteDataSet Call
```python
# Execute any stored procedure
success, result_xml, message = data_service.execute_dataset(
    "procedureName",  # Without _WS suffix
    ["param1_name", "param1_value", "param2_name", "param2_value"]
)
```

## Important Notes

1. **Procedure Naming**: The service automatically appends '_WS' to prevent calling base procedures
2. **Parameter Format**: Parameters must be passed as alternating name/value pairs
3. **XML Escaping**: The response contains escaped XML that is automatically unescaped
4. **Authentication**: Token is required and handled automatically

## Error Handling
The service handles:
- Authentication failures
- Network errors
- XML parsing errors
- Missing producer records
- Invalid stored procedure names

## Testing
Run the producer lookup test:
```bash
python3 test_producer_lookup.py
```

## Integration with Policy Lifecycle
The producer GUIDs obtained from this lookup are required for:
- Creating quotes
- Associating quotes with producers  
- Commission calculations
- Producer reporting
- Policy documentation