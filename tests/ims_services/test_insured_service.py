"""
Tests for IMS Insured Service

Tests insured creation, search, matching, and location management.
"""

import unittest
from test_base import IMSServiceTestBase
import logging

logger = logging.getLogger(__name__)


class TestIMSInsuredService(IMSServiceTestBase):
    """Test IMS Insured Service functionality"""
    
    def test_01_create_insured(self):
        """Test creating a new insured"""
        # Generate test data
        insured_data = self.generate_insured_data()
        self.log_test_data(insured_data, "Creating Insured")
        
        # Create insured
        insured_guid = self.insured_service.create_insured(insured_data)
        
        # Verify
        self.assertIsGuid(insured_guid)
        self.track_entity("insureds", insured_guid)
        
        logger.info(f"Created insured: {insured_guid}")
    
    def test_02_find_insured_by_exact_name(self):
        """Test finding insured by exact name match"""
        # Create test insured
        insured_data = self.generate_insured_data("ExactMatch")
        insured_guid = self.insured_service.create_insured(insured_data)
        self.track_entity("insureds", insured_guid)
        
        # Search by exact name
        found_guid = self.insured_service.find_insured_by_name(
            name=insured_data["name"],
            tax_id=insured_data["tax_id"]
        )
        
        # Verify
        self.assertEqual(found_guid, insured_guid, "Should find insured by exact name")
        logger.info(f"Found insured by exact name: {found_guid}")
    
    def test_03_insured_matching_fuzzy(self):
        """Test fuzzy matching for insureds"""
        # Create insured with specific name
        base_name = f"ABC Transport Company LLC {self.test_id}"
        insured_data = self.generate_insured_data()
        insured_data["name"] = base_name
        insured_guid = self.insured_service.create_insured(insured_data)
        self.track_entity("insureds", insured_guid)
        
        # Test variations that should match
        variations = [
            base_name.replace("LLC", "L.L.C."),  # Different LLC format
            base_name.replace("LLC", ""),         # Without suffix
            base_name.replace("Company", "Co."),  # Abbreviated
            base_name.upper(),                     # Different case
        ]
        
        for variation in variations:
            logger.info(f"Testing variation: '{variation}'")
            
            search_criteria = {
                "name": variation,
                "tax_id": insured_data["tax_id"]
            }
            
            match = self.insured_service.matcher.find_best_match(search_criteria)
            
            self.assertIsNotNone(match, f"Should find match for variation: {variation}")
            self.assertEqual(match.get("InsuredGUID"), insured_guid, 
                           f"Should match correct insured for: {variation}")
    
    def test_04_find_or_create_existing(self):
        """Test find_or_create with existing insured"""
        # Create insured
        insured_data = self.generate_insured_data("FindOrCreate")
        original_guid = self.insured_service.create_insured(insured_data)
        self.track_entity("insureds", original_guid)
        
        # Try to create same insured again
        found_guid = self.insured_service.find_or_create_insured(insured_data)
        
        # Should return existing
        self.assertEqual(found_guid, original_guid, "Should return existing insured")
        logger.info("Find or create returned existing insured")
    
    def test_05_find_or_create_new(self):
        """Test find_or_create with new insured"""
        # Generate unique data
        insured_data = self.generate_insured_data("UniqueNew")
        
        # Find or create (should create)
        insured_guid = self.insured_service.find_or_create_insured(insured_data)
        
        # Verify
        self.assertIsGuid(insured_guid)
        self.track_entity("insureds", insured_guid)
        
        logger.info(f"Find or create created new insured: {insured_guid}")
    
    def test_06_add_insured_location(self):
        """Test adding location to insured"""
        # Create insured
        insured_data = self.generate_insured_data("WithLocation")
        insured_guid = self.insured_service.create_insured(insured_data)
        self.track_entity("insureds", insured_guid)
        
        # Add location
        location_data = {
            "address": "456 Branch Street",
            "city": "Houston",
            "state": "TX",
            "zip_code": "77001",
            "description": "Houston Branch Office"
        }
        
        self.log_test_data(location_data, "Adding Location")
        
        location_id = self.insured_service.add_insured_location(insured_guid, location_data)
        
        # Verify
        self.assertIsNotNone(location_id)
        self.assertIsInstance(location_id, int)
        self.assertGreater(location_id, 0)
        
        logger.info(f"Added location ID: {location_id}")
    
    def test_07_business_type_determination(self):
        """Test business type determination"""
        test_cases = [
            ("Test Company LLC", 5),          # LLC
            ("Test Corp", 1),                 # Corporation
            ("Test Inc.", 1),                 # Corporation
            ("John Doe", 3),                  # Individual (no business suffix)
            ("Test Partnership", 2),          # Partnership
            ("Test Sole Prop", 4),           # Sole Proprietor
        ]
        
        for name, expected_type in test_cases:
            insured_data = {"name": name, "business_type": ""}
            determined_type = self.insured_service._determine_business_type(insured_data)
            
            self.assertEqual(determined_type, expected_type, 
                           f"Business type for '{name}' should be {expected_type}")
            logger.info(f"'{name}' -> Type {determined_type}")
    
    def test_08_update_insured(self):
        """Test updating insured information"""
        # Create insured
        insured_data = self.generate_insured_data("ToUpdate")
        insured_guid = self.insured_service.create_insured(insured_data)
        self.track_entity("insureds", insured_guid)
        
        # Update data
        updated_data = insured_data.copy()
        updated_data["address"] = "789 Updated Avenue"
        updated_data["city"] = "Austin"
        updated_data["zip_code"] = "78701"
        
        # Update insured
        success = self.insured_service.update_insured(insured_guid, updated_data)
        
        # Verify
        self.assertTrue(success, "Update should succeed")
        logger.info(f"Successfully updated insured {insured_guid}")
    
    def test_09_tax_id_matching(self):
        """Test matching by tax ID"""
        # Create insured with specific tax ID
        tax_id = "12-3456789"
        insured_data = self.generate_insured_data("TaxIDMatch")
        insured_data["tax_id"] = tax_id
        insured_guid = self.insured_service.create_insured(insured_data)
        self.track_entity("insureds", insured_guid)
        
        # Search with different tax ID formats
        tax_id_variations = [
            "12-3456789",    # Exact
            "123456789",     # Without dash
            "12 3456789",    # With space
        ]
        
        for variation in tax_id_variations:
            search_criteria = {
                "name": "Different Name Entirely",
                "tax_id": variation
            }
            
            match = self.insured_service.matcher.find_best_match(search_criteria)
            
            self.assertIsNotNone(match, f"Should find match by tax ID: {variation}")
            self.assertEqual(match.get("InsuredGUID"), insured_guid,
                           f"Should match correct insured by tax ID: {variation}")
    
    def test_10_no_duplicate_creation(self):
        """Test that duplicates are not created"""
        # Create base insured
        base_name = f"Duplicate Test Company {self.test_id}"
        insured_data = self.generate_insured_data()
        insured_data["name"] = base_name
        original_guid = self.insured_service.create_insured(insured_data)
        self.track_entity("insureds", original_guid)
        
        # Try variations that should match existing
        variations = [
            {"name": base_name.upper()},  # Case variation
            {"name": base_name + " LLC"},  # Added suffix
            {"name": base_name, "address": "Different Address"},  # Different address
        ]
        
        for variation_data in variations:
            test_data = insured_data.copy()
            test_data.update(variation_data)
            
            found_guid = self.insured_service.find_or_create_insured(test_data)
            
            self.assertEqual(found_guid, original_guid,
                           f"Should not create duplicate for: {variation_data}")
            logger.info(f"Correctly matched existing insured for: {variation_data}")


