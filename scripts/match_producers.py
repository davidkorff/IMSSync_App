#!/usr/bin/env python
"""
Match Producers - Script to match producers between source systems and IMS
"""
import os
import sys
import json
import csv
import argparse
import logging
from datetime import datetime

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from producer_matcher import ProducerMatcher


def setup_logger():
    """Set up logging for the script"""
    logger = logging.getLogger('match_producers')
    logger.setLevel(logging.INFO)
    
    # Create handlers
    file_handler = logging.FileHandler('match_producers.log')
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
    parser = argparse.ArgumentParser(description='Match Producers Between Source Systems and IMS')
    
    parser.add_argument('--ims-producers', required=True,
                       help='Path to IMS producers CSV file')
    
    parser.add_argument('--source-producers', required=True,
                       help='Path to source system producers CSV file')
    
    parser.add_argument('--source-system', required=True,
                       help='Name of the source system (e.g., tritan)')
    
    parser.add_argument('--output', required=False, default='producer_matches.csv',
                       help='Output CSV file path')
    
    parser.add_argument('--config', required=False,
                       help='Path to ProducerMatcher configuration file')
    
    parser.add_argument('--interactive', action='store_true',
                       help='Enable interactive matching')
    
    parser.add_argument('--threshold', type=int, required=False, default=80,
                       help='Match threshold (0-100)')
    
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    
    return parser.parse_args()


def load_producers_from_csv(csv_path):
    """
    Load producers from a CSV file
    
    Args:
        csv_path: Path to the CSV file
        
    Returns:
        list: List of producers, each as a dictionary
    """
    producers = []
    try:
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                producers.append(row)
        return producers
    except Exception as e:
        logging.getLogger('match_producers').error(f"Error loading producers from CSV: {e}")
        return []


def save_matches_to_csv(matches, output_file):
    """
    Save producer matches to a CSV file
    
    Args:
        matches: Dictionary mapping source producer names to IMS producer GUIDs
        output_file: Output file path
    """
    logger = logging.getLogger('match_producers')
    
    try:
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Source Producer', 'IMS Producer GUID'])
            for source_name, ims_guid in matches.items():
                writer.writerow([source_name, ims_guid])
        
        logger.info(f"Saved {len(matches)} producer matches to {output_file}")
    except Exception as e:
        logger.error(f"Error saving producer matches to CSV: {e}")


def main():
    """Main function"""
    args = parse_args()
    
    # Set up logging
    logger = setup_logger()
    
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    # Load producers
    logger.info(f"Loading IMS producers from {args.ims_producers}")
    ims_producers = load_producers_from_csv(args.ims_producers)
    
    logger.info(f"Loading {args.source_system} producers from {args.source_producers}")
    source_producers = load_producers_from_csv(args.source_producers)
    
    if not ims_producers:
        logger.error("No IMS producers loaded. Aborting.")
        return 1
        
    if not source_producers:
        logger.error(f"No {args.source_system} producers loaded. Aborting.")
        return 1
    
    # Create producer matcher
    matcher = ProducerMatcher(args.config)
    
    # Set match threshold if specified
    if args.threshold:
        matcher.match_threshold = args.threshold
    
    # Load IMS producers
    matcher.load_ims_producers(ims_producers)
    
    # Match producers
    logger.info(f"Matching {len(source_producers)} {args.source_system} producers to IMS producers")
    matches = matcher.batch_match_producers(source_producers, args.source_system, args.interactive)
    
    # Save matches to CSV
    save_matches_to_csv(matches, args.output)
    
    # Print summary
    match_count = len(matches)
    total_count = len(source_producers)
    match_percentage = (match_count / total_count * 100) if total_count > 0 else 0
    
    print(f"\nMatching Results:")
    print(f"Matched {match_count} of {total_count} producers ({match_percentage:.1f}%)")
    print(f"Results written to {args.output}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 