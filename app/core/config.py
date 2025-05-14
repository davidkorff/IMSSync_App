import os
from pydantic_settings import BaseSettings
from typing import List, Dict, Optional
import json
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "IMS Integration API"
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    
    # Security settings
    API_KEY_NAME: str = "X-API-Key"
    API_KEYS: List[str] = json.loads(os.getenv("API_KEYS", '["test_api_key"]'))
    
    # IMS settings
    IMS_ENVIRONMENTS: Dict = {
        "ims_one": {
            "config_file": "IMS_ONE.config",
            "username": os.getenv("IMS_ONE_USERNAME", "david.korff"),
            "password": os.getenv("IMS_ONE_PASSWORD", "kCeTLc2bxqOmG72ZBvMFkA=="),
            "sources": {
                "triton": {
                    "default_producer_guid": os.getenv("TRITON_DEFAULT_PRODUCER_GUID", "00000000-0000-0000-0000-000000000000"),
                    "default_line_guid": os.getenv("TRITON_PRIMARY_LINE_GUID", "00000000-0000-0000-0000-000000000000"),
                    "excess_line_guid": os.getenv("TRITON_EXCESS_LINE_GUID", "00000000-0000-0000-0000-000000000000"),
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
                    "default_producer_guid": os.getenv("TRITON_DEFAULT_PRODUCER_GUID", "00000000-0000-0000-0000-000000000000"),
                    "default_line_guid": os.getenv("TRITON_PRIMARY_LINE_GUID", "00000000-0000-0000-0000-000000000000"),
                    "excess_line_guid": os.getenv("TRITON_EXCESS_LINE_GUID", "00000000-0000-0000-0000-000000000000"),
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