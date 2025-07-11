# Microservice Architecture Implementation

## Overview

The IMS Integration system has been fully refactored into a microservice architecture. All services are now implemented and operational, providing independent, reusable components that can be leveraged by any route or integration.

## Architecture Principles

1. **Single Responsibility**: Each microservice handles one business domain
2. **Loose Coupling**: Services communicate through well-defined interfaces
3. **High Cohesion**: Related functionality stays together
4. **Service Independence**: Each service can be deployed and scaled independently
5. **Standardized Communication**: All services use the same patterns for interaction

## Implemented Microservice Structure

```
app/microservices/
├── core/
│   ├── __init__.py
│   ├── base_service.py          # Base class for all microservices
│   ├── service_registry.py      # Service discovery and registration
│   ├── exceptions.py            # Common exceptions
│   └── models.py               # Shared data models
│
├── data_access/
│   ├── __init__.py
│   ├── service.py              # DataAccessService - Database queries & caching
│   └── models.py               # Query and cache models
│
├── insured/
│   ├── __init__.py
│   ├── service.py              # InsuredService - Insured management
│   ├── models.py               # Insured models
│   └── matcher.py              # Fuzzy matching logic
│
├── quote/
│   ├── __init__.py
│   ├── service.py              # QuoteService - Submission, quote, rating, binding
│   └── models.py               # Quote/Submission models
│
├── policy/
│   ├── __init__.py
│   ├── service.py              # PolicyService - Lifecycle operations
│   └── models.py               # Policy models
│
├── invoice/
│   ├── __init__.py
│   ├── service.py              # InvoiceService - Invoice retrieval with retry
│   └── models.py               # Invoice models
│
├── document/
│   ├── __init__.py
│   ├── service.py              # DocumentService - Document generation
│   └── models.py               # Document models
│
├── producer/
│   ├── __init__.py
│   ├── service.py              # ProducerService - Producer/agent management
│   └── models.py               # Producer models
│
└── __init__.py                 # Service initialization and registration
```

## Service Descriptions

### 1. Core Infrastructure (`core/`)

**BaseMicroservice**
- Base class for all microservices
- Provides common functionality: logging, health checks, SOAP client management
- Implements service lifecycle methods

**ServiceRegistry**
- Singleton registry for service management
- Lazy instantiation of services
- Dependency injection support

### 2. DataAccessService (`data_access/`)

**Purpose**: Database operations and caching

**Key Features**:
- Execute SQL queries with parameterization
- Store and retrieve program-specific data
- Cache lookup data (business types, states, etc.)
- Redis caching support

**Example Usage**:
```python
data_service = get_service('data_access')

# Execute query
query = QueryRequest(
    query="SELECT * FROM Insureds WHERE Name LIKE @Name",
    parameters={"Name": "%ABC Company%"}
)
result = await data_service.execute_query(query)

# Get cached lookup data
business_types = await data_service.get_lookup_data(LookupType.BUSINESS_TYPES)
```

### 3. InsuredService (`insured/`)

**Purpose**: Manage insured entities

**Key Features**:
- Find or create insureds with fuzzy matching
- Search by name, FEIN, or address
- Automatic matching with configurable thresholds
- Source system tracking

**Example Usage**:
```python
insured_service = get_service('insured')

insured_data = InsuredCreate(
    name="ABC Company LLC",
    tax_id="12-3456789",
    address="123 Main St",
    city="Dallas",
    state="TX",
    zip_code="75201"
)

response = await insured_service.find_or_create(insured_data)
```

### 4. QuoteService (`quote/`)

**Purpose**: Handle submissions, quotes, rating, and binding

**Key Features**:
- Create submissions
- Create and rate quotes
- Add premiums and fees
- Bind quotes to create policies
- Issue policies

**Example Usage**:
```python
quote_service = get_service('quote')

# Create submission
submission = await quote_service.create_submission(submission_data)

# Create quote
quote = await quote_service.create_quote(quote_data)

# Rate quote
rating = await quote_service.rate_quote(rating_request)

# Bind quote
bind_result = await quote_service.bind_quote(bind_request)
```

### 5. PolicyService (`policy/`)

**Purpose**: Policy lifecycle operations

**Key Features**:
- Get control numbers
- Cancel policies
- Create endorsements
- Reinstate policies
- Track policy status

