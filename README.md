# RSG Integration Service

A FastAPI-based service that processes Triton insurance transactions and integrates with IMS (Insurance Management System) web services.

## Features

- **Transaction Processing**: Handles multiple transaction types:
  - **Bind**: Creates insured, submission, quote, and binds the policy
  - **Unbind**: Unbinds an existing policy
  - **Issue**: Issues a bound policy
  - **Midterm Endorsement**: Creates and binds endorsements
  - **Cancellation**: Cancels policies with invoice generation

- **Modular Architecture**: Separate service modules for each IMS interaction
- **Invoice Management**: Automatic invoice retrieval for Bind, Midterm Endorsement, and Cancellation transactions
- **Excel Rater Support**: Upload Excel rater files for quotes
- **Policy Tracking**: Persistent storage of policy number to GUID mappings

## Architecture

```
app/
├── api/                    # API endpoints
│   ├── triton.py          # Triton transaction endpoints
│   └── ims.py             # Direct IMS service endpoints
├── services/              # Business logic
│   ├── ims/              # IMS service modules
│   │   ├── auth_service.py
│   │   ├── insured_service.py
│   │   ├── quote_service.py
│   │   └── invoice_service.py
│   └── triton_processor.py
├── models/                # Data models
└── utils/                 # Utilities
```

## Installation

### Local Development

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and configure:
   ```bash
   cp .env.example .env
   ```
5. Run the service:
   ```bash
   python main.py
   ```

### Docker

1. Build and run with Docker Compose:
   ```bash
   docker-compose up -d
   ```

## Configuration

Configure the service using environment variables:

- `IMS_BASE_URL`: Base URL for IMS web services
- `IMS_ONE_USERNAME`: IMS username for authentication
- `IMS_ONE_PASSWORD`: Triple DES encrypted password for IMS
- `IMS_PROGRAM_CODE`: IMS program code (default: TRTON)
- `IMS_PROJECT_NAME`: IMS project name (default: RSG_Integration)
- `TRITON_API_KEY`: API key for Triton authentication
- `DEBUG`: Enable debug mode
- `LOG_LEVEL`: Logging level (INFO, DEBUG, ERROR)

## API Endpoints

### Triton Endpoints

- `POST /api/triton/transaction/new`: Process new transaction
- `POST /api/triton/transaction/{transaction_id}/excel-rater`: Upload Excel rater

### IMS Direct Endpoints

- `GET /api/ims/insured/search`: Search for insured by name and address
- `POST /api/ims/insured`: Create new insured
- `GET /api/ims/invoice/{policy_guid}`: Get invoice details
- `GET /api/ims/invoice/{policy_guid}/pdf`: Download invoice PDF

### Health Check

- `GET /`: Basic health check
- `GET /health`: Detailed health information

## Transaction Flow

### Bind Transaction
1. Search for existing insured by name and address
2. Create insured if not found
3. Create submission
4. Create quote
5. Bind quote to create policy
6. Retrieve invoice details
7. Store policy mapping

### Midterm Endorsement
1. Look up policy by policy number
2. Create endorsement transaction
3. Bind endorsement
4. Retrieve invoice details

## Development

### Project Structure
- Services are modular and can be used independently
- Each IMS service inherits from `BaseIMSService`
- Authentication tokens are managed automatically
- Policy mappings are stored in `data/policies.json`

### Adding New Transaction Types
1. Add the transaction type to the `TritonPayload` model
2. Implement processing method in `TritonProcessor`
3. Add any required IMS service methods
4. Update documentation

## Testing

Example test payload:
```json
{
  "transaction_type": "Bind",
  "transaction_id": "5754934b-a66c-4173-8972-ab6c7fe1d384",
  "policy_number": "GAH-106050-250924",
  "insured_name": "BLC Industries, LLC",
  "address_1": "2222 The Dells",
  "city": "Kalamazoo",
  "state": "MI",
  "zip": "49048",
  ...
}
```

## Error Handling

- All endpoints return appropriate HTTP status codes
- Detailed error messages in response body
- Comprehensive logging for debugging
- Transaction rollback on failure

## Security

- SOAP authentication tokens expire after 1 hour
- Environment-based configuration
- CORS configured for API access
- No hardcoded credentials

## Troubleshooting

### Authentication Errors

If you get authentication errors:
1. Ensure `IMS_ONE_USERNAME` and `IMS_ONE_PASSWORD` are set in your `.env` file
2. The password must be Triple DES encrypted - do not use plain text
3. Check that the IMS web services are accessible from your server

### Common Error Messages

- **"contactType must be either I, P, or C"**: This indicates the wrong login method is being used. The service should use `LoginIMSUser` not `Login`.
- **"Server was unable to process request"**: Check your credentials and ensure the IMS service is available.
- **"Policy not found"**: The policy number doesn't exist in the local store. Ensure the policy was created through a Bind transaction first.