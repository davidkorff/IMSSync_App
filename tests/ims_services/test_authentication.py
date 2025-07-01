"""
Tests for IMS Authentication Manager

Tests token management, renewal, and multi-environment support.
"""

import unittest
import time
from datetime import datetime, timedelta
from test_base import IMSServiceTestBase
from app.services.ims.base_service import IMSAuthenticationManager


class TestIMSAuthentication(IMSServiceTestBase):
    """Test IMS authentication functionality"""
    
    def test_01_get_token(self):
        """Test getting an authentication token"""
        # Get token
        token = self.auth_manager.get_token(self.environment)
        
        # Verify token
        self.assertIsNotNone(token, "Token should not be None")
        self.assertIsInstance(token, str, "Token should be a string")
        self.assertGreater(len(token), 20, "Token should be at least 20 characters")
        
        # Log token info
        logger.info(f"Successfully obtained token: {token[:20]}...")
    
    def test_02_token_caching(self):
        """Test that tokens are cached and reused"""
        # Get first token
        token1 = self.auth_manager.get_token(self.environment)
        
        # Get second token immediately
        token2 = self.auth_manager.get_token(self.environment)
        
        # Should be the same token (cached)
        self.assertEqual(token1, token2, "Second token should be cached")
        
        logger.info("Token caching verified")
    
    def test_03_token_invalidation(self):
        """Test token invalidation"""
        # Get initial token
        token1 = self.auth_manager.get_token(self.environment)
        
        # Invalidate token
        self.auth_manager.invalidate_token(self.environment)
        logger.info("Token invalidated")
        
        # Get new token
        token2 = self.auth_manager.get_token(self.environment)
        
        # Should be different
        self.assertNotEqual(token1, token2, "New token should be different after invalidation")
        
        logger.info("Token invalidation verified")
    
    def test_04_singleton_pattern(self):
        """Test that authentication manager is a singleton"""
        # Create multiple instances
        manager1 = IMSAuthenticationManager()
        manager2 = IMSAuthenticationManager()
        
        # Should be the same instance
        self.assertIs(manager1, manager2, "Authentication manager should be singleton")
        
        logger.info("Singleton pattern verified")
    
    def test_05_multi_environment(self):
        """Test handling multiple environments"""
        # Skip if only one environment configured
        if len(settings.IMS_ENVIRONMENTS) < 2:
            self.skipTest("Only one environment configured")
        
        # Get tokens for different environments
        tokens = {}
        for env_name in list(settings.IMS_ENVIRONMENTS.keys())[:2]:
            try:
                token = self.auth_manager.get_token(env_name)
                tokens[env_name] = token
                logger.info(f"Got token for {env_name}: {token[:20]}...")
            except Exception as e:
                logger.warning(f"Could not get token for {env_name}: {str(e)}")
        
        # Verify we got at least one token
        self.assertGreater(len(tokens), 0, "Should get at least one token")
        
        # If we got multiple tokens, verify they're different
        if len(tokens) > 1:
            token_values = list(tokens.values())
            self.assertNotEqual(token_values[0], token_values[1], 
                              "Tokens for different environments should be different")
    
    def test_06_invalid_environment(self):
        """Test handling invalid environment"""
        with self.assertRaises(ValueError) as context:
            self.auth_manager.get_token("invalid_environment")
        
        self.assertIn("Unknown IMS environment", str(context.exception))
        logger.info("Invalid environment handling verified")
    
    def test_07_soap_client_access(self):
        """Test getting SOAP client through auth manager"""
        # Get SOAP client
        soap_client = self.auth_manager.get_soap_client(self.environment)
        
        # Verify client
        self.assertIsNotNone(soap_client, "SOAP client should not be None")
        self.assertIsNotNone(soap_client.token, "SOAP client should have token")
        
        # Verify token is set
        manager_token = self.auth_manager.get_token(self.environment)
        self.assertEqual(soap_client.token, manager_token, 
                        "SOAP client token should match manager token")
        
        logger.info("SOAP client access verified")
    
    def test_08_concurrent_token_requests(self):
        """Test concurrent token requests (thread safety)"""
        import threading
        
        tokens = []
        errors = []
        
        def get_token():
            try:
                token = self.auth_manager.get_token(self.environment)
                tokens.append(token)
            except Exception as e:
                errors.append(str(e))
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=get_token)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify no errors
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        
        # All tokens should be the same (cached)
        self.assertEqual(len(set(tokens)), 1, "All concurrent requests should get same token")
        
        logger.info(f"Thread safety verified with {len(threads)} concurrent requests")


if __name__ == "__main__":
    # Set up logging
    import logging
    logger = logging.getLogger(__name__)
    
    # Run tests
    unittest.main(verbosity=2)