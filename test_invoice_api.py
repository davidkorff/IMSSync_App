#!/usr/bin/env python3
"""
Test script for the new /api/triton/invoice endpoint.

This script tests retrieving invoice data using different parameters:
- invoice_num
- quote_guid  
- policy_number
- opportunity_id
"""

import requests
import json
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API configuration
BASE_URL = "http://localhost:7071"  # Adjust if your API runs on a different port
INVOICE_ENDPOINT = f"{BASE_URL}/api/triton/invoice"


def test_invoice_by_quote_guid(quote_guid: str) -> Dict[str, Any]:
    """Test getting invoice by quote GUID."""
    logger.info(f"Testing invoice retrieval by quote_guid: {quote_guid}")
    
    params = {"quote_guid": quote_guid}
    response = requests.get(INVOICE_ENDPOINT, params=params)
    
    logger.info(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        logger.info(f"Success: {data.get('message')}")
        if data.get('invoice_data'):
            logger.info(f"Invoice data retrieved: {json.dumps(data['invoice_data'], indent=2)}")
        return data
    else:
        logger.error(f"Failed: {response.text}")
        return {"error": response.text}


def test_invoice_by_policy_number(policy_number: str) -> Dict[str, Any]:
    """Test getting invoice by policy number."""
    logger.info(f"Testing invoice retrieval by policy_number: {policy_number}")
    
    params = {"policy_number": policy_number}
    response = requests.get(INVOICE_ENDPOINT, params=params)
    
    logger.info(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        logger.info(f"Success: {data.get('message')}")
        if data.get('invoice_data'):
            logger.info(f"Invoice data retrieved: {json.dumps(data['invoice_data'], indent=2)}")
        return data
    else:
        logger.error(f"Failed: {response.text}")
        return {"error": response.text}


def test_invoice_by_opportunity_id(opportunity_id: str) -> Dict[str, Any]:
    """Test getting invoice by opportunity ID."""
    logger.info(f"Testing invoice retrieval by opportunity_id: {opportunity_id}")
    
    params = {"opportunity_id": opportunity_id}
    response = requests.get(INVOICE_ENDPOINT, params=params)
    
    logger.info(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        logger.info(f"Success: {data.get('message')}")
        if data.get('invoice_data'):
            logger.info(f"Invoice data retrieved: {json.dumps(data['invoice_data'], indent=2)}")
        return data
    else:
        logger.error(f"Failed: {response.text}")
        return {"error": response.text}


def test_invoice_by_invoice_num(invoice_num: int) -> Dict[str, Any]:
    """Test getting invoice by invoice number."""
    logger.info(f"Testing invoice retrieval by invoice_num: {invoice_num}")
    
    params = {"invoice_num": invoice_num}
    response = requests.get(INVOICE_ENDPOINT, params=params)
    
    logger.info(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        logger.info(f"Success: {data.get('message')}")
        if data.get('invoice_data'):
            logger.info(f"Invoice data retrieved: {json.dumps(data['invoice_data'], indent=2)}")
        return data
    else:
        logger.error(f"Failed: {response.text}")
        return {"error": response.text}


def test_no_params() -> Dict[str, Any]:
    """Test with no parameters (should fail with 400)."""
    logger.info("Testing invoice retrieval with no parameters (should fail)")
    
    response = requests.get(INVOICE_ENDPOINT)
    
    logger.info(f"Response status: {response.status_code}")
    
    if response.status_code == 400:
        logger.info("Correctly rejected request with no parameters")
        return {"success": "Validation working correctly"}
    else:
        logger.error(f"Unexpected response: {response.text}")
        return {"error": response.text}


def main():
    """Run all invoice API tests."""
    print("\n" + "="*60)
    print("TESTING NEW INVOICE API ENDPOINT")
    print("="*60)
    
    # Test validation (no params)
    print("\n1. Testing validation (no parameters)...")
    test_no_params()
    
    # Example test cases - replace with your actual test data
    print("\n2. Testing with quote_guid...")
    # Replace with an actual quote GUID from your system
    # test_invoice_by_quote_guid("12345678-1234-1234-1234-123456789012")
    
    print("\n3. Testing with policy_number...")
    # Replace with an actual policy number from your system
    # test_invoice_by_policy_number("POL-2025-001")
    
    print("\n4. Testing with opportunity_id...")
    # Replace with an actual opportunity ID from your system
    # test_invoice_by_opportunity_id("OPP-123456")
    
    print("\n5. Testing with invoice_num...")
    # Replace with an actual invoice number from your system
    # test_invoice_by_invoice_num(1001)
    
    print("\n" + "="*60)
    print("To run actual tests, uncomment the test cases above")
    print("and replace with real values from your system")
    print("="*60)


if __name__ == "__main__":
    main()