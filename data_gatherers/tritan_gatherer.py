"""
Tritan Data Gatherer - Data gatherer for Tritan insurance system
"""
import json
import os
from typing import List, Dict, Any, Optional
import requests
from datetime import datetime

from data_gatherers.base_gatherer import BaseDataGatherer
from ims_data_model import (
    PolicyData, 
    InsuredParty, 
    PolicyParty, 
    PolicyLimit,
    PolicyDeductible,
    PolicyCommission
)


class TritanDataGatherer(BaseDataGatherer):
    """Data gatherer for Tritan insurance system"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Tritan data gatherer
        
        Args:
            config: Configuration for the gatherer, must contain:
                - api_url: Tritan API URL
                - api_key: Tritan API key
                - username: Tritan username
                - password: Tritan password
                
                Optional configuration:
                - producer_matcher: ProducerMatcher instance for consistent producer mappings
                - producer_mappings_file: Path to producer mappings file
        """
        super().__init__('tritan', config)
        self.api_url = self.config.get('api_url')
        self.api_key = self.config.get('api_key')
        self.username = self.config.get('username')
        self.password = self.config.get('password')
        self.token = None
        self.session = None
        self.producer_matcher = self.config.get('producer_matcher')
        
        # Load producer mappings if provided
        self.producer_mappings = {}
        mappings_file = self.config.get('producer_mappings_file')
        if mappings_file and os.path.exists(mappings_file):
            self._load_producer_mappings(mappings_file)
        
        # Validate required config
        if not all([self.api_url, self.api_key, self.username, self.password]):
            self.logger.error("Missing required Tritan configuration")
            raise ValueError("Missing required Tritan configuration")
        
    def _load_producer_mappings(self, mappings_file: str):
        """
        Load producer mappings from a file
        
        Args:
            mappings_file: Path to producer mappings file
        """
        try:
            with open(mappings_file, 'r') as f:
                # Check if the file is CSV or JSON
                if mappings_file.endswith('.csv'):
                    import csv
                    reader = csv.reader(f)
                    next(reader)  # Skip header
                    for row in reader:
                        if len(row) >= 2:
                            self.producer_mappings[row[0]] = row[1]
                else:
                    self.producer_mappings = json.load(f)
                
            self.logger.info(f"Loaded {len(self.producer_mappings)} producer mappings from {mappings_file}")
        except Exception as e:
            self.logger.error(f"Error loading producer mappings: {e}")
        
    def connect(self) -> bool:
        """
        Connect to the Tritan API and authenticate
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        self.logger.info(f"Connecting to Tritan API at {self.api_url}")
        
        # Create a session
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'X-API-Key': self.api_key
        })
        
        # Authenticate
        try:
            # TODO: Implement actual Tritan authentication
            # This is a placeholder for the actual authentication process
            auth_response = {'token': 'dummy_token'}
            
            if 'token' in auth_response:
                self.token = auth_response['token']
                self.session.headers.update({'Authorization': f'Bearer {self.token}'})
                self.logger.info("Authenticated with Tritan API")
                return True
            else:
                self.logger.error("Failed to authenticate with Tritan API")
                return False
                
        except Exception as e:
            self.logger.error(f"Error connecting to Tritan API: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the Tritan API"""
        if self.session:
            self.session.close()
            self.session = None
            self.token = None
            self.logger.info("Disconnected from Tritan API")
    
    def get_policies(self, filters: Dict[str, Any] = None) -> List[PolicyData]:
        """
        Get policies from Tritan based on optional filters
        
        Args:
            filters: Optional filters to apply when retrieving policies, such as:
                - start_date: Start date for policy search
                - end_date: End date for policy search
                - policy_number: Specific policy number to retrieve
                - status: Policy status
            
        Returns:
            List[PolicyData]: List of policies in the common data model format
        """
        if not self.session or not self.token:
            self.logger.error("Not connected to Tritan API. Call connect() first.")
            return []
            
        policies = []
        self.logger.info(f"Retrieving policies from Tritan with filters: {filters}")
        
        try:
            # TODO: Implement actual Tritan API calls
            # This is a placeholder for the actual API calls
            
            # Example policy data structure from Tritan API
            tritan_policies = [
                {
                    'policyNumber': 'TRI-12345',
                    'programName': 'Allied Health',
                    'lineOfBusiness': 'Professional Liability',
                    'effectiveDate': '2025-01-01',
                    'expirationDate': '2026-01-01',
                    'boundDate': '2024-12-15',
                    'insured': {
                        'name': 'Example Medical Group',
                        'address': '123 Main St',
                        'city': 'Anytown',
                        'state': 'CA',
                        'zipCode': '90210'
                    },
                    'producer': {
                        'name': 'John Agent',
                        'agency': 'ABC Insurance Agency'
                    },
                    'underwriter': {
                        'name': 'Jane Underwriter',
                        'company': 'XYZ Insurance'
                    },
                    'limits': [
                        {
                            'type': 'Per Occurrence',
                            'amount': '1000000',
                            'aggregate': '3000000'
                        }
                    ],
                    'deductibles': [
                        {
                            'type': 'Per Claim',
                            'amount': '5000'
                        }
                    ],
                    'commission': {
                        'percentage': 15.0
                    },
                    'premium': 5000.0
                }
            ]
            
            # Apply filters if specified
            if filters:
                if 'policy_number' in filters:
                    tritan_policies = [p for p in tritan_policies if p['policyNumber'] == filters['policy_number']]
                
                if 'start_date' in filters:
                    start_date = datetime.strptime(filters['start_date'], '%Y-%m-%d').date()
                    tritan_policies = [p for p in tritan_policies if datetime.strptime(p['effectiveDate'], '%Y-%m-%d').date() >= start_date]
                
                if 'end_date' in filters:
                    end_date = datetime.strptime(filters['end_date'], '%Y-%m-%d').date()
                    tritan_policies = [p for p in tritan_policies if datetime.strptime(p['effectiveDate'], '%Y-%m-%d').date() <= end_date]
                
                if 'limit' in filters and isinstance(filters['limit'], int) and filters['limit'] > 0:
                    tritan_policies = tritan_policies[:filters['limit']]
            
            # Map Tritan policy data to common data model
            for policy_data in tritan_policies:
                try:
                    policy = self._map_policy_data(policy_data)
                    policies.append(policy)
                except Exception as e:
                    self.logger.error(f"Error mapping Tritan policy data: {e}")
                    continue
            
            self.logger.info(f"Retrieved {len(policies)} policies from Tritan")
            return policies
            
        except Exception as e:
            self.logger.error(f"Error retrieving policies from Tritan: {e}")
            return []
    
    def _map_policy_data(self, policy_data: Dict[str, Any]) -> PolicyData:
        """
        Map Tritan policy data to the common data model
        
        Args:
            policy_data: Tritan policy data
            
        Returns:
            PolicyData: Policy data in the common format
        """
        # Parse dates
        effective_date = datetime.strptime(policy_data['effectiveDate'], '%Y-%m-%d').date()
        expiration_date = datetime.strptime(policy_data['expirationDate'], '%Y-%m-%d').date()
        bound_date = datetime.strptime(policy_data['boundDate'], '%Y-%m-%d').date()
        
        # Create insured party
        insured_data = policy_data['insured']
        insured = InsuredParty(
            name=insured_data['name'],
            address1=insured_data.get('address'),
            city=insured_data.get('city'),
            state=insured_data.get('state'),
            zip_code=insured_data.get('zipCode')
        )
        
        # Create producer with mapping if available
        producer_data = policy_data['producer']
        producer_name = producer_data['name']
        
        # Get producer GUID if available
        producer_guid = self._get_producer_guid(producer_name)
        
        producer = PolicyParty(
            name=producer_name,
            location=producer_data.get('agency'),
            contact_info={'guid': producer_guid} if producer_guid else None
        )
        
        # Create underwriter
        underwriter_data = policy_data['underwriter']
        underwriter = PolicyParty(
            name=underwriter_data['name'],
            location=underwriter_data.get('company')
        )
        
        # Create limits
        limits = []
        for limit_data in policy_data.get('limits', []):
            limits.append(PolicyLimit(
                type=limit_data['type'],
                amount=limit_data['amount'],
                aggregate=limit_data.get('aggregate')
            ))
        
        # Create deductibles
        deductibles = []
        for deductible_data in policy_data.get('deductibles', []):
            deductibles.append(PolicyDeductible(
                type=deductible_data['type'],
                amount=deductible_data['amount']
            ))
        
        # Create commission
        commission_data = policy_data.get('commission', {})
        commission = PolicyCommission(
            producer_percentage=commission_data.get('percentage')
        )
        
        # Create the policy data object
        return PolicyData(
            policy_number=policy_data['policyNumber'],
            program=policy_data['programName'],
            line_of_business=policy_data['lineOfBusiness'],
            
            effective_date=effective_date,
            expiration_date=expiration_date,
            bound_date=bound_date,
            
            insured=insured,
            producer=producer,
            underwriter=underwriter,
            
            limits=limits,
            deductibles=deductibles,
            commission=commission,
            
            premium=policy_data['premium'],
            
            additional_info={
                'source_system': 'tritan',
                'raw_data': policy_data
            }
        )
        
    def _get_producer_guid(self, producer_name: str) -> Optional[str]:
        """
        Get the IMS producer GUID for a Tritan producer
        
        Args:
            producer_name: Name of the producer in Tritan
            
        Returns:
            Optional[str]: GUID of the producer in IMS, or None if not found
        """
        # Check if we have a mapping in the producer mappings
        if producer_name in self.producer_mappings:
            return self.producer_mappings[producer_name]
        
        # Check if we have a producer matcher
        if self.producer_matcher:
            guid, score = self.producer_matcher.find_ims_producer(producer_name, 'tritan')
            
            if guid:
                # Cache the mapping for future use
                self.producer_mappings[producer_name] = guid
                return guid
                
        return None 