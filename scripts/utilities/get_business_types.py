#!/usr/bin/env python3
"""
Get business types from IMS to find valid BusinessTypeIDs
"""

import os
import sys
from dotenv import load_dotenv

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.ims_soap_client import IMSSoapClient
from app.core.config import settings

load_dotenv()

def get_business_types():
    """Get business types from IMS"""
    
    # Get environment configuration
    env = os.getenv("DEFAULT_ENVIRONMENT", "ims_one")
    env_config = settings.IMS_ENVIRONMENTS.get(env)
    
    if not env_config:
        print(f"Unknown environment: {env}")
        return
    
    # Create SOAP client
    soap_client = IMSSoapClient(env_config["config_file"], env_config)
    
    # Login
    print(f"Logging in as {env_config['username']}...")
    token = soap_client.login(env_config["username"], env_config["password"])
    print(f"Login successful! Token: {token}")
    
    # Get business types using ExecuteDataSet
    print("\nGetting business types...")
    
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
            
            # Extract data from the DataSet
            if result:
                print("\nAvailable Business Types:")
                print("-" * 50)
                
                # Parse the XML DataSet result
                import xml.etree.ElementTree as ET
                if isinstance(result, str):
                    root = ET.fromstring(result)
                    
                    # Find all Table elements (rows)
                    for table in root.findall('.//Table'):
                        business_type_id = table.find('BusinessTypeID')
                        business_type_name = table.find('BusinessTypeName')
                        
                        if business_type_id is not None and business_type_name is not None:
                            print(f"ID: {business_type_id.text} - {business_type_name.text}")
                else:
                    print("Unexpected response format")
                    print(result)
        
    except Exception as e:
        print(f"Error getting business types: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    get_business_types()