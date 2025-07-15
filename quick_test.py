#!/usr/bin/env python3
"""Quick test script to run the Triton integration test"""

import subprocess
import sys
import os

# Change to the project directory
os.chdir("/mnt/c/Users/david/OneDrive/Documents/RSG/RSG Integration")

# Run the test
result = subprocess.run([sys.executable, "test_triton_integration.py", "TEST.json"], 
                       capture_output=True, text=True)

# Print output
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

# Show last part of error if there was one
if result.returncode != 0:
    lines = result.stdout.split('\n')
    print("\n=== Last 30 lines of output ===")
    for line in lines[-30:]:
        print(line)