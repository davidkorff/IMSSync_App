#!/bin/bash
# Script to run CSV loader and save output for review

# Create logs directory if it doesn't exist
mkdir -p csv_loader_logs

# Generate timestamp for unique log file
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="csv_loader_logs/csv_load_${TIMESTAMP}.log"

# Run the CSV loader with all arguments passed through
# Capture both stdout and stderr
echo "Starting CSV loader at $(date)" | tee "${LOG_FILE}"
echo "Command: python3 load_csv_to_ims.py $@" | tee -a "${LOG_FILE}"
echo "========================================" | tee -a "${LOG_FILE}"

python3 load_csv_to_ims.py "$@" 2>&1 | tee -a "${LOG_FILE}"

echo "========================================" | tee -a "${LOG_FILE}"
echo "Completed at $(date)" | tee -a "${LOG_FILE}"

# Create a symlink to the latest log for easy access
ln -sf "${LOG_FILE}" csv_loader_logs/latest.log

echo ""
echo "Log saved to: ${LOG_FILE}"
echo "View latest log: csv_loader_logs/latest.log"
echo ""
echo "To share this log:"
echo "  git add ${LOG_FILE}"
echo "  git commit -m 'CSV loader results from ${TIMESTAMP}'"
echo "  git push"