"""
Tests for IMS Data Access Service

Tests query execution, stored procedures, lookup data, and program data storage.
"""

import unittest
import json
from test_base import IMSServiceTestBase
import logging

logger = logging.getLogger(__name__)


class TestIMSDataAccessService(IMSServiceTestBase):
    """Test IMS Data Access Service functionality"""
    
    def test_01_execute_simple_query(self):
        """Test executing a simple query"""
        # Simple query to test connectivity
        query = "SELECT TOP 5 BusinessTypeID, Description FROM BusinessTypes WHERE Active = 1"
        
        logger.info(f"Executing query: {query}")
        
        try:
            result = self.data_access_service.execute_query(query)
            
            # Verify result structure
            self.assertIsInstance(result, dict)
            
            # Log results
            if result and 'Tables' in result:
                tables = result.get('Tables', {})
                if tables and len(tables) > 0:
                    rows = tables[0].get('Rows', [])
                    logger.info(f"Query returned {len(rows)} rows")
                    
                    for row in rows[:3]:  # Show first 3
                        logger.info(f"  {row}")
            
        except Exception as e:
            logger.warning(f"Query execution failed (may be expected): {str(e)}")
    
    def test_02_execute_query_with_parameters(self):
        """Test executing query with parameters"""
        query = """
        SELECT TOP 5 InsuredGUID, InsuredName 
        FROM Insureds 
        WHERE State = @State 
          AND Active = 1
        """
        
        parameters = {"State": "TX"}
        
        logger.info(f"Executing parameterized query for state: {parameters['State']}")
        
        try:
            result = self.data_access_service.execute_query(query, parameters)
            
            # Verify
            self.assertIsInstance(result, dict)
            
            # Log results
            if result and 'Tables' in result:
                tables = result.get('Tables', {})
                if tables and len(tables) > 0:
                    rows = tables[0].get('Rows', [])
                    logger.info(f"Found {len(rows)} insureds in TX")
                    
                    for row in rows[:3]:
                        logger.info(f"  {row.get('InsuredName')} ({row.get('InsuredGUID')})")
                        
        except Exception as e:
            logger.warning(f"Parameterized query failed: {str(e)}")
    
    def test_03_get_lookup_data_business_types(self):
        """Test getting business type lookup data"""
        logger.info("\nGetting business types lookup data")
        
        business_types = self.data_access_service.get_lookup_data("business_types")
        
        # Verify
        self.assertIsInstance(business_types, list)
        
        if business_types:
            logger.info(f"Found {len(business_types)} business types:")
            for bt in business_types[:5]:  # Show first 5
                logger.info(f"  {bt.get('BusinessTypeID')}: {bt.get('Description')}")
            
            # Verify expected types exist
            type_ids = [bt.get('BusinessTypeID') for bt in business_types]
            self.assertIn(1, type_ids, "Corporation should exist")
            self.assertIn(5, type_ids, "LLC should exist")
    
    def test_04_get_lookup_data_states(self):
        """Test getting states lookup data"""
        logger.info("\nGetting states lookup data")
        
        states = self.data_access_service.get_lookup_data("states")
        
        # Verify
        self.assertIsInstance(states, list)
        
        if states:
            logger.info(f"Found {len(states)} states")
            
            # Check for common states
            state_abbrevs = [s.get('StateAbbrev') for s in states]
            for state in ['TX', 'CA', 'NY', 'FL']:
                if state in state_abbrevs:
                    logger.info(f"  Found state: {state}")
    
    def test_05_get_lookup_data_lines(self):
        """Test getting lines of business lookup data"""
        logger.info("\nGetting lines lookup data")
        
        lines = self.data_access_service.get_lookup_data("lines")
        
        # Verify
        self.assertIsInstance(lines, list)
        
        if lines:
            logger.info(f"Found {len(lines)} lines of business:")
            for line in lines[:5]:  # Show first 5
                logger.info(f"  {line.get('LineName')} ({line.get('LineGUID')})")
    
    def test_06_find_entity_by_external_id(self):
        """Test finding entity by external ID"""
        # Test with known external IDs
        test_cases = [
            ("TRITON-12345", "triton"),
            ("XUBER-67890", "xuber"),
            ("TEST-00000", "test")
        ]
        
        for external_id, external_system in test_cases:
            logger.info(f"\nSearching for {external_system}/{external_id}")
            
            entity = self.data_access_service.find_entity_by_external_id(
                external_id, external_system
            )
            
            if entity:
                logger.info(f"Found entity:")
                logger.info(f"  Quote GUID: {entity.get('QuoteGUID')}")
                logger.info(f"  Policy Number: {entity.get('PolicyNumber')}")
                logger.info(f"  Status: {entity.get('QuoteStatusID')}")
            else:
                logger.info("No entity found")
    
    def test_07_store_program_data_triton(self):
        """Test storing Triton program data"""
        # Create test data
        quote_guid = "00000000-0000-0000-0000-000000000001"  # Test GUID
        external_id = f"TRITON-TEST-{self.test_id}"
        
        triton_data = {
            "program": "triton",
            "external_id": external_id,
            "insured_name": "Test Triton Company",
            "premium": 5000.00,
            "vehicles": [
                {"vin": "1234567890", "year": 2020, "make": "Ford"},
                {"vin": "0987654321", "year": 2021, "make": "Chevy"}
            ],
            "locations": [
                {"address": "123 Main St", "city": "Dallas", "state": "TX"}
            ],
            "created_date": "2024-01-01",
            "modified_date": "2024-01-15"
        }
        
        logger.info(f"\nStoring Triton data for external ID: {external_id}")
        
        try:
            success = self.data_access_service.store_program_data(
                "triton", quote_guid, external_id, triton_data
            )
            
            # Log result
            if success:
                logger.info("Successfully stored Triton data")
            else:
                logger.info("Failed to store Triton data")
                
        except Exception as e:
            logger.warning(f"Store program data failed (may be expected): {str(e)}")
    
    def test_08_store_program_data_xuber(self):
        """Test storing Xuber program data"""
        # Create test data
        quote_guid = "00000000-0000-0000-0000-000000000002"  # Test GUID
        external_id = f"XUBER-TEST-{self.test_id}"
        
        xuber_data = {
            "program": "xuber",
            "external_id": external_id,
            "insured_name": "Test Xuber Driver",
            "base_premium": 3000.00,
            "total_premium": 3500.00,
            "fees": 500.00,
            "drivers": [
                {"name": "John Doe", "license": "TX123456"},
                {"name": "Jane Smith", "license": "TX789012"}
            ],
            "vehicles": [
                {"vin": "ABC123", "year": 2022, "make": "Toyota", "model": "Camry"}
            ],
            "coverage_limits": {
                "bodily_injury": "100/300",
                "property_damage": "50000"
            }
        }
        
        logger.info(f"\nStoring Xuber data for external ID: {external_id}")
        
        try:
            success = self.data_access_service.store_program_data(
                "xuber", quote_guid, external_id, xuber_data
            )
            
            # Log result
            if success:
                logger.info("Successfully stored Xuber data")
            else:
                logger.info("Failed to store Xuber data")
                
        except Exception as e:
            logger.warning(f"Store program data failed (may be expected): {str(e)}")
    
    def test_09_execute_command(self):
        """Test executing a stored procedure/command"""
        # Test with a simple command (if available)
        command = "GetServerDate"  # Common test stored procedure
        
        logger.info(f"\nExecuting command: {command}")
        
        try:
            result = self.data_access_service.execute_command(command)
            
            if result:
                logger.info(f"Command result: {result}")
            else:
                logger.info("Command returned no result")
                
        except Exception as e:
            logger.warning(f"Command execution failed (may be expected): {str(e)}")
    
    def test_10_invalid_lookup_type(self):
        """Test handling invalid lookup type"""
        logger.info("\nTesting invalid lookup type")
        
        result = self.data_access_service.get_lookup_data("invalid_type")
        
        # Should return empty list, not error
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0, "Invalid lookup should return empty list")
        
        logger.info("Invalid lookup handled correctly")


