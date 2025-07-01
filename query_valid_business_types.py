#!/usr/bin/env python3
"""
Query valid BusinessTypeIDs from IMS using GetInsuredBusinessTypes API
"""

import os
import sys
import xml.etree.ElementTree as ET

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.ims_soap_client import IMSSoapClient
from app.core.config import settings

# Try to load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed, using system environment variables only")

def query_business_types():
    """Query business types from IMS using GetInsuredBusinessTypes"""
    
    # Get environment configuration
    env = os.getenv("DEFAULT_ENVIRONMENT", "ims_one")
    env_config = settings.IMS_ENVIRONMENTS.get(env)
    
    if not env_config:
        print(f"Unknown environment: {env}")
        return
    
    # Create SOAP client
    soap_client = IMSSoapClient(env_config["config_file"], env_config)
    
    # Login
    print(f"Logging in to {env} as {env_config['username']}...")
    try:
        token = soap_client.login(env_config["username"], env_config["password"])
        print(f"Login successful! Token: {token}")
    except Exception as e:
        print(f"Login failed: {str(e)}")
        return
    
    # Call GetInsuredBusinessTypes
    print("\nQuerying business types using GetInsuredBusinessTypes...")
    
    body_content = """
    <GetInsuredBusinessTypes xmlns="http://tempuri.org/IMSWebServices/InsuredFunctions" />
    """
    
    try:
        response = soap_client._make_soap_request(
            soap_client.insured_url,
            "http://tempuri.org/IMSWebServices/InsuredFunctions/GetInsuredBusinessTypes",
            body_content
        )
        
        if response and 'soap:Body' in response:
            types_response = response['soap:Body'].get('GetInsuredBusinessTypesResponse', {})
            result = types_response.get('GetInsuredBusinessTypesResult')
            
            if result:
                print("\nAvailable Business Types:")
                print("-" * 60)
                print(f"{'ID':<10} {'Business Type Name':<40}")
                print("-" * 60)
                
                # Parse the XML result
                try:
                    # The result is typically a DataTable in XML format
                    root = ET.fromstring(result)
                    
                    # Find all rows in the DataTable
                    for row in root.findall('.//Table'):
                        business_type_id = row.find('BusinessTypeID')
                        business_type_name = row.find('BusinessTypeName')
                        
                        if business_type_id is not None and business_type_name is not None:
                            print(f"{business_type_id.text:<10} {business_type_name.text:<40}")
                    
                    print("-" * 60)
                    print("\nNote: The error shows BusinessTypeID 13 doesn't exist.")
                    print("Update the mapping in flat_transformer.py to use a valid ID from above.")
                    
                except Exception as e:
                    print(f"Error parsing XML result: {str(e)}")
                    print(f"Raw result: {result}")
            else:
                print("No result returned from GetInsuredBusinessTypes")
        
    except Exception as e:
        print(f"Error querying business types: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Also try ExecuteDataSet as an alternative
    print("\n\nAlternatively, querying lstBusinessTypes table directly...")
    
    sql_query = "SELECT BusinessTypeID, BusinessTypeName FROM lstBusinessTypes ORDER BY BusinessTypeID"
    
    body_content = f"""
    <ExecuteDataSet xmlns="http://tempuri.org/IMSWebServices/DataAccess">
        <strSQLStatement>{sql_query}</strSQLStatement>
    </ExecuteDataSet>
    """
    
    try:
        response = soap_client._make_soap_request(
            soap_client.data_access_url,
            "http://tempuri.org/IMSWebServices/DataAccess/ExecuteDataSet",
            body_content
        )
        
        if response and 'soap:Body' in response:
            exec_response = response['soap:Body'].get('ExecuteDataSetResponse', {})
            result = exec_response.get('ExecuteDataSetResult', {})
            
            if result:
                print("\nBusiness Types from lstBusinessTypes table:")
                print("-" * 60)
                print(f"{'ID':<10} {'Business Type Name':<40}")
                print("-" * 60)
                
                # Parse the XML DataSet result
                try:
                    root = ET.fromstring(result)
                    
                    # Find all Table elements (rows)
                    for table in root.findall('.//Table'):
                        business_type_id = table.find('BusinessTypeID')
                        business_type_name = table.find('BusinessTypeName')
                        
                        if business_type_id is not None and business_type_name is not None:
                            print(f"{business_type_id.text:<10} {business_type_name.text:<40}")
                    
                    print("-" * 60)
                    
                except Exception as e:
                    print(f"Error parsing DataSet result: {str(e)}")
                    print(f"Raw result: {result}")
        
    except Exception as e:
        print(f"Error with ExecuteDataSet: {str(e)}")

if __name__ == "__main__":
    query_business_types()