#!/usr/bin/env python
"""
Extract Tritan Producers - Script to extract producer information from Tritan
"""
import os
import sys
import json
import csv
import argparse
import logging
from datetime import datetime
import requests

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data_gatherers.tritan_gatherer import TritanDataGatherer


def setup_logger():
    """Set up logging for the script"""
    logger = logging.getLogger('extract_tritan_producers')
    logger.setLevel(logging.INFO)
    
    # Create handlers
    file_handler = logging.FileHandler('extract_tritan_producers.log')
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
    parser = argparse.ArgumentParser(description='Extract Producer Information from Tritan')
    
    parser.add_argument('--config', required=True,
                       help='Path to Tritan configuration file')
    
    parser.add_argument('--output', required=False, default='tritan_producers.csv',
                       help='Output CSV file path')
    
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    
    return parser.parse_args()


def get_tritan_producers(config_path):
    """
    Get all producers from Tritan
    
    Args:
        config_path: Path to Tritan configuration file
        
    Returns:
        list: List of producers, each as a dictionary with 'name' and other keys
    """
    logger = logging.getLogger('extract_tritan_producers')
    logger.info("Retrieving producers from Tritan")
    
    # Load configuration
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return []
    
    # Initialize Tritan data gatherer
    try:
        gatherer = TritanDataGatherer(config)
    except Exception as e:
        logger.error(f"Error initializing Tritan data gatherer: {e}")
        return []
    
    # Connect to Tritan
    if not gatherer.connect():
        logger.error("Failed to connect to Tritan. Aborting.")
        return []
    
    producers = []
    
    try:
        # TODO: Implement actual Tritan API call to retrieve producers
        # This is a placeholder for the actual API call
        
        # For now, return sample producers
        producers = [
            {
                "name": "ABC Insurance Agency",
                "code": "ABC001",
                "agency": "ABC Insurance",
                "contact": "John Doe",
                "email": "john.doe@abcinsurance.com"
            },
            {
                "name": "XYZ Insurance Brokers",
                "code": "XYZ002",
                "agency": "XYZ Brokers Inc.",
                "contact": "Jane Smith",
                "email": "jane.smith@xyzbrokers.com"
            },
            {
                "name": "Smith, John - Insurance Agency",
                "code": "SJA003",
                "agency": "John Smith Insurance",
                "contact": "John Smith",
                "email": "john@smithinsurance.com"
            }
        ]
        
        logger.info(f"Retrieved {len(producers)} producers from Tritan")
        
    except Exception as e:
        logger.error(f"Error retrieving producers from Tritan: {e}")
    finally:
        # Disconnect from Tritan
        gatherer.disconnect()
    
    return producers


def save_to_csv(producers, output_file):
    """
    Save producers to a CSV file
    
    Args:
        producers: List of producers
        output_file: Output file path
    """
    logger = logging.getLogger('extract_tritan_producers')
    
    try:
        if not producers:
            logger.error("No producers to save")
            return
            
        # Get all possible keys from all producers
        fieldnames = set()
        for producer in producers:
            fieldnames.update(producer.keys())
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(fieldnames))
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
    
    # Get producers
    producers = get_tritan_producers(args.config)
    
    # Save to CSV
    if producers:
        save_to_csv(producers, args.output)
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 