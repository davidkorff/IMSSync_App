# Triton-RSG IMS Integration Requirements

## Overview

This document outlines the requirements and specifications for integrating the Triton system with the RSG IMS Integration API. The integration enables seamless policy data transfer between Triton and RSG's IMS platform.

## Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0 | 2025-05-19 | David Korff | Initial specification |

## Integration Architecture

The integration follows a unidirectional push model where Triton sends transaction data to RSG's API at specific trigger points in the policy lifecycle. The architecture consists of:

1. **Event Triggers**: Points in the Triton system where transactions are initiated
2. **Transaction Formatting**: Preparing data in the required format
3. **API Communication**: Securely sending data to RSG's API endpoint
4. **Asynchronous Processing**: RSG processes transactions asynchronously and provides status endpoints

![Architecture Diagram](https://via.placeholder.com/800x400?text=Triton-RSG+Integration+Architecture)

## API Endpoint

### Base URL

**Production**: `https://api.rsgims.com/triton/api/v1`  
**Staging**: `https://api-staging.rsgims.com/triton/api/v1`  
**Development**: `https://api-dev.rsgims.com/triton/api/v1`  

### Authentication

All API requests must include the following headers:

```
X-API-Key: [Your API Key]
X-Client-Id: [Your Client ID]
X-Triton-Version: [Optional Triton Version]
```

API keys and client IDs will be provided separately for each environment.

## Endpoints

### Transaction Submission

**POST /transactions**

Submits a new transaction to the RSG system.

**Request Body**: JSON object containing transaction data (see Data Models section)

**Response**:
```json
{
  "transaction_id": "string",
  "status": "received",
  "reference_id": "RSG-[transaction_id]",
  "message": "string"
}
```

### Transaction Status

**GET /transactions/{transaction_id}**

Retrieves the status of a previously submitted transaction.

**Response**:
```json
{
  "transaction_id": "string",
  "status": "string",
  "ims_status": "string",
  "message": "string"
}
```

## Data Models

The integration supports three transaction types, each with its own data model.

### 1. Binding Transaction

Used when a new policy is bound or a policy is renewed.

```json
{
  "transaction_type": "binding",
  "transaction_id": "string (UUID)",
  "transaction_date": "ISO-8601 date",
  
  "policy_number": "string",
  "effective_date": "ISO-8601 date",
  "expiration_date": "ISO-8601 date",
  "retroactive_date": "ISO-8601 date (optional)",
  "gl_retroactive_date": "ISO-8601 date (optional)",
  "is_renewal": boolean,
  
  "account": {
    "id": "string (optional)",
    "name": "string",
    "street_1": "string",
    "street_2": "string (optional)",
    "city": "string",
    "state": "string",
    "zip": "string",
    "full_address": "string (optional)",
    "mailing_address": {
      "street_1": "string",
      "street_2": "string (optional)",
      "city": "string",
      "state": "string",
      "zip": "string"
    }
  },
  
  "producer": {
    "id": "string (optional)",
    "name": "string",
    "first_name": "string (optional)",
    "last_name": "string (optional)",
    "email": "string (optional)",
    "phone": "string (optional)",
    "agency_id": "string (optional)",
    "agency_name": "string (optional)",
    "agency": {
      "id": "string",
      "name": "string",
      "address": "string (optional)",
      "terms": "string (optional)",
      "email": "string (optional)",
      "active": boolean (optional)
    }
  },
  
  "broker_information": {
    // Optional broker details
  },
  
  "program": {
    "id": "string",
    "name": "string"
  },
  
  "underwriter": {
    "id": "string (optional)",
    "name": "string (optional)",
    "email": "string (optional)"
  },
  
  "premium": {
    "annual_premium": number,
    "annual_premium_rounded": number (optional),
    "policy_fee": number (optional),
    "taxes_and_fees": object (optional),
    "grand_total": number (optional),
    "premium_entries": array (optional),
    "commission_rate": number (optional),
    "invoice_line_items": array (optional),
    "invoice_number": "string (optional)",
    "invoice_date": "ISO-8601 date (optional)",
    "invoice_due_date": "ISO-8601 date (optional)"
  },
  
  "exposures": [
    {
      "id": "string (optional)",
      "program_class_id": "string (optional)",
      "program_class_name": "string (optional)",
      "coverage_id": "string (optional)",
      "coverage_name": "string (optional)",
      "territory_id": "string (optional)",
      "territory_name": "string (optional)",
      "limit": object (optional),
      "deductible": (object|number) (optional)
    }
  ],
  
  "endorsements": [
    {
      "id": "string (optional)",
      "endorsement_id": "string (optional)",
      "endorsement_code": "string (optional)",
      "endorsement_name": "string (optional)",
      "input_text": "string (optional)",
      "input_value": any (optional),
      "retroactive_date": "ISO-8601 date (optional)"
    }
  ]
}
```

### 2. Midterm Endorsement Transaction

Used when a policy endorsement is created, invoiced, paid, or voided.

```json
{
  "transaction_type": "midterm_endorsement",
  "transaction_id": "string (UUID)",
  "transaction_date": "ISO-8601 date",
  "transaction_status": "string (created|invoiced|paid|voided)",
  
  "policy_number": "string",
  "effective_date": "ISO-8601 date",
  "expiration_date": "ISO-8601 date",
  
  "endorsement": {
    "id": "string",
    "endorsement_id": "string (optional)",
    "endorsement_code": "string (optional)",
    "endorsement_number": "string (optional)",
    "description": "string (optional)",
    "effective_from": "ISO-8601 date (optional)",
    "premium": number (optional),
    "premium_description": "string (optional)",
    "invoice_number": "string (optional)",
    "invoice_date": "ISO-8601 date (optional)",
    "paid_date": "ISO-8601 date (optional)",
    "void_date": "ISO-8601 date (optional)",
    "credit": boolean (optional)
  },
  
  "invoice_details": {
    "invoice_line_items": array (optional),
    "invoice_total": number (optional),
    "invoice_due_date": "ISO-8601 date (optional)"
  },
  
  "account": {
    "id": "string",
    "name": "string"
  },
  
  "producer": {
    // Same structure as in binding transaction
  }
}
```

### 3. Cancellation Transaction

Used when a policy is cancelled.

```json
{
  "transaction_type": "cancellation",
  "transaction_id": "string (UUID)",
  "transaction_date": "ISO-8601 date",
  
  "policy_number": "string",
  "effective_date": "ISO-8601 date",
  "expiration_date": "ISO-8601 date",
  "cancellation_date": "ISO-8601 date",
  "cancellation_reason": "string",
  
  "days_in_effect": number (optional),
  "return_premium_entries": array (optional),
  
  "account": {
    "id": "string",
    "name": "string"
  },
  
  "producer": {
    // Same structure as in binding transaction
  },
  
  "original_premium": object (optional)
}
```

## Implementation Requirements

### Triton System Changes

The Triton system will need the following modifications:

1. **API Client Implementation**:
   - Create an HTTP client to communicate with the RSG API
   - Implement proper authentication and headers
   - Handle timeouts and retries

2. **Transaction Handling**:
   - Create data models matching the required schemas
   - Implement transformers to convert from Triton's internal format
   - Create transaction queue for failed transactions

3. **Integration Points**:
   - Modify BindOpportunityInteractor to send binding transactions
   - Modify OpportunityMidtermEndorsementsController to send endorsement transactions
   - Modify CancelOpportunityInteractor to send cancellation transactions

4. **Configuration**:
   - Environment-specific settings for API URLs
   - Secure storage of API keys

5. **Monitoring and Logging**:
   - Track all API communications
   - Create alerting for failed transactions
   - Implement transaction logging

### Environment Configuration

Add the following environment variables to your deployment configuration:

```
# RSG API Settings
RSG_API_BASE_URL=https://api.rsgims.com/triton/api/v1
RSG_API_KEY=your_api_key_here
RSG_CLIENT_ID=triton
RSG_TIMEOUT=30
RSG_MAX_RETRIES=3
RSG_INTEGRATION_ENABLED=true
```

## Error Handling

### HTTP Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid input data |
| 401 | Unauthorized - Invalid API key or client ID |
| 404 | Not Found - Resource not found |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server-side error |

### Error Response Format

```json
{
  "status_code": number,
  "detail": "string",
  "errors": [
    {
      "field": "string",
      "message": "string"
    }
  ]
}
```

### Retry Strategy

For transient errors (HTTP 429, 500, 502, 503, 504):
1. Implement exponential backoff (5^retry_count minutes)
2. Maximum 3 retry attempts
3. Log failed transactions after max retries
4. Send alerts to operations team for manual intervention

## Testing

### Test Environments

| Environment | URL | Description |
|-------------|-----|-------------|
| Development | https://api-dev.rsgims.com/triton/api/v1 | For initial integration testing |
| Staging | https://api-staging.rsgims.com/triton/api/v1 | For pre-production validation |
| Production | https://api.rsgims.com/triton/api/v1 | Production environment |

### Test Credentials

Development and staging credentials will be provided separately.

### Test Plan

1. **Unit Testing**:
   - Validate transaction data models
   - Test API client with mock responses
   - Test error handling and retry logic

2. **Integration Testing**:
   - Test binding workflow with sample policies
   - Test endorsement workflow with various scenarios
   - Test cancellation workflow
   - Validate transaction status checking

3. **End-to-End Testing**:
   - Complete policy lifecycle testing
   - Error scenario testing
   - Performance and load testing

## Implementation Timeline

| Phase | Timeline | Description |
|-------|----------|-------------|
| 1 | Week 1-2 | API client implementation and data models |
| 2 | Week 3-4 | Integration points and transaction handling |
| 3 | Week 5-6 | Error handling, logging, and monitoring |
| 4 | Week 7-8 | Testing and validation |
| 5 | Week 9-10 | Deployment and go-live |

## Production Deployment Checklist

- [ ] API credentials secured in environment variables
- [ ] All unit and integration tests passing
- [ ] Logging and monitoring implemented
- [ ] Error handling and retry strategy verified
- [ ] Support procedures documented
- [ ] Rollback plan defined
- [ ] Performance tested under expected load

## Support and Operations

### Contact Information

**RSG Technical Support**:
- Email: ims-support@rsg.com
- Phone: (555) 123-4567
- Hours: 9 AM - 5 PM EST, Monday-Friday

**Escalation Path**:
1. Technical Support Team
2. Integration Project Manager
3. Technical Director

### Monitoring Recommendations

1. **Transaction Success Rate**:
   - Monitor percentage of successful transactions
   - Alert threshold: < 95% success rate

2. **API Response Time**:
   - Track average and P95 response times
   - Alert threshold: > 2s average, > 5s P95

3. **Failed Transactions**:
   - Track number of failed transactions
   - Alert threshold: > 5 consecutive failures or > 10 failures per hour

4. **Retry Queue**:
   - Monitor size of retry queue
   - Alert threshold: > 20 transactions in retry queue

## Appendix

### Sample Requests and Responses

#### Binding Transaction

**Request**:
```json
{
  "transaction_type": "binding",
  "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "transaction_date": "2025-05-19T14:30:00Z",
  "policy_number": "AHC-12345",
  "effective_date": "2025-06-01T00:00:00Z",
  "expiration_date": "2026-06-01T00:00:00Z",
  "account": {
    "name": "Acme Corp",
    "street_1": "123 Main St",
    "city": "Anytown",
    "state": "CA",
    "zip": "90210"
  },
  "producer": {
    "name": "John Smith",
    "agency": {
      "id": "AG-001",
      "name": "ABC Insurance Agency"
    }
  },
  "program": {
    "id": "PROG-001",
    "name": "AHC Primary"
  },
  "premium": {
    "annual_premium": 10000.00
  },
  "exposures": [
    {
      "coverage_name": "General Liability",
      "limit": {
        "each_occurrence": 1000000,
        "general_aggregate": 2000000
      },
      "deductible": 5000
    }
  ]
}
```

**Response**:
```json
{
  "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "received",
  "reference_id": "RSG-550e8400-e29b-41d4-a716-446655440000",
  "message": "Triton binding transaction received successfully and queued for processing"
}
```

### Changelog

**v1.0 (2025-05-19)**
- Initial documentation release