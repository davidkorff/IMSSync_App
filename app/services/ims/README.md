# IMS Services Module

This module provides a clean, modular interface to IMS web services. Each service is responsible for a specific domain of IMS functionality.

## Architecture Overview

The IMS services module is organized into the following components:

### 1. Base Service (`base_service.py`)
- **IMSAuthenticationManager**: Singleton class that manages authentication tokens across all services
  - Automatic token renewal
  - Thread-safe token management
  - Environment-specific authentication
- **BaseIMSService**: Base class for all IMS services
  - Common error handling
  - Automatic authentication
  - Logging and audit trails

### 2. Domain-Specific Services

#### Insured Service (`insured_service.py`)
Handles all insured-related operations:
- Finding existing insureds
- Creating new insureds
- Managing insured locations
- Managing insured contacts
- Business type determination

#### Producer Service (`producer_service.py`)
Manages producer operations:
- Producer search and lookup
- Producer contact management
- Producer location management
- Underwriter assignments
- Default producer configuration by source system

#### Quote Service (`quote_service.py`)
Handles quote lifecycle:
- Creating submissions
- Creating quotes
- Managing quote options
- Premium operations
- Excel rater integration
- Policy binding and issuance
- External system linking

#### Document Service (`document_service.py`)
Manages document operations:
- Creating policy documents
- Creating quote documents
- Retrieving documents
- Managing rating sheets
- Document associations

#### Data Access Service (`data_access_service.py`)
Provides data access operations:
- Executing queries
- Executing stored procedures
- Managing program-specific data
- Lookup data retrieval
- Cross-system entity search

### 3. Workflow Orchestrator (`workflow_orchestrator.py`)
Coordinates services to implement complete workflows:
- Transaction processing pipeline
- State management
- Error handling and recovery
- Data transformation
- External system integration

## Usage Examples

### Basic Usage

```python
from app.services.ims import IMSInsuredService, IMSQuoteService

# Initialize services
insured_service = IMSInsuredService(environment="ims_one")
quote_service = IMSQuoteService(environment="ims_one")

# Find or create an insured
insured_data = {
    "name": "ABC Corporation",
    "tax_id": "12-3456789",
    "address": "123 Main St",
    "city": "Dallas",
    "state": "TX",
    "zip_code": "75001"
}
insured_guid = insured_service.find_or_create_insured(insured_data)

# Create a submission
submission_data = {
    "insured_guid": insured_guid,
    "producer_contact_guid": "...",
    "submission_date": datetime.now().date()
}
submission_guid = quote_service.create_submission(submission_data)
```

### Using the Workflow Orchestrator

```python
from app.services.ims.workflow_orchestrator import IMSWorkflowOrchestrator
from app.models.transaction_models import Transaction

# Initialize orchestrator
orchestrator = IMSWorkflowOrchestrator(environment="ims_one")

# Process a transaction
transaction = Transaction(...)
result = orchestrator.process_transaction(transaction)
```

## Configuration

The IMS services use configuration from `app.core.config.Settings.IMS_ENVIRONMENTS`:

```python
IMS_ENVIRONMENTS = {
    "ims_one": {
        "config_file": "IMS_ONE.config",
        "username": "...",
        "password": "...",
        "sources": {
            "triton": {
                "default_producer_guid": "...",
                "default_line_guid": "...",
                "raters": {...}
            }
        }
    }
}
```

## Authentication

Authentication is handled automatically by the `IMSAuthenticationManager`:
- Tokens are cached and reused across services
- Automatic renewal before expiration (7-hour lifetime)
- Thread-safe for concurrent operations
- Automatic retry on authentication failures

## Error Handling

All services include comprehensive error handling:
- Automatic retry on authentication errors
- Detailed logging of operations
- Transaction-level error tracking
- Graceful degradation for non-critical operations

## Best Practices

1. **Use the Orchestrator for Complete Workflows**
   - Don't call individual services directly unless necessary
   - The orchestrator handles state management and error recovery

2. **Environment Management**
   - Always specify the environment when initializing services
   - Use consistent environments across related operations

3. **Error Handling**
   - Wrap service calls in try-except blocks
   - Check return values for success indicators
   - Log errors with appropriate context

4. **Data Validation**
   - Validate data before passing to services
   - Services perform basic validation but assume well-formed data

5. **Transaction Management**
   - Use the Transaction model for state tracking
   - Keep transaction logs updated throughout processing

## Extending the Services

To add new functionality:

1. **New Service Methods**
   - Add to the appropriate domain service
   - Follow existing patterns for error handling
   - Update the orchestrator if needed

2. **New Services**
   - Inherit from `BaseIMSService`
   - Implement domain-specific methods
   - Add to `__init__.py` exports

3. **New Workflows**
   - Add methods to the orchestrator
   - Coordinate existing services
   - Maintain transaction state

## Testing

When testing IMS services:

1. Use a test environment configuration
2. Mock SOAP responses for unit tests
3. Use integration tests sparingly (IMS calls are slow)
4. Test error scenarios thoroughly
5. Verify token management works correctly