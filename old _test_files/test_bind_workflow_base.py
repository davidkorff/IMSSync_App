"""
Base test module for bind workflow testing with enhanced logging
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def log_soap_request(service_name: str, method_name: str, request_body: str):
    """Log SOAP request details"""
    logger.info(f"\n{'='*60}")
    logger.info(f"SOAP REQUEST - {service_name}.{method_name}")
    logger.info(f"{'='*60}")
    logger.info(f"Request Body:\n{request_body}")
    logger.info(f"{'='*60}\n")

def log_soap_response(service_name: str, method_name: str, response_body: str, status_code: int):
    """Log SOAP response details"""
    logger.info(f"\n{'='*60}")
    logger.info(f"SOAP RESPONSE - {service_name}.{method_name}")
    logger.info(f"{'='*60}")
    logger.info(f"Status Code: {status_code}")
    logger.info(f"Response Body:\n{response_body}")
    logger.info(f"{'='*60}\n")

def log_test_step(step_name: str, details: Dict[str, Any] = None):
    """Log test step execution"""
    logger.info(f"\n{'*'*60}")
    logger.info(f"TEST STEP: {step_name}")
    if details:
        logger.info(f"Details: {json.dumps(details, indent=2)}")
    logger.info(f"{'*'*60}\n")

def create_test_payload(
    transaction_type: str,
    opportunity_id: int,
    policy_number: str = None,
    opportunity_type: str = "new",
    expiring_opportunity_id: int = None,
    expiring_policy_number: str = None
) -> Dict[str, Any]:
    """Create a test payload for bind transactions"""
    base_payload = {
        "transaction_id": f"TEST_{transaction_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "transaction_type": transaction_type,
        "transaction_date": datetime.now().strftime("%m/%d/%Y"),
        "source_system": "TRITON_TEST",
        
        # Business info
        "opportunity_id": opportunity_id,
        "opportunity_type": opportunity_type,
        "policy_number": policy_number or f"TST{opportunity_id:06d}",
        "expiring_opportunity_id": expiring_opportunity_id,
        "expiring_policy_number": expiring_policy_number,
        
        # Insured info
        "insured_name": "Test Insurance Company LLC",
        "insured_state": "MI",
        "insured_zip": "48226",
        "address_1": "123 Test Street",
        "city": "Detroit",
        "state": "MI",
        "zip": "48226",
        
        # Coverage info
        "effective_date": "01/01/2025",
        "expiration_date": "01/01/2026",
        "bound_date": datetime.now().strftime("%m/%d/%Y"),
        
        # Business details
        "class_of_business": "General Liability",
        "program_name": "Test Program",
        "business_type": "Retail",
        "status": "Active",
        
        # Personnel
        "underwriter_name": "Shavonda Ellis",
        "producer_name": "Mike Woodworth",
        
        # Financial info
        "gross_premium": 25000.00,
        "commission_rate": 17.5,
        "net_premium": 20625.00,
        "base_premium": 20000.00,
        
        # Limits
        "limit_amount": "1000000/2000000",
        "deductible_amount": "10000",
        
        # Dates
        "invoice_date": datetime.now().strftime("%m/%d/%Y")
    }
    
    return base_payload

def save_test_results(test_name: str, results: Dict[str, Any]):
    """Save test results to a file for review"""
    filename = f"test_results_{test_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Test results saved to: {filename}")

class TestResult:
    """Container for test results"""
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.steps = []
        self.errors = []
        self.success = True
        self.start_time = datetime.now()
        
    def add_step(self, step_name: str, success: bool, details: Dict[str, Any] = None, error: str = None):
        """Add a test step result"""
        step_result = {
            "step_name": step_name,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "details": details or {},
            "error": error
        }
        self.steps.append(step_result)
        if not success:
            self.success = False
            if error:
                self.errors.append(f"{step_name}: {error}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get test summary"""
        return {
            "test_name": self.test_name,
            "success": self.success,
            "duration": (datetime.now() - self.start_time).total_seconds(),
            "total_steps": len(self.steps),
            "failed_steps": len([s for s in self.steps if not s["success"]]),
            "errors": self.errors,
            "steps": self.steps
        }