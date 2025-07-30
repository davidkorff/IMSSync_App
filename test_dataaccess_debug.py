#!/usr/bin/env python3
"""Debug DataAccess parameter format issue"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.ims.auth_service import AuthService
from app.services.ims.data_access_service import DataAccessService

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Enable SOAP debug logging
logging.getLogger('zeep.transports').setLevel(logging.DEBUG)

# Load environment variables
load_dotenv()

def test_dataaccess_formats():
    """Test different parameter formats for DataAccess"""
    
    # Initialize services
    auth_service = AuthService()
    data_access = DataAccessService(auth_service)
    
    quote_guid = "d8d3d6b3-ba59-4eb5-a8c6-b392848db6e2"
    
    print("\n" + "="*50)
    print("Testing DataAccess Parameter Formats")
    print("="*50)
    
    # Test 1: Current format - array of strings
    print("\n1. Testing array format ['@QuoteGuid', 'value']:")
    try:
        results = data_access.execute_dataset("spGetQuoteOptions", {"QuoteGuid": quote_guid})
        print(f"SUCCESS: Got {len(results)} results")
    except Exception as e:
        print(f"FAILED: {str(e)}")
    
    # Test 2: Try without @ symbol
    print("\n2. Testing without @ symbol:")
    try:
        # Temporarily modify the method to not add @
        params = ["QuoteGuid", quote_guid]
        token = auth_service.get_token()
        
        response = data_access.client.service.ExecuteDataSet(
            procedureName="spGetQuoteOptions",
            parameters=params,
            _soapheaders=data_access.get_header(token)
        )
        print(f"SUCCESS: {response}")
    except Exception as e:
        print(f"FAILED: {str(e)}")
    
    # Test 3: Try empty parameters
    print("\n3. Testing with empty parameters array:")
    try:
        token = auth_service.get_token()
        
        response = data_access.client.service.ExecuteDataSet(
            procedureName="spGetQuoteOptions",
            parameters=[],
            _soapheaders=data_access.get_header(token)
        )
        print(f"Result: {response}")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Test 4: Try None for parameters
    print("\n4. Testing with None for parameters:")
    try:
        token = auth_service.get_token()
        
        response = data_access.client.service.ExecuteDataSet(
            procedureName="spGetQuoteOptions",
            parameters=None,
            _soapheaders=data_access.get_header(token)
        )
        print(f"Result: {response}")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # Test 5: Try a simple test procedure that doesn't require parameters
    print("\n5. Testing a procedure without parameters:")
    try:
        # Try to get lines or states which typically don't need parameters
        token = auth_service.get_token()
        
        response = data_access.client.service.ExecuteDataSet(
            procedureName="DK_GetLines",  # This procedure should exist without _WS
            parameters=[],
            _soapheaders=data_access.get_header(token)
        )
        print(f"SUCCESS: {response}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_dataaccess_formats()