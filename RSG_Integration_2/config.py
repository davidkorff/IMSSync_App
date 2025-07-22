import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

IMS_CONFIG = {
    "base_url": os.getenv("IMS_BASE_URL", "http://10.64.32.234"),
    "environments": {
        "login": os.getenv("IMS_LOGIN_ENV", "/ims_one"),
        "services": os.getenv("IMS_SERVICES_ENV", "/ims_origintest")
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
        "password": os.getenv("IMS_ONE_PASSWORD"),  # Already encrypted
        "program_code": os.getenv("IMS_PROGRAM_CODE", "TRTON"),
        "project_name": os.getenv("IMS_PROJECT_NAME", "RSG_Integration")
    },
    "timeout": int(os.getenv("IMS_TIMEOUT", "30"))
}

TRITON_CONFIG = {
    "api_key": os.getenv("TRITON_API_KEY"),
    "webhook_secret": os.getenv("TRITON_WEBHOOK_SECRET")
}

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

APP_CONFIG = {
    "debug": os.getenv("DEBUG", "False").lower() == "true",
    "host": os.getenv("HOST", "0.0.0.0"),
    "port": int(os.getenv("PORT", "8000")),
    "log_level": os.getenv("LOG_LEVEL", "INFO")
}