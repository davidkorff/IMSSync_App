# IMS Integration

This project provides a service to integrate bound policy data from external sources (like Triton) into the IMS (Insurance Management System) platform.

## Overview

The integration allows importing bound policy data from various sources (like Triton) and creating submissions and quotes in IMS through its SOAP web services. The service exposes REST API endpoints that accept JSON or XML payloads and processes them asynchronously.

## Architecture

The integration follows a modern web service architecture:

1. **REST API Layer**: FastAPI-based endpoints for receiving transaction data from external systems.

2. **Transaction Processing**: Asynchronous processing of incoming transactions with status tracking.

3. **Data Transformation**: Conversion of source-specific data to the common policy model.

4. **IMS Integration Layer**: The core integration layer that interacts with IMS SOAP APIs.

## Components

- **app/main.py**: FastAPI application entry point
- **app/api/routes.py**: API endpoint definitions
- **app/services/transaction_service.py**: Manages transactions and their lifecycle
- **app/services/transaction_processor.py**: Processes transactions based on their type
- **app/services/ims_integration_service.py**: Main integration module that works with IMS
- **app/services/ims_soap_client.py**: Handles SOAP XML request/response processing
- **app/models/policy_data.py**: Data models for transactions and policy data
- **app/core/config.py**: Configuration settings for different environments
- **IMS_Configs/**: Configuration files for different IMS environments
- **Documentation/**: Documentation for IMS web services
- **OutstandingQuestions.txt**: Tracking document for open questions and issues

## Requirements

- Python 3.9+
- Required packages: See requirements.txt

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd rsg-integration

# Create and activate a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Service

```bash
# Start the service with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The service will start and listen for incoming transactions on port 8000.

## API Endpoints

### Transaction Endpoints

**Create a New Transaction**

```http
POST /api/transaction/new
Content-Type: application/json
X-API-Key: your-api-key

{
  "policy": {
    "policy_number": "TRI-123456",
    "effective_date": "2025-06-01",
    "expiration_date": "2026-06-01",
    "bound_date": "2025-05-15",
    ... (other policy data)
  }
}
```

**Update an Existing Policy**

```http
POST /api/transaction/update
Content-Type: application/json
X-API-Key: your-api-key

{
  "policy_number": "TRI-123456",
  "updates": {
    "premium": 15000.00,
    ... (other fields to update)
  }
}
```

**Check Transaction Status**

```http
GET /api/transaction/{transaction_id}
X-API-Key: your-api-key
```

**Health Check**

```http
GET /api/health
```

## Configuration

Edit the `.env` file to set environment variables:

```
API_KEYS=["your-api-key-1", "your-api-key-2"]
IMS_ONE_USERNAME=your-username
IMS_ONE_PASSWORD=your-encrypted-password
ISCMGA_TEST_USERNAME=your-username
ISCMGA_TEST_PASSWORD=your-encrypted-password
```

## Data Model

The integration uses a common data model (PolicyData) that includes:

- Policy Identification: policy number, program, line of business
- Dates: effective date, expiration date, bound date
- Insured Information: name, address, contact details
- Parties: producer, underwriter, locations
- Policy Details: limits, deductibles, commission
- Financial Information: premium
- Additional Data: source-specific information

## Transaction Processing

The service processes incoming transactions asynchronously:

1. When a transaction is received, it's assigned a unique transaction ID and stored
2. The transaction is queued for processing in the background
3. The client can check the status of the transaction using the transaction ID
4. Once processing is complete, the transaction status is updated

## Data Formats

The service supports both JSON and XML data formats. The content type header should be set appropriately:

- `application/json` for JSON data
- `application/xml` or `text/xml` for XML data

If the content type is not specified, the service will attempt to determine the format from the content.

## Implementing New Features

To extend the transaction processor:

1. Update the `_transform_to_policy_submission` method in `transaction_processor.py` to map from Triton's data format to the PolicySubmission model
2. Implement any additional validation or business logic in the transaction processor
3. Add new endpoints to the API as needed

## Deployment

The service can be deployed using various methods:

### Docker

To containerize the application (Dockerfile to be created):

```bash
# Build Docker image
docker build -t rsg-ims-integration .

# Run container
docker run -d -p 8000:8000 --name rsg-ims-integration rsg-ims-integration
```

### Production Deployment

For production, it's recommended to use Gunicorn as the WSGI server:

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Security

The service uses API keys for authentication. Each API key can be associated with specific permissions or rate limits as needed.

API keys are defined in the `.env` file or environment variables:

## Data Mapping

The integration maps the following data from source systems to IMS:

### Authentication Data
- Username
- Password (triple DES encrypted)

### Submission Data
- Insured (guid)
- ProducerContact (guid)
- Underwriter (guid)
- SubmissionDate (date)
- ProducerLocation (guid)
- TACSR (guid) - Technical Assistant/Customer Service Rep
- InHouseProducer (guid)

### Quote Data
- Submission (guid - created from submission data)
- QuotingLocation (guid)
- IssuingLocation (guid)
- CompanyLocation (guid)
- Line (guid)
- StateID (string)
- ProducerContact (guid)
- QuoteStatusID (int)
- Effective (date)
- Expiration (date)
- BillingTypeID (int)
- FinanceCompany (guid)

### Quote Detail
- CompanyCommission (decimal)
- ProducerCommission (decimal)
- TermsOfPayment (int)
- ProgramCode (string)
- CompanyContactGuid (guid)
- RaterID (int)
- FactorSetGuid (guid)
- ProgramID (int)
- LineGUID (guid)
- CompanyLocationGUID (guid)

### Risk Information
- PolicyName (string)
- CorporationName (string)
- DBA (string)
- Contact details (Name, Address, etc.)
- Tax identifiers (SSN/FEIN)
- Contact information (Phone, Fax, etc.)
- BusinessType (int)
