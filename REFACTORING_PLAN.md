# Triton-IMS Integration Refactoring Plan

## Goal
Simplify the flow: **Triton payload → Convert for IMS → Push to IMS**

## Proposed Architecture

### 1. Single Entry Point for Triton
```
POST /api/triton/webhook
```
- One endpoint that handles all Triton transaction types
- Immediate validation and error response
- Simple async/sync mode support

### 2. Simplified Data Flow
```
TritonWebhook → TritonProcessor → IMSClient
     ↓              ↓                ↓
  Validate      Transform         Direct IMS
  & Route       to IMS            API Calls
```

### 3. Core Components

#### a) TritonWebhook (app/api/triton_webhook.py)
- Single endpoint for all Triton events
- Basic validation
- Route to processor

#### b) TritonProcessor (app/services/triton_processor.py)
- Handles all transaction types in one place
- Simple switch statement for routing
- Direct transformation and IMS calls
- Clear error handling with detailed logging

#### c) IMSClient (app/services/ims_client.py)
- Simplified SOAP client
- Direct method calls for each IMS operation
- No complex orchestration

#### d) Simplified Models
- Remove complex Transaction model
- Use simple DTOs for each operation
- No nested state tracking

### 4. Transaction Type Handlers

Each transaction type gets a simple, focused handler:

```python
class TritonProcessor:
    def process_binding(self, data: dict) -> dict:
        # 1. Transform data
        ims_data = self.transform_binding(data)
        
        # 2. Create/find insured
        insured_guid = self.ims.find_or_create_insured(ims_data['insured'])
        
        # 3. Create submission
        submission_guid = self.ims.create_submission({
            'insured_guid': insured_guid,
            'producer_guid': self.get_producer_guid(data),
            ...
        })
        
        # 4. Create quote
        quote_guid = self.ims.create_quote({
            'submission_guid': submission_guid,
            ...
        })
        
        # 5. Add premium
        self.ims.add_premium(quote_guid, ims_data['premium'])
        
        # 6. Bind policy
        policy_number = self.ims.bind_policy(quote_guid)
        
        # 7. Return result
        return {
            'success': True,
            'policy_number': policy_number,
            'ims_reference': quote_guid
        }
```

### 5. Error Handling Strategy

```python
class TritonError(Exception):
    def __init__(self, stage: str, message: str, details: dict = None):
        self.stage = stage
        self.message = message
        self.details = details or {}
```

- Clear error stages (VALIDATION, TRANSFORMATION, IMS_CALL)
- Detailed error context
- Easy to debug and troubleshoot

### 6. Configuration Simplification

Single config file with clear structure:
```python
TRITON_CONFIG = {
    'producers': {
        'default': 'GUID-HERE',
        'mapping': {
            'producer_name': 'GUID'
        }
    },
    'lines': {
        'primary': 'GUID-HERE',
        'excess': 'GUID-HERE'
    },
    'defaults': {
        'business_type_id': 1,
        'underwriter_guid': 'GUID-HERE'
    }
}
```

### 7. Logging Strategy

Structured logging at each step:
```python
logger.info("TRITON_BINDING", extra={
    'transaction_id': data.get('transaction_id'),
    'policy_number': data.get('policy_number'),
    'stage': 'CREATE_INSURED',
    'insured_name': data.get('account', {}).get('name')
})
```

## Implementation Steps

1. **Create new simplified components**
   - triton_webhook.py
   - triton_processor.py
   - ims_client.py

2. **Remove unnecessary files**
   - Complex workflow orchestrator
   - Transaction service layers
   - Nested models

3. **Simplify configuration**
   - Single config structure
   - Clear defaults
   - Easy to modify

4. **Add comprehensive logging**
   - Each step logged
   - Easy to trace issues
   - Performance metrics

5. **Create simple tests**
   - Unit tests for each handler
   - Integration tests with mock IMS
   - Easy to run and debug

## Benefits

1. **Easier to understand**: Linear flow, no complex state machines
2. **Easier to debug**: Clear error messages, simple stack traces
3. **Easier to extend**: Add new transaction types easily
4. **Better performance**: Fewer layers, direct calls
5. **Maintainable**: Each component has single responsibility