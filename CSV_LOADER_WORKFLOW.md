# CSV Loader Workflow for Remote Debugging

This workflow allows you to run the CSV loader on your local network (with IMS access) and share the results via GitHub for analysis.

## On Your Local Machine (with IMS access)

### Running the CSV Loader

```bash
# Use the wrapper script to capture all output
./run_csv_loader.sh 2 --sync

# Examples:
./run_csv_loader.sh 1                    # Run with file 1, async mode
./run_csv_loader.sh 2 --sync            # Run with file 2, sync mode  
./run_csv_loader.sh 2 --poll            # Run with file 2, poll mode
```

The script will:
1. Run the CSV loader
2. Capture ALL output (stdout and stderr)
3. Save to `csv_loader_logs/csv_load_TIMESTAMP.log`
4. Create a symlink at `csv_loader_logs/latest.log`
5. Show you the git commands to push

### Sharing Results

```bash
# Add and commit the log
git add csv_loader_logs/latest.log
git commit -m "CSV loader results with IMS sync"
git push
```

## On Claude/Analysis Machine

### Checking Latest Results

Tell Claude: "Check the latest CSV loader results"

Or manually:
```bash
# Pull latest changes
git pull

# Check results
python3 check_csv_results.py

# Or directly read
cat csv_loader_logs/latest.log
```

## What Gets Logged

- Complete output from load_csv_to_ims.py
- All error messages and stack traces
- IMS responses (when using --sync)
- Transaction IDs for follow-up
- Timestamps for timing analysis

## Directory Structure

```
csv_loader_logs/
├── csv_load_20250623_123456.log    # Timestamped logs
├── csv_load_20250623_134512.log
└── latest.log -> csv_load_20250623_134512.log  # Symlink to most recent
```

## Benefits

1. **Complete Output**: Captures everything you see on screen
2. **Persistent**: Logs are saved and tracked in git
3. **Easy Sharing**: Just push to GitHub
4. **Latest Link**: Always know which log is newest
5. **Analysis Ready**: Claude can read and analyze the full output