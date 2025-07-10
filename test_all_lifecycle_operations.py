"""
Test runner for all policy lifecycle operations
Run this to test cancellation, endorsement, and reinstatement workflows
"""

import subprocess
import sys
import time

def run_test(test_file, description):
    """Run a test file and display results"""
    print("\n" + "=" * 70)
    print(f"Running: {description}")
    print("=" * 70)
    
    try:
        # Run the test file
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True
        )
        
        # Display output
        print(result.stdout)
        
        if result.stderr:
            print("ERRORS:")
            print(result.stderr)
            
        if result.returncode != 0:
            print(f"Test failed with return code: {result.returncode}")
            
    except Exception as e:
        print(f"Error running test: {str(e)}")
    
    # Pause between tests
    time.sleep(2)

def main():
    """Run all lifecycle tests"""
    print("Policy Lifecycle Operations Test Suite")
    print("=" * 70)
    print("This will test all policy lifecycle operations:")
    print("- Cancellation")
    print("- Endorsement")
    print("- Reinstatement")
    print("- Complete Lifecycle (New -> Endorse -> Cancel -> Reinstate)")
    
    # Make sure the API server is running
    print("\nIMPORTANT: Make sure the FastAPI server is running on http://localhost:8000")
    print("Run: uvicorn app.main:app --reload")
    input("\nPress Enter to continue...")
    
    # Run individual tests
    tests = [
        ("test_cancellation_flow.py", "Policy Cancellation Test"),
        ("test_endorsement_flow.py", "Policy Endorsement Test"),
        ("test_reinstatement_flow.py", "Policy Reinstatement Test"),
        ("test_policy_lifecycle.py", "Complete Policy Lifecycle Test")
    ]
    
    for test_file, description in tests:
        run_test(test_file, description)
    
    print("\n" + "=" * 70)
    print("All tests completed!")
    print("=" * 70)

if __name__ == "__main__":
    main()