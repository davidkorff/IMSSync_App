import logging
from typing import Optional, Dict, Any
from uuid import UUID

from .base_service import BaseIMSService
from .auth_service import AuthService

logger = logging.getLogger(__name__)

class InsuredService(BaseIMSService):
    """Service for IMS insured operations"""
    
    def __init__(self, auth_service: AuthService):
        super().__init__("insured_functions")
        self.auth_service = auth_service
    
    def find_by_name_and_address(self, name: str, address: str, city: str, 
                                state: str, zip_code: str) -> Optional[UUID]:
        """Search for insured by name and address"""
        try:
            token = self.auth_service.get_token()
            response = self.client.service.FindInsuredByName(
                insuredName=name,
                city=city,
                state=state,
                zip=zip_code,
                zipPlus="",
                _soapheaders=self.get_header(token)
            )
            
            if response and str(response) != "00000000-0000-0000-0000-000000000000":
                logger.info(f"Found insured with GUID: {response}")
                return UUID(str(response))
            
            logger.info(f"No insured found for {name}")
            return None
            
        except Exception as e:
            logger.error(f"Error finding insured: {e}")
            raise
    
    def create_with_location(self, data: Dict[str, Any]) -> UUID:
        """Create a new insured with primary location"""
        try:
            token = self.auth_service.get_token()
            response = self.client.service.AddInsuredWithLocation(
                insuredName=data["insured_name"],
                insuredType=data.get("business_type", "individual"),
                locationCode="LOC001",
                locationType="Primary",
                address1=data["address_1"],
                address2=data.get("address_2", ""),
                city=data["city"],
                state=data["state"],
                zip=data["zip"],
                _soapheaders=self.get_header(token)
            )
            
            insured_guid = UUID(str(response))
            logger.info(f"Created insured with GUID: {insured_guid}")
            return insured_guid
            
        except Exception as e:
            logger.error(f"Error creating insured: {e}")
            raise