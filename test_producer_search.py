#!/usr/bin/env python3
"""
Test script to search for producers in IMS
Use this to find actual Producer GUIDs for configuration
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add app directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.ims_soap_client import IMSSoapClient
from app.core.config import settings

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_producer_search():
    """Test producer search functionality"""
    try:
        # Get environment configuration
        env = os.getenv('DEFAULT_ENVIRONMENT', 'iscmga_test')
        env_config = settings.IMS_ENVIRONMENTS.get(env)
        
        if not env_config:
            print(f"❌ Environment '{env}' not found in configuration")
            return False
            
        print(f"🔧 Using environment: {env}")
        print(f"📁 Config file: {env_config['config_file']}")
        print(f"👤 Username: {env_config['username']}")
        
        # Initialize SOAP client
        soap_client = IMSSoapClient(env_config['config_file'])
        
        # Login
        print("\n🔐 Logging in to IMS...")
        token = soap_client.login(env_config['username'], env_config['password'])
        print(f"✅ Login successful! Token: {token[:20]}...")
        
        # Test producer searches
        search_terms = [
            "Ryan Specialty",
            "RSG", 
            "ISCMGA",
            "Allied",
            "Test"
        ]
        
        print(f"\n🔍 Searching for producers...")
        all_producers = []
        
        for search_term in search_terms:
            print(f"\n--- Searching for: '{search_term}' ---")
            
            # Search for producers
            body_content = f"""
            <ProducerSearch xmlns="http://tempuri.org/IMSWebServices/ProducerFunctions">
                <searchString>{search_term}</searchString>
                <startWith>false</startWith>
            </ProducerSearch>
            """
            
            try:
                response = soap_client._make_soap_request(
                    soap_client.producer_functions_url,
                    "http://tempuri.org/IMSWebServices/ProducerFunctions/ProducerSearch",
                    body_content
                )
                
                if response and 'soap:Body' in response:
                    search_response = response['soap:Body'].get('ProducerSearchResponse', {})
                    search_result = search_response.get('ProducerSearchResult', {})
                    
                    if search_result:
                        producer_locations = search_result.get('ProducerLocation', [])
                        
                        # Convert to list if it's a single item
                        if not isinstance(producer_locations, list):
                            producer_locations = [producer_locations]
                        
                        for location in producer_locations:
                            producer_name = location.get('ProducerName', 'Unknown')
                            producer_guid = location.get('ProducerLocationGuid', 'No GUID')
                            location_name = location.get('LocationName', 'Unknown')
                            
                            print(f"  📍 {producer_name} - {location_name}")
                            print(f"     GUID: {producer_guid}")
                            
                            all_producers.append({
                                'name': producer_name,
                                'location': location_name,
                                'guid': producer_guid
                            })
                    else:
                        print(f"  ❌ No producers found for '{search_term}'")
                else:
                    print(f"  ❌ Invalid response for '{search_term}'")
                    
            except Exception as e:
                print(f"  ❌ Error searching for '{search_term}': {str(e)}")
        
        # Summary
        if all_producers:
            print(f"\n📊 Found {len(all_producers)} total producer locations")
            print("\n🔧 Copy these GUIDs to your .env file:")
            print("TRITON_DEFAULT_PRODUCER_GUID=" + all_producers[0]['guid'])
            
            # Show unique producers
            unique_producers = {}
            for p in all_producers:
                if p['name'] not in unique_producers:
                    unique_producers[p['name']] = p['guid']
            
            print(f"\n📋 Available Producers ({len(unique_producers)}):")
            for name, guid in unique_producers.items():
                print(f"  {name}: {guid}")
        else:
            print("\n❌ No producers found. Check your search terms or IMS configuration.")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Testing IMS Producer Search")
    print("=" * 50)
    
    success = test_producer_search()
    
    if success:
        print("\n✅ Producer search test completed successfully")
    else:
        print("\n❌ Producer search test failed")
        sys.exit(1)