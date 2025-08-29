# Environment Separation Guide - Dev vs Prod
## Understanding the Problem

Right now, you have ONE environment. This means:
- If you test something and break it, production breaks
- If you change a database, you might affect live data
- You can't test safely

The solution: **Separate Dev and Prod environments**

---

## The Simple Approach: Two .env Files

### What You'll Have:
```
RSG_Integration_2/
├── .env.development    # Dev settings
├── .env.production     # Prod settings
├── .env               # Active config (DON'T commit this)
├── main.py            # Your app
└── config.py          # Reads the .env file
```

### How It Works:

**For Development:**
```bash
cp .env.development .env
python main.py
# Runs on port 8000, uses dev database
```

**For Production:**
```bash
cp .env.production .env
python main.py
# Runs on port 8001, uses prod database
```

---

## Setting Up Your Environment Files

### 1. Create .env.development
```env
# ==============================================
# DEVELOPMENT ENVIRONMENT
# ==============================================

# APP SETTINGS
ENVIRONMENT=development
DEBUG=True
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=DEBUG

# DEV DATABASE (TEST DATA ONLY!)
DB_SERVER=dev-sql-server.company.com
DB_NAME=IMS_TEST
DB_USERNAME=dev_user
DB_PASSWORD=dev_password

# IMS DEV SERVICES
IMS_BASE_URL=http://10.64.32.234/ims_test
IMS_ONE_USERNAME=test_user
IMS_ONE_PASSWORD=test_password

# TEST API KEYS (not real ones!)
TRITON_API_KEY=test_key_12345
TRITON_WEBHOOK_SECRET=test_secret

# DEV SPECIFIC
ENABLE_DEBUG_ENDPOINTS=True
ALLOW_TEST_TRANSACTIONS=True
```

### 2. Create .env.production
```env
# ==============================================
# PRODUCTION ENVIRONMENT - REAL DATA!
# ==============================================

# APP SETTINGS
ENVIRONMENT=production
DEBUG=False  # NEVER True in production!
HOST=0.0.0.0
PORT=8001
LOG_LEVEL=INFO

# PROD DATABASE (LIVE DATA - BE CAREFUL!)
DB_SERVER=prod-sql-server.company.com
DB_NAME=IMS_PRODUCTION
DB_USERNAME=prod_user
DB_PASSWORD=prod_password_SECURE

# IMS PROD SERVICES
IMS_BASE_URL=http://10.64.32.234/ims_one
IMS_ONE_USERNAME=prod_user
IMS_ONE_PASSWORD=prod_password_SECURE

# REAL API KEYS (KEEP SECRET!)
TRITON_API_KEY=real_key_abc789xyz
TRITON_WEBHOOK_SECRET=real_secret_SECURE

# PROD SPECIFIC
ENABLE_DEBUG_ENDPOINTS=False
ALLOW_TEST_TRANSACTIONS=False
```

---

## The Better Approach: Environment Variable

Instead of copying files, use an environment variable:

### Modify config.py
```python
import os
from dotenv import load_dotenv

# Determine which environment to use
ENV = os.getenv('APP_ENV', 'development')  # Default to dev

# Load the appropriate .env file
if ENV == 'production':
    load_dotenv('.env.production')
else:
    load_dotenv('.env.development')

# Now load your config as normal
APP_CONFIG = {
    'environment': ENV,
    'debug': os.getenv('DEBUG', 'False').lower() == 'true',
    'port': int(os.getenv('PORT', '8000')),
    # ... rest of config
}
```

### To Run:
```bash
# Development
APP_ENV=development python main.py

# Production
APP_ENV=production python main.py
```

---

## Safety Features to Add

### 1. Visual Indicator in Logs
```python
# In main.py
if APP_CONFIG['environment'] == 'production':
    logger.warning("="*50)
    logger.warning("RUNNING IN PRODUCTION MODE")
    logger.warning("="*50)
else:
    logger.info("Running in development mode")
```

### 2. Prevent Accidents
```python
# In your transaction handler
def process_transaction(data):
    if APP_CONFIG['environment'] == 'development':
        if data.get('amount', 0) > 10000:
            logger.warning("Large transaction in DEV - limiting to $10,000")
            data['amount'] = 10000
    
    # Process transaction...
```

