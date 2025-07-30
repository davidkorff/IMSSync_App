#!/usr/bin/env python3
"""
Test script to list available IMS operations
"""

from zeep import Client
from config import IMS_CONFIG

def list_operations(service_name, endpoint):
    """List all operations available in a service"""
    try:
        wsdl_url = f"{IMS_CONFIG['base_url']}{endpoint}?wsdl"
        client = Client(wsdl_url)
        
        print(f"\n{service_name} Operations:")
        print("=" * 50)
        
        # Get all operations
        for service in client.wsdl.services.values():
            for port in service.ports.values():
                operations = sorted(port.binding.all_operations.keys())
                for op in operations:
                    print(f"  - {op}")
        
        return operations
    except Exception as e:
        print(f"Error accessing {service_name}: {e}")
        return []

if __name__ == "__main__":
    print("IMS Available Operations")
    print("=" * 50)
    
    # Check each service
    services = [
        ("Logon", IMS_CONFIG["endpoints"]["logon"]),
        ("InsuredFunctions", IMS_CONFIG["endpoints"]["insured_functions"]),
        ("QuoteFunctions", IMS_CONFIG["endpoints"]["quote_functions"]),
    ]
    
    for service_name, endpoint in services:
        list_operations(service_name, endpoint)