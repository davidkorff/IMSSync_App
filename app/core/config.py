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
            "password": os.getenv("IMS_ONE_PASSWORD", "kCeTLc2bxqOmG72ZBvMFkA==")
        },
        "iscmga_test": {
            "config_file": "ISCMGA_Test.config",
            "username": os.getenv("ISCMGA_TEST_USERNAME", "dkorff"),
            "password": os.getenv("ISCMGA_TEST_PASSWORD", "kCeTLc2bxqOmG72ZBvMFkA==")
        }
    }
    
    DEFAULT_ENVIRONMENT: str = "iscmga_test"
    
    # Logging settings
    LOG_LEVEL: str = "INFO"

settings = Settings() 