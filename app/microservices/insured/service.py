"""
Insured Microservice Implementation
"""

import time
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.microservices.core import (
    BaseMicroservice, 
    ServiceConfig, 
    ServiceResponse,
    ServiceError
)
from app.microservices.core.exceptions import ValidationError
from .models import (
    Insured,
    InsuredCreate,
    InsuredUpdate,
    InsuredLocation,
    InsuredContact,
    InsuredSearchCriteria,
    InsuredSearchResult
)
from .matcher import InsuredMatcher


class InsuredService(BaseMicroservice):
    """
    Microservice for managing insureds in IMS
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        if not config:
            config = ServiceConfig(
                name="insured",
                version="1.0.0"
            )
        super().__init__(config)
        
        # Initialize matcher for fuzzy matching
        self.matcher = InsuredMatcher()
    
    def _on_initialize(self):
        """Service-specific initialization"""
        self.logger.info("Insured service specific initialization")
        # Any insured-specific setup
    
    def _on_shutdown(self):
        """Service-specific shutdown"""
        self.logger.info("Insured service specific shutdown")
    
    async def find_by_name(self, name: str, exact_match: bool = False) -> ServiceResponse:
        """
        Find insureds by name
        
        Args:
            name: Name to search for
            exact_match: Whether to require exact match
            
        Returns:
            ServiceResponse with list of matching insureds
        """
        self._log_operation("find_by_name", {"name": name, "exact_match": exact_match})
        
        try:
            # Call IMS to search by name
            result = self.soap_client.service.FindInsuredByName(
                strName=name,
                blnExactMatch=exact_match
            )
            
            insureds = []
            if result and hasattr(result, 'Insureds'):
                for ims_insured in result.Insureds.Insured:
                    insureds.append(self._map_ims_to_model(ims_insured))
            
            return ServiceResponse(
                success=True,
                data=insureds,
                metadata={"count": len(insureds)}
            )
            
        except Exception as e:
            return self._handle_error(e, "find_by_name")
    
    async def find_by_criteria(self, criteria: InsuredSearchCriteria) -> ServiceResponse:
        """
        Find insureds by multiple criteria
        
        Args:
            criteria: Search criteria
            
        Returns:
            ServiceResponse with InsuredSearchResult
        """
        self._log_operation("find_by_criteria", criteria.dict(exclude_none=True))
        start_time = time.time()
        
        try:
            insureds = []
            
            # Search by name if provided
            if criteria.name:
                name_results = await self.find_by_name(criteria.name, criteria.exact_match)
                if name_results.success and name_results.data:
                    insureds.extend(name_results.data)
            
            # Search by tax ID if provided
            if criteria.tax_id and not insureds:
                tax_results = await self.find_by_tax_id(criteria.tax_id)
                if tax_results.success and tax_results.data:
                    insureds.extend(tax_results.data)
            
            # Filter results based on additional criteria
            if insureds and any([criteria.city, criteria.state, criteria.zip_code]):
                insureds = self._filter_by_location(insureds, criteria)
            
            # Apply limit
            if len(insureds) > criteria.limit:
                insureds = insureds[:criteria.limit]
            
            execution_time = (time.time() - start_time) * 1000
            
            result = InsuredSearchResult(
                insureds=insureds,
                total_count=len(insureds),
                search_criteria=criteria,
                execution_time_ms=execution_time
            )
            
            return ServiceResponse(
                success=True,
                data=result
            )
            
        except Exception as e:
            return self._handle_error(e, "find_by_criteria")
    
    async def find_by_tax_id(self, tax_id: str) -> ServiceResponse:
        """
        Find insureds by tax ID
        
        Args:
            tax_id: Tax ID to search for
            
        Returns:
            ServiceResponse with list of matching insureds
        """
        self._log_operation("find_by_tax_id", {"tax_id": tax_id})
        
        try:
            # Call IMS to search by SSN/FEIN
            result = self.soap_client.service.FindInsuredBySSN(
                strSSN=tax_id
            )
            
            insureds = []
            if result and hasattr(result, 'Insureds'):
                for ims_insured in result.Insureds.Insured:
                    insureds.append(self._map_ims_to_model(ims_insured))
            
            return ServiceResponse(
                success=True,
                data=insureds,
                metadata={"count": len(insureds)}
            )
            
        except Exception as e:
            return self._handle_error(e, "find_by_tax_id")
    
    async def find_or_create(self, data: InsuredCreate) -> ServiceResponse:
        """
        Find existing insured or create new one
        
        Args:
            data: Insured data
            
        Returns:
            ServiceResponse with Insured
        """
        self._log_operation("find_or_create", {"name": data.name})
        
        try:
            # Search for existing
            search_criteria = InsuredSearchCriteria(
                name=data.name,
                tax_id=data.tax_id,
                address=data.address,
                city=data.city,
                state=data.state
            )
            
            search_result = await self.find_by_criteria(search_criteria)
            
            if search_result.success and search_result.data.insureds:
                # Use matcher to find best match
                best_match = self.matcher.find_best_match(
                    data.dict(),
                    [ins.dict() for ins in search_result.data.insureds]
                )
                
                if best_match:
                    self.logger.info(f"Found existing insured: {best_match.guid}")
                    return ServiceResponse(
                        success=True,
                        data=best_match,
                        metadata={"action": "found"}
                    )
            
            # Create new insured
            return await self.create(data)
            
        except Exception as e:
            return self._handle_error(e, "find_or_create")
    
    async def create(self, data: InsuredCreate) -> ServiceResponse:
        """
        Create a new insured
        
        Args:
            data: Insured data
            
        Returns:
            ServiceResponse with created Insured
        """
        self._log_operation("create", {"name": data.name})
        
        try:
            # Validate data
            if not data.name:
                raise ValidationError("Insured name is required")
            
            # Prepare IMS data
            ims_data = {
                "CorporationName": data.name,
                "DBAName": data.dba_name or "",
                "FEIN": data.tax_id or "",
                "BusinessTypeID": data.business_type_id or self._get_default_business_type_id(data.source)
            }
            
            # Call IMS to create insured
            if data.address:
                # Create with location
                result = self.soap_client.service.AddInsuredWithLocation(
                    CorporationName=ims_data["CorporationName"],
                    DBAName=ims_data["DBAName"],
                    FEIN=ims_data["FEIN"],
                    BusinessTypeID=ims_data["BusinessTypeID"],
                    Address1=data.address,
                    Address2="",
                    City=data.city or "",
                    State=data.state or "",
                    ZipCode=data.zip_code or "",
                    OfficePhone=data.phone or "",
                    Description="Primary Location"
                )
            else:
                # Create without location
                result = self.soap_client.service.AddInsured(
                    CorporationName=ims_data["CorporationName"],
                    DBAName=ims_data["DBAName"],
                    FEIN=ims_data["FEIN"],
                    BusinessTypeID=ims_data["BusinessTypeID"]
                )
            
            if not result:
                raise ServiceError("Failed to create insured - no response from IMS")
            
            # Get the created insured
            insured_guid = str(result)
            get_result = await self.get_by_guid(insured_guid)
            
            if get_result.success:
                return ServiceResponse(
                    success=True,
                    data=get_result.data,
                    metadata={"action": "created"}
                )
            else:
                # Return basic info if get fails
                insured = Insured(
                    guid=insured_guid,
                    name=data.name,
                    dba_name=data.dba_name,
                    tax_id=data.tax_id,
                    business_type=data.business_type,
                    business_type_id=data.business_type_id,
                    created_date=datetime.now()
                )
                
                return ServiceResponse(
                    success=True,
                    data=insured,
                    metadata={"action": "created"},
                    warnings=["Could not retrieve full insured details"]
                )
            
        except Exception as e:
            return self._handle_error(e, "create")
    
    async def get_by_guid(self, guid: str) -> ServiceResponse:
        """
        Get insured by GUID
        
        Args:
            guid: Insured GUID
            
        Returns:
            ServiceResponse with Insured
        """
        self._log_operation("get_by_guid", {"guid": guid})
        
        try:
            # Call IMS to get insured
            result = self.soap_client.service.GetInsured(
                InsuredGUID=guid
            )
            
            if not result:
                return ServiceResponse(
                    success=False,
                    error=f"Insured not found: {guid}"
                )
            
            insured = self._map_ims_to_model(result)
            
            return ServiceResponse(
                success=True,
                data=insured
            )
            
        except Exception as e:
            return self._handle_error(e, "get_by_guid")
    
    async def update(self, guid: str, data: InsuredUpdate) -> ServiceResponse:
        """
        Update an existing insured
        
        Args:
            guid: Insured GUID
            data: Update data
            
        Returns:
            ServiceResponse with updated Insured
        """
        self._log_operation("update", {"guid": guid})
        
        try:
            # Get current insured
            get_result = await self.get_by_guid(guid)
            if not get_result.success:
                return get_result
            
            current = get_result.data
            
            # Prepare update data
            update_data = data.dict(exclude_unset=True)
            if not update_data:
                return ServiceResponse(
                    success=True,
                    data=current,
                    warnings=["No fields to update"]
                )
            
            # Call IMS to update
            result = self.soap_client.service.UpdateInsured(
                InsuredGUID=guid,
                CorporationName=data.name or current.name,
                DBAName=data.dba_name or current.dba_name or "",
                FEIN=data.tax_id or current.tax_id or "",
                BusinessTypeID=data.business_type_id or current.business_type_id
            )
            
            # Get updated insured
            return await self.get_by_guid(guid)
            
        except Exception as e:
            return self._handle_error(e, "update")
    
    async def add_location(self, guid: str, location: InsuredLocation) -> ServiceResponse:
        """
        Add a location to an insured
        
        Args:
            guid: Insured GUID
            location: Location data
            
        Returns:
            ServiceResponse with location ID
        """
        self._log_operation("add_location", {"guid": guid})
        
        try:
            # Call IMS to add location
            result = self.soap_client.service.AddInsuredLocation(
                InsuredGUID=guid,
                Address1=location.address,
                Address2=location.address2 or "",
                City=location.city,
                State=location.state,
                ZipCode=location.zip_code,
                OfficePhone="",
                Description=location.description or "Additional Location"
            )
            
            if not result:
                raise ServiceError("Failed to add location")
            
            return ServiceResponse(
                success=True,
                data={"location_id": str(result)},
                metadata={"insured_guid": guid}
            )
            
        except Exception as e:
            return self._handle_error(e, "add_location")
    
    async def add_contact(self, guid: str, contact: InsuredContact) -> ServiceResponse:
        """
        Add a contact to an insured
        
        Args:
            guid: Insured GUID
            contact: Contact data
            
        Returns:
            ServiceResponse with contact ID
        """
        self._log_operation("add_contact", {"guid": guid})
        
        try:
            # Call IMS to add contact
            result = self.soap_client.service.AddInsuredContact(
                InsuredGUID=guid,
                FirstName=contact.first_name,
                LastName=contact.last_name,
                Title=contact.title or "",
                Email=contact.email or "",
                Phone=contact.phone or "",
                Mobile=contact.mobile or "",
                IsPrimary=contact.is_primary
            )
            
            if not result:
                raise ServiceError("Failed to add contact")
            
            return ServiceResponse(
                success=True,
                data={"contact_id": str(result)},
                metadata={"insured_guid": guid}
            )
            
        except Exception as e:
            return self._handle_error(e, "add_contact")
    
    def _map_ims_to_model(self, ims_insured: Any) -> Insured:
        """Map IMS insured object to our model"""
        return Insured(
            guid=str(ims_insured.InsuredGUID),
            insured_id=getattr(ims_insured, 'InsuredID', None),
            name=ims_insured.CorporationName,
            dba_name=getattr(ims_insured, 'DBAName', None),
            tax_id=getattr(ims_insured, 'FEIN', None),
            business_type_id=getattr(ims_insured, 'BusinessTypeID', None),
            created_date=getattr(ims_insured, 'CreatedDate', datetime.now()),
            modified_date=getattr(ims_insured, 'ModifiedDate', None),
            active=getattr(ims_insured, 'Active', True),
            has_submissions=getattr(ims_insured, 'HasSubmissions', False)
        )
    
    def _filter_by_location(self, insureds: List[Insured], criteria: InsuredSearchCriteria) -> List[Insured]:
        """Filter insureds by location criteria"""
        filtered = []
        
        for insured in insureds:
            # Check primary location
            match = True
            
            if criteria.city and insured.locations:
                match = any(
                    loc.city.lower() == criteria.city.lower() 
                    for loc in insured.locations if loc.is_primary
                )
            
            if match and criteria.state and insured.locations:
                match = any(
                    loc.state.upper() == criteria.state.upper() 
                    for loc in insured.locations if loc.is_primary
                )
            
            if match and criteria.zip_code and insured.locations:
                match = any(
                    loc.zip_code.startswith(criteria.zip_code) 
                    for loc in insured.locations if loc.is_primary
                )
            
            if match:
                filtered.append(insured)
        
        return filtered
    
    def _get_default_business_type_id(self, source: Optional[str]) -> int:
        """Get default business type ID for source"""
        # Source-specific defaults
        defaults = {
            "triton": 5,
            "xuber": 6,
            "default": 1
        }
        
        return defaults.get(source.lower() if source else "default", 1)