"""
Core Transaction Processor
Coordinates processing of standard transactions from any source to any destination
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from .models import StandardTransaction, TransactionStatus, TransactionType
from ..services.transaction_log_service import TransactionLogService

logger = logging.getLogger(__name__)


class TransactionProcessor:
    """
    Core processor that handles standardized transactions
    Independent of source or destination
    """
    
    def __init__(self, log_service: Optional[TransactionLogService] = None):
        self.processors = {}
        self.destinations = {}
        self.log_service = log_service
        
    def register_destination(self, name: str, destination_adapter):
        """Register a destination adapter (e.g., IMS, other systems)"""
        self.destinations[name] = destination_adapter
        logger.info(f"Registered destination: {name}")
    
    async def process_transaction(
        self, 
        transaction: StandardTransaction, 
        destination: str = "ims"
    ) -> Dict[str, Any]:
        """
        Process a standardized transaction through the pipeline
        
        Args:
            transaction: StandardTransaction object
            destination: Name of registered destination
            
        Returns:
            Dict with processing results
        """
        result = {
            "transaction_id": transaction.source_transaction_id,
            "source_system": transaction.source_system,
            "transaction_type": transaction.transaction_type.value,
            "status": "failed",
            "message": "",
            "ims_policy_number": None,
            "processing_time": None,
            "errors": []
        }
        
        start_time = datetime.now()
        log_id = None
        
        try:
            logger.info(
                f"Processing {transaction.transaction_type.value} transaction "
                f"{transaction.source_transaction_id} from {transaction.source_system}"
            )
            
            # Create transaction log entry if service is available
            if self.log_service:
                # Determine resource type and ID based on transaction type
                resource_type = "opportunity"  # Default for now
                resource_id = int(transaction.source_transaction_id) if transaction.source_transaction_id.isdigit() else 0
                
                # Check if already processed
                if self.log_service.check_already_processed(
                    resource_type, resource_id, transaction.transaction_type.value
                ):
                    logger.info(f"Transaction {transaction.source_transaction_id} already processed successfully")
                    result["status"] = "completed"
                    result["message"] = "Transaction already processed"
                    return result
                
                # Create log entry
                log_id = self.log_service.create_transaction_log(
                    transaction_type=transaction.transaction_type.value,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    external_transaction_id=transaction.source_transaction_id,
                    request_data=transaction.to_dict() if hasattr(transaction, 'to_dict') else {}
                )
                
                if log_id:
                    result["log_id"] = log_id
            
            # Update transaction status
            transaction.status = TransactionStatus.PROCESSING
            
            # Validate transaction
            validation_errors = transaction.validate()
            if validation_errors:
                result["errors"] = validation_errors
                result["message"] = f"Validation failed: {', '.join(validation_errors)}"
                transaction.status = TransactionStatus.FAILED
                transaction.error_message = result["message"]
                logger.error(f"Transaction validation failed: {validation_errors}")
                return result
            
            # Get destination adapter
            if destination not in self.destinations:
                result["message"] = f"Unknown destination: {destination}"
                result["errors"] = [result["message"]]
                transaction.status = TransactionStatus.FAILED
                transaction.error_message = result["message"]
                logger.error(result["message"])
                return result
            
            destination_adapter = self.destinations[destination]
            
            # Process based on transaction type
            if transaction.transaction_type == TransactionType.NEW_BUSINESS:
                ims_result = await self._process_new_business(transaction, destination_adapter)
            elif transaction.transaction_type == TransactionType.RENEWAL:
                ims_result = await self._process_renewal(transaction, destination_adapter)
            elif transaction.transaction_type == TransactionType.ENDORSEMENT:
                ims_result = await self._process_endorsement(transaction, destination_adapter)
            elif transaction.transaction_type == TransactionType.CANCELLATION:
                ims_result = await self._process_cancellation(transaction, destination_adapter)
            else:
                result["message"] = f"Unsupported transaction type: {transaction.transaction_type}"
                result["errors"] = [result["message"]]
                transaction.status = TransactionStatus.FAILED
                transaction.error_message = result["message"]
                logger.error(result["message"])
                return result
            
            # Update result with IMS response
            if ims_result.get("status") == "completed":
                result["status"] = "completed"
                result["message"] = "Transaction processed successfully"
                result["ims_policy_number"] = ims_result.get("ims_policy_number")
                transaction.status = TransactionStatus.COMPLETED
                transaction.processed_at = datetime.now()
                
                logger.info(
                    f"Successfully processed transaction {transaction.source_transaction_id}, "
                    f"IMS policy: {result['ims_policy_number']}"
                )
                
                # Update transaction log with success
                if self.log_service and log_id:
                    self.log_service.update_transaction_log(
                        log_id=log_id,
                        status="completed",
                        response_data=ims_result,
                        ims_policy_number=result["ims_policy_number"]
                    )
            else:
                result["message"] = ims_result.get("message", "Unknown IMS error")
                result["errors"] = ims_result.get("errors", [])
                transaction.status = TransactionStatus.FAILED
                transaction.error_message = result["message"]
                
                logger.error(
                    f"IMS processing failed for transaction {transaction.source_transaction_id}: "
                    f"{result['message']}"
                )
                
                # Update transaction log with failure
                if self.log_service and log_id:
                    self.log_service.update_transaction_log(
                        log_id=log_id,
                        status="failed",
                        response_data=ims_result,
                        error_message=result["message"]
                    )
        
        except Exception as e:
            result["message"] = f"Processing error: {str(e)}"
            result["errors"] = [str(e)]
            transaction.status = TransactionStatus.FAILED
            transaction.error_message = result["message"]
            
            logger.exception(
                f"Exception processing transaction {transaction.source_transaction_id}"
            )
            
            # Update transaction log with exception
            if self.log_service and log_id:
                self.log_service.update_transaction_log(
                    log_id=log_id,
                    status="failed",
                    error_message=result["message"]
                )
        
        finally:
            end_time = datetime.now()
            result["processing_time"] = (end_time - start_time).total_seconds()
        
        return result
    
    async def _process_new_business(
        self, 
        transaction: StandardTransaction, 
        destination_adapter
    ) -> Dict[str, Any]:
        """Process new business transaction"""
        logger.info(f"Processing new business for policy {transaction.policy_number}")
        
        try:
            # Standard IMS workflow for new business:
            # 1. Find/Add Insured
            # 2. Add Submission  
            # 3. Add Quote
            # 4. Add Premium
            # 5. Bind Policy
            # 6. Issue Policy
            # 7. Generate Documents
            
            return await destination_adapter.process_new_business(transaction)
            
        except Exception as e:
            logger.exception("Error in new business processing")
            return {
                "success": False,
                "error": str(e),
                "errors": [str(e)]
            }
    
    async def _process_renewal(
        self, 
        transaction: StandardTransaction, 
        destination_adapter
    ) -> Dict[str, Any]:
        """Process renewal transaction"""
        logger.info(f"Processing renewal for policy {transaction.policy_number}")
        
        try:
            # Similar to new business but may have different workflow
            return await destination_adapter.process_renewal(transaction)
            
        except Exception as e:
            logger.exception("Error in renewal processing")
            return {
                "success": False,
                "error": str(e),
                "errors": [str(e)]
            }
    
    async def _process_endorsement(
        self, 
        transaction: StandardTransaction, 
        destination_adapter
    ) -> Dict[str, Any]:
        """Process endorsement transaction"""
        logger.info(f"Processing endorsement for policy {transaction.policy_number}")
        
        try:
            return await destination_adapter.process_endorsement(transaction)
            
        except Exception as e:
            logger.exception("Error in endorsement processing")
            return {
                "success": False,
                "error": str(e),
                "errors": [str(e)]
            }
    
    async def _process_cancellation(
        self, 
        transaction: StandardTransaction, 
        destination_adapter
    ) -> Dict[str, Any]:
        """Process cancellation transaction"""
        logger.info(f"Processing cancellation for policy {transaction.policy_number}")
        
        try:
            return await destination_adapter.process_cancellation(transaction)
            
        except Exception as e:
            logger.exception("Error in cancellation processing")
            return {
                "success": False,
                "error": str(e),
                "errors": [str(e)]
            }
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            "destinations_registered": list(self.destinations.keys()),
            "uptime": "TODO: implement uptime tracking"
        }


# Global processor instance
processor = TransactionProcessor()