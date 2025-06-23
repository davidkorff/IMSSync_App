import os
from pydantic_settings import BaseSettings
from typing import List, Dict, Optional
import json
from dotenv import load_dotenv

load_dotenv()

# Debug: Print loaded environment variables
import logging
logger = logging.getLogger(__name__)
logger.info("Loading environment variables...")
logger.info(f"DEFAULT_ENVIRONMENT: {os.getenv('DEFAULT_ENVIRONMENT')}")
logger.info(f"TRITON_DEFAULT_OFFICE_GUID: {os.getenv('TRITON_DEFAULT_OFFICE_GUID')}")
logger.info(f"TRITON_DEFAULT_PRODUCER_GUID: {os.getenv('TRITON_DEFAULT_PRODUCER_GUID')}")

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "IMS Integration API"
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    
    # Security settings
    API_KEY_NAME: str = "X-API-Key"
    API_KEYS: List[str] = json.loads(os.getenv("API_KEYS", '["test_api_key"]'))
    
    # Triton-specific security settings
    TRITON_API_KEYS: List[str] = json.loads(os.getenv("TRITON_API_KEYS", '["triton_test_key"]'))
    TRITON_CLIENT_IDS: List[str] = json.loads(os.getenv("TRITON_CLIENT_IDS", '["triton"]'))
    
    # IMS settings
    IMS_ENVIRONMENTS: Dict = {
        "ims_one": {
            "config_file": "IMS_ONE.config",
            "username": os.getenv("IMS_ONE_USERNAME", "david.korff"),
            "password": os.getenv("IMS_ONE_PASSWORD", "kCeTLc2bxqOmG72ZBvMFkA=="),
            "sources": {
                "triton": {
                    "default_producer_guid": os.getenv("TRITON_DEFAULT_PRODUCER_GUID", "895E9291-CFB6-4299-8799-9AF77DF937D6"),
                    "default_line_guid": os.getenv("TRITON_PRIMARY_LINE_GUID", "07564291-CBFE-4BBE-88D1-0548C88ACED4"),
                    "excess_line_guid": os.getenv("TRITON_EXCESS_LINE_GUID", "08798559-321C-4FC0-98ED-A61B92215F31"),
                    "default_underwriter_guid": os.getenv("TRITON_DEFAULT_UNDERWRITER_GUID", "E4391D2A-58FB-4E2D-8B7D-3447D9E18C88"),
                    "issuing_location_guid": os.getenv("TRITON_ISSUING_LOCATION_GUID", "C5C006BB-6437-42F3-95D4-C090ADD3B37D"),
                    "company_location_guid": os.getenv("TRITON_COMPANY_LOCATION_GUID", "DF35D4C7-C663-4974-A886-A1E18D3C9618"),
                    "quoting_location_guid": os.getenv("TRITON_QUOTING_LOCATION_GUID", "C5C006BB-6437-42F3-95D4-C090ADD3B37D"),
                    "default_business_type_id": int(os.getenv("TRITON_DEFAULT_BUSINESS_TYPE_ID", "1")),
                    "default_office_guid": os.getenv("TRITON_DEFAULT_OFFICE_GUID", "00000000-0000-0000-0000-000000000000"),
                    "raters": {
                        "AHC Primary": {
                            "rater_id": int(os.getenv("TRITON_PRIMARY_RATER_ID", "1")),
                            "factor_set_guid": os.getenv("TRITON_PRIMARY_FACTOR_SET_GUID", "00000000-0000-0000-0000-000000000000"),
                            "template": "triton_primary.xlsx"
                        },
                        "AHC Excess": {
                            "rater_id": int(os.getenv("TRITON_EXCESS_RATER_ID", "2")),
                            "factor_set_guid": os.getenv("TRITON_EXCESS_FACTOR_SET_GUID", "00000000-0000-0000-0000-000000000000"),
                            "template": "triton_excess.xlsx"
                        }
                    }
                },
                "xuber": {
                    "default_producer_guid": os.getenv("XUBER_DEFAULT_PRODUCER_GUID", "00000000-0000-0000-0000-000000000000"),
                    "default_line_guid": os.getenv("XUBER_DEFAULT_LINE_GUID", "00000000-0000-0000-0000-000000000000"),
                    "raters": {
                        "AHC Primary": {
                            "rater_id": int(os.getenv("XUBER_PRIMARY_RATER_ID", "3")),
                            "factor_set_guid": os.getenv("XUBER_PRIMARY_FACTOR_SET_GUID", "00000000-0000-0000-0000-000000000000"),
                            "template": "xuber_primary.xlsx"
                        }
                    }
                }
            }
        },
        "iscmga_test": {
            "config_file": "ISCMGA_Test.config",
            "username": os.getenv("ISCMGA_TEST_USERNAME", "dkorff"),
            "password": os.getenv("ISCMGA_TEST_PASSWORD", "kCeTLc2bxqOmG72ZBvMFkA=="),
            "sources": {
                "triton": {
                    "default_producer_guid": os.getenv("TRITON_DEFAULT_PRODUCER_GUID", "895E9291-CFB6-4299-8799-9AF77DF937D6"),
                    "default_line_guid": os.getenv("TRITON_PRIMARY_LINE_GUID", "07564291-CBFE-4BBE-88D1-0548C88ACED4"),
                    "excess_line_guid": os.getenv("TRITON_EXCESS_LINE_GUID", "08798559-321C-4FC0-98ED-A61B92215F31"),
                    "default_underwriter_guid": os.getenv("TRITON_DEFAULT_UNDERWRITER_GUID", "E4391D2A-58FB-4E2D-8B7D-3447D9E18C88"),
                    "issuing_location_guid": os.getenv("TRITON_ISSUING_LOCATION_GUID", "C5C006BB-6437-42F3-95D4-C090ADD3B37D"),
                    "company_location_guid": os.getenv("TRITON_COMPANY_LOCATION_GUID", "DF35D4C7-C663-4974-A886-A1E18D3C9618"),
                    "quoting_location_guid": os.getenv("TRITON_QUOTING_LOCATION_GUID", "C5C006BB-6437-42F3-95D4-C090ADD3B37D"),
                    "default_business_type_id": int(os.getenv("TRITON_DEFAULT_BUSINESS_TYPE_ID", "1")),
                    "default_office_guid": os.getenv("TRITON_DEFAULT_OFFICE_GUID", "00000000-0000-0000-0000-000000000000"),
                    "raters": {
                        "AHC Primary": {
                            "rater_id": int(os.getenv("TRITON_PRIMARY_RATER_ID", "1")),
                            "factor_set_guid": os.getenv("TRITON_PRIMARY_FACTOR_SET_GUID", "00000000-0000-0000-0000-000000000000"),
                            "template": "triton_primary.xlsx"
                        },
                        "AHC Excess": {
                            "rater_id": int(os.getenv("TRITON_EXCESS_RATER_ID", "2")),
                            "factor_set_guid": os.getenv("TRITON_EXCESS_FACTOR_SET_GUID", "00000000-0000-0000-0000-000000000000"),
                            "template": "triton_excess.xlsx"
                        }
                    }
                },
                "xuber": {
                    "default_producer_guid": os.getenv("XUBER_DEFAULT_PRODUCER_GUID", "00000000-0000-0000-0000-000000000000"),
                    "default_line_guid": os.getenv("XUBER_DEFAULT_LINE_GUID", "00000000-0000-0000-0000-000000000000"),
                    "raters": {
                        "AHC Primary": {
                            "rater_id": int(os.getenv("XUBER_PRIMARY_RATER_ID", "3")),
                            "factor_set_guid": os.getenv("XUBER_PRIMARY_FACTOR_SET_GUID", "00000000-0000-0000-0000-000000000000"),
                            "template": "xuber_primary.xlsx"
                        }
                    }
                }
            }
        }
    }
    
    DEFAULT_ENVIRONMENT: str = "iscmga_test"
    
    # Logging settings
    LOG_LEVEL: str = "INFO"

settings = Settings() 