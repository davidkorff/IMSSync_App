# Microservice Architecture Usage Guide

## Overview

The IMS Integration system uses a comprehensive microservice architecture with all core services fully implemented. This guide explains how to use these microservices in your code.

## Quick Start

### 1. Getting a Service

```python
from app.microservices import get_service

# Get service instances
insured_service = get_service('insured')
quote_service = get_service('quote')
policy_service = get_service('policy')
invoice_service = get_service('invoice')
document_service = get_service('document')
producer_service = get_service('producer')
data_access_service = get_service('data_access')
```

Services are created on-demand (lazy instantiation) and cached for reuse.

### 2. Service Response Format

All services return a standardized response:

```python
ServiceResponse:
    success: bool              # Operation success status
    data: Optional[Any]        # Return data (service-specific)
    error: Optional[str]       # Error message if failed
    metadata: Optional[Dict]   # Additional information
    warnings: Optional[List]   # Non-fatal warnings
```

## Available Microservices

### 1. InsuredService

**Purpose**: Manage insured entities with intelligent matching

```python
from app.microservices.insured import InsuredCreate, InsuredSearch

insured_service = get_service('insured')

# Find or create an insured
insured_data = InsuredCreate(
    name="ABC Company LLC",
    tax_id="12-3456789",
    business_type_id=5,
    address="123 Main St",
    city="Dallas",
    state="TX",
    zip_code="75201",
    source="triton",
    external_id="TRI-12345"
)

response = await insured_service.find_or_create(insured_data)
if response.success:
    insured = response.data
    print(f"Insured GUID: {insured.guid}")

# Search for insureds
search_criteria = InsuredSearch(
    name="ABC Company",
    state="TX",
    limit=10
)

results = await insured_service.search(search_criteria)
```

### 2. QuoteService

**Purpose**: Handle submissions, quotes, rating, and binding

```python
from app.microservices.quote import (
    SubmissionCreate, QuoteCreate, RatingRequest, BindRequest
)

quote_service = get_service('quote')

# Create submission
submission_data = SubmissionCreate(
    insured_guid=insured.guid,
    submission_date=date.today(),
    producer_contact_guid=producer_guid,
    underwriter_guid=underwriter_guid
)

submission_response = await quote_service.create_submission(submission_data)
submission = submission_response.data

# Create quote
quote_data = QuoteCreate(
    submission_guid=submission.guid,
    effective_date=date(2025, 1, 1),
    expiration_date=date(2026, 1, 1),
    state="TX",
    line_guid=line_guid,
    quoting_location_guid=location_guid
)

quote_response = await quote_service.create_quote(quote_data)
quote = quote_response.data

# Rate the quote
rating_request = RatingRequest(
    quote_guid=quote.guid,
    rating_method="manual",
    manual_premium=Decimal("10000.00")
)

rating_response = await quote_service.rate_quote(rating_request)
rating = rating_response.data

# Bind the quote
bind_request = BindRequest(
    quote_option_id=rating.quote_option_id,
    policy_number_override="TRI-123456",
    bind_date=date.today()
)

bind_response = await quote_service.bind_quote(bind_request)
policy = bind_response.data
```

### 3. PolicyService

**Purpose**: Policy lifecycle operations

```python
from app.microservices.policy import (
    CancellationRequest, EndorsementRequest, ReinstatementRequest
)

policy_service = get_service('policy')

# Get control number
control_response = await policy_service.get_control_number("TRI-123456")
control_number = control_response.data["control_number"]

# Cancel policy
cancel_request = CancellationRequest(
    control_number=control_number,
    cancellation_date=date.today(),
    cancellation_reason_id=1,
    comments="Cancelled per insured request",
    flat_cancel=False
)

cancel_response = await policy_service.cancel_policy(cancel_request)

# Create endorsement
endorse_request = EndorsementRequest(
    control_number=control_number,
    endorsement_effective_date=date.today(),
    endorsement_reason_id=1,
    endorsement_comment="Premium adjustment",
    premium_change=Decimal("500.00")
)

endorse_response = await policy_service.create_endorsement(endorse_request)

# Reinstate policy
reinstate_request = ReinstatementRequest(
    control_number=control_number,
    reinstatement_date=date.today(),
    reinstatement_reason_id=1,
    comments="Payment received",
    payment_received=Decimal("1000.00")
)

reinstate_response = await policy_service.reinstate_policy(reinstate_request)
```

