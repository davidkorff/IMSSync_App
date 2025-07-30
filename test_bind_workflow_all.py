"""
Run all bind workflow tests
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from test_1_store_transaction import test_store_transaction
from test_2_rebind_detection import test_rebind_detection
from test_3_new_business_bind import test_new_business_bind
from test_4_renewal_bind import test_renewal_bind
from test_bind_workflow_base import save_test_results
from datetime import datetime

def run_all_tests():
    """Run all bind workflow tests"""
    print(f"\n{'='*80}")
    print("BIND WORKFLOW TEST SUITE")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    all_results = {
        "suite_name": "Bind Workflow Tests",
        "start_time": datetime.now().isoformat(),
        "tests": []
    }
    
    # Define tests to run
    tests = [
        ("Store Transaction Data", test_store_transaction),
        ("Rebind Detection", test_rebind_detection),
        ("New Business Bind", test_new_business_bind),
        ("Renewal Bind", test_renewal_bind)
    ]
    
    total_tests = len(tests)
    passed_tests = 0
    
    # Run each test
    for i, (test_name, test_func) in enumerate(tests, 1):
        print(f"\n{'='*80}")
        print(f"Running Test {i}/{total_tests}: {test_name}")
        print(f"{'='*80}\n")
        
        try:
            test_result = test_func()
            summary = test_result.get_summary()
            all_results["tests"].append(summary)
            
            if test_result.success:
                passed_tests += 1
                print(f"\n✓ Test PASSED: {test_name}")
            else:
                print(f"\n✗ Test FAILED: {test_name}")
                if test_result.errors:
                    print("Errors:")
                    for error in test_result.errors:
                        print(f"  - {error}")
                        
        except Exception as e:
            print(f"\n✗ Test CRASHED: {test_name}")
            print(f"Exception: {str(e)}")
            all_results["tests"].append({
                "test_name": test_name,
                "success": False,
                "error": f"Test crashed: {str(e)}",
                "crashed": True
            })
    
    # Summary
    all_results["end_time"] = datetime.now().isoformat()
    all_results["total_tests"] = total_tests
    all_results["passed_tests"] = passed_tests
    all_results["failed_tests"] = total_tests - passed_tests
    all_results["success_rate"] = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n{'='*80}")
    print("TEST SUITE SUMMARY")
    print(f"{'='*80}")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {all_results['success_rate']:.1f}%")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    # Save comprehensive results
    save_test_results("all_bind_workflow_tests", all_results)
    
    return all_results

if __name__ == "__main__":
    run_all_tests()