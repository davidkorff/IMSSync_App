# IMS Authentication Process

## Overview
The IMS authentication service handles login and token management for all IMS web service calls.

## Configuration
Set the following environment variables or add them to a `.env` file:

```bash
IMS_BASE_URL=http://10.64.32.234/ims_one
IMS_ONE_USERNAME=your_username
IMS_ONE_PASSWORD=your_triple_des_encrypted_password
```

## Authentication Flow

### 1. Login Request
- **Endpoint**: `POST http://10.64.32.234/ims_one/logon.asmx`
- **SOAPAction**: `http://tempuri.org/IMSWebServices/Logon/LoginIMSUser`
- **Content-Type**: `text/xml; charset=utf-8`

**Request Body**:
```xml
<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
               xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <LoginIMSUser xmlns="http://tempuri.org/IMSWebServices/Logon">
            <userName>your_username</userName>
            <tripleDESEncryptedPassword>your_encrypted_password</tripleDESEncryptedPassword>
        </LoginIMSUser>
    </soap:Body>
</soap:Envelope>
```

### 2. Success Response
```xml
<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" 
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
               xmlns:xsd="http://www.w3.org/2001/XMLSchema">
    <soap:Body>
        <LoginIMSUserResponse xmlns="http://tempuri.org/IMSWebServices/Logon">
            <LoginIMSUserResult xsi:type="LoginReturnExt">
                <UserGuid>fb01e05b-fbc3-467c-bd25-7163c63080a4</UserGuid>
                <Token>d66c6744-a467-4602-894e-8a226bd5b6ea</Token>
            </LoginIMSUserResult>
        </LoginIMSUserResponse>
    </soap:Body>
</soap:Envelope>
```

### 3. Failure Response
When authentication fails, the response contains null GUIDs:
```xml
<UserGuid>00000000-0000-0000-0000-000000000000</UserGuid>
<Token>00000000-0000-0000-0000-000000000000</Token>
```

## Usage

### Import and Initialize
```python
from app.services.ims.auth_service import get_auth_service

# Get singleton instance
auth_service = get_auth_service()
```

### Login
```python
success, message = auth_service.login()
if success:
    print(f"Logged in successfully. Token: {auth_service.token}")
else:
    print(f"Login failed: {message}")
```

### Get Token for API Calls
```python
# Token is automatically refreshed if expired
token = auth_service.token

# Get headers for authenticated requests
headers = auth_service.get_auth_headers()
```

### Check Authentication Status
```python
if auth_service.is_authenticated():
    print("Currently authenticated")
else:
    print("Not authenticated")
```

## Token Management
- Tokens are cached with an 8-hour expiry
- The `token` property automatically refreshes expired tokens
- Use `get_auth_headers()` to get properly formatted headers for IMS requests

## Testing
Run the standalone test:
```bash
export IMS_ONE_USERNAME=your_username
export IMS_ONE_PASSWORD=your_encrypted_password
python3 test_ims_standalone.py
```

## Security Notes
1. The password must be Triple DES encrypted before sending to IMS
2. Never log or display the full token or password
3. Tokens should be treated as sensitive data
4. The service automatically handles token expiration and refresh