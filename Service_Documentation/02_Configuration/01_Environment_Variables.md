# Environment Variables Configuration Guide

This guide provides a complete reference for all environment variables used by the RSG Integration Service. Copy `.env.example` to `.env` and update with your values.

## Core Application Settings

### API Configuration
```bash
# API version prefix
API_V1_STR="/api/v1"

# Project name (appears in API documentation)
PROJECT_NAME="IMS Integration API"

# Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL="INFO"

# Default IMS environment to use
DEFAULT_ENVIRONMENT="iscmga_test"  # Options: "ims_one", "iscmga_test"
```

### CORS Settings
```bash
# IMPORTANT: Change from ["*"] for production!
CORS_ORIGINS='["https://your-domain.com", "https://api.your-domain.com"]'
# Default is ["*"] which allows all origins - MUST be restricted in production
```

## Security Configuration

### API Keys
```bash
# Generic API keys for transaction endpoints
API_KEYS='["your-secure-api-key-1", "your-secure-api-key-2"]'

# Source-specific API keys
TRITON_API_KEYS='["triton-secure-key-1", "triton-secure-key-2"]'
TRITON_CLIENT_IDS='["triton"]'

XUBER_API_KEYS='["xuber-secure-key-1"]'
XUBER_CLIENT_IDS='["xuber"]'
```

**⚠️ Security Best Practices:**
- Generate strong, unique API keys (minimum 32 characters)
- Rotate keys every 90 days
- Never commit actual keys to version control
- Use different keys for each environment

## IMS Environment Settings

### IMS One Environment
```bash
# IMS One credentials
IMS_ONE_USERNAME="your_ims_one_username"
IMS_ONE_PASSWORD="your_encrypted_password"

# Note: Passwords should be encrypted using IMS encryption
```

### ISCMGA Test Environment
```bash
# ISCMGA Test credentials
ISCMGA_TEST_USERNAME="your_iscmga_username"
ISCMGA_TEST_PASSWORD="your_encrypted_password"
```

## Source System Configuration

### Triton Integration
```bash
# Producer Configuration
TRITON_DEFAULT_PRODUCER_GUID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

# Line of Business GUIDs
TRITON_PRIMARY_LINE_GUID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
TRITON_EXCESS_LINE_GUID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

# Rater Configuration - Primary
TRITON_PRIMARY_RATER_ID=12345
TRITON_PRIMARY_FACTOR_SET_GUID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

# Rater Configuration - Excess
TRITON_EXCESS_RATER_ID=67890
TRITON_EXCESS_FACTOR_SET_GUID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

# Triton Database Connection (for polling)
TRITON_MYSQL_HOST="triton-staging.ctfcgagzmyca.us-east-1.rds.amazonaws.com"
TRITON_MYSQL_PORT="3306"
TRITON_MYSQL_DATABASE="triton_staging"
TRITON_MYSQL_USER="your_mysql_user"
TRITON_MYSQL_PASSWORD="your_mysql_password"
```

### Xuber Integration
```bash
# Producer Configuration
XUBER_DEFAULT_PRODUCER_GUID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

# Line of Business GUID
XUBER_DEFAULT_LINE_GUID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

# Rater Configuration
XUBER_PRIMARY_RATER_ID=11111
XUBER_PRIMARY_FACTOR_SET_GUID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

## Database Configuration

### Local MySQL (for IMS transaction logs)
```bash
LOCAL_MYSQL_HOST="localhost"
LOCAL_MYSQL_PORT="3306"
LOCAL_MYSQL_DATABASE="ims_integration"
LOCAL_MYSQL_USER="your_local_mysql_user"
LOCAL_MYSQL_PASSWORD="your_local_mysql_password"
```

### Polling Service Settings
```bash
# Polling interval in seconds
POLL_INTERVAL_SECONDS=60

# Number of transactions to process per batch
POLL_BATCH_SIZE=10

# Enable/disable Triton polling
ENABLE_TRITON_POLLING="true"  # Set to "false" to disable
```

## AWS Configuration (if using SSM tunnel)

### SSM Tunnel Settings
```bash
# EC2 instance ID for SSM tunnel
SSM_INSTANCE_ID="i-xxxxxxxxxxxxxxxxx"

# Enable SSM tunnel (instead of direct connection)
USE_SSM_TUNNEL="false"  # Set to "true" if using SSM tunnel

# Local port for SSM tunnel
SSM_LOCAL_PORT=13306
```

### AWS Credentials
Configure in `~/.aws/credentials`:
```ini
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
region = us-east-1
```

## How to Obtain Required GUIDs

### 1. Producer GUIDs
```bash
# Use the test script to search for producers
python test_producer_search.py

# Or use IMS ProducerSearch API:
# Search by name to get ProducerLocationGuid
```

### 2. Line of Business GUIDs
```sql
-- Query IMS database:
SELECT LineGuid, LineName 
FROM tblLines 
WHERE Active = 1 
  AND LineName LIKE '%Allied Healthcare%';
```

### 3. Rater IDs and Factor Set GUIDs
Contact IMS administrator or query:
```sql
-- Get rater information
SELECT RaterID, RaterName, FactorSetGuid 
FROM tblExcelRating_Raters 
WHERE Active = 1;
```

### 4. Underwriter GUIDs
```sql
-- Query for underwriters
SELECT UnderwriterGuid, FirstName, LastName 
FROM tblUnderwriters 
WHERE Active = 1;
```

## Environment-Specific Examples

### Development Environment
```bash
DEFAULT_ENVIRONMENT="iscmga_test"
LOG_LEVEL="DEBUG"
CORS_ORIGINS='["*"]'  # OK for development
API_KEYS='["test_key_123"]'
ENABLE_TRITON_POLLING="false"  # Manual testing
```

### Production Environment
```bash
DEFAULT_ENVIRONMENT="ims_one"
LOG_LEVEL="INFO"
CORS_ORIGINS='["https://api.rsgims.com"]'
API_KEYS='["prod_key_ABC123..."]'  # Strong 32+ char keys
ENABLE_TRITON_POLLING="true"
POLL_INTERVAL_SECONDS=300  # 5 minutes
```

## Validation

After setting environment variables, validate configuration:

```bash
# Test IMS connection
python test_ims_login.py

# Test database connection
python test_db_connection.py

# Test producer search
python test_producer_search.py
```

## Troubleshooting

### Common Issues

1. **"Invalid GUID format"**
   - Ensure GUIDs are in format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
   - Don't use placeholder values like `00000000-0000-0000-0000-000000000000`

2. **"Authentication failed"**
   - Verify IMS credentials are correct
   - Ensure passwords are properly encrypted
   - Check network connectivity to IMS servers

3. **"Producer not found"**
   - Run `test_producer_search.py` to find valid producer GUIDs
   - Verify producer is active in the IMS environment

4. **"Database connection failed"**
   - Check MySQL host and port accessibility
   - Verify credentials have necessary permissions
   - For AWS RDS, check security group settings

## Security Checklist

- [ ] All default/test API keys replaced with strong values
- [ ] CORS origins restricted to specific domains
- [ ] Database passwords are strong and unique
- [ ] No credentials committed to version control
- [ ] Different credentials for each environment
- [ ] API keys rotated regularly (90 days)
- [ ] Access logs monitored for unauthorized attempts