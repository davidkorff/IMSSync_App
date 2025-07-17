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
            
            # Create insured object
            insured = {
                'BusinessTypeID': 9,  # LLC - Partnership (hardcoded per IMS requirement)
                'CorporationName': data["insured_name"] if data.get("business_type") != "individual" else None,
                'LastName': data["insured_name"] if data.get("business_type") == "individual" else None,
                'NameOnPolicy': data["insured_name"],
                'DBA': None,
                'FEIN': None,
                'SSN': None,
                'DateOfBirth': None,
                'RiskId': None,
                'Office': "00000000-0000-0000-0000-000000000000"  # Default GUID
            }
            
            # Create location object
            location = {
                'InsuredGuid': "00000000-0000-0000-0000-000000000000",  # Will be set by server
                'InsuredLocationGuid': "00000000-0000-0000-0000-000000000000",  # Will be set by server
                'LocationName': 'Primary',
                'Address1': data["address_1"],
                'Address2': data.get("address_2", ""),
                'City': data["city"],
                'County': None,
                'State': data["state"],
                'Zip': data["zip"],
                'ZipPlus': None,
                'ISOCountryCode': 'US',
                'Region': None,
                'Phone': None,
                'Fax': None,
                'Email': None,
                'Website': None,
                'DeliveryMethodID': 1,  # Default
                'LocationTypeID': 1,  # Primary
                'MobileNumber': None,
                'OptOut': False
            }
            
            response = self.client.service.AddInsuredWithLocation(
                insured=insured,
                location=location,
                _soapheaders=self.get_header(token)
            )
            
            insured_guid = UUID(str(response))
            logger.info(f"Created insured with GUID: {insured_guid}")
            return insured_guid
            
        except Exception as e:
            logger.error(f"Error creating insured: {e}")
            raise