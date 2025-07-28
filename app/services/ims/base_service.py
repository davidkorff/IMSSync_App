import logging
import requests
from typing import Optional
from abc import ABC, abstractmethod

from app.services.ims.auth_service import get_auth_service

logger = logging.getLogger(__name__)


class BaseIMSService(ABC):
    """Base class for IMS services with common functionality."""
    
    def __init__(self):
        self._auth_service = None
        
    def _get_auth_service(self):
        """Get auth service instance."""
        if self._auth_service is None:
            self._auth_service = get_auth_service()
        return self._auth_service
    
    def _make_request(self, endpoint: str, soap_body: str, headers: dict) -> Optional[requests.Response]:
        """Make SOAP request to IMS."""
        try:
            response = requests.post(
                endpoint,
                data=soap_body,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response
            else:
                logger.error(f"Request failed with status {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return None