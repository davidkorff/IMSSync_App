#!/usr/bin/env python3
"""
Test script to verify IMS login and configuration
Run this first to ensure IMS connectivity works
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

def test_ims_login():
    """Test IMS login functionality"""
    try:
        # Get environment configuration
        env = os.getenv('DEFAULT_ENVIRONMENT', 'iscmga_test')
        env_config = settings.IMS_ENVIRONMENTS.get(env)
        
        if not env_config:
            print(f"❌ Environment '{env}' not found in configuration")
            print(f"Available environments: {list(settings.IMS_ENVIRONMENTS.keys())}")
            return False
            
        print(f"🔧 Using environment: {env}")
        print(f"📁 Config file: {env_config['config_file']}")
        print(f"👤 Username: {env_config['username']}")
        
        # Check if config file exists
        config_path = os.path.join("IMS_Configs", env_config['config_file'])
        if not os.path.exists(config_path):
            print(f"❌ Config file not found: {config_path}")
            print("Available config files:")
            config_dir = "IMS_Configs"
            if os.path.exists(config_dir):
                for file in os.listdir(config_dir):
                    print(f"  - {file}")
            return False
        else:
            print(f"✅ Config file found: {config_path}")
        
        # Initialize SOAP client
        print("\n🔌 Initializing SOAP client...")
        soap_client = IMSSoapClient(env_config['config_file'])
        
        print(f"🌐 Logon URL: {soap_client.logon_url}")
        print(f"🌐 Quote Functions URL: {soap_client.quote_functions_url}")
        print(f"🌐 Insured Functions URL: {soap_client.insured_functions_url}")
        print(f"🌐 Producer Functions URL: {soap_client.producer_functions_url}")
        
        # Test login
        print("\n🔐 Testing login...")
        token = soap_client.login(env_config['username'], env_config['password'])
        
        if token:
            print(f"✅ Login successful!")
            print(f"🎫 Token: {token[:20]}...")
            print(f"🎫 Full token length: {len(token)} characters")
            return True
        else:
            print("❌ Login failed - no token received")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        print("Full error details:")
        traceback.print_exc()
        return False

def test_basic_connectivity():
    """Test basic network connectivity to IMS endpoints"""
    import requests
    
    try:
        # Test environments
        environments = ['iscmga_test', 'ims_one']
        
        for env in environments:
            env_config = settings.IMS_ENVIRONMENTS.get(env)
            if not env_config:
                continue
                
            print(f"\n🌐 Testing connectivity to {env}...")
            
            # Try to initialize client and get URLs
            soap_client = IMSSoapClient(env_config['config_file'])
            
            # Test logon URL
            try:
                response = requests.get(soap_client.logon_url + "?WSDL", timeout=10)
                if response.status_code == 200:
                    print(f"  ✅ Logon endpoint accessible")
                else:
                    print(f"  ❌ Logon endpoint returned {response.status_code}")
            except Exception as e:
                print(f"  ❌ Logon endpoint unreachable: {str(e)}")
                
    except Exception as e:
        print(f"❌ Connectivity test error: {str(e)}")

if __name__ == "__main__":
    print("🧪 Testing IMS Login and Configuration")
    print("=" * 50)
    
    # Test basic connectivity first
    test_basic_connectivity()
    
    print("\n" + "=" * 50)
    
    # Test login
    success = test_ims_login()
    
    if success:
        print("\n✅ IMS login test completed successfully")
        print("\n🔄 Next steps:")
        print("1. Run: python test_producer_search.py")
        print("2. Update .env with real Producer GUIDs")
        print("3. Run: python run_mysql_polling.py")
    else:
        print("\n❌ IMS login test failed")
        print("\n🔧 Troubleshooting:")
        print("1. Check your .env file configuration")
        print("2. Verify IMS config files exist in IMS_Configs/")
        print("3. Confirm network access to IMS endpoints")
        print("4. Validate username/password credentials")
        sys.exit(1)