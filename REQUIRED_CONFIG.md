# Required Configuration for IMS Network Deployment

## Critical Environment Variables to Set in .env

### IMS Authentication
```bash
# Use actual IMS credentials
IMS_ONE_USERNAME=your_actual_username
IMS_ONE_PASSWORD=your_encrypted_password
# OR
ISCMGA_TEST_USERNAME=your_actual_username  
ISCMGA_TEST_PASSWORD=your_encrypted_password

# Set which environment to use
DEFAULT_ENVIRONMENT=ims_one  # or iscmga_test
```

### Triton Database Connection
```bash
# Set these for your Triton database access
TRITON_MYSQL_HOST=triton-production.hostname.com  # or localhost if tunneling
TRITON_MYSQL_PORT=3306  # or 13307 if using tunnel
TRITON_MYSQL_DATABASE=triton_production
TRITON_MYSQL_USER=your_triton_db_user
TRITON_MYSQL_PASSWORD=your_triton_db_password
```

### IMS GUIDs (MUST BE UPDATED)
**🚨 These are currently dummy values and MUST be replaced:**

```bash
# Producer GUIDs - Get from IMS producer search
TRITON_DEFAULT_PRODUCER_GUID=12345678-1234-1234-1234-123456789012

# Line of Business GUIDs - Get from IMS
TRITON_PRIMARY_LINE_GUID=12345678-1234-1234-1234-123456789012
TRITON_EXCESS_LINE_GUID=12345678-1234-1234-1234-123456789012

# Excel Rater Configuration - Get from IMS admin
TRITON_PRIMARY_RATER_ID=123
TRITON_PRIMARY_FACTOR_SET_GUID=12345678-1234-1234-1234-123456789012
TRITON_EXCESS_RATER_ID=124
TRITON_EXCESS_FACTOR_SET_GUID=12345678-1234-1234-1234-123456789012
```

## How to Get Real GUIDs

### 1. Find Producer GUIDs
```bash
# Run this test to search for producers:
python test_producer_search.py

# Or use the IMS web interface to find producer GUIDs
```

### 2. Find Line of Business GUIDs
Query IMS database or use web interface to get Line GUIDs for:
- Allied Healthcare Primary
- Allied Healthcare Excess

### 3. Find Rater IDs and Factor Set GUIDs
Contact IMS administrator for:
- Excel Rater IDs for your product lines
- Factor Set GUIDs for each rater

### 4. Find Underwriter GUIDs
Query IMS for available underwriters in your environment.

## Minimum Required for Testing

At minimum, you need:
1. **Valid IMS credentials** (username/password)
2. **One valid Producer GUID** (can be found via ProducerSearch)
3. **One valid Line GUID** (for quote creation)
4. **Triton database access** (host/user/password)

## Files That Must Exist

1. **IMS Config Files** (should already exist):
   - `IMS_Configs/IMS_ONE.config`
   - `IMS_Configs/ISCMGA_Test.config`

2. **Dependencies** (install via pip):
   - mysql-connector-python
   - openpyxl
   - requests
   - fastapi
   - uvicorn
   - xmltodict

## Quick Validation Commands

```bash
# Test IMS connection
python test_ims_login.py

# Test database connection  
python -c "from app.services.mysql_extractor import MySQLExtractor; print('DB connection test')"

# Test producer search
python test_producer_search.py

# Run full integration test
python run_mysql_polling.py
```