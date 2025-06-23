#!/usr/bin/env python3
"""
Test runner for IMS Services

This script runs all IMS service tests with proper configuration and reporting.
"""

import os
import sys
import unittest
import argparse
import logging
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))


def setup_logging(verbose=False):
    """Set up logging configuration"""
    log_level = logging.DEBUG if verbose else logging.INFO
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Create logs directory
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Log file name with timestamp
    log_file = os.path.join(log_dir, f'test_run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return log_file


def get_test_modules():
    """Get list of test modules"""
    return [
        'test_authentication',
        'test_insured_service',
        'test_producer_service',
        'test_quote_service',
        'test_document_service',
        'test_data_access_service',
        'test_workflow_orchestrator'
    ]


def run_specific_test(test_name, verbose=False):
    """Run a specific test module or test case"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Check if it's a module name
    if test_name in get_test_modules():
        module = __import__(test_name)
        suite.addTests(loader.loadTestsFromModule(module))
    else:
        # Try to load as a specific test case
        parts = test_name.split('.')
        if len(parts) >= 2:
            module_name = parts[0]
            test_case = '.'.join(parts[1:])
            module = __import__(module_name)
            suite.addTests(loader.loadTestsFromName(test_case, module))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def run_all_tests(verbose=False, pattern=None):
    """Run all tests or tests matching pattern"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Get test modules
    modules = get_test_modules()
    
    # Filter by pattern if provided
    if pattern:
        modules = [m for m in modules if pattern in m]
    
    # Load tests
    for module_name in modules:
        try:
            module = __import__(module_name)
            suite.addTests(loader.loadTestsFromModule(module))
        except Exception as e:
            print(f"Error loading module {module_name}: {str(e)}")
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def print_available_tests():
    """Print available test modules and their test cases"""
    print("\nAvailable Test Modules:")
    print("=" * 50)
    
    for module_name in get_test_modules():
        print(f"\n{module_name}:")
        try:
            module = __import__(module_name)
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromModule(module)
            
            # Extract test cases
            for test_group in suite:
                if hasattr(test_group, '__iter__'):
                    for test_case in test_group:
                        test_class = test_case.__class__.__name__
                        test_method = test_case._testMethodName
                        print(f"  - {test_class}.{test_method}")
        except Exception as e:
            print(f"  Error loading module: {str(e)}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Run IMS Service Tests')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose output')
    parser.add_argument('-l', '--list', action='store_true',
                        help='List available tests')
    parser.add_argument('-t', '--test', type=str,
                        help='Run specific test module or test case')
    parser.add_argument('-p', '--pattern', type=str,
                        help='Run tests matching pattern')
    parser.add_argument('-e', '--env', type=str, default='ims_one',
                        choices=['ims_one', 'iscmga_test'],
                        help='IMS environment to test against')
    parser.add_argument('--skip-binding', action='store_true',
                        help='Skip binding/issuance tests')
    parser.add_argument('--skip-excel', action='store_true',
                        help='Skip Excel rater tests')
    
    args = parser.parse_args()
    
    # Set environment
    os.environ['IMS_TEST_ENV'] = args.env
    
    # Set skip flags
    if args.skip_binding:
        os.environ['SKIP_BINDING_TESTS'] = 'true'
    if args.skip_excel:
        os.environ['SKIP_EXCEL_TESTS'] = 'true'
    
    # List tests if requested
    if args.list:
        print_available_tests()
        return 0
    
    # Setup logging
    log_file = setup_logging(args.verbose)
    print(f"\nTest log file: {log_file}")
    print(f"Testing against environment: {args.env}")
    print("=" * 60)
    
    # Run tests
    success = False
    
    try:
        if args.test:
            # Run specific test
            print(f"\nRunning test: {args.test}")
            success = run_specific_test(args.test, args.verbose)
        else:
            # Run all tests or pattern
            if args.pattern:
                print(f"\nRunning tests matching: {args.pattern}")
            else:
                print("\nRunning all tests")
            success = run_all_tests(args.verbose, args.pattern)
    
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\nError running tests: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Print summary
    print("\n" + "=" * 60)
    if success:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        print(f"Check log file for details: {log_file}")
        return 1


if __name__ == "__main__":
    sys.exit(main())