**Example Usage**:
```python
policy_service = get_service('policy')

# Cancel policy
cancel_request = CancellationRequest(
    control_number=control_number,
    cancellation_date=date.today(),
    cancellation_reason_id=1
)
result = await policy_service.cancel_policy(cancel_request)
```

### 6. InvoiceService (`invoice/`)

**Purpose**: Invoice management

**Key Features**:
- Get latest invoice by policy
- Retrieve all invoices
- Built-in retry logic
- Invoice status tracking

**Example Usage**:
```python
invoice_service = get_service('invoice')

# Get latest invoice with retry
invoice = await invoice_service.get_latest_by_policy(
    policy_number="TRI-123456",
    max_attempts=3
)
```

### 7. DocumentService (`document/`)

**Purpose**: Document generation

**Key Features**:
- Generate policy documents
- Support multiple formats (PDF, DOC)
- Document types: Binder, Invoice, Policy, Endorsement
- Template-based generation

**Example Usage**:
```python
document_service = get_service('document')

doc_request = GenerateDocumentRequest(
    document_type=DocumentType.BINDER,
    policy_number="TRI-123456",
    format="PDF"
)
document = await document_service.generate_document(doc_request)
```

### 8. ProducerService (`producer/`)

**Purpose**: Producer/agent management

**Key Features**:
- Find producers by name or GUID
- Create new producers
- Manage producer contacts
- Find underwriters
- Commission tracking

**Example Usage**:
```python
producer_service = get_service('producer')

# Find producer by name
producer = await producer_service.get_by_name("ABC Agency")

# Find underwriter
underwriter = await producer_service.find_underwriter_by_name("John Doe")
```

## Service Communication

Services communicate through:

1. **ServiceRegistry**: Get service instances
2. **ServiceResponse**: Standardized response format
3. **Async/Await**: All service methods are async

### Response Format

```python
@dataclass
class ServiceResponse:
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    warnings: Optional[List[str]] = None
```

## Complete Workflow Example

The `triton_processor_microservices.py` file demonstrates a complete NEW BUSINESS workflow using all services:

```python
class TritonProcessorMicroservices:
    def __init__(self):
        # Get all services
        self.insured_service = get_service('insured')
        self.producer_service = get_service('producer')
        self.quote_service = get_service('quote')
        self.policy_service = get_service('policy')
        self.invoice_service = get_service('invoice')
        self.document_service = get_service('document')
        self.data_access_service = get_service('data_access')
    
    async def process_new_business(self, data):
        # 1. Find or create insured
        # 2. Get producer information
        # 3. Create submission
        # 4. Create quote
        # 5. Rate the quote
        # 6. Bind the policy
        # 7. Issue the policy
        # 8. Retrieve invoice
        # 9. Generate documents
        # 10. Store transaction data
```

## Health Monitoring

All services implement health checks:

```python
health_status = await service.health_check()
# Returns: ServiceHealth with status, version, uptime, dependencies
```

## Configuration

Services use environment variables for configuration:

```env
# Service-specific settings
INSURED_MATCH_THRESHOLD=80
INVOICE_RETRY_DELAY=2
DOCUMENT_TEMPLATE_PATH=/templates

# Default GUIDs
DEFAULT_PRODUCER_GUID=...
DEFAULT_UNDERWRITER_GUID=...
```

## Benefits of This Architecture

1. **Modularity**: Each service is independent
2. **Reusability**: Services can be used by any integration
3. **Maintainability**: Clear separation of concerns
4. **Testability**: Services can be tested in isolation
5. **Scalability**: Services can be scaled independently
6. **Error Isolation**: Failures are contained within services

## Future Enhancements

While all core services are implemented, potential enhancements include:

1. **Service Mesh**: Add service discovery and load balancing
2. **Event Bus**: Implement event-driven communication
3. **API Gateway**: Centralized API management
4. **Monitoring**: Enhanced metrics and tracing
5. **Caching**: Distributed caching layer

## Migration from Monolithic

The system maintains backward compatibility while offering the new microservice architecture. Existing code can gradually migrate to use the new services.

## Conclusion

The microservice architecture is fully implemented and operational. All services provide clean interfaces, comprehensive error handling, and are ready for production use. The architecture supports the complete insurance policy lifecycle from quote to claim.