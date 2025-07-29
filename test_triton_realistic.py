"""
Realistic Triton Integration Test
Sends JSON payloads to the API endpoint exactly as Triton would
"""
import json
import requests
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import sys
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'triton_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TritonTestClient:
    """Test client that mimics Triton's behavior"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.endpoint = f"{base_url}/api/triton/transaction/new"
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "Triton-Test-Client/1.0"
        })
    
    def send_transaction(self, json_file: str) -> Dict[str, Any]:
        """
        Send a transaction from a JSON file to the API endpoint
        
        Args:
            json_file: Path to the JSON file containing the transaction
            
        Returns:
            Dict containing the test results
        """
        test_result = {
            "json_file": json_file,
            "start_time": datetime.now().isoformat(),
            "request": {},
            "response": {},
            "success": False,
            "steps": []
        }
        
        try:
            # Step 1: Load JSON file
            logger.info(f"\n{'='*60}")
            logger.info(f"TRITON TEST: {json_file}")
            logger.info(f"{'='*60}")
            
            with open(json_file, 'r') as f:
                payload = json.load(f)
            
            test_result["request"]["payload"] = payload
            test_result["steps"].append({
                "step": "Load JSON",
                "success": True,
                "details": {
                    "file": json_file,
                    "transaction_id": payload.get("transaction_id"),
                    "transaction_type": payload.get("transaction_type"),
                    "opportunity_id": payload.get("opportunity_id")
                }
            })
            
            logger.info(f"Loaded transaction:")
            logger.info(f"  Transaction ID: {payload.get('transaction_id')}")
            logger.info(f"  Type: {payload.get('transaction_type')}")
            logger.info(f"  Opportunity ID: {payload.get('opportunity_id')}")
            logger.info(f"  Policy Number: {payload.get('policy_number')}")
            
            # Step 2: Send to API endpoint
            logger.info(f"\nSending to: {self.endpoint}")
            logger.debug(f"Request payload:\n{json.dumps(payload, indent=2)}")
            
            response = self.session.post(
                self.endpoint,
                json=payload,
                timeout=120  # 2 minute timeout
            )
            
            # Store response details
            test_result["response"]["status_code"] = response.status_code
            test_result["response"]["headers"] = dict(response.headers)
            
            # Try to parse JSON response
            try:
                response_data = response.json()
                test_result["response"]["body"] = response_data
            except:
                test_result["response"]["body"] = response.text
                response_data = {}
            
            test_result["steps"].append({
                "step": "Send to API",
                "success": response.status_code in [200, 201],
                "details": {
                    "status_code": response.status_code,
                    "url": self.endpoint
                }
            })
            
            logger.info(f"\nResponse Status: {response.status_code}")
            logger.debug(f"Response Headers:\n{json.dumps(dict(response.headers), indent=2)}")
            logger.debug(f"Response Body:\n{json.dumps(response_data, indent=2) if response_data else response.text}")
            
            # Step 3: Analyze response
            if response.status_code == 200:
                success = response_data.get("success", False)
                message = response_data.get("message", "No message")
                data = response_data.get("data", {})
                
                test_result["success"] = success
                
                if success:
                    logger.info(f"\n✓ TRANSACTION SUCCESSFUL")
                    logger.info(f"  Message: {message}")
                    
                    # Log key results
                    if data:
                        if data.get("quote_guid"):
                            logger.info(f"  Quote GUID: {data.get('quote_guid')}")
                        if data.get("bound_policy_number"):
                            logger.info(f"  Bound Policy: {data.get('bound_policy_number')}")
                        if data.get("bind_status"):
                            logger.info(f"  Bind Status: {data.get('bind_status')}")
                        
                        test_result["steps"].append({
                            "step": "Process Results",
                            "success": True,
                            "details": data
                        })
                else:
                    logger.error(f"\n✗ TRANSACTION FAILED")
                    logger.error(f"  Message: {message}")
                    if response_data.get("error"):
                        logger.error(f"  Error: {response_data.get('error')}")
                    
                    test_result["steps"].append({
                        "step": "Process Results",
                        "success": False,
                        "error": message
                    })
            else:
                # HTTP error
                logger.error(f"\n✗ HTTP ERROR: {response.status_code}")
                if response_data and "detail" in response_data:
                    logger.error(f"  Detail: {response_data['detail']}")
                elif response.text:
                    logger.error(f"  Response: {response.text}")
                
                test_result["steps"].append({
                    "step": "HTTP Error",
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                })
            
        except FileNotFoundError:
            error_msg = f"JSON file not found: {json_file}"
            logger.error(error_msg)
            test_result["steps"].append({
                "step": "Load JSON",
                "success": False,
                "error": error_msg
            })
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in file: {str(e)}"
            logger.error(error_msg)
            test_result["steps"].append({
                "step": "Parse JSON",
                "success": False,
                "error": error_msg
            })
        except requests.exceptions.Timeout:
            error_msg = "Request timed out after 120 seconds"
            logger.error(error_msg)
            test_result["steps"].append({
                "step": "Timeout",
                "success": False,
                "error": error_msg
            })
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            logger.error(error_msg)
            test_result["steps"].append({
                "step": "Request Error",
                "success": False,
                "error": error_msg
            })
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            test_result["steps"].append({
                "step": "Exception",
                "success": False,
                "error": error_msg
            })
        
        test_result["end_time"] = datetime.now().isoformat()
        
        # Save detailed results
        result_file = f"test_result_{Path(json_file).stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, 'w') as f:
            json.dump(test_result, f, indent=2, default=str)
        logger.info(f"\nDetailed results saved to: {result_file}")
        
        return test_result

def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Test Triton integration with JSON files")
    parser.add_argument("json_files", nargs="+", help="JSON file(s) to test")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of the API")
    parser.add_argument("--compare", action="store_true", help="Compare results between files")
    
    args = parser.parse_args()
    
    # Create test client
    client = TritonTestClient(args.url)
    
    # Run tests
    results = []
    for json_file in args.json_files:
        print(f"\n{'='*80}")
        print(f"Testing: {json_file}")
        print(f"{'='*80}")
        
        result = client.send_transaction(json_file)
        results.append(result)
        
        # Summary
        if result["success"]:
            print(f"\n✓ SUCCESS: {json_file}")
        else:
            print(f"\n✗ FAILED: {json_file}")
    
    # Overall summary
    print(f"\n{'='*80}")
    print("TEST SUMMARY")
    print(f"{'='*80}")
    print(f"Total Tests: {len(results)}")
    print(f"Passed: {sum(1 for r in results if r['success'])}")
    print(f"Failed: {sum(1 for r in results if not r['success'])}")
    
    # Compare results if requested
    if args.compare and len(results) > 1:
        print(f"\n{'='*80}")
        print("COMPARISON")
        print(f"{'='*80}")
        
        for i, result in enumerate(results):
            json_file = result["json_file"]
            response_data = result.get("response", {}).get("body", {})
            if isinstance(response_data, dict):
                data = response_data.get("data", {})
                print(f"\n{json_file}:")
                print(f"  Success: {result['success']}")
                print(f"  Quote GUID: {data.get('quote_guid', 'N/A')}")
                print(f"  Policy Number: {data.get('bound_policy_number', 'N/A')}")
                print(f"  Status: {data.get('bind_status', 'N/A')}")

if __name__ == "__main__":
    main()