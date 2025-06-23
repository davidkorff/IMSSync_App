# RSG Integration Service Overview

## What is RSG Integration Service?

The RSG Integration Service is a middleware platform that facilitates seamless data transfer between external insurance systems (like Triton and Xuber) and the IMS (Insurance Management System). It acts as a bridge, transforming policy data from various sources into IMS-compatible formats and managing the complete policy lifecycle.

## Key Features

- **Multi-Source Support**: Integrates with multiple insurance platforms (Triton, Xuber, and extensible to others)
- **Flexible Data Formats**: Accepts both JSON and XML input formats
- **Asynchronous Processing**: Non-blocking transaction processing with status tracking
- **Complete Policy Lifecycle**: Handles new business, endorsements, cancellations, and renewals
- **Secure API**: API key-based authentication with source-specific validation
- **Database Polling**: Optional MySQL polling for Triton transactions
- **Real-time Webhooks**: Support for push-based integrations

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────┐
│ Source Systems  │────▶│ RSG Integration API  │────▶│     IMS     │
│ (Triton/Xuber) │     │                      │     │   (SOAP)    │
└─────────────────┘     └──────────────────────┘     └─────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │ Transaction  │
                        │   Database   │
                        └──────────────┘
```

## Core Components

### 1. API Service
- **FastAPI-based REST API**: Modern, high-performance web framework
- **Endpoint Types**:
  - Generic transaction endpoints (`/api/transaction/{type}`)
  - Source-specific endpoints (`/api/triton/transaction/{type}`)
  - Health and monitoring endpoints

### 2. Transaction Processing
- **Transaction Service**: Manages transaction lifecycle and state
- **Source-Specific Services**: Triton and Xuber integration services
- **IMS Workflow Service**: Handles IMS SOAP API communication

### 3. Data Storage
- **SQLite Database**: Stores transaction data and processing state
- **MySQL Integration**: Optional polling for Triton transactions
- **Transaction States**: Tracks progress through IMS workflow

### 4. Integration Workflow

The typical integration flow follows these steps:

1. **Receive Transaction**: Accept data via API or database polling
2. **Validate & Transform**: Convert to IMS-compatible format
3. **IMS Processing**:
   - Create/Find Insured
   - Create Submission
   - Create Quote
   - Apply Rating/Premium
   - Bind Policy
   - Issue Policy
4. **Status Updates**: Track progress and handle errors
5. **Response**: Return transaction ID and status

## Transaction Types

The service supports these transaction types:

- **new**: New business policies
- **update**: Policy updates/endorsements
- **cancellation**: Policy cancellations
- **endorsement**: Mid-term changes
- **reinstatement**: Cancelled policy reinstatements

## Key Benefits

1. **Reduced Integration Complexity**: Single integration point for multiple sources
2. **Data Consistency**: Standardized transformation to IMS format
3. **Error Handling**: Robust retry mechanisms and error tracking
4. **Scalability**: Asynchronous processing handles high volumes
5. **Flexibility**: Easy to add new source systems
6. **Auditability**: Complete transaction history and logging

## Use Cases

- **New Policy Creation**: Automatically create policies in IMS from external systems
- **Policy Updates**: Synchronize endorsements and changes
- **Bulk Processing**: Handle large volumes via database polling
- **Real-time Integration**: Immediate processing via webhooks
- **Multi-Program Support**: Different insurance programs with custom rules

## Next Steps

- Review [Prerequisites](./03_Prerequisites.md) for system requirements
- Follow the [Quick Start Guide](./02_Quick_Start.md) to begin integration
- Check [Configuration Guide](../02_Configuration/01_Environment_Variables.md) for setup details