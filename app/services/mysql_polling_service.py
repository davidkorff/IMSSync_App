"""
MySQL Polling Service for Triton IMS Integration
Polls Triton's MySQL database for pending transactions and processes them through IMS
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

from .mysql_extractor import MySQLExtractor, TritonPolicyData, TransactionStatus
from .ims_workflow_service import IMSWorkflowService
from .transaction_processor import TransactionProcessor
from ..core.config import settings
from ..models.transaction_models import TransactionCreate, TransactionType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MySQLPollingService:
    """Service to poll MySQL database and process pending IMS transactions"""
    
    def __init__(self):
        """Initialize the polling service"""
        # MySQL configuration from environment or settings
        self.mysql_config = {
            'host': os.getenv('TRITON_MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('TRITON_MYSQL_PORT', '3306')),
            'database': os.getenv('TRITON_MYSQL_DATABASE', 'triton'),
            'username': os.getenv('TRITON_MYSQL_USER', 'triton_user'),
            'password': os.getenv('TRITON_MYSQL_PASSWORD', '')
        }
        
        # Polling configuration
        self.poll_interval = int(os.getenv('POLL_INTERVAL_SECONDS', '60'))
        self.batch_size = int(os.getenv('POLL_BATCH_SIZE', '10'))
        self.is_running = False
        
        # Initialize services
        self.extractor = None
        self.ims_service = IMSWorkflowService()
        self.processor = TransactionProcessor()
        
    async def start(self):
        """Start the polling service"""
        logger.info("Starting MySQL polling service...")
        
        # Initialize MySQL connection
        self.extractor = MySQLExtractor(**self.mysql_config)
        self.extractor.connect()
        
        self.is_running = True
        
        # Start polling loop
        await self._polling_loop()
        
    async def stop(self):
        """Stop the polling service"""
        logger.info("Stopping MySQL polling service...")
        self.is_running = False
        
        if self.extractor:
            self.extractor.disconnect()
            
    async def _polling_loop(self):
        """Main polling loop"""
        while self.is_running:
            try:
                # Poll for pending transactions
                await self._process_pending_transactions()
                
                # Wait before next poll
                await asyncio.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"Error in polling loop: {str(e)}", exc_info=True)
                await asyncio.sleep(self.poll_interval)
                
    async def _process_pending_transactions(self):
        """Process pending transactions from MySQL"""
        try:
            # Get pending transactions
            transactions = self.extractor.get_pending_transactions(limit=self.batch_size)
            
            if not transactions:
                logger.debug("No pending transactions found")
                return
                
            logger.info(f"Found {len(transactions)} pending transactions")
            
            # Process each transaction
            for tx in transactions:
                await self._process_single_transaction(tx)
                
        except Exception as e:
            logger.error(f"Error processing pending transactions: {str(e)}", exc_info=True)
            
    async def _process_single_transaction(self, transaction: Dict):
        """Process a single transaction"""
        tx_id = transaction['id']
        tx_type = transaction['transaction_type']
        resource_id = transaction['resource_id']
        
        logger.info(f"Processing transaction {tx_id}: {tx_type} for resource {resource_id}")
        
        try:
            # Update status to processing
            self.extractor.update_transaction_status(tx_id, TransactionStatus.PROCESSING.value)
            
            # Extract data based on transaction type
            if tx_type == 'binding':
                await self._process_binding(tx_id, resource_id)
            elif tx_type == 'midterm_endorsement':
                await self._process_endorsement(tx_id, resource_id)
            elif tx_type == 'cancellation':
                await self._process_cancellation(tx_id, resource_id)
            else:
                raise ValueError(f"Unknown transaction type: {tx_type}")
                
        except Exception as e:
            logger.error(f"Error processing transaction {tx_id}: {str(e)}", exc_info=True)
            
            # Update status to retry or failed
            attempt_count = transaction.get('attempt_count', 0)
            if attempt_count < 2:
                self.extractor.update_transaction_status(
                    tx_id, 
                    TransactionStatus.RETRY.value,
                    error_message=str(e)
                )
            else:
                self.extractor.update_transaction_status(
                    tx_id,
                    TransactionStatus.FAILED.value,
                    error_message=f"Failed after {attempt_count + 1} attempts: {str(e)}"
                )
                
    async def _process_binding(self, transaction_id: int, opportunity_id: int):
        """Process a binding transaction"""
        # Extract opportunity data
        policy_data = self.extractor.get_opportunity_data(opportunity_id)
        
        if not policy_data:
            raise ValueError(f"No data found for opportunity {opportunity_id}")
            
        # Convert to IMS format
        ims_data = self._convert_to_ims_format(policy_data)
        
        # Create internal transaction record
        transaction = TransactionCreate(
            source="triton_mysql",
            transaction_type=TransactionType.NEW,
            external_id=f"MYSQL-{transaction_id}",
            data=ims_data
        )
        
        # Process through IMS workflow
        result = await self.ims_service.process_transaction(transaction.dict())
        
        # Update transaction status
        if result.get('success'):
            self.extractor.update_transaction_status(
                transaction_id,
                TransactionStatus.COMPLETED.value,
                ims_response=result
            )
            logger.info(f"Successfully processed binding for opportunity {opportunity_id}")
        else:
            raise Exception(result.get('error', 'Unknown error'))
            
    async def _process_endorsement(self, transaction_id: int, endorsement_id: int):
        """Process an endorsement transaction"""
        # TODO: Implement endorsement processing
        logger.warning(f"Endorsement processing not yet implemented for {endorsement_id}")
        
        # For now, mark as failed
        self.extractor.update_transaction_status(
            transaction_id,
            TransactionStatus.FAILED.value,
            error_message="Endorsement processing not implemented"
        )
        
    async def _process_cancellation(self, transaction_id: int, opportunity_id: int):
        """Process a cancellation transaction"""
        # TODO: Implement cancellation processing
        logger.warning(f"Cancellation processing not yet implemented for {opportunity_id}")
        
        # For now, mark as failed
        self.extractor.update_transaction_status(
            transaction_id,
            TransactionStatus.FAILED.value,
            error_message="Cancellation processing not implemented"
        )
        
    def _convert_to_ims_format(self, policy_data: TritonPolicyData) -> Dict:
        """Convert Triton policy data to IMS format"""
        return {
            "policy_number": policy_data.policy_number,
            "effective_date": policy_data.effective_date.isoformat(),
            "expiration_date": policy_data.expiration_date.isoformat(),
            "bound_date": policy_data.bound_date.isoformat(),
            
            "insured": {
                "name": policy_data.insured_name,
                "tax_id": policy_data.insured_tax_id,
                "business_type": "Corporation",  # TODO: Map from Triton
                "contact": {
                    "address_line_1": policy_data.insured_address,
                    "city": policy_data.insured_city,
                    "state": policy_data.insured_state,
                    "postal_code": policy_data.insured_zip
                }
            },
            
            "producer": {
                "name": policy_data.producer_name,
                "email": policy_data.producer_email,
                "phone": policy_data.producer_phone,
                "agency": {
                    "name": policy_data.agency_name,
                    "id": policy_data.agency_id
                }
            },
            
            "underwriter": {
                "name": policy_data.underwriter_name,
                "email": policy_data.underwriter_email
            },
            
            "coverages": [{
                "type": policy_data.class_of_business,
                "limit": policy_data.limit_amount,
                "deductible": policy_data.deductible_amount,
                "retroactive_date": policy_data.retroactive_date.isoformat() if policy_data.retroactive_date else None
            }],
            
            "premiums": {
                "annual_premium": policy_data.gross_premium,
                "policy_fee": policy_data.policy_fee,
                "taxes_and_fees": policy_data.taxes_and_fees,
                "commission_rate": policy_data.commission_rate,
                "commission_amount": policy_data.commission_amount
            },
            
            "program": {
                "name": policy_data.program_name,
                "class": policy_data.class_of_business
            },
            
            "transaction": {
                "type": policy_data.transaction_type,
                "business_type": policy_data.business_type
            }
        }


# Standalone runner for the polling service
async def run_polling_service():
    """Run the polling service standalone"""
    service = MySQLPollingService()
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(run_polling_service())