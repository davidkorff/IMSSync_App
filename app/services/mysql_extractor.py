"""
MySQL Data Extractor for Triton Database
Extracts policy data from Triton's MySQL database for IMS integration
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import json
from dataclasses import dataclass
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)


class TransactionStatus(Enum):
    """Transaction status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class TritonPolicyData:
    """Data structure for Triton policy information based on BDX requirements"""
    # Required fields first (no defaults)
    # Policy Information
    policy_number: str
    
    # Dates
    effective_date: datetime
    expiration_date: datetime
    bound_date: datetime
    
    # Insured Information
    insured_name: str
    insured_address: str
    insured_city: str
    insured_state: str
    insured_zip: str
    
    # Producer/Agency Information
    producer_name: str
    agency_name: str
    
    # Business Details
    class_of_business: str
    program_name: str
    business_type: str  # New Business, Renewal, etc.
    transaction_type: str  # O = Original, P = Policy Change
    
    # Financial Information
    gross_premium: float
    commission_rate: float
    commission_amount: float
    policy_fee: float
    taxes_and_fees: float
    net_premium: float
    
    # Coverage Information
    limit_amount: float
    deductible_amount: float
    
    # Optional fields with defaults
    umr: Optional[str] = None
    agreement_number: Optional[str] = None
    section_number: Optional[str] = None
    invoice_date: Optional[datetime] = None
    insured_tax_id: Optional[str] = None
    producer_email: Optional[str] = None
    producer_phone: Optional[str] = None
    agency_id: Optional[str] = None
    parent_broker: Optional[str] = None
    underwriter_name: Optional[str] = None
    underwriter_email: Optional[str] = None
    exposure_factor: Optional[float] = None
    retroactive_date: Optional[datetime] = None
    status: str = "bound"
    coverage_type: Optional[str] = None
    territory: Optional[str] = None


