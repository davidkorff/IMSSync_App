#!/usr/bin/env python
"""
Run IMS Integration - Main script to run the IMS policy data integration

Usage:
    python run_ims_integration.py --env=iscmga_test --source=csv --file=BDX_Samples/Bound\ Policies\ report\ 4.25.25.csv
    python run_ims_integration.py --env=iscmga_test --source=tritan --config=tritan_config.json
"""
import os
import sys
import json
import argparse
from datetime import datetime
import config
from ims_integration import IMSIntegration
from data_gatherers import list_gatherers


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(description='IMS Policy Data Integration')
    
    # Environment selection
    parser.add_argument('--env', required=False, default='iscmga_test',
                        choices=list(config.ENVIRONMENTS.keys()),
                        help='Environment to use for the integration')
    
    # Source selection
    parser.add_argument('--source', required=True,
                        choices=list(list_gatherers().keys()),
                        help='Source system to gather data from')
    
    # CSV source specific arguments
    parser.add_argument('--file', required=False,
                        help='Path to the CSV file (required for CSV source)')
    
    # API source specific arguments
    parser.add_argument('--config', required=False,
                        help='Path to source system configuration file (required for API sources)')
    
    # Filter options
    parser.add_argument('--start-date', required=False,
                        help='Start date for policy search (YYYY-MM-DD)')
    
    parser.add_argument('--end-date', required=False,
                        help='End date for policy search (YYYY-MM-DD)')
    
    parser.add_argument('--policy-number', required=False,
                        help='Specific policy number to retrieve')
    
    # Output options
    parser.add_argument('--output', required=False,
                        default='ims_integration_results.json',
                        help='Path to the output JSON file for results')
    
    # Debug options
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')
    
    parser.add_argument('--limit', type=int, default=0,
                        help='Limit the number of policies to process (0 = no limit)')
    
    return parser.parse_args()


def validate_args(args):
    """Validate command-line arguments"""
    errors = []
    
    # Validate source-specific requirements
    if args.source == 'csv':
        if not args.file:
            errors.append("--file is required for CSV source")
        elif not os.path.exists(args.file):
            errors.append(f"File {args.file} does not exist")
    elif args.source in ['tritan', 'xuber']:
        if not args.config:
            errors.append(f"--config is required for {args.source} source")
        elif not os.path.exists(args.config):
            errors.append(f"Config file {args.config} does not exist")
    
    return errors


def main():
    """Main function to run the integration"""
    args = parse_args()
    
    # Validate arguments
    errors = validate_args(args)
    if errors:
        for error in errors:
            print(f"Error: {error}")
        return 1
    
    # Initialize the IMS integration
    ims = IMSIntegration(env=args.env)
    
    # Set debug logging if requested
    if args.debug:
        import logging
        ims.logger.setLevel(logging.DEBUG)
    
    # Prepare filters
    filters = {}
    if args.start_date:
        filters['start_date'] = args.start_date
    if args.end_date:
        filters['end_date'] = args.end_date
    if args.policy_number:
        filters['policy_number'] = args.policy_number
    if args.limit and args.limit > 0:
        filters['limit'] = args.limit
    
    # Record start time
    start_time = datetime.now()
    print(f"Starting IMS integration at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Environment: {args.env}")
    print(f"Source: {args.source}")
    
    try:
        # Process policies from the specified source
        if args.source == 'csv':
            results = ims.process_policies_from_csv(args.file, filters)
        elif args.source == 'tritan':
            # Load Tritan configuration
            with open(args.config, 'r') as f:
                tritan_config = json.load(f)
            results = ims.process_policies_from_tritan(tritan_config, filters)
        else:
            print(f"Error: Source {args.source} not implemented yet")
            return 1
        
        # Record end time
        end_time = datetime.now()
        elapsed_time = end_time - start_time
        
        # Add timing information to results
        results['timing'] = {
            'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'elapsed_seconds': elapsed_time.total_seconds()
        }
        
        # Add run information to results
        results['run_info'] = {
            'environment': args.env,
            'source': args.source,
            'filters': filters
        }
        
        # Write results to JSON file
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        if results.get('success', False):
            print(f"\nCompleted processing {results['total']} policies")
            print(f"Succeeded: {results['succeeded']}, Failed: {results['failed']}")
            print(f"Elapsed time: {elapsed_time}")
            print(f"Results written to {args.output}")
            return 0
        else:
            print(f"\nError: {results.get('error', 'Unknown error')}")
            return 1
            
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 