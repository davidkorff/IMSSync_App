"""
Example of Triton Processor refactored to use microservices
This shows how existing code can be updated to use the new microservice architecture
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.microservices import get_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class TritonProcessorRefactored:
    """
    Triton processor using microservice architecture
    """
    
    def __init__(self):
        """Initialize with microservices from registry"""
        # Get services from registry - they're created on demand
        self.insured_service = get_service('insured')
        self.data_access_service = get_service('data_access')
        
        # Future services:
        # self.quote_service = get_service('quote')
        # self.policy_service = get_service('policy')
        # self.invoice_service = get_service('invoice')
        
        logger.info("TritonProcessorRefactored initialized with microservices")
    
    async def process_new_business(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process NEW BUSINESS transaction using microservices
        """
        result = {
            "success": False,
            "ims_response": {},
            "errors": []
        }
        
        try:
            # Step 1: Find or create insured using microservice
            logger.info("Processing insured through microservice")
            
            from app.microservices.insured import InsuredCreate
            insured_data = InsuredCreate(
                name=data.get("insured_name"),
                tax_id=data.get("tax_id"),
                address=data.get("address_1"),
                city=data.get("city"),
                state=data.get("state", data.get("insured_state")),
                zip_code=data.get("zip", data.get("insured_zip")),
                source="triton",
                external_id=data.get("transaction_id")
            )
            
            insured_response = await self.insured_service.find_or_create(insured_data)
            
            if not insured_response.success:
                result["errors"].append(f"Failed to process insured: {insured_response.error}")
                return result
            
            insured = insured_response.data
            result["ims_response"]["insured_guid"] = insured.guid
            logger.info(f"Insured processed: {insured.guid}")
            
            # Step 2: Store Triton-specific data using data access microservice
            logger.info("Storing Triton data through microservice")
            
            from app.microservices.data_access import ProgramData
            program_data = ProgramData(
                program="triton",
                quote_guid="temp-guid",  # Will be updated after quote creation
                external_id=data.get("transaction_id"),
                data=data
            )
            
            store_response = await self.data_access_service.store_program_data(program_data)
            
            if store_response.success:
                logger.info("Triton data stored successfully")
            else:
                logger.warning(f"Failed to store Triton data: {store_response.error}")
            
            # Step 3: Get lookup data example
            from app.microservices.data_access import LookupType
            business_types_response = await self.data_access_service.get_lookup_data(
                LookupType.BUSINESS_TYPES
            )
            
            if business_types_response.success:
                logger.info(f"Retrieved {business_types_response.data.count} business types")
            
            # Future steps would use other microservices:
            # submission = await self.quote_service.create_submission(...)
            # quote = await self.quote_service.create_quote(...)
            # policy = await self.policy_service.bind(...)
            # invoice = await self.invoice_service.get_latest_by_policy(...)
            
            result["success"] = True
            
        except Exception as e:
            logger.error(f"Error in process_new_business: {str(e)}")
            result["errors"].append(str(e))
        
        return result
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of all microservices
        """
        health_status = {}
        
        # Check each service
        services = [
            ('insured', self.insured_service),
            ('data_access', self.data_access_service)
        ]
        
        for name, service in services:
            try:
                health = await service.health_check()
                health_status[name] = {
                    "status": health.status.value,
                    "version": health.version,
                    "uptime": health.uptime_seconds
                }
            except Exception as e:
                health_status[name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return health_status


# Example usage in routes
async def example_route_handler(transaction_data: Dict[str, Any]):
    """
    Example of how a route would use the refactored processor
    """
    processor = TritonProcessorRefactored()
    
    # Check health first
    health = await processor.health_check()
    logger.info(f"Service health: {health}")
    
    # Process transaction
    result = await processor.process_new_business(transaction_data)
    
    return result