class MySQLExtractor:
    """Extract policy data from Triton's MySQL database"""
    
    def __init__(self, host: str, port: int, database: str, 
                 username: str, password: str, ssl_config: Optional[Dict] = None):
        """
        Initialize MySQL connection parameters
        
        Args:
            host: MySQL server host
            port: MySQL server port
            database: Database name
            username: MySQL username
            password: MySQL password
            ssl_config: SSL configuration if required
        """
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.ssl_config = ssl_config
        self.connection = None
        
    def connect(self):
        """Establish MySQL connection"""
        try:
            import mysql.connector
            
            config = {
                'host': self.host,
                'port': self.port,
                'database': self.database,
                'user': self.username,
                'password': self.password,
                'autocommit': False
            }
            
            if self.ssl_config:
                config.update(self.ssl_config)
                
            self.connection = mysql.connector.connect(**config)
            logger.info(f"Connected to MySQL database: {self.database}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MySQL: {str(e)}")
            raise
            
    def disconnect(self):
        """Close MySQL connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Disconnected from MySQL database")
            
    def get_pending_transactions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Fetch pending IMS transactions from ims_transaction_logs table
        
        Args:
            limit: Maximum number of transactions to fetch
            
        Returns:
            List of pending transactions
        """
        query = """
        SELECT 
            itl.id,
            itl.transaction_type,
            itl.resource_type,
            itl.resource_id,
            itl.status,
            itl.attempt_count,
            itl.created_at,
            itl.error_message
        FROM ims_transaction_logs itl
        WHERE itl.status IN ('pending', 'retry')
        AND itl.attempt_count < 3
        ORDER BY itl.created_at ASC
        LIMIT %s
        """
        
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(query, (limit,))
        transactions = cursor.fetchall()
        cursor.close()
        
        return transactions
        
    def get_opportunity_data(self, opportunity_id: int) -> Optional[TritonPolicyData]:
        """
        Extract full policy data for an opportunity (binding transaction)
        
        Args:
            opportunity_id: The opportunity ID from Triton
            
        Returns:
            TritonPolicyData object with all required fields
        """
        query = """
        SELECT 
            -- Opportunity/Policy Information
            o.id AS opportunity_id,
            o.policy_number,
            o.effective_date,
            o.expiration_date,
            o.bound_date,
            o.retroactive_date,
            o.gl_retroactive_date,
            o.status,
            o.business_profession,
            
            -- Account/Insured Information
            a.id AS account_id,
            a.name AS insured_name,
            a.street_1 AS insured_address,
            a.street_2 AS insured_address2,
            a.city AS insured_city,
            a.state AS insured_state,
            a.zip AS insured_zip,
            
            -- Mailing Address if different
            addr.street_1 AS mailing_address,
            addr.street_2 AS mailing_address2,
            addr.city AS mailing_city,
            addr.state AS mailing_state,
            addr.zip AS mailing_zip,
            
            -- Producer Information
            p.id AS producer_id,
            p.first_name AS producer_first_name,
            p.last_name AS producer_last_name,
            p.email AS producer_email,
            p.phone AS producer_phone,
            
            -- Agency Information
            ag.id AS agency_id,
            ag.name AS agency_name,
            ag.email AS agency_email,
            ag.parent_agency AS parent_broker,
            ag.terms AS agency_terms,
            
            -- Program Information
            pr.id AS program_id,
            pr.name AS program_name,
            pr.policy_number_prefix AS program_code,
            
            -- Quote Information
            q.id AS quote_id,
            q.annual_premium,
            q.invoice_date,
            q.send_invoice,
            
            -- Coverage/Exposure Information
            e.id AS exposure_id,
            e.factor AS exposure_factor,
            pc.name AS program_class_name,
            t.name AS territory_name,
            
            -- Limits and Deductibles
            l.amounts AS limit_amounts,
            d.amount AS deductible_amount
            
        FROM opportunities o
        INNER JOIN accounts a ON o.account_id = a.id
        LEFT JOIN addresses addr ON a.mailing_address_id = addr.id
        INNER JOIN producers p ON o.producer_id = p.id
        INNER JOIN agencies ag ON p.agency_id = ag.id
        LEFT JOIN programs pr ON o.program_id = pr.id
        LEFT JOIN quotes q ON q.opportunity_id = o.id AND q.status = 'bound'
        LEFT JOIN exposures e ON e.opportunity_id = o.id
        LEFT JOIN program_classes pc ON e.program_class_id = pc.id
        LEFT JOIN territories t ON e.territory_id = t.id
        LEFT JOIN limits l ON e.limit_id = l.id
        LEFT JOIN deductibles d ON e.deductible_id = d.id
        WHERE o.id = %s
        """
        
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(query, (opportunity_id,))
        result = cursor.fetchone()
        cursor.close()
        
        if not result:
            logger.warning(f"No opportunity found with ID: {opportunity_id}")
            return None
            
        # Get additional quote details for premiums and fees
        premium_details = self.get_quote_premiums(opportunity_id)
        fees_details = self.get_quote_fees(opportunity_id)
        broker_info = self.get_broker_information(opportunity_id)
        
        # Get endorsements if any
        endorsements = self.get_opportunity_endorsements(opportunity_id)
        
        # Create TritonPolicyData object
        policy_data = TritonPolicyData(
            # Policy Information
            policy_number=result['policy_number'] or f"TRITON-{opportunity_id}",
            effective_date=result['effective_date'],
            expiration_date=result['expiration_date'],
            bound_date=result['bound_date'] or datetime.now(),
            invoice_date=result['invoice_date'],
            
            # Insured Information
            insured_name=result['insured_name'],
            insured_address=result['insured_address'] or '',
            insured_city=result['insured_city'] or '',
            insured_state=result['insured_state'] or '',
            insured_zip=result['insured_zip'] or '',
            insured_tax_id=broker_info.get('tax_id'),
            
            # Producer/Agency Information
            producer_name=f"{result.get('producer_first_name', '')} {result.get('producer_last_name', '')}".strip(),
            producer_email=result.get('producer_email'),
            producer_phone=result.get('producer_phone'),
            agency_name=result.get('agency_name', ''),
            agency_id=str(result.get('agency_id', '')),
            parent_broker=result.get('parent_broker'),
            
            # Underwriter Information  
            underwriter_name=result.get('underwriter_name'),
            underwriter_email=result.get('underwriter_email'),
            
            # Business Details
            class_of_business=result.get('program_class_name') or 'Allied Healthcare',
            program_name=result.get('program_name', ''),
            business_type='Renewal' if result.get('is_renewal') else 'New Business',
            transaction_type='O',  # Original
            
            # Financial Information
            gross_premium=float(result.get('annual_premium') or 0),
            commission_rate=float(result.get('agency_terms') or 10.0),
            commission_amount=float(result.get('annual_premium') or 0) * (float(result.get('agency_terms') or 10.0) / 100),
            policy_fee=float(fees_details.get('policy_fee', 0)),
            taxes_and_fees=float(fees_details.get('total_taxes_and_fees', 0)),
            net_premium=float(result.get('annual_premium') or 0) - (float(result.get('annual_premium') or 0) * (float(result.get('agency_terms') or 10.0) / 100)),
            
            # Coverage Information
            limit_amount=self._parse_limit_amount(result.get('limit_amounts', '1000000')),
            deductible_amount=self._parse_money_amount(result.get('deductible_amount', '0')),
            exposure_factor=result.get('exposure_factor'),
            retroactive_date=result.get('retroactive_date'),
            
            # Additional BDX Fields
            status='bound',
            coverage_type=result.get('program_class_name'),
            territory=result.get('territory_name')
        )
        
        return policy_data
        
    def get_quote_premiums(self, opportunity_id: int) -> Dict[str, Any]:
        """Get detailed premium information from quotes"""
        # Simplified query with only known columns
        return {}
        
    def get_quote_fees(self, opportunity_id: int) -> Dict[str, Any]:
        """Get fees and taxes for an opportunity"""
        # Return default values for now
        return {
            'policy_fee': 250.0,  # Default policy fee
            'total_taxes_and_fees': 0.0
        }
        
    def get_broker_information(self, opportunity_id: int) -> Dict[str, Any]:
        """Get broker/surplus lines information"""
        query = """
        SELECT 
            bi.name,
            bi.license_no,
            bi.address,
            bi.state,
            bi.zip,
            bi.license_no as tax_id  -- License number might serve as tax ID
        FROM broker_information bi
        WHERE bi.opportunity_id = %s
        ORDER BY bi.id DESC
        LIMIT 1
        """
        
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(query, (opportunity_id,))
        result = cursor.fetchone()
        cursor.close()
        
        return result or {}
        
    def get_opportunity_endorsements(self, opportunity_id: int) -> List[Dict[str, Any]]:
        """Get endorsements for an opportunity"""
        query = """
        SELECT 
            oe.id,
            e.code AS endorsement_code,
            e.name AS endorsement_name,
            oe.input_text,
            oe.retroactive_date
        FROM opportunity_endorsements oe
        INNER JOIN endorsements e ON oe.endorsement_id = e.id
        WHERE oe.opportunity_id = %s
        """
        
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(query, (opportunity_id,))
        endorsements = cursor.fetchall()
        cursor.close()
        
        return endorsements
        
    def _parse_limit_amount(self, limit_string: str) -> float:
        """Parse limit amount from string format like '$1,000,000/$3,000,000'"""
        if not limit_string:
            return 1000000.0
            
        try:
            # Handle format like "$1,000,000/$3,000,000"
            if '/' in limit_string:
                # Get the per occurrence limit (first part)
                limit_string = limit_string.split('/')[0]
            
            # Remove $ and commas, then convert to float
            limit_string = limit_string.replace('$', '').replace(',', '').strip()
            return float(limit_string)
        except:
            logger.warning(f"Could not parse limit amount: {limit_string}, defaulting to 1000000")
            return 1000000.0
            
    def _parse_money_amount(self, amount_string: str) -> float:
        """Parse money amount from string format like '$1,000' or '1000'"""
        if not amount_string:
            return 0.0
            
        try:
            # If it's already a number, return it
            if isinstance(amount_string, (int, float)):
                return float(amount_string)
                
            # Remove $ and commas, then convert to float
            amount_string = str(amount_string).replace('$', '').replace(',', '').strip()
            return float(amount_string) if amount_string else 0.0
        except:
            logger.warning(f"Could not parse money amount: {amount_string}, defaulting to 0")
            return 0.0
        
    def update_transaction_status(self, transaction_id: int, status: str, 
                                  error_message: Optional[str] = None,
                                  ims_response: Optional[Dict] = None):
        """Update the status of a transaction in ims_transaction_logs"""
        query = """
        UPDATE ims_transaction_logs
        SET 
            status = %s,
            error_message = %s,
            response_data = %s,
            attempt_count = attempt_count + 1,
            last_attempt_at = NOW(),
            completed_at = CASE WHEN %s IN ('completed', 'failed') THEN NOW() ELSE NULL END
        WHERE id = %s
        """
        
        cursor = self.connection.cursor()
        cursor.execute(query, (
            status,
            error_message,
            json.dumps(ims_response) if ims_response else None,
            status,
            transaction_id
        ))
        self.connection.commit()
        cursor.close()
        
        logger.info(f"Updated transaction {transaction_id} status to: {status}")
        
    def extract_policies_for_bdx(self, start_date: datetime, end_date: datetime) -> List[TritonPolicyData]:
        """
        Extract all bound policies within a date range for BDX reporting
        
        Args:
            start_date: Start date for extraction
            end_date: End date for extraction
            
        Returns:
            List of TritonPolicyData objects
        """
        query = """
        SELECT DISTINCT o.id
        FROM opportunities o
        WHERE o.status = 'bound'
        AND o.bound_date BETWEEN %s AND %s
        ORDER BY o.bound_date ASC
        """
        
        cursor = self.connection.cursor()
        cursor.execute(query, (start_date, end_date))
        opportunity_ids = [row[0] for row in cursor.fetchall()]
        cursor.close()
        
        policies = []
        for opp_id in opportunity_ids:
            policy_data = self.get_opportunity_data(opp_id)
            if policy_data:
                policies.append(policy_data)
                
        logger.info(f"Extracted {len(policies)} policies for BDX reporting")
        return policies