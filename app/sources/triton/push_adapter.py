"""
Triton Push Adapter
Handles incoming webhook data from Triton and converts to StandardTransaction format
"""

import logging
from typing import Dict, Any, Optional, List

from ...core.models import (
    StandardTransaction, StandardInsured, StandardProducer, StandardAgency,
    StandardUnderwriter, StandardFinancials, StandardCoverage, StandardBDXFields,
    TransactionType, create_standard_address, create_standard_contact
)

logger = logging.getLogger(__name__)


class TritonPushAdapter:
    """
    Adapter for handling push data from Triton webhooks
    Converts Triton API payload to StandardTransaction format
    """
    
    def __init__(self):
        pass
    
    async def process_webhook_data(self, payload: Dict[str, Any]) -> StandardTransaction:
        """
        Convert Triton webhook payload to StandardTransaction
        
        Args:
            payload: JSON payload from Triton webhook
            
        Returns:
            StandardTransaction object
        """
        logger.info(f"Processing Triton webhook for transaction {payload.get('transaction_id')}")
        
        try:
            # Determine transaction type from payload
            transaction_type = self._determine_transaction_type(payload)
            
            # Extract core policy information
            policy_info = payload.get('policy', {})
            
            # Create insured
            insured = self._create_insured_from_payload(payload.get('insured', {}))
            
            # Create producer
            producer = self._create_producer_from_payload(payload.get('producer', {}))
            
            # Create agency
            agency = self._create_agency_from_payload(payload.get('agency', {}))
            
            # Create underwriter
            underwriter = self._create_underwriter_from_payload(payload.get('underwriter', {}))
            
            # Create financials
            financials = self._create_financials_from_payload(payload.get('financials', {}))
            
            # Create coverages
            coverages = self._create_coverages_from_payload(payload.get('coverages', []))
            
            # Create BDX fields
            bdx_fields = self._create_bdx_fields_from_payload(payload.get('bdx_fields', {}))
            
            # Create transaction
            transaction = StandardTransaction(
                source_system="triton",
                source_transaction_id=str(payload.get('transaction_id')),
                transaction_type=transaction_type,
                policy_number=policy_info.get('policy_number'),
                opportunity_name=policy_info.get('opportunity_name'),
                program_name=policy_info.get('program_name', ''),
                program_code=policy_info.get('program_code', ''),
                effective_date=self._parse_date(policy_info.get('effective_date')),
                expiration_date=self._parse_date(policy_info.get('expiration_date')),
                bound_date=self._parse_date(policy_info.get('bound_date')),
                paid_date=self._parse_date(policy_info.get('paid_date')),
                policy_sent_date=self._parse_date(policy_info.get('policy_sent_date')),
                insured=insured,
                producer=producer,
                agency=agency,
                underwriter=underwriter,
                coverages=coverages,
                financials=financials,
                bdx_fields=bdx_fields,
                territory=policy_info.get('territory'),
                is_tail_policy=policy_info.get('is_tail_policy', False),
                is_renewal=policy_info.get('is_renewal', False),
                previous_policy_number=policy_info.get('previous_policy_number'),
                source_data=payload  # Store original payload for debugging
            )
            
            logger.info(f"Successfully converted Triton webhook to StandardTransaction")
            return transaction
            
        except Exception as e:
            logger.error(f"Failed to convert Triton webhook payload: {e}")
            raise
    
    def _determine_transaction_type(self, payload: Dict[str, Any]) -> TransactionType:
        """Determine transaction type from payload"""
        transaction_type_str = payload.get('transaction_type', '').lower()
        
        if transaction_type_str == 'new_business':
            return TransactionType.NEW_BUSINESS
        elif transaction_type_str == 'renewal':
            return TransactionType.RENEWAL
        elif transaction_type_str == 'endorsement':
            return TransactionType.ENDORSEMENT
        elif transaction_type_str == 'cancellation':
            return TransactionType.CANCELLATION
        else:
            # Try to infer from other fields
            if payload.get('policy', {}).get('is_renewal'):
                return TransactionType.RENEWAL
            else:
                return TransactionType.NEW_BUSINESS
    
    def _create_insured_from_payload(self, insured_data: Dict[str, Any]) -> StandardInsured:
        """Create StandardInsured from payload data"""
        address_data = insured_data.get('address', {})
        
        return StandardInsured(
            name=insured_data.get('name', ''),
            address=create_standard_address(
                street_1=address_data.get('street_1', ''),
                street_2=address_data.get('street_2'),
                city=address_data.get('city', ''),
                state=address_data.get('state', ''),
                zip=address_data.get('zip', '')
            ),
            business_type=insured_data.get('business_type'),
            tax_id=insured_data.get('tax_id'),
            dba=insured_data.get('dba'),
            additional_named_insureds=insured_data.get('additional_named_insureds'),
            scheduled_locations=insured_data.get('scheduled_locations')
        )
    
    def _create_producer_from_payload(self, producer_data: Dict[str, Any]) -> StandardProducer:
        """Create StandardProducer from payload data"""
        return StandardProducer(
            id=str(producer_data.get('id', '')),
            first_name=producer_data.get('first_name', ''),
            last_name=producer_data.get('last_name', ''),
            email=producer_data.get('email', ''),
            phone=producer_data.get('phone'),
            license_number=producer_data.get('license_number')
        )
    
    def _create_agency_from_payload(self, agency_data: Dict[str, Any]) -> StandardAgency:
        """Create StandardAgency from payload data"""
        address_data = agency_data.get('address', {})
        contact_data = agency_data.get('contact', {})
        
        return StandardAgency(
            id=str(agency_data.get('id', '')),
            name=agency_data.get('name', ''),
            address=create_standard_address(
                street_1=address_data.get('street_1', ''),
                street_2=address_data.get('street_2'),
                city=address_data.get('city', ''),
                state=address_data.get('state', ''),
                zip=address_data.get('zip', '')
            ),
            contact=create_standard_contact(
                name=contact_data.get('name', agency_data.get('name', '')),
                email=contact_data.get('email'),
                phone=contact_data.get('phone')
            ),
            parent_agency=agency_data.get('parent_agency'),
            commission_rate=float(agency_data.get('commission_rate', 0)),
            always_file_taxes=agency_data.get('always_file_taxes', False)
        )
    
    def _create_underwriter_from_payload(self, underwriter_data: Dict[str, Any]) -> StandardUnderwriter:
        """Create StandardUnderwriter from payload data"""
        if not underwriter_data.get('id'):
            return None
        
        return StandardUnderwriter(
            id=str(underwriter_data.get('id')),
            name=underwriter_data.get('name', ''),
            email=underwriter_data.get('email'),
            phone=underwriter_data.get('phone')
        )
    
    def _create_financials_from_payload(self, financials_data: Dict[str, Any]) -> StandardFinancials:
        """Create StandardFinancials from payload data"""
        financials = StandardFinancials(
            gross_premium=float(financials_data.get('gross_premium', 0)),
            base_premium=float(financials_data.get('base_premium', 0)),
            policy_fee=float(financials_data.get('policy_fee', 0)),
            surplus_lines_tax=float(financials_data.get('surplus_lines_tax', 0)),
            stamping_fee=float(financials_data.get('stamping_fee', 0)),
            other_fees=float(financials_data.get('other_fees', 0)),
            commission_percent=float(financials_data.get('commission_percent', 0)),
            credit_debit_factor=float(financials_data.get('credit_debit_factor', 1.0)),
            invoice_number=financials_data.get('invoice_number'),
            invoice_date=self._parse_date(financials_data.get('invoice_date'))
        )
        
        # Calculate derived fields
        financials.calculate_totals()
        
        return financials
    
    def _create_coverages_from_payload(self, coverages_data: List[Dict[str, Any]]) -> List[StandardCoverage]:
        """Create StandardCoverage list from payload data"""
        coverages = []
        
        for coverage_data in coverages_data:
            coverage = StandardCoverage(
                coverage_type=coverage_data.get('coverage_type', 'General'),
                limits=coverage_data.get('limits'),
                deductible=coverage_data.get('deductible'),
                premium=float(coverage_data.get('premium', 0)) if coverage_data.get('premium') else None,
                rating_unit=coverage_data.get('rating_unit'),
                rating_count=float(coverage_data.get('rating_count', 0)) if coverage_data.get('rating_count') else None,
                territory=coverage_data.get('territory'),
                retroactive_date=self._parse_date(coverage_data.get('retroactive_date'))
            )
            coverages.append(coverage)
        
        return coverages
    
    def _create_bdx_fields_from_payload(self, bdx_data: Dict[str, Any]) -> Optional[StandardBDXFields]:
        """Create StandardBDXFields from payload data"""
        if not any(bdx_data.values()):
            return None
        
        return StandardBDXFields(
            umr=bdx_data.get('umr'),
            agreement_no=bdx_data.get('agreement_no'),
            section_no=bdx_data.get('section_no'),
            coverholder_name=bdx_data.get('coverholder_name'),
            slip_commission_percent=float(bdx_data.get('slip_commission_percent', 0)) if bdx_data.get('slip_commission_percent') else None
        )
    
    def _parse_date(self, date_str: str):
        """Parse date string to date object"""
        if not date_str:
            return None
        
        try:
            from datetime import datetime
            return datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
        except:
            try:
                return datetime.strptime(date_str, '%Y-%m-%d').date()
            except:
                logger.warning(f"Could not parse date: {date_str}")
                return None