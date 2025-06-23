# PowerShell script to run CSV loader and save output

# Create logs directory if it doesn't exist
$logsDir = "csv_loader_logs"
if (!(Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir | Out-Null
}

# Generate timestamp
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = "$logsDir\csv_load_$timestamp.log"

# Build command
$args_string = $args -join " "
Write-Host "Running: python load_csv_to_ims.py $args_string" -ForegroundColor Green

# Run and capture output
$output = @()
$output += "Starting CSV loader at $(Get-Date)"
$output += "Command: python load_csv_to_ims.py $args_string"
$output += "========================================"

# Run python and capture output
try {
    $result = python load_csv_to_ims.py $args 2>&1 | Out-String -Stream
    $output += $result
} catch {
    $output += "ERROR: $_"
}

$output += "========================================"
$output += "Completed at $(Get-Date)"

# Save to file
$output | Out-File -FilePath $logFile -Encoding UTF8

# Copy to latest.log
Copy-Item $logFile "$logsDir\latest.log" -Force

# Display results
Write-Host "`nLog saved to: $logFile" -ForegroundColor Yellow
Write-Host "View latest log: $logsDir\latest.log" -ForegroundColor Yellow
Write-Host "`nTo share this log:" -ForegroundColor Cyan
Write-Host "  git add $logsDir\latest.log"
Write-Host "  git commit -m `"CSV loader results from $timestamp`""
Write-Host "  git push"

# Also display the output
Write-Host "`n=== OUTPUT ===" -ForegroundColor Magenta
Get-Content $logFile