class TestIMSInsuredMatcher(IMSServiceTestBase):
    """Test the Insured Matcher functionality"""
    
    def test_01_name_normalization(self):
        """Test business name normalization"""
        matcher = self.insured_service.matcher
        
        test_cases = [
            ("ABC Company, LLC", "ABC COMPANY"),
            ("XYZ Corp.", "XYZ"),
            ("Test & Associates", "TEST ASSOCIATES"),
            ("International Business Inc", "INTERNATIONAL BUSINESS"),
        ]
        
        for original, expected in test_cases:
            normalized = matcher._normalize_business_name(original)
            self.assertEqual(normalized, expected,
                           f"Normalization of '{original}' failed")
            logger.info(f"'{original}' -> '{normalized}'")
    
    def test_02_address_normalization(self):
        """Test address normalization"""
        matcher = self.insured_service.matcher
        
        test_cases = [
            ("123 Main Street", "123 MAIN ST"),
            ("456 Oak Avenue Suite 100", "456 OAK AVE STE 100"),
            ("789 North Boulevard", "789 N BLVD"),
        ]
        
        for original, expected in test_cases:
            normalized = matcher._normalize_address(original)
            self.assertEqual(normalized, expected,
                           f"Address normalization of '{original}' failed")
            logger.info(f"'{original}' -> '{normalized}'")
    
    def test_03_match_scoring(self):
        """Test match scoring algorithm"""
        matcher = self.insured_service.matcher
        
        # Create test criteria
        search_criteria = {
            "name": "ABC Transport LLC",
            "tax_id": "12-3456789",
            "address": "123 Main St",
            "state": "TX"
        }
        
        # Test exact match
        exact_match = {
            "InsuredName": "ABC Transport LLC",
            "TaxID": "12-3456789",
            "Address1": "123 Main St",
            "State": "TX"
        }
        
        score = matcher._calculate_match_score(search_criteria, exact_match)
        self.assertGreaterEqual(score, 0.95, "Exact match should score very high")
        logger.info(f"Exact match score: {score:.2f}")
        
        # Test partial match
        partial_match = {
            "InsuredName": "ABC Transport Company LLC",  # Similar name
            "TaxID": "12-3456789",  # Same tax ID
            "Address1": "123 Main Street",  # Similar address
            "State": "TX"  # Same state
        }
        
        score = matcher._calculate_match_score(search_criteria, partial_match)
        self.assertGreaterEqual(score, 0.80, "Partial match should score high")
        self.assertLess(score, 0.95, "Partial match should score less than exact")
        logger.info(f"Partial match score: {score:.2f}")
        
        # Test poor match
        poor_match = {
            "InsuredName": "XYZ Company",  # Different name
            "TaxID": "98-7654321",  # Different tax ID
            "Address1": "789 Oak Ave",  # Different address
            "State": "CA"  # Different state
        }
        
        score = matcher._calculate_match_score(search_criteria, poor_match)
        self.assertLess(score, 0.50, "Poor match should score low")
        logger.info(f"Poor match score: {score:.2f}")


if __name__ == "__main__":
    unittest.main(verbosity=2)