# Triton-IMS Integration Guide (Simplified Architecture)

## Overview

The refactored Triton-IMS integration provides a simple, linear flow:

**Triton Webhook → Process Data → Push to IMS**

## Key Components

### 1. Triton Webhook (`/api/triton/webhook`)
- Single endpoint for ALL Triton transactions
- Handles binding, cancellation, endorsement, reinstatement
- Supports sync/async processing

### 2. TritonProcessor (`app/services/triton_processor.py`)
- Simple, linear processing for each transaction type
- Built-in Excel rating support
- Preserves ALL Triton data (nothing is lost)

### 3. IMSClient (`app/services/ims_client.py`)
- Clean wrapper around IMS SOAP services
- Direct method calls, no complex orchestration
- Clear error handling

### 4. Configuration (`app/config/triton_config.py`)
- All settings in one place
- Environment variables for sensitive data
- Easy to modify mappings

## Quick Start

### 1. Environment Setup

```bash
# Required environment variables
export IMS_ENVIRONMENT=ims_one
export IMS_ONE_USERNAME=your_username
export IMS_ONE_PASSWORD=your_password
export TRITON_API_KEYS=your_api_key
export TRITON_DEFAULT_PRODUCER_GUID=895E9291-CFB6-4299-8799-9AF77DF937D6
```

### 2. Start the Service

```bash
# Using Docker
docker-compose up

# Or directly
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. Test the Integration

```bash
# Health check
curl http://localhost:8000/api/triton/health

# Send a test binding transaction
curl -X POST http://localhost:8000/api/triton/webhook \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d @sample_binding.json
```

## Transaction Examples

### Policy Binding

```json
{
  "transaction_type": "binding",
  "transaction_id": "TRN-12345",
  "policy_number": "POL-2024-001",
  "effective_date": "2024-01-01",
  "expiration_date": "2025-01-01",
  "account": {
    "id": "ACC-789",
    "name": "ABC Company",
    "street_1": "123 Main St",
    "city": "Dallas",
    "state": "TX",
    "zip": "75201"
  },
  "producer": {
    "name": "XYZ Agency"
  },
  "premium": {
    "annual_premium": 50000
  },
  "exposures": [
    {
      "coverage_name": "General Liability",
      "limit": {"value": 1000000},
      "deductible": {"value": 5000}
    }
  ]
}
```

### Policy Cancellation

```json
{
  "transaction_type": "cancellation",
  "transaction_id": "TRN-12346",
  "policy_number": "POL-2024-001",
  "cancellation_date": "2024-06-01",
  "cancellation_reason": "non-payment"
}
```

## Excel Rating

The system automatically uses Excel rating when:
- Complex rating data is present (multiple exposures, rating factors)
- `use_excel_rating: true` in the payload
- Custom fields need to be preserved

### How It Works

1. **Data Preservation**: ALL Triton data is converted to Excel format
2. **IMS Rating**: The Excel file is uploaded to IMS for rating
3. **Storage**: The raw data is saved as a rating sheet for audit

### Excel Structure

The generated Excel file contains:
- **Sheet 1 "Rating Data"**: Standard fields for IMS rating
- **Sheet 2 "Triton Raw Data"**: ALL original Triton data (flattened)

## Configuration

### Producer Mapping

Edit `app/config/triton_config.py`:

```python
'producers': {
    'default': 'DEFAULT-PRODUCER-GUID',
    'mapping': {
        'ABC Agency': 'ABC-AGENCY-GUID',
        'XYZ Broker': 'XYZ-BROKER-GUID'
    }
}
```

### Rater Configuration

```python
'raters': {
    'primary': {
        'rater_id': 1,
        'factor_set_guid': 'PRIMARY-FACTOR-SET-GUID',
        'template': 'triton_primary.xlsx'
    },
    'excess': {
        'rater_id': 2,
        'factor_set_guid': 'EXCESS-FACTOR-SET-GUID',
        'template': 'triton_excess.xlsx'
    }
}
```

## Error Handling

Errors are returned with clear context:

```json
{
  "status": "error",
  "error": {
    "stage": "BINDING",
    "message": "Failed to create insured",
    "details": {
      "transaction_id": "TRN-12345",
      "insured_name": "ABC Company"
    }
  }
}
```

### Error Stages
- `VALIDATION`: Input data validation failed
- `TRANSFORMATION`: Data transformation error
- `IMS_CALL`: IMS API call failed
- `BINDING`: Policy binding process error
- `CANCELLATION`: Cancellation process error
- `ENDORSEMENT`: Endorsement process error
- `REINSTATEMENT`: Reinstatement process error

## Logging

Structured logging for easy troubleshooting:

```
2024-01-01 10:00:00 - INFO - TRITON_BINDING_TRANSFORM - transaction_id=TRN-12345
2024-01-01 10:00:01 - INFO - TRITON_BINDING_INSURED - transaction_id=TRN-12345 insured_name="ABC Company"
2024-01-01 10:00:02 - INFO - TRITON_BINDING_EXCEL_RATING - transaction_id=TRN-12345
2024-01-01 10:00:05 - INFO - TRITON_BINDING_SUCCESS - transaction_id=TRN-12345 policy_number=POL-2024-001
```

## Async Processing

For long-running operations, use async mode:

```bash
curl -X POST http://localhost:8000/api/triton/webhook?sync_mode=false \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d @large_submission.json
```

Response:
```json
{
  "status": "accepted",
  "data": {
    "transaction_id": "TRN-12345",
    "message": "Transaction queued for processing"
  }
}
```

## Troubleshooting

### Common Issues

1. **Producer Not Found**
   - Check producer mapping in config
   - Verify producer name matches exactly

2. **Excel Rating Failed**
   - Ensure openpyxl is installed: `pip install openpyxl`
   - Check rater configuration
   - Verify Excel template exists

3. **IMS Connection Failed**
   - Check username/password
   - Verify IMS environment URL
   - Check network connectivity

### Debug Mode

Enable detailed logging:

```python
import logging
logging.getLogger('app.services.triton_processor').setLevel(logging.DEBUG)
logging.getLogger('app.services.ims_client').setLevel(logging.DEBUG)
```

## Testing

### Unit Tests

```bash
# Test TritonProcessor
python -m pytest tests/test_triton_processor.py

