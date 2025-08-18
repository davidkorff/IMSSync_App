#!/usr/bin/env python3
"""
Robust test runner that handles environment setup and import issues
"""
import os
import sys
import subprocess
import argparse
import json
from pathlib import Path

def setup_environment():
    """Setup Python environment and paths"""
    # Add current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Set PYTHONPATH environment variable
    os.environ['PYTHONPATH'] = current_dir
    
    # Check for .env file
    env_file = os.path.join(current_dir, '.env')
    if not os.path.exists(env_file):
        env_example = os.path.join(current_dir, '.env.example')
        if os.path.exists(env_example):
            print("Warning: .env file not found. Creating from .env.example...")
            try:
                with open(env_example, 'r') as src, open(env_file, 'w') as dst:
                    dst.write(src.read())
                print("Created .env file - please update with your credentials")
            except Exception as e:
                print(f"Error creating .env file: {e}")
    
    return current_dir

def check_dependencies():
    """Check if required Python packages are installed"""
    required_packages = [
        'dotenv',
        'requests',
        'lxml',
        'zeep',
        'pydantic'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            # Try alternate names
            if package == 'dotenv':
                try:
                    __import__('python-dotenv')
                except ImportError:
                    missing.append('python-dotenv')
            else:
                missing.append(package)
    
    if missing:
        print("\nMissing required packages:")
        for pkg in missing:
            print(f"  - {pkg}")
        print("\nInstall with: pip install -r requirements.txt")
        return False
    
    return True

def run_test_direct(test_name, json_file=None):
    """Run test by importing and calling directly"""
    print(f"\nRunning {test_name} directly...")
    
    try:
        # Dynamically import the test module
        if test_name == "test_3_new_business_bind":
            # Import with proper error handling
            try:
                # First ensure all dependencies are loaded
                import logging
                logging.basicConfig(level=logging.INFO)
                
                # Import base modules first
                import test_bind_workflow_base
                from app.services.transaction_handler import get_transaction_handler
                
                # Now import the test
                from test_3_new_business_bind import test_new_business_bind
                
                # Run the test
                result = test_new_business_bind(json_file=json_file)
                return result.success if hasattr(result, 'success') else False
                
            except ImportError as e:
                print(f"Import error: {e}")
                print("\nTrying subprocess method instead...")
                return False
                
    except Exception as e:
        print(f"Error running test directly: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_test_subprocess(test_script, json_file=None):
    """Run test in a subprocess to avoid import issues"""
    print(f"\nRunning {test_script} in subprocess...")
    
    cmd = [sys.executable, test_script]
    if json_file:
        cmd.extend(['--json', json_file])
    
    # Set up environment
    env = os.environ.copy()
    env['PYTHONPATH'] = os.pathsep.join(sys.path)
    
    try:
        # Run the test
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"Error running subprocess: {e}")
        return False

def validate_json(json_file):
    """Validate JSON file before running tests"""
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        print(f"\n✓ JSON file is valid")
        print(f"  Transaction ID: {data.get('transaction_id', 'NOT SET')}")
        print(f"  Transaction Type: {data.get('transaction_type', 'NOT SET')}")
        print(f"  Opportunity ID: {data.get('opportunity_id', 'NOT SET')}")
        
        # Check for required fields
        required = ['transaction_id', 'transaction_type', 'opportunity_id', 'insured_name']
        missing = [f for f in required if f not in data or data[f] is None]
        
        if missing:
            print(f"\nWarning: Missing required fields: {', '.join(missing)}")
            
        return True
        
    except FileNotFoundError:
        print(f"\n✗ Error: JSON file '{json_file}' not found")
        return False
    except json.JSONDecodeError as e:
        print(f"\n✗ Error: Invalid JSON in file: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Error reading JSON file: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Robust test runner for Triton integration tests')
    parser.add_argument('test', nargs='?', default='test_3_new_business_bind',
                       help='Test to run (default: test_3_new_business_bind)')
    parser.add_argument('--json', '-j', type=str, help='Path to JSON file containing test payload')
    parser.add_argument('--method', '-m', choices=['direct', 'subprocess', 'both'], default='both',
                       help='Method to run test (default: both)')
    parser.add_argument('--check-only', action='store_true', help='Only check environment and JSON')
    
    args = parser.parse_args()
    
    print("="*60)
    print("Triton Integration Test Runner")
    print("="*60)
    
    # Setup environment
    print("\n1. Setting up environment...")
    working_dir = setup_environment()
    print(f"   Working directory: {working_dir}")
    print(f"   Python path: {sys.path[0]}")
    
    # Check dependencies
    print("\n2. Checking dependencies...")
    if not check_dependencies():
        if not args.check_only:
            print("\n✗ Missing dependencies. Please install required packages.")
            return 1
    else:
        print("   ✓ All dependencies found")
    
    # Validate JSON if provided
    if args.json:
        print("\n3. Validating JSON file...")
        if not validate_json(args.json):
            return 1
    
    if args.check_only:
        print("\n✓ Environment check complete")
        return 0
    
    # Run the test
    print(f"\n4. Running test: {args.test}")
    
    success = False
    
    if args.method in ['direct', 'both']:
        # Try direct method
        if args.test.endswith('.py'):
            test_name = args.test[:-3]
        else:
            test_name = args.test
            
        success = run_test_direct(test_name, args.json)
    
    if not success and args.method in ['subprocess', 'both']:
        # Try subprocess method
        test_script = args.test if args.test.endswith('.py') else f"{args.test}.py"
        success = run_test_subprocess(test_script, args.json)
    
    # Summary
    print("\n" + "="*60)
    if success:
        print("✓ TEST COMPLETED SUCCESSFULLY")
    else:
        print("✗ TEST FAILED OR COULD NOT RUN")
    print("="*60)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())