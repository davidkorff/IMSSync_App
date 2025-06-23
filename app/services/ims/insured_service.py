"""
IMS Insured Service

This service handles all insured-related operations in IMS including:
- Finding existing insureds
- Creating new insureds
- Managing insured locations
- Managing insured contacts
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.services.ims.base_service import BaseIMSService
from app.services.ims.insured_matcher import InsuredMatcher

logger = logging.getLogger(__name__)


class IMSInsuredService(BaseIMSService):
    """Service for managing insureds in IMS"""
    
    def __init__(self, environment: Optional[str] = None):
        super().__init__(environment)
        self.matcher = InsuredMatcher(self)
    
    def find_insured_by_name(self, name: str, tax_id: Optional[str] = None, 
                            city: str = "", state: str = "", zip_code: str = "") -> Optional[str]:
        """
        Find an insured by name and optionally other criteria
        
        Args:
            name: The insured's name
            tax_id: Optional tax ID (SSN or FEIN) for more precise matching
            city: Optional city for filtering
            state: Optional state for filtering  
            zip_code: Optional zip code for filtering
            
        Returns:
            The insured GUID if found, None otherwise
        """
        self._log_operation("find_insured_by_name", {"name": name, "tax_id": tax_id})
        
        try:
            result = self.soap_client.find_insured_by_name(name, tax_id, city, state, zip_code)
            
            if result:
                logger.info(f"Found existing insured: {result}")
            else:
                logger.info(f"No existing insured found for: {name}")
                
            return result
            
        except Exception as e:
            self._handle_soap_error(e, "find_insured_by_name")
            # Retry once after handling auth errors
            return self.soap_client.find_insured_by_name(name, tax_id, city, state, zip_code)
    
    def find_or_create_insured(self, insured_data: Dict[str, Any]) -> str:
        """
        Find an existing insured or create a new one if not found
        
        This method uses sophisticated matching logic to avoid creating duplicates.
        
        Args:
            insured_data: Dictionary containing insured information
            
        Returns:
            The insured GUID
        """
        # Use the matcher to find the best match
        search_criteria = {
            "name": insured_data.get("name", ""),
            "tax_id": insured_data.get("tax_id"),
            "address": insured_data.get("address"),
            "city": insured_data.get("city"),
            "state": insured_data.get("state"),
            "zip_code": insured_data.get("zip_code")
        }
        
        logger.info(f"Searching for existing insured with criteria: {search_criteria}")
        
        # Use advanced matching
        match = self.matcher.find_best_match(search_criteria)
        
        if match:
            insured_guid = match.get("InsuredGUID")
            logger.info(f"Found existing insured: {match.get('InsuredName')} ({insured_guid})")
            
            # Update insured info if needed
            if self._should_update_insured(insured_data, match):
                logger.info("Updating existing insured with new information")
                self.update_insured(insured_guid, insured_data)
            
            return insured_guid
        
        # No match found - create new insured
        logger.info(f"No matching insured found - creating new: {insured_data.get('name')}")
        return self.create_insured(insured_data)
    
    def create_insured(self, insured_data: Dict[str, Any]) -> str:
        """
        Create a new insured in IMS
        
        Args:
            insured_data: Dictionary containing insured information
            
        Returns:
            The new insured GUID
        """
        self._log_operation("create_insured", {"name": insured_data.get("name")})
        
        try:
            # Validate required fields
            if not insured_data.get("name"):
                raise ValueError("Insured name is required")
            
            # Determine business type
            business_type_id = self._determine_business_type(insured_data)
            insured_data["business_type_id"] = business_type_id
            
            # Get default office GUID from source configuration
            source = insured_data.get("source", "triton")
            source_config = self._get_source_config(source)
            insured_data["office_guid"] = source_config.get("default_office_guid", "00000000-0000-0000-0000-000000000000")
            
            # Create the insured
            insured_guid = self.soap_client.add_insured(insured_data)
            
            logger.info(f"Created new insured: {insured_guid}")
            return insured_guid
            
        except Exception as e:
            if "authentication" in str(e).lower():
                self._handle_soap_error(e, "create_insured")
                # Retry once
                return self.soap_client.add_insured(insured_data)
            raise
    
    def add_insured_location(self, insured_guid: str, location_data: Dict[str, Any]) -> int:
        """
        Add a location to an insured
        
        Args:
            insured_guid: The insured's GUID
            location_data: Dictionary containing location information
            
        Returns:
            The location ID
        """
        self._log_operation("add_insured_location", {
            "insured_guid": insured_guid,
            "address": location_data.get("address")
        })
        
        try:
            # Set defaults
            location_data.setdefault("country", "USA")
            location_data.setdefault("description", "Primary Location")
            
            location_id = self.soap_client.add_insured_location(insured_guid, location_data)
            
            logger.info(f"Added location {location_id} to insured {insured_guid}")
            return location_id
            
        except Exception as e:
            if "authentication" in str(e).lower():
                self._handle_soap_error(e, "add_insured_location")
                # Retry once
                return self.soap_client.add_insured_location(insured_guid, location_data)
            raise
    
    def add_insured_contact(self, insured_guid: str, contact_data: Dict[str, Any]) -> str:
        """
        Add a contact to an insured
        
        Args:
            insured_guid: The insured's GUID
            contact_data: Dictionary containing contact information
            
        Returns:
            The contact GUID
        """
        self._log_operation("add_insured_contact", {
            "insured_guid": insured_guid,
            "contact_name": contact_data.get("name")
        })
        
        # Build the contact XML
        body_content = f"""
        <AddInsuredContact xmlns="http://tempuri.org/IMSWebServices/InsuredFunctions">
            <insuredGuid>{insured_guid}</insuredGuid>
            <contact>
                <FirstName>{contact_data.get('first_name', '')}</FirstName>
                <LastName>{contact_data.get('last_name', '')}</LastName>
                <Email>{contact_data.get('email', '')}</Email>
                <Phone>{contact_data.get('phone', '')}</Phone>
                <Title>{contact_data.get('title', '')}</Title>
            </contact>
        </AddInsuredContact>
        """
        
        try:
            response = self.soap_client._make_soap_request(
                self.soap_client.insured_functions_url,
                "http://tempuri.org/IMSWebServices/InsuredFunctions/AddInsuredContact",
                body_content
            )
            
            # Extract contact GUID from response
            if response and 'soap:Body' in response:
                add_response = response['soap:Body'].get('AddInsuredContactResponse', {})
                contact_guid = add_response.get('AddInsuredContactResult')
                
                if contact_guid:
                    logger.info(f"Added contact {contact_guid} to insured {insured_guid}")
                    return contact_guid
                    
            raise ValueError("Failed to add insured contact: No GUID returned")
            
        except Exception as e:
            if "authentication" in str(e).lower():
                self._handle_soap_error(e, "add_insured_contact")
                # Retry once
                return self.add_insured_contact(insured_guid, contact_data)
            raise
    
    def get_insured_info(self, insured_guid: str) -> Dict[str, Any]:
        """
        Get detailed information about an insured
        
        Args:
            insured_guid: The insured's GUID
            
        Returns:
            Dictionary containing insured information
        """
        self._log_operation("get_insured_info", {"insured_guid": insured_guid})
        
        body_content = f"""
        <GetInsured xmlns="http://tempuri.org/IMSWebServices/InsuredFunctions">
            <insuredGuid>{insured_guid}</insuredGuid>
        </GetInsured>
        """
        
        try:
            response = self.soap_client._make_soap_request(
                self.soap_client.insured_functions_url,
                "http://tempuri.org/IMSWebServices/InsuredFunctions/GetInsured",
                body_content
            )
            
            # Parse and return the response
            if response and 'soap:Body' in response:
                get_response = response['soap:Body'].get('GetInsuredResponse', {})
                insured_info = get_response.get('GetInsuredResult', {})
                
                if insured_info:
                    logger.info(f"Retrieved info for insured {insured_guid}")
                    return insured_info
                    
            return {}
            
        except Exception as e:
            if "authentication" in str(e).lower():
                self._handle_soap_error(e, "get_insured_info")
                # Retry once
                return self.get_insured_info(insured_guid)
            raise
    
    def _determine_business_type(self, insured_data: Dict[str, Any]) -> int:
        """
        Determine the business type ID based on insured data
        
        Business Type IDs:
        1 = Corporation
        2 = Partnership  
        3 = Individual
        4 = Sole Proprietor
        5 = LLC
        6 = Other
        """
        # Check if explicitly provided
        if "business_type_id" in insured_data:
            return int(insured_data["business_type_id"])
        
        # Check business type name
        business_type = insured_data.get("business_type", "").lower()
        
        type_mapping = {
            "corporation": 1,
            "corp": 1,
            "inc": 1,
            "partnership": 2,
            "individual": 3,
            "person": 3,
            "sole proprietor": 4,
            "sole prop": 4,
            "llc": 5,
            "limited liability": 5
        }
        
        for key, value in type_mapping.items():
            if key in business_type:
                return value
        
        # Check if it's an individual based on tax ID
        tax_id = insured_data.get("tax_id", "")
        if tax_id and len(tax_id.replace("-", "")) == 9:
            # SSN format suggests individual
            if not any(corp_indicator in insured_data.get("name", "").lower() 
                      for corp_indicator in ["inc", "llc", "corp", "company", "ltd"]):
                return 3  # Individual
        
        # Default to Corporation
        return 1
    
    def _should_update_insured(self, new_data: Dict[str, Any], existing_data: Dict[str, Any]) -> bool:
        """Check if existing insured should be updated with new data"""
        # Check if key fields have changed
        fields_to_check = ["Address1", "City", "State", "ZipCode", "TaxID"]
        
        for field in fields_to_check:
            new_value = new_data.get(field.lower(), "")
            existing_value = existing_data.get(field, "")
            
            # If new data has a value and it's different from existing
            if new_value and new_value != existing_value:
                return True
        
        return False
    
    def update_insured(self, insured_guid: str, insured_data: Dict[str, Any]) -> bool:
        """
        Update an existing insured's information
        
        Args:
            insured_guid: The insured's GUID
            insured_data: Updated insured information
            
        Returns:
            True if successful
        """
        self._log_operation("update_insured", {"insured_guid": insured_guid})
        
        # Determine business type
        business_type_id = self._determine_business_type(insured_data)
        is_individual = business_type_id in [3, 4]
        
        # Parse name for individuals
        name = insured_data.get("name", "")
        first_name = last_name = corporation_name = ""
        
        if is_individual:
            name_parts = name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""
        else:
            corporation_name = name
        
        body_content = f"""
        <UpdateInsured xmlns="http://tempuri.org/IMSWebServices/InsuredFunctions">
            <insuredGuid>{insured_guid}</insuredGuid>
            <insured>
                <BusinessTypeID>{business_type_id}</BusinessTypeID>
                <FirstName>{first_name}</FirstName>
                <LastName>{last_name}</LastName>
                <CorporationName>{corporation_name}</CorporationName>
                <FEIN>{insured_data.get('tax_id', '') if not is_individual else ''}</FEIN>
                <SSN>{insured_data.get('tax_id', '') if is_individual else ''}</SSN>
            </insured>
        </UpdateInsured>
        """
        
        try:
            response = self.soap_client._make_soap_request(
                self.soap_client.insured_functions_url,
                "http://tempuri.org/IMSWebServices/InsuredFunctions/UpdateInsured",
                body_content
            )
            
            if response and 'soap:Body' in response:
                update_response = response['soap:Body'].get('UpdateInsuredResponse', {})
                result = update_response.get('UpdateInsuredResult', False)
                
                if result:
                    logger.info(f"Successfully updated insured {insured_guid}")
                    return True
                else:
                    logger.error(f"Failed to update insured {insured_guid}")
                    return False
            
            return False
            
        except Exception as e:
            if "authentication" in str(e).lower():
                self._handle_soap_error(e, "update_insured")
                # Retry once
                return self.update_insured(insured_guid, insured_data)
            raise