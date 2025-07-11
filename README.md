# RSG IMS Integration Service

A comprehensive integration service that connects external insurance systems (like Triton) with IMS (Insurance Management System) through a microservice architecture.

## Overview

This service provides REST API endpoints for:
- Processing NEW BUSINESS transactions from external sources
- Policy lifecycle operations (cancellation, endorsement, reinstatement)
- Invoice generation and retrieval
- Complete integration with IMS SOAP web services

## Architecture

### Microservice Architecture

The system uses a modular microservice architecture with the following services:

1. **Insured Service** - Manages insured entities with fuzzy matching capabilities
2. **Quote Service** - Handles submissions, quotes, rating, and binding
3. **Policy Service** - Manages policy lifecycle operations
4. **Invoice Service** - Retrieves and manages invoices with retry logic
5. **Document Service** - Generates policy documents (binders, invoices, etc.)
6. **Producer Service** - Manages producers/agents and underwriters
7. **Data Access Service** - Provides database queries and caching

### Key Components

```
app/
├── api/
│   ├── sources/
│   │   └── triton_routes.py         # Triton-specific endpoints
│   └── invoice_routes.py            # Invoice endpoints
├── microservices/
│   ├── core/                        # Base service infrastructure
│   ├── insured/                     # Insured management
│   ├── quote/                       # Quote/submission handling
│   ├── policy/                      # Policy lifecycle
│   ├── invoice/                     # Invoice operations
│   ├── document/                    # Document generation
│   ├── producer/                    # Producer management
│   └── data_access/                 # Database operations
├── services/
│   ├── triton_processor.py          # Triton transaction processor
│   └── ims/                         # IMS SOAP client and services
└── models/                          # Data models
```

## API Endpoints

### Triton Integration

**Process Transaction**
```http
POST /api/triton/transaction/new
Content-Type: application/json

{
  "transaction_type": "NEW BUSINESS",
  "insured_name": "ABC Company LLC",
  "policy_number": "TRI-123456",
  "effective_date": "2025-01-01",
  "expiration_date": "2026-01-01",
  "premium": 10000.00,
  ...
}
```

### Invoice Operations

**Get Latest Invoice by Policy**
```http
GET /api/invoices/policy/{policy_number}/latest
```

**Get All Invoices by Policy**
```http
GET /api/invoices/policy/{policy_number}
```

**Get Invoice as PDF**
```http
GET /api/invoices/{invoice_guid}/pdf
```

### Policy Lifecycle

The Triton endpoint supports all lifecycle operations through the `transaction_type` field:
- `NEW BUSINESS` - Create new policy
- `CANCEL` - Cancel existing policy
- `MIDTERM_ENDORSEMENT` - Endorse policy
- `REINSTATEMENT` - Reinstate cancelled policy

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd RSG-Integration

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Create a `.env` file with the following variables:

```env
# IMS Credentials
IMS_USERNAME=your_username
IMS_PASSWORD=your_encrypted_password
IMS_ENVIRONMENT=https://yourims.imsone.com

# Default GUIDs (obtain from IMS)
TRITON_DEFAULT_PRODUCER_GUID=
TRITON_PRIMARY_LINE_GUID=
TRITON_EXCESS_LINE_GUID=
TRITON_DEFAULT_UNDERWRITER_GUID=
TRITON_ISSUING_LOCATION_GUID=
TRITON_COMPANY_LOCATION_GUID=
TRITON_QUOTING_LOCATION_GUID=
TRITON_DEFAULT_BUSINESS_TYPE_ID=5
```

## Running the Service

```bash
# Development
uvicorn app.main:app --reload --port 8000

# Production
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Testing

```bash
# Test with sample data
python test_policy_lifecycle.py

# Test specific operations
python test_cancellation_flow.py
python test_endorsement_flow.py
python test_reinstatement_flow.py
```

## Transaction Processing Flow

### NEW BUSINESS Flow
1. Search for insured by name (create if not found)
2. Create submission with default GUIDs
3. Create and rate quote
4. Add premium and fees
5. Bind policy with provided policy number
6. Generate invoice after binding
7. Return comprehensive response with IMS data and invoice

### Key Features
- Automatic insured matching with fuzzy logic
- Retry logic for invoice retrieval
- Comprehensive error handling and logging
- Support for both primary and excess lines
- Flexible premium and fee handling

## Microservice Usage

```python
from app.microservices import get_service

# Get services
insured_service = get_service('insured')
quote_service = get_service('quote')
policy_service = get_service('policy')

# Use services
response = await insured_service.find_or_create(insured_data)
if response.success:
    insured = response.data
```

## Response Format

```json
{
  "success": true,
  "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "ims_response": {
    "insured_guid": "...",
    "submission_guid": "...",
    "quote_guid": "...",
    "policy_number": "TRI-123456"
  },
  "invoice_details": {
    "invoice_number": "INV-001",
    "total_amount": "10500.00",
    "due_date": "2025-02-01"
  }
}
```

## Error Handling

The service provides detailed error responses:
```json
{
  "success": false,
  "error": "Detailed error message",
  "transaction_id": "..."
}
```

## Documentation

- [Policy Lifecycle Operations](POLICY_LIFECYCLE_OPERATIONS.md)
- [Integration Guide](INTEGRATION_GUIDE.md)
- [Endpoint Summary](ENDPOINT_SUMMARY.md)
- [Microservice Architecture](MICROSERVICE_ARCHITECTURE_DESIGN.md)

## Support

For issues or questions:
1. Check the documentation in the `Documentation/` folder
2. Review test files for usage examples
3. Contact the development team