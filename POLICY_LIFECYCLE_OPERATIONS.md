# Policy Lifecycle Operations

This document describes the policy lifecycle operations implemented in the RSG Integration Service.

## Overview

The RSG Integration Service now supports complete policy lifecycle management, synchronizing policy changes from Triton to IMS:

- **Policy Cancellation**: Cancel active policies with pro-rata or flat cancellation options
- **Policy Endorsement**: Create midterm endorsements to modify policy coverage
- **Policy Reinstatement**: Reinstate cancelled policies with payment tracking

## Implementation Details

### 1. Extended Transaction Types

Added new transaction types to `app/models/transaction_models.py`:
- `CANCELLATION`
- `ENDORSEMENT` 
- `REINSTATEMENT`

### 2. Policy Lifecycle Service

Created `app/services/ims/policy_lifecycle_service.py` with methods:
- `cancel_policy()`: Calls the CancelPolicy stored procedure
- `create_endorsement()`: Calls the CreateEndorsement stored procedure
- `reinstate_policy()`: Calls the ReinstatePolicy stored procedure

### 3. Workflow Orchestrator Updates

Enhanced `app/services/ims/workflow_orchestrator.py` with:
- `_process_cancellation()`: Handles cancellation workflow
- `_process_endorsement()`: Handles endorsement workflow
- `_process_reinstatement()`: Handles reinstatement workflow

### 4. Triton Transformer Updates

Updated `app/integrations/triton/transformer.py` to transform:
- Cancellation transactions: Extract control number, cancellation date, reason
- Endorsement transactions: Extract endorsement details, premium changes
- Reinstatement transactions: Extract payment details, reinstatement date

### 5. API Route Support

The `/api/triton/transaction/new` endpoint supports all transaction types:
- `/cancellation`
- `/endorsement` or `/midterm_endorsement`
- `/reinstatement`

## Stored Procedures

The following stored procedures must be loaded into IMS:

1. **CancelPolicy_WS**
   - Cancels a policy and handles invoice reversal
   - Parameters: ControlNumber, CancellationDate, CancellationReasonID, etc.

2. **CreateEndorsement_WS**
   - Creates a policy endorsement
   - Parameters: ControlNumber, EndorsementEffectiveDate, EndorsementComment, etc.

3. **ReinstatePolicy_WS**
   - Reinstates a cancelled policy
   - Parameters: ControlNumber, ReinstatementDate, PaymentReceived, etc.

## Testing

Test files are provided for each operation:

1. **test_cancellation_flow.py**: Tests policy cancellation
2. **test_endorsement_flow.py**: Tests policy endorsement
3. **test_reinstatement_flow.py**: Tests policy reinstatement
4. **test_policy_lifecycle.py**: Tests complete lifecycle flow
5. **test_all_lifecycle_operations.py**: Runs all tests in sequence

### Running Tests

1. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload
   ```

2. Run individual tests:
   ```bash
   python test_cancellation_flow.py
   python test_endorsement_flow.py
   python test_reinstatement_flow.py
   ```

3. Or run all tests:
   ```bash
   python test_all_lifecycle_operations.py
   ```

## Important Notes

1. **Control Number Lookup**: The `_extract_control_number()` method in the transformer currently uses a placeholder. This needs to be implemented to look up the actual control number from IMS based on the policy number.

2. **Reason Code Mapping**: The transformer includes mapping functions for cancellation, endorsement, and reinstatement reasons. These mappings may need to be adjusted based on your IMS configuration.

3. **User GUID**: The workflow orchestrator attempts to extract user GUID from the transaction data. If not provided, it uses a default GUID based on the source system configuration.

4. **Synchronous Processing**: By default, transactions are processed synchronously. The API waits for IMS processing to complete before returning a response.

## Transaction Flow

1. **Triton** sends a lifecycle transaction to the appropriate endpoint
2. **Source Routes** creates a transaction with the correct type
3. **Triton Transformer** transforms the data for IMS
4. **Workflow Orchestrator** routes to the appropriate processor
5. **Policy Lifecycle Service** calls the corresponding stored procedure
6. **IMS** processes the operation and returns results
7. **Response** is sent back to Triton with the operation status

## Error Handling

- All operations include comprehensive error logging
- Failed operations update the transaction status to FAILED
- Error messages are captured in the transaction processing logs
- Stored procedure errors are bubbled up with descriptive messages