"""
Enhanced configuration that supports multiple environments.
Replace your current config.py with this version.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import logging

# Determine which environment to use
ENV = os.getenv('APP_ENV', 'development').lower()

# Validate environment
VALID_ENVIRONMENTS = ['development', 'production', 'test']
if ENV not in VALID_ENVIRONMENTS:
    print(f"ERROR: Invalid environment '{ENV}'. Must be one of: {VALID_ENVIRONMENTS}")
    sys.exit(1)

# Load the appropriate .env file
BASE_DIR = Path(__file__).resolve().parent
if ENV == 'production':
    env_file = BASE_DIR / '.env.production'
    if not env_file.exists():
        print("ERROR: .env.production file not found!")
        print("Copy .env.production.example and configure it.")
        sys.exit(1)
    load_dotenv(env_file)
elif ENV == 'development':
    env_file = BASE_DIR / '.env.development'
    if not env_file.exists():
        print("WARNING: .env.development not found, using .env")
        load_dotenv()  # Fall back to .env
    else:
        load_dotenv(env_file)
else:
    load_dotenv()  # Default .env file

# Log which environment is being used
print("=" * 50)
print(f"Loading configuration for: {ENV.upper()} environment")
print(f"Using env file: {env_file if 'env_file' in locals() else '.env'}")
print("=" * 50)

# Verify critical settings for production
if ENV == 'production':
    if os.getenv('DEBUG', 'False').lower() == 'true':
        print("ERROR: DEBUG cannot be True in production!")
        sys.exit(1)
    if not os.getenv('DB_PASSWORD') or os.getenv('DB_PASSWORD') == 'dev_password':
        print("ERROR: Invalid database password for production!")
        sys.exit(1)

# IMS Configuration
IMS_CONFIG = {
    "BASE_URL": os.getenv("IMS_BASE_URL", "http://10.64.32.234/ims_one"),
    "base_url": os.getenv("IMS_BASE_URL", "http://10.64.32.234/ims_one").rsplit('/', 1)[0],
    "environments": {
        "login": os.getenv("IMS_LOGIN_ENV", "/ims_one"),
        "services": os.getenv("IMS_SERVICES_ENV", "/ims_one")
    },
    "endpoints": {
        "logon": "/logon.asmx",
        "insured_functions": "/insuredfunctions.asmx",
        "quote_functions": "/quotefunctions.asmx",
        "document_functions": "/documentfunctions.asmx",
        "invoice_factory": "/invoicefactory.asmx",
        "producer_functions": "/producerfunctions.asmx",
        "data_access": "/dataaccess.asmx",
        "clearance": "/clearance.asmx"
    },
    "credentials": {
        "username": os.getenv("IMS_ONE_USERNAME"),
        "password": os.getenv("IMS_ONE_PASSWORD"),
        "program_code": os.getenv("IMS_PROGRAM_CODE", "TRTON"),
        "project_name": os.getenv("IMS_PROJECT_NAME", "RSG_Integration")
    },
    "timeout": int(os.getenv("IMS_TIMEOUT", "30"))
}

# Triton Configuration
TRITON_CONFIG = {
    "api_key": os.getenv("TRITON_API_KEY"),
    "webhook_secret": os.getenv("TRITON_WEBHOOK_SECRET")
}

# Quote Configuration
QUOTE_CONFIG = {
    "quoting_location": os.getenv("IMS_QUOTING_LOCATION", "C5C006BB-6437-42F3-95D4-C090ADD3B37D"),
    "issuing_location": os.getenv("IMS_ISSUING_LOCATION", "C5C006BB-6437-42F3-95D4-C090ADD3B37D"),
    "company_location": os.getenv("IMS_COMPANY_LOCATION", "DF35D4C7-C663-4974-A886-A1E18D3C9618"),
    "primary_line_guid": os.getenv("TRITON_PRIMARY_LINE_GUID", "07564291-CBFE-4BBE-88D1-0548C88ACED4"),
    "default_quote_status_id": 1,
    "default_billing_type_id": 3,
    "default_policy_type_id": 1,
    "default_business_type_id": 9,
    "default_company_commission": 0.25
}

# Application Configuration
APP_CONFIG = {
    "environment": ENV,
    "debug": os.getenv("DEBUG", "False").lower() == "true",
    "host": os.getenv("HOST", "0.0.0.0"),
    "port": int(os.getenv("PORT", "8000")),
    "log_level": os.getenv("LOG_LEVEL", "INFO")
}

# Environment-specific features
FEATURE_FLAGS = {
    "enable_debug_endpoints": os.getenv("ENABLE_DEBUG_ENDPOINTS", "False").lower() == "true",
    "allow_test_transactions": os.getenv("ALLOW_TEST_TRANSACTIONS", "False").lower() == "true",
    "show_sql_queries": os.getenv("SHOW_SQL_QUERIES", "False").lower() == "true",
    "mock_external_calls": os.getenv("MOCK_EXTERNAL_CALLS", "False").lower() == "true",
    "max_test_amount": float(os.getenv("MAX_TEST_AMOUNT", "0"))
}

# Database Configuration (Critical - different per environment!)
DATABASE_CONFIG = {
    "server": os.getenv("DB_SERVER"),
    "database": os.getenv("DB_NAME"),
    "username": os.getenv("DB_USERNAME"),
    "password": os.getenv("DB_PASSWORD"),
}

# Validate database config
if not all([DATABASE_CONFIG["server"], DATABASE_CONFIG["database"], 
            DATABASE_CONFIG["username"], DATABASE_CONFIG["password"]]):
    print("ERROR: Database configuration incomplete!")
    print(f"Check your {ENV} environment file")
    sys.exit(1)

# Helper function to check if in production
def is_production():
    return ENV == 'production'

# Helper function to check if in development
def is_development():
    return ENV == 'development'

# Log configuration summary (without sensitive data)
if __name__ == "__main__":
    print("\nConfiguration Summary:")
    print(f"  Environment: {ENV}")
    print(f"  Port: {APP_CONFIG['port']}")
    print(f"  Debug: {APP_CONFIG['debug']}")
    print(f"  Database: {DATABASE_CONFIG['database']}")
    print(f"  IMS URL: {IMS_CONFIG['BASE_URL']}")
    print(f"  Debug Endpoints: {FEATURE_FLAGS['enable_debug_endpoints']}")
    print(f"  Test Transactions: {FEATURE_FLAGS['allow_test_transactions']}")
    print("\n✓ Configuration loaded successfully!")