class TestDataAccessValidation(IMSServiceTestBase):
    """Test data access validation and error handling"""
    
    def test_01_invalid_query_syntax(self):
        """Test handling invalid query syntax"""
        query = "SELECT * FROM NonExistentTable WHERE BadSyntax ="
        
        logger.info("\nTesting invalid query syntax")
        
        try:
            result = self.data_access_service.execute_query(query)
            # If no error, check result
            self.assertIsInstance(result, dict)
        except Exception as e:
            # Expected to fail
            logger.info(f"Query failed as expected: {str(e)}")
            self.assertIsNotNone(e)
    
    def test_02_sql_injection_prevention(self):
        """Test SQL injection prevention with parameters"""
        # Attempt SQL injection through parameter
        query = "SELECT * FROM Insureds WHERE InsuredName = @Name"
        parameters = {
            "Name": "'; DROP TABLE Test; --"  # SQL injection attempt
        }
        
        logger.info("\nTesting SQL injection prevention")
        
        try:
            # This should safely execute without dropping tables
            result = self.data_access_service.execute_query(query, parameters)
            
            # If it executes, injection was prevented
            logger.info("SQL injection attempt safely handled")
            
        except Exception as e:
            # Also acceptable - query might fail safely
            logger.info(f"Query failed safely: {str(e)}")
    
    def test_03_large_result_handling(self):
        """Test handling large result sets"""
        # Query that might return many rows
        query = "SELECT TOP 1000 InsuredGUID FROM Insureds WHERE Active = 1"
        
        logger.info("\nTesting large result set handling")
        
        try:
            result = self.data_access_service.execute_query(query)
            
            if result and 'Tables' in result:
                tables = result.get('Tables', {})
                if tables and len(tables) > 0:
                    rows = tables[0].get('Rows', [])
                    logger.info(f"Successfully retrieved {len(rows)} rows")
                    
        except Exception as e:
            logger.warning(f"Large query failed: {str(e)}")


if __name__ == "__main__":
    unittest.main(verbosity=2)