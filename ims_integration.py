"""
IMS Integration - Main module for integrating external policy data with IMS
"""
import os
import csv
import json
import logging
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Any, Optional

import config
from ims_soap_client import IMSSoapClient
from ims_lookup_service import IMSLookupService
from ims_data_model import PolicyData
from data_gatherers import get_gatherer


class IMSIntegration:
    def __init__(self, env="iscmga_test"):
        """Initialize the IMS integration with the specified environment"""
        self.env = env
        self.environment = config.ENVIRONMENTS.get(env, {})
        self.config_file = self.environment.get("config_file")
        self.username = self.environment.get("username")
        self.password = self.environment.get("password")
        self.token = None
        self.user_guid = None
        self.urls = self._load_config()
        self.logger = self._setup_logger()
        self.soap_client = IMSSoapClient(self)
        self.lookup_service = IMSLookupService(self)
        
    def _load_config(self):
        """Load the configuration file and extract needed URLs"""
        try:
            tree = ET.parse(self.config_file)
            root = tree.getroot()
            urls = {}
            for setting in root.findall(".//appSettings/add"):
                key = setting.get('key')
                value = setting.get('value')
                if key.startswith('WebServices') and key.endswith('Url'):
                    service_name = key.replace('WebServices', '').replace('Url', '')
                    urls[service_name.lower()] = value
            return urls
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}
            
    def _setup_logger(self):
        """Set up logging for the integration"""
        logger = logging.getLogger('ims_integration')
        logger.setLevel(logging.INFO)
        
        # Create handlers
        file_handler = logging.FileHandler('ims_integration.log')
        console_handler = logging.StreamHandler()
        
        # Create formatters and add to handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to the logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def login(self):
        """Login to IMS and get an authentication token"""
        return self.soap_client.login()
    
    def prepare_submission_data(self, policy: PolicyData):
        """
        Prepare the submission data structure for IMS
        
        This transforms the PolicyData object from the common data model
        to the format expected by the IMS AddQuoteWithSubmission API call
        """
        # Lookup all GUIDs needed for this policy
        guids = self._lookup_guids_for_policy(policy)
        
        # Build the submission data structure
        submission_data = {
            'submission': {
                'Insured': guids['insured'],
                'ProducerContact': guids['producer'],
                'Underwriter': guids['underwriter'],
                'SubmissionDate': policy.bound_date.strftime('%Y-%m-%d'),
                'ProducerLocation': guids['producer_location'],
                'TACSR': '00000000-0000-0000-0000-000000000000',  # Placeholder
                'InHouseProducer': '00000000-0000-0000-0000-000000000000'  # Placeholder
            },
            'quote': {
                # Submission GUID will be set by IMS
                'QuotingLocation': guids['producer_location'],
                'IssuingLocation': guids['producer_location'],
                'CompanyLocation': guids['company_location'],
                'Line': guids['line'],
                'StateID': policy.insured.state or '',
                'ProducerContact': guids['producer'],
                'QuoteStatusID': 1,  # Placeholder, need to determine correct status
                'Effective': policy.effective_date.strftime('%Y-%m-%d'),
                'Expiration': policy.expiration_date.strftime('%Y-%m-%d'),
                'BillingTypeID': 1,  # Placeholder, need to determine correct billing type
                'QuoteDetail': {
                    'CompanyCommission': policy.commission.company_percentage if policy.commission and policy.commission.company_percentage else 0,
                    'ProducerCommission': policy.commission.producer_percentage if policy.commission and policy.commission.producer_percentage else 0,
                    'TermsOfPayment': policy.commission.terms_of_payment if policy.commission and policy.commission.terms_of_payment else 1,
                    'ProgramCode': policy.program,
                    'CompanyContactGuid': '00000000-0000-0000-0000-000000000000',  # Placeholder
                    'RaterID': 1,  # Placeholder
                    'FactorSetGuid': '00000000-0000-0000-0000-000000000000',  # Placeholder
                    'ProgramID': 1,  # Placeholder
                    'LineGUID': guids['line'],
                    'CompanyLocationGUID': guids['company_location']
                },
                'RiskInformation': {
                    'PolicyName': policy.policy_number,
                    'CorporationName': policy.insured.corporation_name or policy.insured.name,
                    'DBA': policy.insured.dba or '',
                    'Address1': policy.insured.address1 or '',
                    'Address2': policy.insured.address2 or '',
                    'City': policy.insured.city or '',
                    'State': policy.insured.state or '',
                    'ZipCode': policy.insured.zip_code or '',
                    'ZipPlus': policy.insured.zip_plus or '',
                    'Phone': policy.insured.phone or '',
                    'Fax': policy.insured.fax or '',
                    'Mobile': policy.insured.mobile or ''
                }
            }
        }
        
        return submission_data
    
    def add_quote_with_submission(self, submission_data):
        """
        Call the AddQuoteWithSubmission API to create a submission and quote in IMS
        """
        return self.soap_client.add_quote_with_submission(submission_data)
    
    def _lookup_guids_for_policy(self, policy: PolicyData) -> Dict[str, str]:
        """
        Look up all GUIDs needed for a policy
        
        Args:
            policy: Policy data object
            
        Returns:
            Dict[str, str]: Dictionary of GUIDs keyed by entity type
        """
        guids = {
            'insured': self.lookup_service.lookup_insured(policy.insured.name),
            'producer': self.lookup_service.lookup_producer(policy.producer.name),
            'underwriter': self.lookup_service.lookup_underwriter(policy.underwriter.name),
            'line': self.lookup_service.lookup_line(policy.line_of_business),
            'program': self.lookup_service.lookup_program(policy.program),
            'producer_location': self.lookup_service.lookup_location(
                policy.producer.location or policy.producer.name, 'producer'),
            'company_location': self.lookup_service.lookup_location(
                policy.company_location or policy.underwriter.location or '', 'company')
        }
        
        return guids
    
    def process_policies_from_source(self, source_type: str, source_config: Dict[str, Any], 
                                    filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process policies from a specific source
        
        Args:
            source_type: Type of source system (csv, tritan, etc.)
            source_config: Configuration for the source
            filters: Optional filters to apply when retrieving policies
            
        Returns:
            Dict[str, Any]: Results of the integration
        """
        self.logger.info(f"Starting policy processing from {source_type} source")
        
        # Login to IMS
        if not self.login():
            self.logger.error("Failed to login to IMS. Aborting.")
            return {'success': False, 'error': 'Authentication failed'}
        
        # Get the appropriate data gatherer
        gatherer = get_gatherer(source_type, **source_config)
        
        if not gatherer:
            error_msg = f"No data gatherer available for source type: {source_type}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        
        # Retrieve policies from the source
        try:
            with gatherer:
                policies = gatherer.get_policies(filters)
        except Exception as e:
            error_msg = f"Error retrieving policies from {source_type}: {e}"
            self.logger.error(error_msg)
            return {'success': False, 'error': error_msg}
        
        # Track results
        results = {
            'total': len(policies),
            'succeeded': 0,
            'failed': 0,
            'quotes': []
        }
        
        # Process each policy
        for i, policy in enumerate(policies):
            self.logger.info(f"Processing policy {i+1}/{len(policies)}: {policy.policy_number}")
            
            try:
                # Prepare submission data
                submission_data = self.prepare_submission_data(policy)
                
                # Add quote with submission
                quote_guid = self.add_quote_with_submission(submission_data)
                
                if quote_guid:
                    self.logger.info(f"Successfully created quote with GUID: {quote_guid}")
                    results['succeeded'] += 1
                    results['quotes'].append({
                        'policy_number': policy.policy_number,
                        'quote_guid': quote_guid
                    })
                else:
                    self.logger.error(f"Failed to create quote for policy: {policy.policy_number}")
                    results['failed'] += 1
            except Exception as e:
                self.logger.error(f"Error processing policy {policy.policy_number}: {e}")
                results['failed'] += 1
        
        # Summarize results
        self.logger.info(f"Completed processing {results['total']} policies")
        self.logger.info(f"Succeeded: {results['succeeded']}, Failed: {results['failed']}")
        
        results['success'] = True
        return results
    
    def process_policies_from_csv(self, csv_file: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process policies from a CSV file
        
        Args:
            csv_file: Path to the CSV file
            filters: Optional filters to apply when retrieving policies
            
        Returns:
            Dict[str, Any]: Results of the integration
        """
        return self.process_policies_from_source('csv', {'file_path': csv_file}, filters)
    
    def process_policies_from_tritan(self, config: Dict[str, Any], 
                                    filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process policies from Tritan
        
        Args:
            config: Tritan configuration
            filters: Optional filters to apply when retrieving policies
            
        Returns:
            Dict[str, Any]: Results of the integration
        """
        return self.process_policies_from_source('tritan', config, filters)


# Example usage
if __name__ == "__main__":
    # Initialize the IMS integration
    ims = IMSIntegration()
    
    # Process policies from CSV
    results = ims.process_policies_from_csv("BDX_Samples/Bound Policies report 4.25.25.csv")
    
    # Write results to a JSON file
    with open("ims_integration_results.json", "w") as f:
        json.dump(results, f, indent=2) 