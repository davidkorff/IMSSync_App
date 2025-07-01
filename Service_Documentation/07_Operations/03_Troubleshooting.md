# Troubleshooting Guide

This guide helps diagnose and resolve common issues with the RSG Integration Service.

## Quick Diagnostics

### Service Health Check
```bash
# Check if service is running
curl http://localhost:8000/api/health

# Check service status (if using systemd)
systemctl status rsg-api

# Check if port is listening
netstat -an | grep 8000
lsof -i :8000
```

### Log Analysis
```bash
# View recent logs
tail -f ims_integration.log

# Search for errors
grep ERROR ims_integration.log

# Check specific transaction
grep "transaction_id_here" ims_integration.log
```

## Common Issues and Solutions

### 1. Service Won't Start

#### Symptom
```
Error: Address already in use
```

#### Solution
```bash
# Find process using port
lsof -i :8000
# Kill the process
kill -9 <PID>
# Or use different port
python -m app.main --port 8001
```

#### Symptom
```
ModuleNotFoundError: No module named 'fastapi'
```

#### Solution
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### 2. IMS Connection Issues

#### Symptom
```
Error: IMS login failed - Connection refused
```

#### Diagnosis & Solution
```bash
# Test network connectivity
ping dc02imsws01.rsgcorp.local
telnet dc02imsws01.rsgcorp.local 9213

# Check DNS resolution
nslookup dc02imsws01.rsgcorp.local

# Verify firewall rules
sudo iptables -L | grep 9213
```

#### Symptom
```
Error: Invalid credentials
```

#### Solution
1. Verify username in `.env`
2. Check password encryption:
   ```python
   # Password should be encrypted, not plain text
   # Contact IMS admin for encrypted password
   ```
3. Test with `test_ims_login.py`

### 3. Database Connection Issues

#### Symptom
```
Error: Can't connect to MySQL server
```

#### Solution
```bash
# Test MySQL connection
mysql -h hostname -P 3306 -u username -p

# For Triton via SSM tunnel
aws ssm start-session --target i-instanceid \
  --document-name AWS-StartPortForwardingSession \
  --parameters '{"portNumber":["3306"],"localPortNumber":["13306"]}'

# Update .env
TRITON_MYSQL_HOST=localhost
TRITON_MYSQL_PORT=13306
```

#### Symptom
```
Error: Access denied for user
```

#### Solution
```sql
-- Grant necessary permissions
GRANT SELECT ON triton_db.* TO 'integration_user'@'%';
FLUSH PRIVILEGES;
```

### 4. Transaction Processing Errors

#### Debugging IMS Processing Issues

##### Using Synchronous Mode for Immediate Feedback
```bash
# Submit transaction with sync mode to see IMS errors immediately
python load_csv_to_ims.py 1 --sync

# Or with cURL
curl -X POST "http://localhost:8000/api/transaction/new?source=triton&sync_mode=true" \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d @transaction.json
```

##### Check Enhanced Transaction Status
```bash
# Get detailed IMS processing information
curl http://localhost:8000/api/transaction/{transaction_id} \
  -H "X-API-Key: your-key" | jq

# Look for:
# - ims_details.processing_status
# - ims_details.error
# - ims_details.processing_logs
```

##### Common IMS Processing Errors

| Error Stage | Common Issues | Solution |
|-------------|---------------|----------|
| `insured_created` | Missing required fields | Check insured_name, address fields |
| `submission_created` | Invalid producer GUID | Verify producer exists in IMS |
| `quote_created` | Missing coverage info | Add required coverage fields |
| `rated` | Premium calculation error | Check premium/rates configuration |
| `bound` | Missing underwriter | Assign valid underwriter GUID |

#### Symptom
```
Error: Producer not found
```

#### Solution
```bash
# Search for producers
python test_producer_search.py

# Update .env with valid GUID
TRITON_DEFAULT_PRODUCER_GUID=valid-guid-here
```

#### Symptom
```
Error: Invalid GUID format
```

#### Solution
- Ensure GUIDs are in format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- Don't use zeros: `00000000-0000-0000-0000-000000000000`
- Get valid GUIDs from IMS admin or search APIs

#### Symptom
```
Error: Quote creation failed - Missing required field
```

#### Solution
1. Check transaction data has all required fields
2. Review field mapping in logs
3. Validate against [Field Mapping Guide](../04_Integration_Guides/04_Field_Mapping.md)

### 5. API Authentication Issues

#### Symptom
```
401 Unauthorized
```

#### Solution
```bash
# Verify API key in request
curl -H "X-API-Key: your-key" http://localhost:8000/api/health

# Check API keys in .env
grep API_KEYS .env
# Format must be: API_KEYS='["key1", "key2"]'
```