### 4. InvoiceService

**Purpose**: Invoice retrieval with automatic retry

```python
invoice_service = get_service('invoice')

# Get latest invoice with retry
invoice_response = await invoice_service.get_latest_by_policy(
    policy_number="TRI-123456",
    max_attempts=3  # Will retry up to 3 times with delays
)

if invoice_response.success:
    invoice = invoice_response.data
    print(f"Invoice: {invoice.invoice_number}")
    print(f"Amount: ${invoice.total_amount}")
    print(f"Due Date: {invoice.due_date}")

# Get all invoices
all_invoices = await invoice_service.get_invoices_by_policy("TRI-123456")

# Get invoice by GUID
invoice = await invoice_service.get_invoice("invoice-guid-here")
```

### 5. DocumentService

**Purpose**: Generate policy documents

```python
from app.microservices.document import GenerateDocumentRequest, DocumentType

document_service = get_service('document')

# Generate binder
doc_request = GenerateDocumentRequest(
    document_type=DocumentType.BINDER,
    policy_number="TRI-123456",
    format="PDF"
)

doc_response = await document_service.generate_document(doc_request)
if doc_response.success:
    document = doc_response.data
    print(f"Document generated: {document.document_path}")

# Generate invoice as PDF
invoice_doc = GenerateDocumentRequest(
    document_type=DocumentType.INVOICE,
    entity_guid=invoice.guid,
    format="PDF"
)

pdf_response = await document_service.generate_document(invoice_doc)
```

### 6. ProducerService

**Purpose**: Producer/agent management

```python
from app.microservices.producer import ProducerCreate, ProducerContactCreate

producer_service = get_service('producer')

# Find producer by name
producer_response = await producer_service.get_by_name("ABC Agency")

# Create new producer
new_producer = ProducerCreate(
    producer_name="XYZ Insurance Agency",
    producer_code="XYZ001",
    tax_id="98-7654321",
    address1="456 Oak St",
    city="Houston",
    state="TX",
    zip_code="77001",
    contact_first_name="John",
    contact_last_name="Doe",
    contact_email="john@xyzagency.com",
    default_commission_rate=Decimal("15.0")
)

create_response = await producer_service.create_producer(new_producer)

# Find underwriter
underwriter = await producer_service.find_underwriter_by_name("Jane Smith")

# Add producer contact
contact = ProducerContactCreate(
    producer_guid=producer.producer_guid,
    first_name="Sarah",
    last_name="Johnson",
    email="sarah@xyzagency.com",
    phone="555-0123",
    is_primary=True,
    license_number="TX-12345",
    license_states=["TX", "OK", "LA"]
)

contact_response = await producer_service.add_contact(contact)
```

### 7. DataAccessService

**Purpose**: Direct database access and caching

```python
from app.microservices.data_access import QueryRequest, LookupType

data_access_service = get_service('data_access')

# Execute custom query
query = QueryRequest(
    query="""
        SELECT TOP 10 
            PolicyNumber, InsuredName, Premium
        FROM Policies 
        WHERE State = @State 
          AND EffectiveDate >= @StartDate
        ORDER BY Premium DESC
    """,
    parameters={
        "State": "TX",
        "StartDate": "2025-01-01"
    }
)

result = await data_access_service.execute_query(query)
if result.success:
    for row in result.data.tables[0]["rows"]:
        print(f"{row['PolicyNumber']}: ${row['Premium']}")

# Get cached lookup data
business_types = await data_access_service.get_lookup_data(LookupType.BUSINESS_TYPES)
states = await data_access_service.get_lookup_data(LookupType.STATES)
lines = await data_access_service.get_lookup_data(LookupType.LINES)

# Store program-specific data
program_data = ProgramData(
    program="triton",
    quote_guid=quote.guid,
    external_id="TRI-12345",
    data={"custom_field": "value"}
)

await data_access_service.store_program_data(program_data)
```

