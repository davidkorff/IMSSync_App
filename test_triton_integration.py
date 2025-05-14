#!/usr/bin/env python3
"""
Test script for Triton integration
"""

import logging
import json
import requests
import sys
import time
from datetime import date, datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "test_api_key"

def generate_test_data():
    """Generate sample Triton policy data"""
    
    # Use effective dates in the future
    today = date.today()
    effective_date = today + timedelta(days=30)
    expiration_date = effective_date.replace(year=effective_date.year + 1)
    
    # Sample policy data in JSON format
    return {
        "policy_number": f"TRI-TEST-{int(time.time())}",
        "effective_date": effective_date.isoformat(),
        "expiration_date": expiration_date.isoformat(),
        "bound_date": today.isoformat(),
        "program": "Test Program",
        "line_of_business": "General Liability",
        "state": "TX",
        "insured": {
            "name": "Triton Test Company LLC",
            "dba": "Test Co",
            "contact": {
                "name": "John Smith",
                "email": "john@example.com",
                "phone": "555-123-4567",
                "address": "123 Main St",
                "city": "Austin",
                "state": "TX",
                "zip_code": "78701"
            },
            "tax_id": "12-3456789",
            "business_type": "LLC"
        },
        "locations": [
            {
                "address": "123 Main St",
                "city": "Austin",
                "state": "TX",
                "zip_code": "78701",
                "country": "USA",
                "description": "Main Office"
            }
        ],
        "producer": {
            "name": "ABC Insurance Agency",
            "id": "TRITON-PROD-123",
            "contact": {
                "name": "Jane Doe",
                "email": "jane@example.com",
                "phone": "555-987-6543"
            },
            "commission": 15.0
        },
        "underwriter": "Bob Johnson",
        "coverages": [
            {
                "type": "General Liability",
                "limit": 1000000.0,
                "deductible": 5000.0,
                "premium": 10000.0
            }
        ],
        "premium": 10000.0,
        "billing_type": "Agency Bill",
        "additional_data": {
            "source_system": "triton",
            "source_id": f"TRITON-ID-{int(time.time())}"
        }
    }

def create_triton_transaction():
    """Create a new transaction using the Triton-specific endpoint"""
    
    url = f"{BASE_URL}/api/triton/transaction/new"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    data = generate_test_data()
    
    logger.info(f"Sending test transaction to {url}")
    logger.info(f"Policy Number: {data['policy_number']}")
    
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Transaction created: {result.get('transaction_id')}")
        logger.info(f"Status: {result.get('status')}")
        logger.info(f"Message: {result.get('message')}")
        
        return result.get('transaction_id')
    except requests.exceptions.RequestException as e:
        logger.error(f"Error creating transaction: {str(e)}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response: {e.response.text}")
        return None

def check_transaction_status(transaction_id):
    """Check the status of a transaction"""
    
    url = f"{BASE_URL}/api/transaction/{transaction_id}"
    headers = {
        "X-API-Key": API_KEY
    }
    
    logger.info(f"Checking status of transaction {transaction_id}")
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Transaction {transaction_id} status: {result.get('status')}")
        logger.info(f"IMS status: {result.get('ims_status')}")
        logger.info(f"Message: {result.get('message')}")
        
        return result
    except requests.exceptions.RequestException as e:
        logger.error(f"Error checking transaction status: {str(e)}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response: {e.response.text}")
        return None

def main():
    """Main test function"""
    
    # Create a transaction
    transaction_id = create_triton_transaction()
    if not transaction_id:
        logger.error("Failed to create transaction")
        sys.exit(1)
    
    # Check status a few times
    for i in range(5):
        time.sleep(3)  # Wait a bit between checks
        status = check_transaction_status(transaction_id)
        if not status:
            logger.error("Failed to check status")
            continue
            
        # If processing is complete, we can stop checking
        if status.get('status') in ['completed', 'failed']:
            break
    
    logger.info("Test completed")

if __name__ == "__main__":
    main()