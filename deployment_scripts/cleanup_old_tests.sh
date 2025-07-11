#!/bin/bash
# Clean up old test files and organize the test directory

echo "Organizing test files..."

# Create archive for old tests
mkdir -p old_tests_archive

# Move all old test_*.py files to archive (except the ones we want to keep)
for file in test_*.py; do
    if [[ "$file" != "test_with_real_data.py" && "$file" != "test_simplified_flow.py" ]]; then
        if [[ -f "$file" ]]; then
            echo "Moving $file to archive..."
            mv "$file" old_tests_archive/
        fi
    fi
done

# Keep these essential test files
echo ""
echo "Keeping essential test files:"
echo "  - test_with_real_data.py (for quick testing)"
echo "  - test_simplified_flow.py (demonstrates the architecture)"
echo "  - tests/ directory (organized test structure)"

# Show what's in the new test structure
echo ""
echo "New test structure:"
find tests -type f -name "*.py" | sort

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "To run tests:"
echo "  cd tests && python test_with_test_json.py"
echo ""
echo "Old tests archived in: old_tests_archive/"