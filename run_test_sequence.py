#!/usr/bin/env python3
"""
Test Sequence Runner
Runs a sequence of tests with generated payloads in the appropriate order.

Usage:
    python run_test_sequence.py <test_number> <steps>
    
    test_number: The number prefix for test files (e.g., 20 for test20bind.json)
    steps: Number of steps to execute (1-7)
           1 = Step 3 only (bind)
           2 = Steps 3,6 (bind, unbind)
           3 = Steps 3,6,3 (bind, unbind, bind2)
           4 = Steps 3,6,3,5 (bind, unbind, bind2, issue)
           5 = Steps 3,6,3,5,7 (bind, unbind, bind2, issue, endorsement)
           6 = Steps 3,6,3,5,7,8 (bind, unbind, bind2, issue, endorsement, cancel)
           7 = Steps 3,6,3,5,7,8,9 (all steps including reinstatement)

Example:
    python run_test_sequence.py 20 3  # Run first 3 steps with test20*.json files
    python run_test_sequence.py 20 7  # Run all steps with test20*.json files
"""

import sys
import os
import subprocess
import json
import time
from datetime import datetime
from typing import List, Tuple, Dict, Any

class TestSequenceRunner:
    """Manages the execution of test sequences"""
    
    def __init__(self, test_number: int, max_steps: int):
        """
        Initialize the test runner
        
        Args:
            test_number: The number prefix for test files
            max_steps: Maximum number of steps to execute (1-7)
        """
        self.test_number = test_number
        self.max_steps = max_steps
        self.results = []
        self.start_time = None
        
        # Define the test sequence
        self.test_sequence = [
            ('bind', 'test_3_new_business_bind_v2.py', f'test{test_number}bind.json'),
            ('unbind', 'test_6_unbind_policy.py', f'test{test_number}unbind.json'),
            ('bind2', 'test_3_new_business_bind_v2.py', f'test{test_number}bind2.json'),
            ('issue', 'test_5_issue_policy.py', f'test{test_number}issue.json'),
            ('endorsement', 'test_7_midterm_endorsement.py', f'test{test_number}endt.json'),
            ('cancel', 'test_8_cancellation.py', f'test{test_number}cancel.json'),
            ('reinstate', 'test_9_reinstatement.py', f'test{test_number}reinstate.json')
        ]
    
    def run_test(self, test_script: str, json_file: str) -> Tuple[bool, str, float]:
        """
        Run a single test
        
        Args:
            test_script: Path to the test script
            json_file: Path to the JSON payload file
            
        Returns:
            Tuple of (success, output, duration)
        """
        print(f"\n{'='*80}")
        print(f"Running: {test_script} with {json_file}")
        print(f"{'='*80}")
        
        # Check if files exist
        if not os.path.exists(test_script):
            error_msg = f"Test script not found: {test_script}"
            print(f"❌ {error_msg}")
            return False, error_msg, 0.0
        
        if not os.path.exists(json_file):
            error_msg = f"JSON file not found: {json_file}"
            print(f"❌ {error_msg}")
            return False, error_msg, 0.0
        
        # Load and display the payload being sent
        print("\n📤 REQUEST PAYLOAD:")
        print("-" * 40)
        try:
            with open(json_file, 'r') as f:
                payload = json.load(f)
                print(json.dumps(payload, indent=2))
        except Exception as e:
            print(f"Error reading payload: {e}")
        print("-" * 40)
        
        # Run the test
        start_time = time.time()
        try:
            # Build command
            cmd = [sys.executable, test_script, '--json', json_file]
            print(f"\nCommand: {' '.join(cmd)}")
            
            # Execute
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            duration = time.time() - start_time
            
            # Check result
            if result.returncode == 0:
                print(f"\n✅ Test passed in {duration:.2f} seconds")
                return True, result.stdout, duration
            else:
                print(f"\n❌ Test failed with return code {result.returncode}")
                print("\n📥 FULL OUTPUT:")
                print("=" * 80)
                print(result.stdout)
                if result.stderr:
                    print("\n⚠️ ERROR OUTPUT:")
                    print("=" * 80)
                    print(result.stderr)
                
                # Try to extract response payload from output
                self.extract_response_payload(result.stdout)
                
                return False, f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}", duration
                
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            error_msg = f"Test timed out after {duration:.2f} seconds"
            print(f"❌ {error_msg}")
            return False, error_msg, duration
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Exception running test: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg, duration
    
    def extract_response_payload(self, output: str):
        """
        Try to extract and display response payload from test output
        
        Args:
            output: The stdout from the test
        """
        try:
            # Look for common response patterns in the output
            lines = output.split('\n')
            in_response = False
            response_lines = []
            
            for line in lines:
                # Look for response indicators
                if any(indicator in line.lower() for indicator in ['response:', 'received:', 'error response:', 'soap response:', 'ims response:']):
                    in_response = True
                    response_lines = []
                elif in_response:
                    if line.strip() and not line.startswith('==='):
                        response_lines.append(line)
                    elif line.startswith('===') and response_lines:
                        break
            
            # Also try to find JSON blocks
            json_start = -1
            json_end = -1
            for i, line in enumerate(lines):
                if line.strip().startswith('{') and json_start == -1:
                    json_start = i
                elif line.strip().endswith('}') and json_start != -1:
                    json_end = i + 1
                    json_text = '\n'.join(lines[json_start:json_end])
                    try:
                        json_obj = json.loads(json_text)
                        print("\n📥 RESPONSE PAYLOAD (JSON):")
                        print("-" * 40)
                        print(json.dumps(json_obj, indent=2))
                        print("-" * 40)
                        return
                    except:
                        pass
            
            # If we found response lines, display them
            if response_lines:
                print("\n📥 RESPONSE DATA:")
                print("-" * 40)
                for line in response_lines[:50]:  # Limit to first 50 lines
                    print(line)
                if len(response_lines) > 50:
                    print(f"... ({len(response_lines) - 50} more lines)")
                print("-" * 40)
                
        except Exception as e:
            # Silently fail - this is best effort
            pass
    
    def run_sequence(self) -> bool:
        """
        Run the test sequence up to max_steps
        
        Returns:
            True if all tests passed, False otherwise
        """
        self.start_time = time.time()
        all_passed = True
        
        print(f"\n{'='*80}")
        print(f"Starting Test Sequence")
        print(f"Test Number: {self.test_number}")
        print(f"Steps to Run: {self.max_steps}")
        print(f"Time: {datetime.now().isoformat()}")
        print(f"{'='*80}")
        
        # Generate test files if they don't exist
        if not self.check_test_files():
            print("\n⚠️  Test files not found. Generating them...")
            if not self.generate_test_files():
                print("❌ Failed to generate test files")
                return False
        
        # Run tests in sequence
        for i, (name, script, json_file) in enumerate(self.test_sequence[:self.max_steps]):
            step_num = i + 1
            print(f"\n\n{'='*80}")
            print(f"STEP {step_num}/{self.max_steps}: {name.upper()}")
            print(f"{'='*80}")
            
            success, output, duration = self.run_test(script, json_file)
            
            self.results.append({
                'step': step_num,
                'name': name,
                'script': script,
                'json_file': json_file,
                'success': success,
                'duration': duration,
                'output': output[:1000] if len(output) > 1000 else output  # Truncate long output
            })
            
            if not success:
                all_passed = False
                print(f"\n{'='*80}")
                print(f"❌ TEST SEQUENCE FAILED AT STEP {step_num} ({name.upper()})")
                print(f"{'='*80}")
                print(f"\nThe test sequence has been stopped due to failure.")
                print(f"Review the request payload and response above for details.")
                break  # Always stop on failure
            else:
                print(f"\n✅ Step {step_num} ({name}) completed successfully")
            
            # Small delay between tests
            if i < self.max_steps - 1:
                print("\nWaiting 2 seconds before next test...")
                time.sleep(2)
        
        return all_passed
    
    def check_test_files(self) -> bool:
        """
        Check if all required test files exist
        
        Returns:
            True if all files exist, False otherwise
        """
        for _, _, json_file in self.test_sequence[:self.max_steps]:
            if not os.path.exists(json_file):
                return False
        return True
    
    def generate_test_files(self) -> bool:
        """
        Generate test files using create_test_files.py
        
        Returns:
            True if generation succeeded, False otherwise
        """
        try:
            cmd = [sys.executable, 'create_test_files.py', str(self.test_number)]
            print(f"Running: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("✅ Test files generated successfully")
                print(result.stdout)
                return True
            else:
                print(f"❌ Failed to generate test files")
                print(f"Error: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Exception generating test files: {e}")
            return False
    
    def print_summary(self):
        """Print a summary of the test results"""
        total_duration = time.time() - self.start_time
        
        print(f"\n\n{'='*80}")
        print(f"TEST SEQUENCE SUMMARY")
        print(f"{'='*80}")
        print(f"Test Number: {self.test_number}")
        print(f"Total Duration: {total_duration:.2f} seconds")
        print(f"\nResults:")
        print(f"{'Step':<6} {'Name':<15} {'Status':<10} {'Duration':<12}")
        print(f"{'-'*6} {'-'*15} {'-'*10} {'-'*12}")
        
        passed = 0
        failed = 0
        
        for result in self.results:
            status = '✅ PASSED' if result['success'] else '❌ FAILED'
            if result['success']:
                passed += 1
            else:
                failed += 1
            print(f"{result['step']:<6} {result['name']:<15} {status:<10} {result['duration']:.2f}s")
        
        print(f"\n{'='*80}")
        print(f"Total: {passed} passed, {failed} failed out of {len(self.results)} tests")
        print(f"{'='*80}")
        
        # Save detailed results to file
        self.save_results()
    
    def save_results(self):
        """Save detailed results to a JSON file"""
        results_file = f"test_sequence_results_{self.test_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(results_file, 'w') as f:
            json.dump({
                'test_number': self.test_number,
                'max_steps': self.max_steps,
                'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
                'total_duration': time.time() - self.start_time,
                'results': self.results
            }, f, indent=2)
        
        print(f"\nDetailed results saved to: {results_file}")


def main():
    """Main function"""
    # Parse arguments
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    
    try:
        test_number = int(sys.argv[1])
        max_steps = int(sys.argv[2])
    except ValueError:
        print(f"Error: Invalid arguments")
        print(__doc__)
        sys.exit(1)
    
    # Validate arguments
    if test_number < 1 or test_number > 999:
        print(f"Error: test_number must be between 1 and 999")
        sys.exit(1)
    
    if max_steps < 1 or max_steps > 7:
        print(f"Error: steps must be between 1 and 7")
        sys.exit(1)
    
    # Create and run test sequence
    runner = TestSequenceRunner(test_number, max_steps)
    
    try:
        success = runner.run_sequence()
        runner.print_summary()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test sequence interrupted by user")
        runner.print_summary()
        sys.exit(2)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    main()