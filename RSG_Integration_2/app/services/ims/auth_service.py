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
            response = self.client.service.LoginIMSUser(
                userName=credentials["username"],
                tripleDESEncryptedPassword=credentials["password"]
            )
            
            # Extract token from response
            token = response.Token if hasattr(response, 'Token') else str(response)
            user_guid = response.UserGuid if hasattr(response, 'UserGuid') else None
            
            self._auth_token = IMSAuthToken(
                token=token,
                expires_at=datetime.now() + timedelta(hours=1)
            )
            logger.info(f"Successfully authenticated with IMS (UserGuid: {user_guid})")
            return self._auth_token.token
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise