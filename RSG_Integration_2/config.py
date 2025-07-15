import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

IMS_CONFIG = {
    "base_url": os.getenv("IMS_BASE_URL", "http://10.64.32.234/ims_one"),
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

APP_CONFIG = {
    "debug": os.getenv("DEBUG", "False").lower() == "true",
    "host": os.getenv("HOST", "0.0.0.0"),
    "port": int(os.getenv("PORT", "8000")),
    "log_level": os.getenv("LOG_LEVEL", "INFO")
}