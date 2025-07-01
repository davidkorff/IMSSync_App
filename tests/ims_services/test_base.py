"""
Base test class for IMS service tests

This provides common functionality for all IMS service tests including:
- Authentication setup
- Test data generation
- Common assertions
"""

import os
import sys
import unittest
import logging
from datetime import datetime, date
from typing import Dict, Any, Optional
import json
import random
import string

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.services.ims import (
    IMSAuthenticationManager,
    IMSInsuredService,
    IMSProducerService,
    IMSQuoteService,
    IMSDocumentService,
    IMSDataAccessService
)
from app.services.ims.workflow_orchestrator import IMSWorkflowOrchestrator
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IMSServiceTestBase(unittest.TestCase):
    """Base class for IMS service tests"""
    
    @classmethod
    def setUpClass(cls):
        """Set up authentication once for all tests"""
        cls.environment = os.getenv("IMS_TEST_ENV", "ims_one")
        logger.info(f"Setting up IMS tests for environment: {cls.environment}")
        
        # Initialize authentication manager
        cls.auth_manager = IMSAuthenticationManager()
        
        # Get initial token to verify connectivity
        try:
            token = cls.auth_manager.get_token(cls.environment)
            logger.info(f"Successfully authenticated, token: {token[:20]}...")
        except Exception as e:
            logger.error(f"Failed to authenticate: {str(e)}")
            raise
        
        # Initialize services
        cls.insured_service = IMSInsuredService(cls.environment)
        cls.producer_service = IMSProducerService(cls.environment)
        cls.quote_service = IMSQuoteService(cls.environment)
        cls.document_service = IMSDocumentService(cls.environment)
        cls.data_access_service = IMSDataAccessService(cls.environment)
        cls.workflow_orchestrator = IMSWorkflowOrchestrator(cls.environment)
        
        # Test data storage
        cls.created_entities = {
            "insureds": [],
            "submissions": [],
            "quotes": [],
            "policies": []
        }
    
    def setUp(self):
        """Set up for each test"""
        self.test_id = self.generate_test_id()
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting test: {self._testMethodName}")
        logger.info(f"Test ID: {self.test_id}")
    
    def tearDown(self):
        """Clean up after each test"""
        logger.info(f"Completed test: {self._testMethodName}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        logger.info("\nTest Summary:")
        logger.info(f"  Created {len(cls.created_entities['insureds'])} insureds")
        logger.info(f"  Created {len(cls.created_entities['submissions'])} submissions")
        logger.info(f"  Created {len(cls.created_entities['quotes'])} quotes")
        logger.info(f"  Created {len(cls.created_entities['policies'])} policies")
    
    # Helper methods for test data generation
    
    def generate_test_id(self) -> str:
        """Generate a unique test ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"TEST-{timestamp}-{random_suffix}"
    
    def generate_insured_data(self, name_suffix: Optional[str] = None) -> Dict[str, Any]:
        """Generate test insured data"""
        suffix = name_suffix or self.test_id
        return {
            "name": f"Test Company {suffix}",
            "tax_id": self.generate_tax_id(),
            "business_type": "LLC",
            "address": f"{random.randint(100, 9999)} Test Street",
            "city": "Dallas",
            "state": "TX",
            "zip_code": "75001"
        }
    
    def generate_tax_id(self) -> str:
        """Generate a test tax ID"""
        # Generate EIN format: XX-XXXXXXX
        area = random.randint(10, 99)
        number = random.randint(1000000, 9999999)
        return f"{area}-{number}"
    
    def generate_producer_name(self) -> str:
        """Generate a test producer name"""
        prefixes = ["Test", "Sample", "Demo"]
        suffixes = ["Agency", "Insurance", "Brokers", "Associates"]
        return f"{random.choice(prefixes)} Producer {random.choice(suffixes)}"
    
    def generate_submission_data(self, insured_guid: str, producer_guid: str) -> Dict[str, Any]:
        """Generate test submission data"""
        return {
            "insured_guid": insured_guid,
            "producer_contact_guid": producer_guid,
            "producer_location_guid": producer_guid,
            "submission_date": date.today(),
            "underwriter_guid": "00000000-0000-0000-0000-000000000000"
        }
    
    def generate_quote_data(self, submission_guid: str) -> Dict[str, Any]:
        """Generate test quote data"""
        return {
            "submission_guid": submission_guid,
            "effective_date": date.today(),
            "expiration_date": date.today().replace(year=date.today().year + 1),
            "state": "TX",
            "line_guid": "00000000-0000-0000-0000-000000000000",
            "quoting_location_guid": "00000000-0000-0000-0000-000000000000",
            "issuing_location_guid": "00000000-0000-0000-0000-000000000000",
            "company_location_guid": "00000000-0000-0000-0000-000000000000",
            "producer_contact_guid": "00000000-0000-0000-0000-000000000000"
        }
    
    def generate_triton_payload(self) -> Dict[str, Any]:
        """Generate a test Triton payload"""
        return {
            "transaction_id": self.generate_test_id(),
            "transaction_date": datetime.now().isoformat(),
            "transaction_type": "NEW_BUSINESS",
            "source_system": "triton",
            "insured_name": f"Test Insured {self.test_id}",
            "insured_state": "TX",
            "insured_zip": "75001",
            "business_type": "LLC",
            "producer_name": self.generate_producer_name(),
            "underwriter_name": "Test Underwriter",
            "effective_date": date.today().isoformat(),
            "expiration_date": date.today().replace(year=date.today().year + 1).isoformat(),
            "bound_date": date.today().isoformat(),
            "gross_premium": "10000.00",
            "policy_fee": "250.00",
            "limit_amount": "1000000",
            "deductible_amount": "5000"
        }
    
    # Common assertions
    
    def assertIsGuid(self, value: str, msg: Optional[str] = None):
        """Assert that a value is a valid GUID"""
        if msg is None:
            msg = f"'{value}' is not a valid GUID"
        
        # Check format: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
        guid_pattern = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
        import re
        self.assertIsNotNone(value, "GUID is None")
        self.assertRegex(value, guid_pattern, msg)
        
        # Check it's not all zeros
        self.assertNotEqual(value, "00000000-0000-0000-0000-000000000000", 
                           "GUID is all zeros")
    
    def assertServiceResponse(self, response: Any, expected_type: type = None):
        """Assert that a service response is valid"""
        self.assertIsNotNone(response, "Service response is None")
        if expected_type:
            self.assertIsInstance(response, expected_type, 
                                f"Response is not of type {expected_type.__name__}")
    
    # Utility methods
    
    def log_test_data(self, data: Dict[str, Any], title: str = "Test Data"):
        """Log test data in a formatted way"""
        logger.info(f"\n{title}:")
        for key, value in data.items():
            logger.info(f"  {key}: {value}")
    
    def track_entity(self, entity_type: str, entity_id: str):
        """Track created entities for cleanup or reporting"""
        if entity_type in self.created_entities:
            self.created_entities[entity_type].append(entity_id)
            logger.info(f"Tracked {entity_type}: {entity_id}")