## Complete Example: NEW BUSINESS Transaction

```python
from app.microservices import get_service
from app.services.triton_processor_microservices import TritonProcessorMicroservices

# Using the complete processor
processor = TritonProcessorMicroservices()

transaction_data = {
    "transaction_type": "NEW BUSINESS",
    "insured_name": "ABC Company LLC",
    "policy_number": "TRI-123456",
    "effective_date": "2025-01-01",
    "expiration_date": "2026-01-01",
    "premium": 10000.00,
    "policy_fee": 250.00,
    "state": "TX",
    "address_1": "123 Main St",
    "city": "Dallas",
    "zip": "75201"
}

result = await processor.process_transaction(transaction_data)

if result["success"]:
    print(f"Policy created: {result['ims_response']['policy_number']}")
    print(f"Invoice: {result['invoice_details']['invoice_number']}")
else:
    print(f"Error: {result['errors']}")
```

## Error Handling

All services provide consistent error handling:

```python
response = await service.some_method(data)

if response.success:
    # Handle success
    result = response.data
    
    # Check for warnings
    if response.warnings:
        for warning in response.warnings:
            logger.warning(warning)
else:
    # Handle error
    logger.error(f"Operation failed: {response.error}")
    
    # Check metadata for additional context
    if response.metadata:
        logger.debug(f"Error context: {response.metadata}")
```

## Health Monitoring

Check service health:

```python
# Individual service health
health = await service.health_check()
print(f"Service: {health.service_name}")
print(f"Status: {health.status.value}")
print(f"Version: {health.version}")
print(f"Uptime: {health.uptime_seconds}s")

# All services health check
processor = TritonProcessorMicroservices()
health_status = await processor.health_check()
print(f"Overall status: {health_status['overall']}")
for service, status in health_status['services'].items():
    print(f"{service}: {status['status']}")
```

## Best Practices

1. **Always check response.success** before using response.data
2. **Use type hints** with service models for better IDE support
3. **Handle warnings** appropriately - they indicate non-fatal issues
4. **Use metadata** for debugging and additional context
5. **Implement retry logic** for transient failures
6. **Log service operations** for troubleshooting
7. **Use transactions** when multiple services need to be coordinated

## Service Dependencies

Some services depend on others:
- QuoteService needs an insured GUID from InsuredService
- PolicyService needs a policy created by QuoteService
- InvoiceService needs a bound policy
- DocumentService may need various entity GUIDs

## Configuration

Services respect environment variables:

```env
# Service configuration
INSURED_MATCH_THRESHOLD=80
INVOICE_RETRY_DELAY=2
INVOICE_MAX_RETRIES=3
DOCUMENT_TEMPLATE_PATH=/templates

# IMS Configuration
IMS_USERNAME=username
IMS_PASSWORD=encrypted_password
IMS_ENVIRONMENT=https://ims.example.com
```

## Troubleshooting

1. **Service not found**: Ensure service is registered in `app/microservices/__init__.py`
2. **SOAP errors**: Check IMS credentials and environment URL
3. **Timeout errors**: Increase service timeout in configuration
4. **Data validation errors**: Review service model requirements
5. **Connection errors**: Verify network connectivity to IMS

## Migration from Old Code

If migrating from the old monolithic code:

```python
# Old way
ims_service = IMSIntegrationService()
result = ims_service.create_insured_and_submission(data)

# New way
insured_service = get_service('insured')
quote_service = get_service('quote')

insured_response = await insured_service.find_or_create(insured_data)
if insured_response.success:
    submission_response = await quote_service.create_submission(submission_data)
```

## Conclusion

The microservice architecture provides clean, modular, and reusable components for all IMS integration needs. Each service is fully documented, tested, and ready for production use.