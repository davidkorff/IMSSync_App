#!/usr/bin/env python
"""
Extract IMS Producers - Script to extract producer information from IMS
"""
import os
import sys
import json
import csv
import argparse
import logging
from datetime import datetime
import xml.etree.ElementTree as ET
import requests

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import config
from ims_soap_client import IMSSoapClient
from ims_integration import IMSIntegration


def setup_logger():
    """Set up logging for the script"""
    logger = logging.getLogger('extract_ims_producers')
    logger.setLevel(logging.INFO)
    
    # Create handlers
    file_handler = logging.FileHandler('extract_ims_producers.log')
    console_handler = logging.StreamHandler()
    
    # Create formatters and add to handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description='Extract Producer Information from IMS')
    
    parser.add_argument('--env', required=False, default='iscmga_test',
                       choices=list(config.ENVIRONMENTS.keys()),
                       help='Environment to use for the extraction')
    
    parser.add_argument('--output', required=False, default='ims_producers.csv',
                       help='Output CSV file path')
    
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    
    return parser.parse_args()


def get_producers(ims: IMSIntegration):
    """
    Get all producers from IMS
    
    Args:
        ims: IMS integration instance
        
    Returns:
        list: List of producers, each as a dictionary with 'guid' and 'name' keys
    """
    logger = logging.getLogger('extract_ims_producers')
    logger.info("Retrieving producers from IMS")
    
    # Login to IMS
    if not ims.login():
        logger.error("Failed to login to IMS. Aborting.")
        return []
    
    # Build SOAP request for GetProducers
    soap_envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Header>
    <TokenHeader xmlns="http://tempuri.org/IMSWebServices/ContactFunctions">
      <Token>{ims.soap_client.token}</Token>
      <Context></Context>
    </TokenHeader>
  </soap:Header>
  <soap:Body>
    <GetProducerList xmlns="http://tempuri.org/IMSWebServices/ContactFunctions" />
  </soap:Body>
</soap:Envelope>"""
    
    headers = {
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': 'http://tempuri.org/IMSWebServices/ContactFunctions/GetProducerList'
    }
    
    try:
        # Construct contact functions URL from logon URL
        contact_functions_url = ims.urls.get('logon').replace('logon.asmx', 'contactfunctions.asmx')
        
        response = requests.post(contact_functions_url, data=soap_envelope, headers=headers)
        
        if response.status_code == 200:
            # Parse the XML response
            root = ET.fromstring(response.content)
            
            # Define namespaces for XPath queries
            namespaces = {
                'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                'ims': 'http://tempuri.org/IMSWebServices/ContactFunctions'
            }
            
            # Extract producers from the response
            producers = []
            
            # Adjust this XPath based on the actual response structure
            producer_nodes = root.findall('.//ims:GetProducerListResult/ims:Producer', namespaces)
            
            for producer_node in producer_nodes:
                guid_node = producer_node.find('ims:ProducerGuid', namespaces)
                name_node = producer_node.find('ims:Name', namespaces)
                
                if guid_node is not None and name_node is not None:
                    producers.append({
                        'guid': guid_node.text,
                        'name': name_node.text
                    })
            
            logger.info(f"Retrieved {len(producers)} producers from IMS")
            return producers
        else:
            logger.error(f"Failed to retrieve producers: {response.status_code}")
            return []
    
    except Exception as e:
        logger.error(f"Error retrieving producers: {e}")
        return []


def save_to_csv(producers, output_file):
    """
    Save producers to a CSV file
    
    Args:
        producers: List of producers
        output_file: Output file path
    """
    logger = logging.getLogger('extract_ims_producers')
    
    try:
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['guid', 'name'])
            writer.writeheader()
            writer.writerows(producers)
        
        logger.info(f"Saved {len(producers)} producers to {output_file}")
    except Exception as e:
        logger.error(f"Error saving producers to CSV: {e}")


def main():
    """Main function"""
    args = parse_args()
    
    # Set up logging
    logger = setup_logger()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    # Initialize IMS integration
    ims = IMSIntegration(env=args.env)
    
    # Get producers
    producers = get_producers(ims)
    
    # Save to CSV
    if producers:
        save_to_csv(producers, args.output)
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 