#### Symptom
```
403 Forbidden - Invalid client ID
```

#### Solution
```bash
# For Triton endpoints, include client ID
curl -H "X-API-Key: triton-key" \
     -H "X-Client-ID: triton" \
     http://localhost:8000/api/triton/transaction/new
```

### 6. Performance Issues

#### Symptom
Slow transaction processing

#### Diagnosis
```bash
# Check system resources
top
free -h
df -h

# Monitor specific transaction
grep "transaction_id" ims_integration.log | grep "Processing time"

# Check database performance
mysql -e "SHOW PROCESSLIST"
```

#### Solutions
1. Increase polling batch size in `.env`
2. Add database indexes
3. Increase worker processes
4. Check IMS server performance

### 7. Data Validation Errors

#### Symptom
```
Error: Invalid date format
```

#### Solution
Ensure dates are in ISO format: `YYYY-MM-DD`
```python
# Correct
"effective_date": "2025-01-01"

# Incorrect
"effective_date": "01/01/2025"
```

#### Symptom
```
Error: State code invalid
```

#### Solution
Use 2-letter state codes: `TX`, `CA`, `NY`

## Debugging Techniques

### 1. Enable Debug Logging
```bash
# In .env
LOG_LEVEL=DEBUG

# Restart service
```

### 2. Test Individual Components
```python
# Test IMS connection only
python test_ims_login.py

# Test producer search
python test_producer_search.py

# Test database connection
python -c "from app.services.mysql_extractor import MySQLExtractor; print('OK')"
```

### 3. Trace Transaction Flow
```bash
# Get transaction details with IMS info
curl http://localhost:8000/api/transaction/{id} \
  -H "X-API-Key: your-key" | jq

# Follow in logs
tail -f ims_integration.log | grep {transaction_id}

# Extract processing logs from response
curl http://localhost:8000/api/transaction/{id} \
  -H "X-API-Key: your-key" | \
  jq -r '.ims_details.processing_logs[]'

# Check specific IMS stage
curl http://localhost:8000/api/transaction/{id} \
  -H "X-API-Key: your-key" | \
  jq '.ims_details | {status: .processing_status, error: .error}'
```

### 4. Validate Input Data
```python
# test_json_validation.py
import json
from jsonschema import validate

# Your transaction data
data = {...}

# Validate JSON structure
try:
    json.dumps(data)
    print("Valid JSON")
except:
    print("Invalid JSON")
```

## Error Reference

### IMS SOAP Errors

| Error | Meaning | Solution |
|-------|---------|----------|
| `Invalid Token` | Session expired | Re-authenticate |
| `Insured exists` | Duplicate insured | Use Find functions |
| `Invalid Line` | Line not configured | Verify Line GUID |
| `No rater found` | Rater not set | Configure rater ID |

### Transaction Status Errors

| Status | Meaning | Action |
|--------|---------|---------|
| `FAILED` | Processing error | Check logs |
| `INVALID_DATA` | Validation failed | Fix data format |
| `IMS_ERROR` | IMS rejected | Check IMS response |
| `TIMEOUT` | Processing timeout | Retry transaction |

## Monitoring Commands

### Real-time Monitoring
```bash
# Watch transaction flow
watch -n 1 'tail -20 ims_integration.log'

# Monitor API calls
tcpdump -i any -n port 8000

# Database queries
mysqladmin -u root -p processlist
```

### Health Checks
```bash
# Create monitoring script
cat > check_health.sh << 'EOF'
#!/bin/bash
response=$(curl -s http://localhost:8000/api/health)
if [[ $response == *"healthy"* ]]; then
    echo "Service is healthy"
else
    echo "Service is unhealthy"
    exit 1
fi
EOF

chmod +x check_health.sh
```

## Getting Additional Help

### Log Collection
When reporting issues, collect:
```bash
# Create diagnostic bundle
mkdir diagnostics
cp ims_integration.log diagnostics/
cp .env diagnostics/.env.sanitized  # Remove passwords
systemctl status rsg-api > diagnostics/service_status.txt
pip freeze > diagnostics/pip_freeze.txt

# Create archive
tar -czf diagnostics.tar.gz diagnostics/
```

### Information to Provide
1. Error messages from logs
2. Transaction IDs
3. Request/response samples
4. Environment details
5. Recent changes

### Support Contacts
- Technical Support: [email]
- IMS Admin Team: [email]
- Emergency: [phone]

## Prevention Tips

1. **Regular Monitoring**: Set up alerts for errors
2. **Log Rotation**: Prevent disk full issues
3. **Database Maintenance**: Regular cleanup
4. **Update Dependencies**: Security patches
5. **Test Changes**: Use staging environment
6. **Document Issues**: Keep resolution log