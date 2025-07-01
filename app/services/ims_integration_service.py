import logging
import uuid
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

from app.models.triton_models import (
    TritonTransaction,
    TritonBindingTransaction,
    TritonMidtermEndorsementTransaction,
    TritonCancellationTransaction
)
from app.models.transaction_models import TransactionType, TransactionStatus, Transaction
from app.services.ims.workflow_orchestrator import IMSWorkflowOrchestrator
from app.integrations.triton.transformer import TritonTransformer

logger = logging.getLogger(__name__)

class IMSIntegrationService:
    """
    Service for handling IMS integration using the new modular architecture.
    
    This service is responsible for:
    1. Receiving and validating transactions from external sources
    2. Transforming data format to our internal format
    3. Initiating the appropriate workflow processes
    4. Providing status updates back to source systems
    """
    
    def __init__(self, environment=None):
        self.workflow_orchestrator = IMSWorkflowOrchestrator(environment)
        self.transformer = TritonTransformer()
        self.environment = environment
        
    async def process_triton_transaction(
        self,
        transaction_data: Dict[Any, Any],
        transaction_type: str
    ) -> Dict[str, Any]:
        """
        Process a transaction received from Triton.
        
        Args:
            transaction_data: The transaction data from Triton
            transaction_type: The type of transaction (binding, midterm_endorsement, cancellation)
            
        Returns:
            A dict containing the transaction ID and status
        """
        # Generate a transaction ID if not provided
        if not transaction_data.get("transaction_id"):
            transaction_data["transaction_id"] = str(uuid.uuid4())
            
        transaction_id = transaction_data["transaction_id"]
        logger.info(f"Processing Triton {transaction_type} transaction {transaction_id}")
        
        # Validate and parse the transaction based on its type
        try:
            if transaction_type == "binding":
                transaction = TritonBindingTransaction(**transaction_data)
            elif transaction_type == "midterm_endorsement":
                transaction = TritonMidtermEndorsementTransaction(**transaction_data)
            elif transaction_type == "cancellation":
                transaction = TritonCancellationTransaction(**transaction_data)
            else:
                raise ValueError(f"Unsupported transaction type: {transaction_type}")
                
            logger.info(f"Validated Triton {transaction_type} transaction {transaction_id}")
        except Exception as e:
            logger.error(f"Error validating Triton transaction {transaction_id}: {str(e)}")
            raise ValueError(f"Invalid transaction data: {str(e)}")
        
        # Transform Triton data to our internal format
        try:
            internal_data = self.transformer.transform_to_internal_format(transaction_data)
            logger.info(f"Transformed Triton transaction {transaction_id} to internal format")
        except Exception as e:
            logger.error(f"Error transforming Triton transaction {transaction_id}: {str(e)}")
            raise ValueError(f"Failed to transform transaction data: {str(e)}")
        
        # Determine internal transaction type
        internal_type_map = {
            "binding": TransactionType.NEW,
            "midterm_endorsement": TransactionType.ENDORSEMENT,
            "cancellation": TransactionType.CANCELLATION
        }
        internal_type = internal_type_map[transaction_type]
        
        # Create internal transaction record
        # This would typically involve database operations, but for this example
        # we'll just create an in-memory object
        internal_transaction = Transaction(
            transaction_id=transaction_id,
            external_id=transaction_data.get("transaction_id"),
            source="triton",
            type=internal_type,
            status=TransactionStatus.RECEIVED,
            data=json.dumps(transaction_data),
            received_at=datetime.now()
        )
        
        # Initiate asynchronous processing via IMS workflow service
        # This would typically be done in a background task
        try:
            # Placeholder for workflow processing
            # In a real implementation, this would dispatch to appropriate workflow steps
            logger.info(f"Initiating IMS workflow for Triton transaction {transaction_id}")
            
            # Example workflow calls (implementation would depend on transaction type)
            if transaction_type == "binding":
                # For binding transactions, create insured, submission, quote, etc.
                # self.ims_workflow.create_insured(internal_data)
                # self.ims_workflow.create_submission(internal_data)
                # self.ims_workflow.create_quote(internal_data)
                # self.ims_workflow.bind_policy(internal_data)
                pass
            elif transaction_type == "midterm_endorsement":
                # For endorsements, process the endorsement
                # self.ims_workflow.process_endorsement(internal_data)
                pass
            elif transaction_type == "cancellation":
                # For cancellations, process the cancellation
                # self.ims_workflow.process_cancellation(internal_data)
                pass
            
            # For now, just log that we would process it
            logger.info(f"Triton transaction {transaction_id} queued for processing")
        except Exception as e:
            logger.error(f"Error initiating workflow for Triton transaction {transaction_id}: {str(e)}")
            # We'll still return success to Triton, as we've received and stored the transaction
            # The actual processing result will be communicated asynchronously
        
        # Return result
        return {
            "transaction_id": transaction_id,
            "status": "received",
            "reference_id": f"RSG-{transaction_id}" 
        }
    
    def process_transaction(self, transaction: Transaction) -> Transaction:
        """
        Process a generic transaction through the IMS workflow using the new modular architecture.
        
        Args:
            transaction: The transaction to process
            
        Returns:
            The updated transaction after processing
        """
        logger.info(f"Processing transaction {transaction.transaction_id} through IMS modular services")
        
        try:
            # Process through the workflow orchestrator
            result = self.workflow_orchestrator.process_transaction(transaction)
            
            # Log the result
            if result.ims_processing.status.value == "issued":
                logger.info(f"Transaction {transaction.transaction_id} successfully completed. "
                          f"Policy: {result.ims_processing.policy.policy_number if result.ims_processing.policy else 'N/A'}")
            elif result.ims_processing.status.value == "error":
                logger.error(f"Transaction {transaction.transaction_id} failed during IMS processing")
            else:
                logger.info(f"Transaction {transaction.transaction_id} partially processed. "
                          f"Status: {result.ims_processing.status.value}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing transaction {transaction.transaction_id}: {str(e)}")
            import traceback
            logger.error(f"Stack trace: {traceback.format_exc()}")
            
            # Update transaction status
            transaction.update_status(
                TransactionStatus.FAILED,
                f"Error during IMS processing: {str(e)}"
            )
            
            # Set IMS processing status to error
            if transaction.ims_processing:
                transaction.ims_processing.status = "error"
                transaction.ims_processing.add_log(f"ERROR: {str(e)}")
            
            raise
    
    async def get_transaction_status(self, transaction_id: str) -> Dict[str, Any]:
        """
        Get the current status of a transaction.
        
        Args:
            transaction_id: The ID of the transaction
            
        Returns:
            A dict containing the transaction status
        """
        # In a real implementation, this would query the database
        # For now, just return a placeholder
        return {
            "transaction_id": transaction_id,
            "status": "processing",
            "message": "Transaction is being processed"
        }