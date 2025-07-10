#!/usr/bin/env python3
"""
Test runner for Triton-IMS integration
Run this from the project root
"""

import os
import sys
import subprocess


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(text.center(60))
    print("=" * 60 + "\n")


def main():
    """Main test runner"""
    print_header("TRITON-IMS INTEGRATION TEST RUNNER")
    
    # Check if server is running
    import requests
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=2)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("⚠️  Server is running but health check failed")
    except:
        print("❌ Server is not running!")
        print("\nPlease start the server first:")
        print("  uvicorn app.main:app --reload")
        return 1
    
    # Available tests
    print("\nAvailable tests:")
    print("1. Quick test with TEST.json (recommended)")
    print("2. Architecture demonstration")
    print("3. Full integration test suite")
    print("4. Exit")
    
    choice = input("\nSelect test to run (1-4): ").strip()
    
    if choice == "1":
        print_header("RUNNING TEST WITH TEST.JSON")
        os.chdir("tests")
        result = subprocess.run([sys.executable, "test_with_test_json.py"])
        return result.returncode
        
    elif choice == "2":
        print_header("ARCHITECTURE DEMONSTRATION")
        result = subprocess.run([sys.executable, "test_simplified_flow.py"])
        return result.returncode
        
    elif choice == "3":
        print_header("FULL INTEGRATION TEST SUITE")
        os.chdir("tests")
        result = subprocess.run([sys.executable, "integration/test_triton_binding.py"])
        return result.returncode
        
    elif choice == "4":
        print("Exiting...")
        return 0
        
    else:
        print("Invalid choice")
        return 1


if __name__ == "__main__":
    sys.exit(main())