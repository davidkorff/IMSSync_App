"""
IMS Destination Adapter
Handles processing StandardTransaction objects through IMS workflow
"""

import logging
from typing import Dict, Any

from ...core.models import StandardTransaction, TransactionType

logger = logging.getLogger(__name__)


class IMSDestinationAdapter:
    """
    Adapter that processes StandardTransaction objects through IMS workflow
    """
    
    def __init__(self, ims_config: Dict[str, Any]):
        self.ims_config = ims_config
        self.workflow_service = None
    
    async def initialize(self):
        """Initialize the IMS workflow service"""
        try:
            # Import here to avoid circular imports
            from .workflow_service import IMSWorkflowService
            
            # Use environment-based initialization  
            # Use ims_one environment instead of iscmga_test
            self.workflow_service = IMSWorkflowService(environment="ims_one")
            
            logger.info("IMS destination adapter initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize IMS workflow service: {e}")
            raise
    
    async def process_new_business(self, transaction: StandardTransaction) -> Dict[str, Any]:
        """Process new business transaction through IMS"""
        logger.info(f"Processing new business transaction {transaction.source_transaction_id}")
        
        try:
            if not self.workflow_service:
                await self.initialize()
            
            # Convert StandardTransaction to the Transaction format expected by IMS workflow
            ims_transaction = self._convert_to_ims_transaction(transaction)
            
            # Process through IMS workflow (note: this is synchronous, not async)
            result_transaction = self.workflow_service.process_transaction(ims_transaction)
            
            # Check if processing was successful
            if result_transaction.status.value == 'completed':
                return {
                    'status': 'completed',
                    'message': 'New business processed successfully',
                    'ims_policy_number': getattr(result_transaction.ims_processing.policy, 'policy_number', None) if result_transaction.ims_processing.policy else None
                }
            else:
                return {
                    'status': 'failed',
                    'message': result_transaction.error_message or 'IMS processing failed',
                    'errors': [result_transaction.error_message] if result_transaction.error_message else ['Unknown IMS error']
                }
        
        except Exception as e:
            logger.exception(f"Error processing new business transaction {transaction.source_transaction_id}")
            return {
                'success': False,
                'error': str(e),
                'errors': [str(e)]
            }
    
    async def process_renewal(self, transaction: StandardTransaction) -> Dict[str, Any]:
        """Process renewal transaction through IMS"""
        logger.info(f"Processing renewal transaction {transaction.source_transaction_id}")
        
        # For now, treat renewals like new business
        # TODO: Implement proper renewal workflow
        return await self.process_new_business(transaction)
    
    async def process_endorsement(self, transaction: StandardTransaction) -> Dict[str, Any]:
        """Process endorsement transaction through IMS"""
        logger.info(f"Processing endorsement transaction {transaction.source_transaction_id}")
        
        return {
            'success': False,
            'error': 'Endorsement processing not yet implemented',
            'errors': ['Endorsement workflow not implemented']
        }
    
    async def process_cancellation(self, transaction: StandardTransaction) -> Dict[str, Any]:
        """Process cancellation transaction through IMS"""
        logger.info(f"Processing cancellation transaction {transaction.source_transaction_id}")
        
        return {
            'success': False,
            'error': 'Cancellation processing not yet implemented',
            'errors': ['Cancellation workflow not implemented']
        }
    
    def _convert_to_ims_transaction(self, transaction: StandardTransaction):
        """
        Convert StandardTransaction to Transaction model expected by IMS workflow service
        This preserves all the important data mapping for actual IMS integration
        """
        from app.models.transaction_models import Transaction, TransactionType
        
        # Build comprehensive raw_data with all the necessary IMS fields
        raw_data = {
            'policy_number': transaction.policy_number,
            'effective_date': transaction.effective_date.isoformat() if transaction.effective_date else None,
            'expiration_date': transaction.expiration_date.isoformat() if transaction.expiration_date else None,
            'transaction_type': transaction.transaction_type.value
        }
        
        # Add insured information - critical for IMS processing
        if transaction.insured:
            raw_data['insured'] = {
                'name': transaction.insured.name,
                'business_type': transaction.insured.business_type,
                'tax_id': transaction.insured.tax_id
            }
            if transaction.insured.address:
                raw_data['insured']['address'] = {
                    'street_1': transaction.insured.address.street_1,
                    'street_2': transaction.insured.address.street_2,
                    'city': transaction.insured.address.city,
                    'state': transaction.insured.address.state,
                    'zip_code': transaction.insured.address.zip_code
                }
        
        # Add producer information - needed for IMS workflow
        if transaction.producer:
            raw_data['producer'] = {
                'name': transaction.producer.full_name,  # Use full_name property
                'first_name': transaction.producer.first_name,
                'last_name': transaction.producer.last_name,
                'email': transaction.producer.email,
                'phone': transaction.producer.phone,
                'license_number': transaction.producer.license_number
            }
        
        # Add agency information
        if transaction.agency:
            raw_data['agency'] = {
                'id': transaction.agency.id,
                'name': transaction.agency.name,
                'commission_rate': transaction.agency.commission_rate,
                'parent_agency': transaction.agency.parent_agency,
                'always_file_taxes': transaction.agency.always_file_taxes
            }
        
        # Add financial information - critical for premium calculations
        if transaction.financials:
            raw_data['financials'] = {
                'gross_premium': transaction.financials.gross_premium,
                'base_premium': transaction.financials.base_premium,
                'policy_fee': transaction.financials.policy_fee,
                'surplus_lines_tax': transaction.financials.surplus_lines_tax,
                'stamping_fee': transaction.financials.stamping_fee,
                'other_fees': transaction.financials.other_fees,
                'commission_percent': transaction.financials.commission_percent,
                'commission_amount': transaction.financials.commission_amount,
                'net_premium': transaction.financials.net_premium,
                'credit_debit_factor': transaction.financials.credit_debit_factor,
                'invoice_number': transaction.financials.invoice_number,
                'invoice_date': transaction.financials.invoice_date.isoformat() if transaction.financials.invoice_date else None
            }
        
        # Add coverage information - needed for rating
        if transaction.coverages:
            raw_data['coverages'] = []
            for coverage in transaction.coverages:
                raw_data['coverages'].append({
                    'coverage_type': coverage.coverage_type,
                    'limits': coverage.limits,  # Use 'limits' not 'limit'
                    'deductible': coverage.deductible,
                    'premium': coverage.premium
                })
        
        # Create Transaction object with complete data
        return Transaction(
            external_id=transaction.source_transaction_id,
            type=TransactionType.NEW,
            source=transaction.source_system,
            raw_data=raw_data
        )