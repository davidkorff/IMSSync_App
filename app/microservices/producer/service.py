"""
Producer Microservice Implementation
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

from app.microservices.core import (
    BaseMicroservice, 
    ServiceConfig, 
    ServiceResponse,
    ServiceError,
    get_service
)
from app.microservices.core.exceptions import ValidationError
from .models import (
    Producer,
    ProducerContact,
    ProducerLocation,
    ProducerSearch,
    ProducerCreate,
    ProducerContactCreate,
    ProducerStatus,
    UnderwriterInfo
)


class ProducerService(BaseMicroservice):
    """
    Microservice for managing producers/agents in IMS
    """
    
    def __init__(self, config: Optional[ServiceConfig] = None):
        if not config:
            config = ServiceConfig(
                name="producer",
                version="1.0.0"
            )
        super().__init__(config)
        
        # Cache for frequently used producers
        self._producer_cache: Dict[str, Producer] = {}
        
        # Get data access service for queries
        self._data_service = None
    
    @property
    def data_service(self):
        """Lazy load data service"""
        if not self._data_service:
            self._data_service = get_service('data_access')
        return self._data_service
    
    def _on_initialize(self):
        """Service-specific initialization"""
        self.logger.info("Producer service specific initialization")
        # Preload default producers if needed
    
    def _on_shutdown(self):
        """Service-specific shutdown"""
        self.logger.info("Producer service specific shutdown")
        self._producer_cache.clear()
    
    async def get_by_name(self, producer_name: str) -> ServiceResponse:
        """
        Get producer by name
        
        Args:
            producer_name: Producer/Agency name
            
        Returns:
            ServiceResponse with Producer
        """
        self._log_operation("get_by_name", {"producer_name": producer_name})
        
        try:
            # Search for producer
            result = self.soap_client.service.ProducerSearch(
                ProducerName=producer_name
            )
            
            if result and hasattr(result, 'Producers'):
                producers = []
                for ims_producer in result.Producers:
                    # Look for exact match
                    if ims_producer.ProducerName.lower() == producer_name.lower():
                        producer = await self._get_full_producer_info(
                            str(ims_producer.ProducerGUID)
                        )
                        if producer:
                            return ServiceResponse(
                                success=True,
                                data=producer
                            )
                
                # No exact match found
                return ServiceResponse(
                    success=False,
                    error=f"Producer not found: {producer_name}"
                )
            else:
                return ServiceResponse(
                    success=False,
                    error=f"Producer not found: {producer_name}"
                )
                
        except Exception as e:
            return self._handle_error(e, "get_by_name")
    
    async def get_by_guid(self, producer_guid: str) -> ServiceResponse:
        """
        Get producer by GUID
        
        Args:
            producer_guid: Producer GUID
            
        Returns:
            ServiceResponse with Producer
        """
        self._log_operation("get_by_guid", {"producer_guid": producer_guid})
        
        # Check cache first
        if producer_guid in self._producer_cache:
            return ServiceResponse(
                success=True,
                data=self._producer_cache[producer_guid],
                metadata={"cached": True}
            )
        
        try:
            producer = await self._get_full_producer_info(producer_guid)
            if producer:
                # Cache the result
                self._producer_cache[producer_guid] = producer
                
                return ServiceResponse(
                    success=True,
                    data=producer
                )
            else:
                return ServiceResponse(
                    success=False,
                    error=f"Producer not found: {producer_guid}"
                )
                
        except Exception as e:
            return self._handle_error(e, "get_by_guid")
    
    async def create_producer(self, data: ProducerCreate) -> ServiceResponse:
        """
        Create a new producer/agency
        
        Args:
            data: Producer creation data
            
        Returns:
            ServiceResponse with created Producer
        """
        self._log_operation("create_producer", {"producer_name": data.producer_name})
        
        try:
            # Create producer with primary location
            result = self.soap_client.service.AddProducerWithLocation(
                ProducerName=data.producer_name,
                ProducerCode=data.producer_code or "",
                TaxID=data.tax_id or "",
                Address1=data.address1,
                Address2=data.address2 or "",
                City=data.city,
                State=data.state,
                ZipCode=data.zip_code,
                Phone=data.phone or "",
                ContactFirstName=data.contact_first_name,
                ContactLastName=data.contact_last_name,
                ContactEmail=data.contact_email or "",
                ContactPhone=data.contact_phone or ""
            )
            
            if not result:
                raise ServiceError("Failed to create producer")
            
            producer_guid = str(result)
            
            # Set commission rate if provided
            if data.default_commission_rate:
                # This would require a custom stored procedure
                self.logger.info(f"Commission rate setting not implemented: {data.default_commission_rate}%")
            
            # Get the created producer
            producer_response = await self.get_by_guid(producer_guid)
            
            if producer_response.success:
                return ServiceResponse(
                    success=True,
                    data=producer_response.data,
                    metadata={"action": "created"}
                )
            else:
                # Return basic info if full retrieval fails
                producer = Producer(
                    producer_guid=producer_guid,
                    producer_name=data.producer_name,
                    producer_code=data.producer_code,
                    tax_id=data.tax_id,
                    status=ProducerStatus.ACTIVE,
                    created_date=datetime.now()
                )
                
                return ServiceResponse(
                    success=True,
                    data=producer,
                    metadata={"action": "created"},
                    warnings=["Could not retrieve full producer details"]
                )
                
        except Exception as e:
            return self._handle_error(e, "create_producer")
    
    async def add_contact(self, data: ProducerContactCreate) -> ServiceResponse:
        """
        Add a contact to a producer
        
        Args:
            data: Contact creation data
            
        Returns:
            ServiceResponse with contact GUID
        """
        self._log_operation("add_contact", {
            "producer_guid": data.producer_guid,
            "contact_name": f"{data.first_name} {data.last_name}"
        })
        
        try:
            # Add producer contact
            result = self.soap_client.service.AddProducerContact(
                ProducerGUID=data.producer_guid,
                LocationGUID=data.location_guid or data.producer_guid,
                FirstName=data.first_name,
                LastName=data.last_name,
                Title=data.title or "",
                Email=data.email or "",
                Phone=data.phone or "",
                Mobile=data.mobile or "",
                IsPrimary=data.is_primary
            )
            
            if not result:
                raise ServiceError("Failed to add producer contact")
            
            contact_guid = str(result)
            
            # Add licenses if provided
            if data.license_number and data.license_states:
                for state in data.license_states:
                    try:
                        self.soap_client.service.AddProducerLicenses(
                            ProducerContactGUID=contact_guid,
                            LicenseNumber=data.license_number,
                            State=state
                        )
                    except Exception as e:
                        self.logger.warning(f"Failed to add license for state {state}: {str(e)}")
            
            return ServiceResponse(
                success=True,
                data={"contact_guid": contact_guid},
                metadata={
                    "producer_guid": data.producer_guid,
                    "contact_name": f"{data.first_name} {data.last_name}"
                }
            )
            
        except Exception as e:
            return self._handle_error(e, "add_contact")
    
    async def get_producer_underwriter(self, producer_guid: str) -> ServiceResponse:
        """
        Get underwriter assigned to a producer
        
        Args:
            producer_guid: Producer GUID
            
        Returns:
            ServiceResponse with UnderwriterInfo
        """
        self._log_operation("get_producer_underwriter", {"producer_guid": producer_guid})
        
        try:
            # Get producer underwriter
            result = self.soap_client.service.GetProducerUnderwriter(
                ProducerGUID=producer_guid
            )
            
            if result:
                underwriter = UnderwriterInfo(
                    underwriter_guid=str(result.UnderwriterGUID),
                    underwriter_name=result.UnderwriterName,
                    email=getattr(result, 'Email', None),
                    phone=getattr(result, 'Phone', None),
                    is_active=getattr(result, 'IsActive', True)
                )
                
                return ServiceResponse(
                    success=True,
                    data=underwriter
                )
            else:
                return ServiceResponse(
                    success=True,
                    data=None,
                    metadata={"message": "No underwriter assigned"}
                )
                
        except Exception as e:
            return self._handle_error(e, "get_producer_underwriter")
    
    async def find_underwriter_by_name(self, underwriter_name: str) -> ServiceResponse:
        """
        Find underwriter by name
        
        Args:
            underwriter_name: Underwriter name
            
        Returns:
            ServiceResponse with underwriter GUID
        """
        self._log_operation("find_underwriter_by_name", {"underwriter_name": underwriter_name})
        
        try:
            # Query for underwriter
            from app.microservices.data_access import QueryRequest
            query = QueryRequest(
                query="""
                SELECT TOP 10 
                    UserGUID,
                    FirstName + ' ' + LastName as FullName,
                    Email,
                    IsActive
                FROM Users
                WHERE IsUnderwriter = 1
                  AND (FirstName + ' ' + LastName LIKE @Name OR LastName LIKE @Name)
                  AND IsActive = 1
                ORDER BY 
                    CASE WHEN FirstName + ' ' + LastName = @ExactName THEN 0 ELSE 1 END,
                    LastName, FirstName
                """,
                parameters={
                    "Name": f"%{underwriter_name}%",
                    "ExactName": underwriter_name
                }
            )
            
            result = await self.data_service.execute_query(query)
            
            if result.success and result.data.row_count > 0:
                # Return first match
                underwriter = result.data.tables[0]["rows"][0]
                return ServiceResponse(
                    success=True,
                    data={
                        "underwriter_guid": underwriter["UserGUID"],
                        "underwriter_name": underwriter["FullName"]
                    }
                )
            else:
                return ServiceResponse(
                    success=False,
                    error=f"Underwriter not found: {underwriter_name}"
                )
                
        except Exception as e:
            return self._handle_error(e, "find_underwriter_by_name")
    
    async def search_producers(self, criteria: ProducerSearch) -> ServiceResponse:
        """
        Search for producers
        
        Args:
            criteria: Search criteria
            
        Returns:
            ServiceResponse with list of producers
        """
        self._log_operation("search_producers", criteria.dict(exclude_none=True))
        
        try:
            # Use SOAP search if simple name search
            if criteria.producer_name and not any([
                criteria.contact_name, criteria.email, criteria.state, criteria.has_underwriter
            ]):
                result = self.soap_client.service.ProducerSearch(
                    ProducerName=criteria.producer_name
                )
                
                producers = []
                if result and hasattr(result, 'Producers'):
                    for ims_producer in result.Producers:
                        # Apply status filter if specified
                        if criteria.status and ims_producer.Status != criteria.status.value:
                            continue
                        
                        producers.append(self._map_search_result(ims_producer))
                        
                        if len(producers) >= criteria.limit:
                            break
                
                return ServiceResponse(
                    success=True,
                    data=producers,
                    metadata={"count": len(producers)}
                )
            
            # For complex searches, use direct query
            # This would require custom stored procedures
            return ServiceResponse(
                success=False,
                error="Complex producer search not yet implemented"
            )
            
        except Exception as e:
            return self._handle_error(e, "search_producers")
    
    async def get_default_producer_guid(self, source: str) -> str:
        """
        Get default producer GUID for a source system
        
        Args:
            source: Source system name
            
        Returns:
            Producer GUID
        """
        # Map source to default producer
        defaults = {
            "triton": os.getenv("TRITON_DEFAULT_PRODUCER_GUID", ""),
            "xuber": os.getenv("XUBER_DEFAULT_PRODUCER_GUID", ""),
            "default": os.getenv("DEFAULT_PRODUCER_GUID", "00000000-0000-0000-0000-000000000000")
        }
        
        return defaults.get(source.lower(), defaults["default"])
    
    async def _get_full_producer_info(self, producer_guid: str) -> Optional[Producer]:
        """Get full producer information including locations and contacts"""
        try:
            # Get producer info
            producer_info = self.soap_client.service.GetProducerInfo(
                ProducerGUID=producer_guid
            )
            
            if not producer_info:
                return None
            
            # Get producer contact info
            contact_info = self.soap_client.service.GetProducerContactInfo(
                ProducerGUID=producer_guid
            )
            
            # Map to model
            producer = Producer(
                producer_guid=producer_guid,
                producer_id=getattr(producer_info, 'ProducerID', None),
                producer_name=producer_info.ProducerName,
                producer_code=getattr(producer_info, 'ProducerCode', None),
                tax_id=getattr(producer_info, 'TaxID', None),
                status=ProducerStatus(getattr(producer_info, 'Status', 'Active')),
                created_date=getattr(producer_info, 'CreatedDate', datetime.now())
            )
            
            # Add primary contact info if available
            if contact_info and hasattr(contact_info, 'Contacts'):
                for contact in contact_info.Contacts:
                    if contact.IsPrimary:
                        producer.primary_contact_name = f"{contact.FirstName} {contact.LastName}"
                        producer.primary_contact_email = getattr(contact, 'Email', None)
                        producer.primary_contact_phone = getattr(contact, 'Phone', None)
                        break
            
            return producer
            
        except Exception as e:
            self.logger.error(f"Error getting full producer info: {str(e)}")
            return None
    
    def _map_search_result(self, ims_producer: Any) -> Producer:
        """Map IMS search result to producer model"""
        return Producer(
            producer_guid=str(ims_producer.ProducerGUID),
            producer_name=ims_producer.ProducerName,
            producer_code=getattr(ims_producer, 'ProducerCode', None),
            status=ProducerStatus(getattr(ims_producer, 'Status', 'Active')),
            primary_contact_name=getattr(ims_producer, 'PrimaryContactName', None),
            primary_contact_email=getattr(ims_producer, 'PrimaryContactEmail', None),
            primary_contact_phone=getattr(ims_producer, 'PrimaryContactPhone', None),
            created_date=getattr(ims_producer, 'CreatedDate', datetime.now())
        )

# Import os for environment variables
import os