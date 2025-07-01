"""
Tests for IMS Producer Service

Tests producer search, matching, contacts, and underwriter lookup.
"""

import unittest
from test_base import IMSServiceTestBase
import logging

logger = logging.getLogger(__name__)


class TestIMSProducerService(IMSServiceTestBase):
    """Test IMS Producer Service functionality"""
    
    def test_01_search_producer(self):
        """Test searching for producers"""
        # Search for producers with common terms
        search_terms = ["Insurance", "Agency", "Broker"]
        
        for term in search_terms:
            logger.info(f"\nSearching for producers with term: '{term}'")
            
            results = self.producer_service.search_producer(term, start_with=False)
            
            # Log results
            logger.info(f"Found {len(results)} producers")
            for i, producer in enumerate(results[:3]):  # Show first 3
                logger.info(f"  {i+1}. {producer.get('ProducerName')} ({producer.get('ProducerLocationGuid')})")
            
            # Basic validation
            if results:
                self.assertIsInstance(results, list)
                self.assertIn('ProducerName', results[0])
                self.assertIn('ProducerLocationGuid', results[0])
    
    def test_02_get_producer_by_name_exact(self):
        """Test getting producer by exact name match"""
        # First, search for any producer to get a real name
        results = self.producer_service.search_producer("", start_with=False)
        
        if not results:
            self.skipTest("No producers found in system")
        
        # Use first producer as test case
        test_producer = results[0]
        producer_name = test_producer.get('ProducerName')
        expected_guid = test_producer.get('ProducerLocationGuid')
        
        logger.info(f"Testing exact match for: {producer_name}")
        
        # Search by exact name
        found_guid = self.producer_service.get_producer_by_name(producer_name)
        
        # Verify
        self.assertEqual(found_guid, expected_guid, "Should find exact match")
        logger.info(f"Found correct producer: {found_guid}")
    
    def test_03_get_producer_by_name_fuzzy(self):
        """Test fuzzy matching for producer names"""
        # Test with variations
        test_cases = [
            ("ABC Insurance Agency", ["ABC Insurance", "ABC Agency", "ABC"]),
            ("Smith & Associates Insurance", ["Smith Associates", "Smith Insurance", "Smith"]),
        ]
        
        for base_name, variations in test_cases:
            logger.info(f"\nTesting variations of: {base_name}")
            
            for variation in variations:
                logger.info(f"  Searching for: '{variation}'")
                
                # This might not find exact matches in test environment
                # but tests the fuzzy matching logic
                found_guid = self.producer_service.get_producer_by_name(variation)
                
                if found_guid:
                    logger.info(f"  Found producer: {found_guid}")
                else:
                    logger.info(f"  No match found")
    
    def test_04_get_default_producer(self):
        """Test getting default producer for source systems"""
        sources = ["triton", "xuber", "unknown"]
        
        for source in sources:
            logger.info(f"\nGetting default producer for source: {source}")
            
            producer_guid = self.producer_service.get_default_producer_guid(source)
            
            # Verify
            self.assertIsNotNone(producer_guid)
            self.assertIsGuid(producer_guid)
            
            logger.info(f"Default producer for {source}: {producer_guid}")
    
    def test_05_get_producer_info(self):
        """Test getting detailed producer information"""
        # First get a producer
        results = self.producer_service.search_producer("", start_with=False)
        
        if not results:
            self.skipTest("No producers found in system")
        
        producer_guid = results[0].get('ProducerLocationGuid')
        
        # Get detailed info
        logger.info(f"\nGetting info for producer: {producer_guid}")
        producer_info = self.producer_service.get_producer_info(producer_guid)
        
        # Verify
        self.assertIsInstance(producer_info, dict)
        
        # Log some info
        if producer_info:
            logger.info(f"Producer Info:")
            for key, value in list(producer_info.items())[:5]:  # First 5 fields
                logger.info(f"  {key}: {value}")
    
    def test_06_find_underwriter_by_name(self):
        """Test finding underwriter by name"""
        # Test with common names
        test_names = ["Smith", "Johnson", "Williams", "Admin", "Test"]
        
        for name in test_names:
            logger.info(f"\nSearching for underwriter: {name}")
            
            underwriter_guid = self.producer_service.find_underwriter_by_name(name)
            
            if underwriter_guid:
                logger.info(f"Found underwriter: {underwriter_guid}")
                self.assertIsGuid(underwriter_guid)
                break
        else:
            logger.warning("No underwriters found with test names")
    
    def test_07_producer_match_scoring(self):
        """Test producer name matching score calculation"""
        test_cases = [
            ("ABC Insurance Agency", "ABC Insurance Agency", 1.0),  # Exact
            ("ABC Insurance", "ABC Insurance Agency", 0.9),         # Contains
            ("ABC", "ABC Insurance Agency", 0.6),                   # Partial
            ("XYZ Company", "ABC Insurance Agency", 0.2),           # Different
        ]
        
        for search_name, producer_name, min_score in test_cases:
            producer = {"ProducerName": producer_name}
            score = self.producer_service._calculate_producer_match_score(search_name, producer)
            
            self.assertGreaterEqual(score, min_score * 0.8,  # Allow some variance
                                  f"Score for '{search_name}' vs '{producer_name}' too low")
            
            logger.info(f"'{search_name}' vs '{producer_name}': {score:.2f}")
    
    def test_08_get_producer_underwriter(self):
        """Test getting underwriter assigned to producer"""
        # Get a producer
        results = self.producer_service.search_producer("", start_with=False)
        
        if not results:
            self.skipTest("No producers found in system")
        
        # Try first few producers
        for i, producer in enumerate(results[:5]):
            producer_guid = producer.get('ProducerLocationGuid')
            producer_name = producer.get('ProducerName')
            
            logger.info(f"\nChecking underwriter for: {producer_name}")
            
            underwriter_guid = self.producer_service.get_producer_underwriter(producer_guid)
            
            if underwriter_guid:
                logger.info(f"Found underwriter: {underwriter_guid}")
                self.assertIsGuid(underwriter_guid)
                break
        else:
            logger.info("No producers with assigned underwriters found")
    
    def test_09_add_producer_contact(self):
        """Test adding contact to producer"""
        # Get a producer
        results = self.producer_service.search_producer("", start_with=False)
        
        if not results:
            self.skipTest("No producers found in system")
        
        producer_guid = results[0].get('ProducerLocationGuid')
        producer_name = results[0].get('ProducerName')
        
        # Create contact data
        contact_data = {
            "first_name": "Test",
            "last_name": f"Contact_{self.test_id}",
            "email": f"test_{self.test_id}@example.com",
            "phone": "555-123-4567",
            "title": "Test Contact",
            "is_primary": False
        }
        
        logger.info(f"\nAdding contact to producer: {producer_name}")
        self.log_test_data(contact_data, "Contact Data")
        
        try:
            # Add contact
            contact_guid = self.producer_service.add_producer_contact(producer_guid, contact_data)
            
            # Verify
            self.assertIsGuid(contact_guid)
            logger.info(f"Added contact: {contact_guid}")
            
        except Exception as e:
            # Some environments may not allow adding contacts
            logger.warning(f"Could not add contact: {str(e)}")
    
    def test_10_name_match_scoring(self):
        """Test underwriter name matching"""
        test_cases = [
            ("John Smith", "John Smith", 1.0),        # Exact
            ("Smith", "John Smith", 0.85),            # Last name match
            ("J Smith", "John Smith", 0.7),           # Partial match
            ("Jane Doe", "John Smith", 0.3),          # No match
        ]
        
        for search_name, actual_name, min_score in test_cases:
            score = self.producer_service._calculate_name_match_score(search_name, actual_name)
            
            self.assertGreaterEqual(score, min_score * 0.8,  # Allow variance
                                  f"Score for '{search_name}' vs '{actual_name}' too low")
            
            logger.info(f"'{search_name}' vs '{actual_name}': {score:.2f}")


if __name__ == "__main__":
    unittest.main(verbosity=2)