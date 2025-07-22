# Payload Processing Documentation

## Overview

The Triton payload processing system is designed to handle insurance transaction data through a comprehensive workflow that integrates with IMS (Insurance Management System). The system processes various transaction types including bind, unbind, issue, midterm_endorsement, cancellation, and reinstatement.

## Architecture

### Services

1. **Authentication Service** (`auth_service.py`)
   - Handles IMS login and token management
   - Auto-refreshes expired tokens
   - Maintains singleton instance with 8-hour token expiry

2. **Insured Service** (`insured_service.py`)
   - Finds existing insureds or creates new ones
   - Returns insured GUID for quote creation

3. **Data Access Service** (`data_access_service.py`)
   - Generic ExecuteDataSet implementation
   - Producer lookup functionality

4. **Underwriter Service** (`underwriter_service.py`)
   - Looks up underwriters by name
   - Returns underwriter GUID

5. **Quote Service** (`quote_service.py`)
   - Creates quotes with AddQuoteWithSubmission
   - Returns quote GUID

6. **Quote Options Service** (`quote_options_service.py`)
   - Adds options to quotes via AutoAddQuoteOptions
   - Returns quote option details

7. **Payload Processor Service** (`payload_processor_service.py`)
   - Validates payloads
   - Executes stored procedure to process data
   - Coordinates data storage, policy updates, and premium registration

### Database Components

**Stored Procedure: spProcessTritonPayload_WS**
- Inserts/updates data in `tblTritonQuoteData`
- Updates policy number in `tblquotes`
- Calls `UpdatePremiumHistoricV3` for premium registration

## Processing Flow

### 1. Payload Reception
The system receives a JSON payload from Triton containing transaction details:
```json
{
  "transaction_type": "bind",
  "policy_number": "GAH-106113-251013",
  "insured_name": "Thrive Network LLC",
  "net_premium": 1714,
  // ... additional fields
}
```

### 2. Authentication
- System authenticates with IMS using credentials from .env file
- Token is cached for 8 hours

### 3. Insured Management
- Searches for existing insured by name
- If not found, creates new insured with location data
- Returns insured GUID

### 4. Producer Lookup
- Executes `getProducerbyName_WS` stored procedure
- Returns producer contact and location GUIDs

### 5. Underwriter Lookup
- Executes `getUserbyName_WS` stored procedure  
- Returns underwriter GUID

### 6. Quote Creation
- Creates quote using AddQuoteWithSubmission
- Uses configuration from QUOTE_CONFIG
- Returns quote GUID

### 7. Quote Options
- Adds options to the quote
- Returns quote option GUID

### 8. Payload Processing
- Validates payload fields
- Executes `spProcessTritonPayload_WS` with 40+ parameters
- Stores transaction data
- Updates policy number
- Registers premium

## Transaction Types

- **bind**: Bind the policy
- **unbind**: Unbind the policy
- **issue**: Issue the policy
- **midterm_endorsement**: Process midterm endorsement changes
- **cancellation**: Cancel the policy
- **reinstatement**: Reinstate cancelled policy

## Data Storage

### tblTritonQuoteData
Stores all payload fields including:
- Quote and option GUIDs
- Policy details (number, dates, premiums)
- Insured information
- Producer and underwriter names
- Transaction metadata

### Policy Updates
- Updates `PolicyNumber` field in `tblquotes`
- Links Triton policy numbers to IMS quotes

### Premium Registration
- Uses `UpdatePremiumHistoricV3` procedure
- References `net_premium` column in `tblTritonQuoteData`

## Error Handling

- Each service returns tuple: (success, data/None, message)
- Transactions are wrapped in SQL transactions with rollback
- Comprehensive logging throughout the process
- Validation ensures required fields are present

## Configuration

### Environment Variables
```
IMS_BASE_URL=https://ims.example.com
IMS_ONE_USERNAME=username
IMS_ONE_PASSWORD=encrypted_password
```

### Quote Configuration
Located in `config.py`:
- Line of business settings
- Location GUIDs
- Coverage types
- Default values

## Testing

The complete workflow can be tested using `test_payload_processing.py`:
```bash
python test_payload_processing.py
```

This orchestrates all services in sequence and processes a test payload.

## Integration Points

1. **Triton → IMS**: Receives transaction payloads
2. **IMS SOAP Services**: Authentication, data operations
3. **SQL Server**: Data storage and processing
4. **Premium System**: Premium registration via stored procedures

## Monitoring

- Each service logs operations with timestamps
- Error details include stack traces
- Transaction IDs enable end-to-end tracking

## Security Considerations

- Passwords are Triple DES encrypted
- Tokens expire after 8 hours
- All SOAP communications use HTTPS
- No credentials are logged

## Future Enhancements

1. Batch processing for multiple transactions
2. Retry logic for transient failures
3. Webhook notifications on completion
4. Enhanced validation rules
5. Audit trail for all operations