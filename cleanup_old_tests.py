"""
Organize old test files into an archive folder
Keep only the new simplified tests
"""

import os
import shutil

# Test files to keep
KEEP_FILES = [
    'test_with_real_data.py',
    'test_simplified_flow.py',
    'tests/'  # Keep the tests directory
]

# Create archive directory
archive_dir = 'old_tests_archive'
if not os.path.exists(archive_dir):
    os.makedirs(archive_dir)

# Get all test files
test_files = [f for f in os.listdir('.') if f.startswith('test_') and f.endswith('.py')]

moved_count = 0
for test_file in test_files:
    if test_file not in KEEP_FILES:
        # Move to archive
        try:
            shutil.move(test_file, os.path.join(archive_dir, test_file))
            print(f"Moved: {test_file}")
            moved_count += 1
        except Exception as e:
            print(f"Error moving {test_file}: {e}")

print(f"\nMoved {moved_count} old test files to {archive_dir}/")
print(f"Kept: {', '.join(KEEP_FILES)}")