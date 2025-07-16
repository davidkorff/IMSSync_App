#!/usr/bin/env python3
"""Test different parameter formats for DataAccess ExecuteDataSet"""

import os
import sys
import logging
from uuid import UUID

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.ims.auth_service import AuthService
from app.services.ims.data_access_service import DataAccessService
from zeep import xsd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_parameter_formats():
    """Test different parameter formats to fix the Key/Value pairs issue"""
    
    # Initialize services
    auth_service = AuthService()
    data_access = DataAccessService(auth_service)
    
    # Test parameters
    procedure_name = "spGetQuoteOptions"
    param_name = "QuoteOptionGuid"
    param_value = "7c5148df-064f-41a1-b732-2d7956b70596"
    
    print("\n" + "="*50)
    print("Testing DataAccess Parameter Formats")
    print("="*50)
    
    # Get token
    token = auth_service.get_token()
    
    # Test 1: Direct dict approach
    print("\n1. Testing direct parameters dict:")
    try:
        # Create the parameters as Zeep expects
        from zeep.helpers import serialize_object
        
        # Create an ArrayOfString manually
        params = data_access.client.get_type('{http://schemas.microsoft.com/2003/10/Serialization/Arrays}ArrayOfstring')
        if params:
            params_obj = params([param_name, param_value])
            print(f"Created ArrayOfstring: {params_obj}")
            
            response = data_access.client.service.ExecuteDataSet(
                procedureName=procedure_name,
                parameters=params_obj,
                _soapheaders=data_access.get_header(token)
            )
            print("SUCCESS!")
            print(f"Response: {response}")
        else:
            print("ArrayOfstring type not found")
    except Exception as e:
        print(f"FAILED: {e}")
    
    # Test 2: Try with different namespace
    print("\n2. Testing with tempuri namespace:")
    try:
        # Try getting type from tempuri namespace
        array_type = data_access.client.get_type('{http://tempuri.org/}ArrayOfString')
        if array_type:
            params_obj = array_type([param_name, param_value])
            print(f"Created ArrayOfString: {params_obj}")
            
            response = data_access.client.service.ExecuteDataSet(
                procedureName=procedure_name,
                parameters=params_obj,
                _soapheaders=data_access.get_header(token)
            )
            print("SUCCESS!")
            print(f"Response: {response}")
        else:
            print("ArrayOfString type not found in tempuri namespace")
    except Exception as e:
        print(f"FAILED: {e}")
    
    # Test 3: Manual construction
    print("\n3. Testing manual array construction:")
    try:
        # Create the structure manually
        ns = {'ns0': 'http://tempuri.org/IMSWebServices/DataAccess'}
        
        # Try creating the parameters structure directly
        from zeep import xsd
        string_array = xsd.ComplexType([
            xsd.Element('{http://tempuri.org/IMSWebServices/DataAccess}string', xsd.String(), min_occurs=0, max_occurs='unbounded')
        ])
        
        params_obj = string_array(string=[param_name, param_value])
        
        response = data_access.client.service.ExecuteDataSet(
            procedureName=procedure_name,
            parameters=params_obj,
            _soapheaders=data_access.get_header(token)
        )
        print("SUCCESS!")
        print(f"Response: {response}")
    except Exception as e:
        print(f"FAILED: {e}")
    
    # Test 4: Inspect what Zeep expects
    print("\n4. Inspecting ExecuteDataSet method signature:")
    try:
        # Get the operation
        operation = data_access.client.service._binding._operations['ExecuteDataSet']
        print(f"Operation name: {operation.name}")
        print(f"Input message: {operation.input}")
        
        # Get the input type
        input_msg = operation.input.body
        print(f"Input body type: {input_msg}")
        
        # Try to get the exact type
        if hasattr(input_msg, 'type'):
            print(f"Parameters type: {input_msg.type}")
    except Exception as e:
        print(f"Could not inspect operation: {e}")

if __name__ == "__main__":
    test_parameter_formats()