# Test IMSClient
python -m pytest tests/test_ims_client.py
```

### Integration Tests

```bash
# Test full flow with mock IMS
python -m pytest tests/test_integration.py
```

### Load Testing

```bash
# Using Apache Bench
ab -n 100 -c 10 -T application/json -p binding.json \
   -H "X-API-Key: your_api_key" \
   http://localhost:8000/api/triton/webhook
```

## Production Deployment

### AWS Deployment

1. Build Docker image:
```bash
docker build -t triton-ims-integration .
docker tag triton-ims-integration:latest your-ecr-repo:latest
docker push your-ecr-repo:latest
```

2. Deploy to ECS/Fargate with environment variables

3. Configure API Gateway for public access

### Monitoring

- Use CloudWatch for logs
- Set up alarms for error rates
- Monitor IMS response times

### Security

1. Use AWS Secrets Manager for credentials
2. Enable API Gateway throttling
3. Implement IP whitelisting for Triton
4. Use HTTPS everywhere

## Support

For issues or questions:
1. Check logs for detailed error messages
2. Review this guide for common issues
3. Contact the development team

## Appendix: Custom Stored Procedures

If you need to store additional Triton data, create this stored procedure in IMS:

```sql
CREATE PROCEDURE StoreTritonData_WS
    @QuoteGUID uniqueidentifier,
    @SourceSystem varchar(50),
    @TransactionID varchar(100),
    @JsonData nvarchar(max)
AS
BEGIN
    INSERT INTO TritonData (QuoteGUID, SourceSystem, TransactionID, JsonData, CreatedDate)
    VALUES (@QuoteGUID, @SourceSystem, @TransactionID, @JsonData, GETDATE())
END
```