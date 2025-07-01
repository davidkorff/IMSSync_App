"""
Xuber integration service
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.services.ims_workflow_service import IMSWorkflowService
from app.models.transaction_models import Transaction, TransactionStatus, IMSProcessingStatus
from app.integrations.xuber.transformer import XuberTransformer

logger = logging.getLogger(__name__)

class XuberIntegrationService:
    """
    Service for integrating with Xuber
    """
    
    def __init__(self, environment=None, config: Optional[Dict[str, Any]] = None):
        """Initialize with environment and configuration"""
        self.environment = environment
        self.config = config or {}
        self.ims_workflow_service = IMSWorkflowService(environment)
        self.transformer = XuberTransformer(config)
    
    def process_transaction(self, transaction: Transaction) -> Transaction:
        """
        Process a Xuber transaction
        """
        logger.info(f"Processing Xuber transaction: {transaction.transaction_id}")
        transaction.ims_processing.add_log("Starting Xuber-specific processing")
        
        try:
            # Transform data
            if not transaction.parsed_data:
                raise ValueError("No parsed data available in transaction")
            
            # Use Xuber-specific transformer
            transformed_data = self.transformer.transform_to_ims_format(transaction.parsed_data)
            transaction.processed_data = transformed_data
            transaction.ims_processing.add_log("Data transformed to IMS format")
            
            # Get Excel rater information
            rater_info = self.transformer.get_excel_rater_info(transaction.parsed_data)
            transaction.ims_processing.excel_rater_id = rater_info.get("rater_id")
            transaction.ims_processing.factor_set_guid = rater_info.get("factor_set_guid")
            transaction.ims_processing.add_log(
                f"Using Excel rater: ID={rater_info.get('rater_id')}, "
                f"LOB={rater_info.get('lob')}"
            )
            
            # Process through IMS workflow
            transaction = self.ims_workflow_service.process_transaction(transaction)
            
            # Any Xuber-specific post-processing can be added here
            
            return transaction
            
        except Exception as e:
            logger.error(f"Error in Xuber processing: {str(e)}")
            transaction.update_status(
                TransactionStatus.FAILED, 
                f"Xuber processing error: {str(e)}"
            )
            transaction.ims_processing.status = IMSProcessingStatus.ERROR
            return transaction