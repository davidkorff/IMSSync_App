# RSG Integration Service - Proposed Architecture

## Current State Analysis

### Current Structure:
```
app/
├── api/
│   ├── routes.py              # General API routes
│   └── source_routes.py       # Triton-specific endpoints (push route)
├── integrations/
│   ├── triton/               # Triton data transformation
│   └── xuber/                # Future Xuber integration
└── services/
    ├── ims_integration_service.py    # IMS workflow logic
    ├── mysql_extractor.py           # Database extraction (pull route)
    └── mysql_polling_service.py     # Polling service (pull route)
```

## 🎯 Proposed Architecture

### Core Principle: **Separate Data Sources from IMS Integration**

```
app/
├── api/
│   ├── routes.py                    # Health, status endpoints
│   └── webhooks/
│       ├── triton_webhook.py        # Triton push notifications
│       └── xuber_webhook.py         # Future Xuber webhooks
├── sources/                         # Data source adapters
│   ├── triton/
│   │   ├── push_adapter.py          # Handle incoming Triton pushes
│   │   ├── pull_adapter.py          # Pull from Triton database
│   │   └── transformer.py           # Triton → standard format
│   └── xuber/
│       ├── push_adapter.py          # Handle incoming Xuber pushes
│       └── transformer.py           # Xuber → standard format
├── destinations/                    # Destination adapters
│   ├── ims/
│   │   ├── workflow_service.py      # IMS SOAP workflow
│   │   ├── soap_client.py           # SOAP communication
│   │   └── document_service.py      # Document generation
│   └── other_systems/               # Future destinations
├── core/
│   ├── models.py                    # Standard transaction models
│   ├── transaction_processor.py     # Main processing engine
│   └── queue_service.py             # Queue management
└── services/
    ├── polling_service.py           # Database polling coordinator
    └── retry_service.py             # Error handling & retries
```

## 🔄 Transaction Flow

### Route 1: Push Integration (Triton → IMS)
```
Triton → webhooks/triton_webhook.py → sources/triton/push_adapter.py 
     → core/transaction_processor.py → destinations/ims/workflow_service.py → IMS
```

### Route 2: Pull Integration (MySQL → IMS)
```
services/polling_service.py → sources/triton/pull_adapter.py 
     → core/transaction_processor.py → destinations/ims/workflow_service.py → IMS
```

### Future: Xuber Integration
```
Xuber → webhooks/xuber_webhook.py → sources/xuber/push_adapter.py 
     → core/transaction_processor.py → destinations/ims/workflow_service.py → IMS
```

## 📊 Benefits of This Architecture

### 1. **Separation of Concerns**
- **Sources**: Handle different data source formats/methods
- **Destinations**: Handle different output systems
- **Core**: Standard processing logic

### 2. **Reusable IMS Integration**
- Same `destinations/ims/` for all sources
- Consistent IMS workflow regardless of data source
- Single place to maintain IMS logic

### 3. **Scalable**
- Easy to add new sources (Lloyd's, other carriers)
- Easy to add new destinations (other management systems)
- Independent development of source/destination adapters

### 4. **Consistent Data Model**
- All sources transform to standard `core/models.py`
- Core processor works with standard format
- Destinations receive consistent data

## 🚀 Implementation Plan

### Phase 1: Restructure Current Code
1. Move `source_routes.py` → `webhooks/triton_webhook.py`
2. Move `mysql_extractor.py` → `sources/triton/pull_adapter.py`
3. Move `ims_workflow_service.py` → `destinations/ims/workflow_service.py`
4. Create `core/transaction_processor.py` as main coordinator

### Phase 2: Standardize Data Models
1. Define standard transaction model in `core/models.py`
2. Update Triton transformer to use standard model
3. Update IMS workflow to consume standard model

### Phase 3: Add Queue Management
1. Implement `core/queue_service.py` for async processing
2. Add retry logic in `services/retry_service.py`
3. Add monitoring and logging

### Phase 4: Polish & Production
1. Add comprehensive error handling
2. Add metrics and monitoring
3. Add configuration management
4. Add health checks

## 🔧 Configuration Strategy

### Environment-Based Config
```python
# config/sources.py
TRITON_CONFIG = {
    "push": {
        "enabled": True,
        "webhook_path": "/webhooks/triton"
    },
    "pull": {
        "enabled": True,
        "database": {
            "host": "localhost",
            "port": 13307,
            "database": "greenhill_db"
        },
        "polling_interval": 300  # 5 minutes
    }
}

XUBER_CONFIG = {
    "push": {
        "enabled": False,  # Future
        "webhook_path": "/webhooks/xuber"
    }
}

IMS_CONFIG = {
    "endpoint": "https://ims.example.com/soap",
    "username": "rsg_user",
    "timeout": 30
}
```

## 🎯 Answer to Your Question

**Yes, absolutely!** Keep the Triton → IMS route standard whether it's push or pull. Structure it like this:

1. **Keep webhook route**: `webhooks/triton_webhook.py` (for pushes from Triton)
2. **Add pull service**: `sources/triton/pull_adapter.py` (for database polling)
3. **Unified destination**: Both routes feed into the same `destinations/ims/workflow_service.py`
4. **Future ready**: Easy to add Xuber or other sources using the same pattern

This way:
- ✅ Triton push data and pull data both use the same IMS integration
- ✅ Easy to test both routes independently
- ✅ Future sources (Xuber, Lloyd's, etc.) can reuse the IMS destination
- ✅ Clear separation between data acquisition and data processing
- ✅ Can run both routes simultaneously if needed

Would you like me to start implementing this restructure?