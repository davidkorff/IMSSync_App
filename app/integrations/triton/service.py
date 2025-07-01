"""
Triton integration service
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.services.ims_workflow_service import IMSWorkflowService
from app.models.transaction_models import Transaction, TransactionStatus, IMSProcessingStatus
from app.integrations.triton.transformer import TritonTransformer

logger = logging.getLogger(__name__)

class TritonIntegrationService:
    """
    Service for integrating with Triton
    """
    
    def __init__(self, environment=None, config: Optional[Dict[str, Any]] = None):
        """Initialize with environment and configuration"""
        self.environment = environment
        self.config = config or {}
        self.ims_workflow_service = IMSWorkflowService(environment)
        self.transformer = TritonTransformer(config)
    
    def process_transaction(self, transaction: Transaction) -> Transaction:
        """
        Process a Triton transaction
        """
        logger.info(f"Processing Triton transaction: {transaction.transaction_id}")
        transaction.ims_processing.add_log("Starting Triton-specific processing")
        
        try:
            # Transform data
            if not transaction.parsed_data:
                raise ValueError("No parsed data available in transaction")
            
            # Use Triton-specific transformer
            transformed_data = self.transformer.transform_to_ims_format(transaction.parsed_data)
            transaction.processed_data = transformed_data
            transaction.ims_processing.add_log("Data transformed to IMS format")
            
            # Debug log to see the transformed data structure
            if "insured_data" in transformed_data:
                business_type_id = transformed_data["insured_data"].get("business_type_id")
                logger.info(f"Transformed data contains business_type_id: {business_type_id}")
                transaction.ims_processing.add_log(f"Transformed business_type_id: {business_type_id}")
            
            # Get Excel rater information
            rater_info = self.transformer.get_excel_rater_info(transaction.parsed_data)
            transaction.ims_processing.excel_rater_id = rater_info.get("rater_id")
            transaction.ims_processing.factor_set_guid = rater_info.get("factor_set_guid")
            transaction.ims_processing.add_log(
                f"Using Excel rater: ID={rater_info.get('rater_id')}, "
                f"LOB={rater_info.get('lob')}, State={rater_info.get('state')}"
            )
            
            # Process through IMS workflow
            transaction = self.ims_workflow_service.process_transaction(transaction)
            
            # Any Triton-specific post-processing can be added here
            
            return transaction
            
        except Exception as e:
            logger.error(f"Error in Triton processing: {str(e)}")
            transaction.update_status(
                TransactionStatus.FAILED, 
                f"Triton processing error: {str(e)}"
            )
            transaction.ims_processing.status = IMSProcessingStatus.ERROR
            return transaction