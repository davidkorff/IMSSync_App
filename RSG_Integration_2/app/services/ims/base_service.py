import logging
from typing import Optional, Dict, Any
from zeep import Client, Settings
from zeep.transports import Transport

from config import IMS_CONFIG

logger = logging.getLogger(__name__)

class BaseIMSService:
    """Base class for all IMS service interactions"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.base_url = IMS_CONFIG["base_url"]
        self.endpoint = IMS_CONFIG["endpoints"].get(service_name)
        self.timeout = IMS_CONFIG["timeout"]
        self._client: Optional[Client] = None
        
        if not self.endpoint:
            raise ValueError(f"Unknown service: {service_name}")
        
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize SOAP client for the service"""
        wsdl_url = f"{self.base_url}{self.endpoint}?wsdl"
        try:
            settings = Settings(strict=False, xml_huge_tree=True)
            transport = Transport(timeout=self.timeout)
            self._client = Client(wsdl_url, transport=transport, settings=settings)
            logger.info(f"Initialized {self.service_name} client")
        except Exception as e:
            logger.error(f"Failed to initialize {self.service_name} client: {e}")
            raise
    
    @property
    def client(self) -> Client:
        """Get the SOAP client"""
        if not self._client:
            raise Exception(f"{self.service_name} client not initialized")
        return self._client
    
    def get_header(self, token: str) -> Dict[str, Any]:
        """Get SOAP header with authentication token"""
        return {
            'TokenHeader': {
                'Token': token,
                'Context': IMS_CONFIG["credentials"]["project_name"]
            }
        }