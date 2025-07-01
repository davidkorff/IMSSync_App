#!/usr/bin/env python3
"""
Test script to push sample Triton policy to the RSG Integration Service
This will test the complete flow: API → Transformation → IMS Integration
"""

import requests
import json
import sys
import time
from datetime import datetime

class TritonPolicyTester:
    def __init__(self, base_url="http://localhost:8000", api_key="test-api-key"):
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        })
    
    def load_sample_policy(self):
        """Load the sample policy from JSON file"""
        try:
            with open("sample_Triton_policy.json", "r") as f:
                content = f.read()
                # Remove JSON comments for valid parsing
                lines = content.split('\n')
                cleaned_lines = []
                for line in lines:
                    # Remove lines that are just comments
                    if line.strip().startswith('//'):
                        continue
                    # Remove inline comments
                    if '//' in line:
                        line = line.split('//')[0].rstrip()
                    cleaned_lines.append(line)
                
                cleaned_content = '\n'.join(cleaned_lines)
                return json.loads(cleaned_content)
        except FileNotFoundError:
            print("Error: sample_Triton_policy.json not found")
            print("Make sure you're running this script from the project root directory")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            sys.exit(1)
    
    def test_health_endpoint(self):
        """Test if the service is running"""
        try:
            response = self.session.get(f"{self.base_url}/api/health")
            if response.status_code == 200:
                print("✅ Service is healthy and running")
                return True
            else:
                print(f"❌ Service health check failed: {response.status_code}")
                return False
        except requests.RequestException as e:
            print(f"❌ Cannot connect to service: {e}")
            print(f"Make sure the service is running on {self.base_url}")
            return False
    
    def push_policy_generic_endpoint(self, policy_data):
        """Push policy to generic transaction endpoint"""
        try:
            print("\n🔄 Pushing policy to generic /transaction/new endpoint...")
            
            response = self.session.post(
                f"{self.base_url}/api/transaction/new",
                json=policy_data,
                params={"source": "triton"}
            )
            
            print(f"📊 Response Status: {response.status_code}")
            print(f"📄 Response Body: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                transaction_id = result.get("transaction_id")
                print(f"✅ Policy created successfully! Transaction ID: {transaction_id}")
                return transaction_id
            else:
                print(f"❌ Failed to create policy: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            print(f"❌ Error pushing policy: {e}")
            return None
    
    def push_policy_triton_endpoint(self, policy_data):
        """Push policy to Triton-specific endpoint"""
        try:
            print("\n🔄 Pushing policy to Triton-specific /api/triton/transaction/new endpoint...")
            
            # Extract transaction type from the data
            transaction_type = policy_data.get("transaction_type", "binding")
            type_mapping = {
                "binding": "new",
                "midterm_endorsement": "endorsement",
                "cancellation": "cancellation"
            }
            endpoint_type = type_mapping.get(transaction_type, "new")
            
            response = self.session.post(
                f"{self.base_url}/api/triton/transaction/{endpoint_type}",
                json=policy_data
            )
            
            print(f"📊 Response Status: {response.status_code}")
            print(f"📄 Response Body: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                transaction_id = result.get("transaction_id")
                print(f"✅ Policy created successfully! Transaction ID: {transaction_id}")
                return transaction_id
            else:
                print(f"❌ Failed to create policy: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            print(f"❌ Error pushing policy: {e}")
            return None
    
    def check_transaction_status(self, transaction_id):
        """Check the status of a transaction"""
        if not transaction_id:
            return
        
        try:
            print(f"\n🔍 Checking status of transaction: {transaction_id}")
            
            response = self.session.get(f"{self.base_url}/api/transaction/{transaction_id}")
            
            if response.status_code == 200:
                result = response.json()
                status = result.get("status")
                ims_status = result.get("ims_processing", {}).get("status")
                
                print(f"📊 Transaction Status: {status}")
                print(f"🏢 IMS Processing Status: {ims_status}")
                
                if result.get("ims_processing", {}).get("logs"):
                    print("\n📝 IMS Processing Logs:")
                    for log in result["ims_processing"]["logs"]:
                        timestamp = log.get("timestamp", "")
                        message = log.get("message", "")
                        print(f"   {timestamp}: {message}")
                
                return result
            else:
                print(f"❌ Failed to get transaction status: {response.status_code}")
                
        except requests.RequestException as e:
            print(f"❌ Error checking transaction status: {e}")
    
    def monitor_transaction(self, transaction_id, max_wait_time=120):
        """Monitor transaction until completion or timeout"""
        if not transaction_id:
            return
        
        print(f"\n⏱️  Monitoring transaction {transaction_id} (max wait: {max_wait_time}s)...")
        
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            result = self.check_transaction_status(transaction_id)
            
            if result:
                status = result.get("status")
                if status in ["completed", "failed"]:
                    print(f"\n🏁 Transaction finished with status: {status}")
                    
                    if status == "completed":
                        ims_processing = result.get("ims_processing", {})
                        policy = ims_processing.get("policy", {})
                        if policy and policy.get("policy_number"):
                            print(f"🎉 SUCCESS! IMS Policy Number: {policy['policy_number']}")
                        else:
                            print("⚠️  Transaction completed but no policy number found")
                    
                    return result
            
            print("⏳ Still processing... waiting 5 seconds")
            time.sleep(5)
        
        print(f"⏰ Timeout reached ({max_wait_time}s). Transaction may still be processing.")
        return None
    
    def run_complete_test(self):
        """Run the complete test sequence"""
        print("🚀 Starting Triton Policy Integration Test")
        print("=" * 50)
        
        # Test service health
        if not self.test_health_endpoint():
            return False
        
        # Load sample policy
        print("\n📄 Loading sample policy...")
        policy_data = self.load_sample_policy()
        policy_number = policy_data.get("policy", {}).get("policy_number", "Unknown")
        print(f"📋 Policy Number: {policy_number}")
        
        # Try both endpoints
        transaction_id = None
        
        # First try the Triton-specific endpoint
        transaction_id = self.push_policy_triton_endpoint(policy_data)
        
        # If that fails, try the generic endpoint
        if not transaction_id:
            transaction_id = self.push_policy_generic_endpoint(policy_data)
        
        # Monitor the transaction
        if transaction_id:
            final_result = self.monitor_transaction(transaction_id)
            
            if final_result and final_result.get("status") == "completed":
                print("\n🎊 TEST PASSED! Policy successfully processed in IMS")
                return True
            else:
                print("\n❌ TEST FAILED! Policy processing did not complete successfully")
                return False
        else:
            print("\n❌ TEST FAILED! Could not create transaction")
            return False

def main():
    """Main function"""
    print("Triton Policy Integration Test")
    print("This script will push the sample policy to the RSG Integration Service")
    print()
    
    # Parse command line arguments
    base_url = "http://localhost:8000"
    api_key = "test-api-key"
    
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    if len(sys.argv) > 2:
        api_key = sys.argv[2]
    
    print(f"🌐 Service URL: {base_url}")
    print(f"🔑 API Key: {api_key}")
    
    # Run the test
    tester = TritonPolicyTester(base_url, api_key)
    success = tester.run_complete_test()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()