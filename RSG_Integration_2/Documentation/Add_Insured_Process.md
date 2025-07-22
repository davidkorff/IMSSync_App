# Add Insured Process

## Overview
The add insured process handles finding existing insureds or creating new ones in IMS based on Triton transaction payloads.

## Flow
1. **Authenticate** - Get valid IMS token
2. **Search** - Try to find existing insured by name and location
3. **Create** - If not found, create new insured with location

## Service Details

### FindInsuredByName
- **URL**: `POST http://10.64.32.234/ims_origintest/insuredfunctions.asmx`
- **SOAPAction**: `http://tempuri.org/IMSWebServices/InsuredFunctions/FindInsuredByName`
- **Returns**: Insured GUID if found, null GUID if not found

### AddInsuredWithLocation
- **URL**: `POST http://10.64.32.234/ims_one/insuredfunctions.asmx`
- **SOAPAction**: `http://tempuri.org/IMSWebServices/InsuredFunctions/AddInsuredWithLocation`
- **Returns**: New insured GUID

### Request Structure (AddInsuredWithLocation)
```xml
<AddInsuredWithLocation xmlns="http://tempuri.org/IMSWebServices/InsuredFunctions">
  <insured>
    <BusinessTypeID>9</BusinessTypeID>
    <CorporationName>{insured_name}</CorporationName>
    <NameOnPolicy>{insured_name}</NameOnPolicy>
  </insured>
  <location>
    <LocationName>{insured_name}</LocationName>
    <Address1>{address_1}</Address1>
    <Address2>{address_2}</Address2>
    <City>{city}</City>
    <State>{state}</State>
    <Zip>{zip}</Zip>
    <ISOCountryCode>USA</ISOCountryCode>
    <DeliveryMethodID>1</DeliveryMethodID>
    <LocationTypeID>1</LocationTypeID>
  </location>
</AddInsuredWithLocation>
```

### Hardcoded Values
- **BusinessTypeID**: 9 (Corporation)
- **ISOCountryCode**: USA
- **DeliveryMethodID**: 1
- **LocationTypeID**: 1 (Primary)

## Usage

### Find or Create Insured
```python
from app.services.ims.insured_service import get_insured_service

insured_service = get_insured_service()

# Process a Triton payload
payload = {
    "insured_name": "Thrive Network LLC",
    "address_1": "17229 SW Reem Ln",
    "address_2": "",
    "city": "Beaverton",
    "state": "OR",
    "zip": "97078"
}

success, insured_guid, message = insured_service.find_or_create_insured(payload)

if success:
    print(f"Insured GUID: {insured_guid}")
    # Use this GUID for subsequent operations
else:
    print(f"Failed: {message}")
```

### Direct Creation
```python
# Create insured directly (without searching first)
success, guid, message = insured_service.add_insured_with_location(
    insured_name="New Company LLC",
    address1="123 Main St",
    city="Dallas",
    state="TX",
    zip_code="75001",
    address2="Suite 100"
)
```

## Payload Mapping
Triton Payload → IMS Fields:
- `insured_name` → `CorporationName`, `NameOnPolicy`, `LocationName`
- `address_1` → `Address1`
- `address_2` → `Address2`
- `city` → `City`
- `state` → `State`
- `zip` → `Zip`

## Error Handling
The service handles:
- Missing insured name
- Missing required location fields
- Authentication failures
- Network errors
- XML parsing errors

## Testing
Run the test:
```bash
export IMS_ONE_USERNAME=your_username
export IMS_ONE_PASSWORD=your_encrypted_password
python3 test_find_or_create_insured.py
```

## Next Steps
After obtaining the insured GUID, it can be used for:
- Creating quotes
- Binding policies
- Managing policy documents
- Invoice generation