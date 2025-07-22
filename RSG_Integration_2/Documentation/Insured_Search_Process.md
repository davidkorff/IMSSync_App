# Insured Search Process

## Overview
The insured search service handles finding existing insured records in IMS using the FindInsuredByName web service.

## Service Details

### Endpoint
- **URL**: `POST http://10.64.32.234/ims_origintest/insuredfunctions.asmx`
- **SOAPAction**: `http://tempuri.org/IMSWebServices/InsuredFunctions/FindInsuredByName`

### Request Structure
```xml
<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
               xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Header>
    <TokenHeader xmlns="http://tempuri.org/IMSWebServices/InsuredFunctions">
      <Token>{authentication_token}</Token>
      <Context>RSG_Integration</Context>
    </TokenHeader>
  </soap:Header>
  <soap:Body>
    <FindInsuredByName xmlns="http://tempuri.org/IMSWebServices/InsuredFunctions">
      <insuredName>{insured_name}</insuredName>
      <city>{city}</city>
      <state>{state}</state>
      <zip>{zip}</zip>
    </FindInsuredByName>
  </soap:Body>
</soap:Envelope>
```

### Response Formats

#### Insured Found
```xml
<FindInsuredByNameResponse xmlns="http://tempuri.org/IMSWebServices/InsuredFunctions">
    <FindInsuredByNameResult>3602d4e6-6353-4f4c-8426-15b82130e88e</FindInsuredByNameResult>
</FindInsuredByNameResponse>
```

#### Insured Not Found
```xml
<FindInsuredByNameResponse xmlns="http://tempuri.org/IMSWebServices/InsuredFunctions">
    <FindInsuredByNameResult>00000000-0000-0000-0000-000000000000</FindInsuredByNameResult>
</FindInsuredByNameResponse>
```

## Usage

### Import and Initialize
```python
from app.services.ims.insured_service import get_insured_service

# Get singleton instance
insured_service = get_insured_service()
```

### Search for Insured
```python
# Search with individual parameters
found, insured_guid, message = insured_service.find_insured_by_name(
    insured_name="Thrive Network LLC",
    city="Beaverton",
    state="OR",
    zip_code="97078"
)

if found:
    print(f"Insured found with GUID: {insured_guid}")
else:
    print("Insured not found - need to create new record")
```

### Process Triton Payload
```python
# Process a Triton transaction payload
payload = {
    "insured_name": "Thrive Network LLC",
    "city": "Beaverton",
    "state": "OR",
    "zip": "97078",
    # ... other fields
}

found, insured_guid, message = insured_service.process_triton_payload(payload)
```

## Integration Flow

1. **Receive Triton Payload**: Extract insured information from the transaction
2. **Authenticate**: Ensure valid IMS token (handled automatically)
3. **Search**: Call FindInsuredByName with the insured details
4. **Process Result**:
   - If found: Use the returned GUID for subsequent operations
   - If not found: Proceed to create new insured record

## Testing
Run the standalone test:
```bash
export IMS_ONE_USERNAME=your_username
export IMS_ONE_PASSWORD=your_encrypted_password
python3 test_find_insured_standalone.py
```

## Error Handling
The service handles:
- Authentication failures
- Network errors
- XML parsing errors
- Invalid/missing insured data

## Next Steps
If the insured is not found, the next step is to create a new insured record using the AddInsured or AddInsuredWithContact web service.