### 3. Different Log Files
```python
# In main.py
if APP_CONFIG['environment'] == 'production':
    log_file = f"logs/prod_{timestamp}.log"
else:
    log_file = f"logs/dev_{timestamp}.log"
```

---

## Database Separation

### CRITICAL: Use Different Databases!

**Development Database:**
- Name: `IMS_TEST` or `IMS_DEV`
- Contains: Copy of prod structure, fake test data
- OK to: Delete, modify, break things

**Production Database:**
- Name: `IMS_PRODUCTION`
- Contains: REAL customer data
- NEVER: Test here directly

### How to Set Up Test Database:
```sql
-- Run on dev server
CREATE DATABASE IMS_TEST;
USE IMS_TEST;

-- Run your table creation scripts
-- Run your stored procedure scripts
-- Insert FAKE test data only
```

---

## Running Both Environments

### Option 1: Same Server, Different Ports
```bash
# Terminal 1 - Development
APP_ENV=development python main.py
# Running on http://localhost:8000

# Terminal 2 - Production
APP_ENV=production python main.py
# Running on http://localhost:8001
```

### Option 2: Different Servers (BEST)
- Dev: Your local machine or dev server
- Prod: AWS production server only

---

## Startup Scripts for Each Environment

### dev_start.sh
```bash
#!/bin/bash
echo "Starting DEVELOPMENT environment..."
export APP_ENV=development
python main.py
```

### prod_start.sh
```bash
#!/bin/bash
echo "WARNING: Starting PRODUCTION environment!"
echo "Press Ctrl+C to cancel, Enter to continue..."
read
export APP_ENV=production
nohup python main.py > logs/prod.log 2>&1 &
echo "Production started with PID: $!"
```

---

## How to Switch Between Environments

### Method 1: Manual Switch
```bash
# Switch to dev
cp .env.development .env
python main.py

# Switch to prod
cp .env.production .env
python main.py
```

### Method 2: Environment Variable (Recommended)
```bash
# Always dev by default
python main.py

# Explicitly run production
APP_ENV=production python main.py
```

### Method 3: Create Aliases
Add to your ~/.bashrc:
```bash
alias run-dev="APP_ENV=development python /path/to/main.py"
alias run-prod="APP_ENV=production python /path/to/main.py"
```

---

## What Changes Between Environments

| Setting | Development | Production |
|---------|------------|------------|
| Port | 8000 | 8001 |
| Database Server | dev-sql.company.com | prod-sql.company.com |
| Database Name | IMS_TEST | IMS_PRODUCTION |
| Debug Mode | True | False |
| Log Level | DEBUG | INFO |
| API Keys | Test keys | Real keys |
| Error Details | Show full errors | Hide sensitive info |

---

## Testing Your Setup

### 1. Verify Correct Environment
```python
# Add to your health endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": APP_CONFIG['environment'],  # Shows dev or prod
        "port": APP_CONFIG['port'],
        "debug": APP_CONFIG['debug']
    }
```

### 2. Test Both
```bash
# Test dev
curl http://localhost:8000/health
# Should show: {"environment": "development", "port": 8000}

# Test prod
curl http://localhost:8001/health
# Should show: {"environment": "production", "port": 8001}
```

---

## Common Mistakes to Avoid

1. **DON'T commit .env files to git**
   ```bash
   # Add to .gitignore
   .env
   .env.production
   .env.development
   ```

2. **DON'T use production database in dev**
   - Always double-check your DB_NAME

3. **DON'T leave DEBUG=True in production**
   - It exposes sensitive information

4. **DON'T use same API keys**
   - Get separate test keys for development

5. **DON'T forget to backup before switching**
   ```bash
   cp .env .env.backup
   ```

---

## Quick Setup Checklist

- [ ] Create .env.development with test settings
- [ ] Create .env.production with real settings
- [ ] Update config.py to check APP_ENV
- [ ] Add environment indicator to logs
- [ ] Create separate startup scripts
- [ ] Test both environments work
- [ ] Add .env files to .gitignore
- [ ] Document which ports are which
- [ ] Set up separate databases
- [ ] Verify can't accidentally run prod in dev mode