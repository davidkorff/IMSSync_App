import logging
from datetime import datetime, timedelta
from typing import Optional

from config import IMS_CONFIG
from app.models.ims_models import IMSAuthToken
from .base_service import BaseIMSService

logger = logging.getLogger(__name__)

class AuthService(BaseIMSService):
    """Service for IMS authentication"""
    
    def __init__(self):
        super().__init__("logon")
        self._auth_token: Optional[IMSAuthToken] = None
    
    def get_token(self) -> str:
        """Get or refresh authentication token"""
        if self._auth_token and self._auth_token.expires_at > datetime.now():
            return self._auth_token.token
        
        return self._authenticate()
    
    def _authenticate(self) -> str:
        """Authenticate with IMS"""
        try:
            credentials = IMS_CONFIG["credentials"]
            response = self.client.service.Login(
                programCode=credentials["program_code"],
                contactType=credentials["contact_type"],
                email=credentials["email"],
                password=credentials["password"],
                projectName=credentials["project_name"]
            )
            
            self._auth_token = IMSAuthToken(
                token=str(response),
                expires_at=datetime.now() + timedelta(hours=1)
            )
            logger.info("Successfully authenticated with IMS")
            return self._auth_token.token
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise