# PowerShell script to start the RSG Integration service
# For development or simple deployment without Docker

# Check if Python is installed
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Host "Python is not installed or not in PATH. Please install Python 3.11" -ForegroundColor Red
    exit 1
}

# Check Python version
$pythonVersion = (python --version) 2>&1
if (-not ($pythonVersion -match "Python 3\.(9|10|11)")) {
    Write-Host "Warning: Python 3.9, 3.10, or 3.11 is recommended. Found: $pythonVersion" -ForegroundColor Yellow
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path ".\venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv venv
    
    if (-not $?) {
        Write-Host "Failed to create virtual environment." -ForegroundColor Red
        exit 1
    }
}

# Activate virtual environment and install dependencies
Write-Host "Activating virtual environment and installing dependencies..." -ForegroundColor Cyan
& .\venv\Scripts\Activate.ps1

if (-not (Test-Path ".\venv\Lib\site-packages\fastapi")) {
    Write-Host "Installing dependencies..." -ForegroundColor Cyan
    pip install -r requirements.txt
    
    if (-not $?) {
        Write-Host "Failed to install dependencies." -ForegroundColor Red
        exit 1
    }
}

# Check if .env file exists
if (-not (Test-Path ".\.env")) {
    Write-Host "Warning: .env file not found. Copying from .env.example..." -ForegroundColor Yellow
    Copy-Item ".\.env.example" ".\.env" -ErrorAction SilentlyContinue
    
    if (-not (Test-Path ".\.env")) {
        Write-Host "Warning: Neither .env nor .env.example found. Service may not work correctly." -ForegroundColor Yellow
    } else {
        Write-Host "Please edit .env file with your configuration." -ForegroundColor Yellow
    }
}

# Create required directories
$directories = @(".\logs", ".\data", ".\templates")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "Created directory: $dir" -ForegroundColor Cyan
    }
}

# Run the service
Write-Host "Starting RSG Integration service..." -ForegroundColor Green
Write-Host "API will be available at http://localhost:8000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the service" -ForegroundColor Yellow
Write-Host ""

python run_service.py --host 0.0.0.0 --port 8000 --reload 