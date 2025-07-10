"""
Integration test for Triton binding transaction using TEST.json
Tests the actual /api/triton/transaction/new endpoint
"""

import json
import requests
import pytest
from datetime import datetime


class TestTritonBinding:
    """Test Triton binding transactions with real TEST.json data"""
    
    BASE_URL = "http://localhost:8000"
    ENDPOINT = "/api/triton/transaction/new"
    API_KEY = "triton_test_key"
    
    @classmethod
    def setup_class(cls):
        """Load TEST.json data"""
        with open('tests/data/TEST.json', 'r') as f:
            cls.test_data = json.load(f)
    
    def test_binding_with_test_json(self):
        """Test binding transaction with actual TEST.json data"""
        
        # The TEST.json has "NEW BUSINESS" as transaction_type, need to normalize it
        payload = self.test_data.copy()
        payload['transaction_type'] = 'binding'  # Override to standard type
        
        # Make request
        response = requests.post(
            f"{self.BASE_URL}{self.ENDPOINT}",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": self.API_KEY
            }
        )
        
        # Print for debugging
        print(f"\nRequest to: {self.ENDPOINT}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        print(f"Response Status: {response.status_code}")
        print(f"Response Body: {json.dumps(response.json(), indent=2)}")
        
        # Assertions
        assert response.status_code == 200
        
        result = response.json()
        assert result['status'] == 'success'
        assert 'data' in result
        
        data = result['data']
        assert data['success'] is True
        assert 'policy_number' in data
        assert 'quote_guid' in data
        assert data['transaction_id'] == payload['transaction_id']
    
    def test_binding_with_minimal_transformation(self):
        """Test with minimal changes to TEST.json"""
        
        # Only change what's absolutely necessary
        payload = {
            **self.test_data,
            'transaction_type': 'binding'  # Only override this
        }
        
        response = requests.post(
            f"{self.BASE_URL}{self.ENDPOINT}",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": self.API_KEY
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result['status'] == 'success'
    
    def test_flat_structure_detection(self):
        """Test that flat structure (TEST.json style) is properly detected"""
        
        # Create a minimal flat structure payload
        flat_payload = {
            "transaction_type": "binding",
            "transaction_id": f"TEST-{datetime.now().timestamp()}",
            "policy_number": self.test_data['policy_number'],
            "insured_name": self.test_data['insured_name'],
            "insured_state": self.test_data['insured_state'],
            "producer_name": self.test_data['producer_name'],
            "gross_premium": self.test_data['gross_premium'],
            "effective_date": self.test_data['effective_date'],
            "expiration_date": self.test_data['expiration_date'],
            "address_1": self.test_data['address_1'],
            "city": self.test_data['city'],
            "state": self.test_data['state'],
            "zip": self.test_data['zip']
        }
        
        response = requests.post(
            f"{self.BASE_URL}{self.ENDPOINT}",
            json=flat_payload,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": self.API_KEY
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result['status'] == 'success'
    
    def test_error_handling(self):
        """Test error handling with invalid data"""
        
        # Missing required fields
        invalid_payload = {
            "transaction_type": "binding",
            "transaction_id": "TEST-INVALID"
            # Missing all required fields
        }
        
        response = requests.post(
            f"{self.BASE_URL}{self.ENDPOINT}",
            json=invalid_payload,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": self.API_KEY
            }
        )
        
        assert response.status_code == 400
        result = response.json()
        assert result['status'] == 'error'
        assert 'error' in result
        assert 'stage' in result['error']
        assert 'message' in result['error']


if __name__ == "__main__":
    # Run tests
    test = TestTritonBinding()
    test.setup_class()
    
    print("=" * 60)
    print("TESTING TRITON BINDING WITH TEST.JSON")
    print("=" * 60)
    
    # Run each test
    try:
        print("\n1. Testing with TEST.json data...")
        test.test_binding_with_test_json()
        print("✅ PASSED")
    except AssertionError as e:
        print(f"❌ FAILED: {e}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    try:
        print("\n2. Testing with minimal transformation...")
        test.test_binding_with_minimal_transformation()
        print("✅ PASSED")
    except AssertionError as e:
        print(f"❌ FAILED: {e}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    try:
        print("\n3. Testing flat structure detection...")
        test.test_flat_structure_detection()
        print("✅ PASSED")
    except AssertionError as e:
        print(f"❌ FAILED: {e}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    try:
        print("\n4. Testing error handling...")
        test.test_error_handling()
        print("✅ PASSED")
    except AssertionError as e:
        print(f"❌ FAILED: {e}")
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("TESTS COMPLETE")
    print("=" * 60)