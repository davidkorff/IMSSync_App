# PowerShell script to start the RSG Integration service using Docker
# For production deployment

# Check if Docker is installed
if (-not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
    Write-Host "Docker is not installed or not in PATH. Please install Docker Desktop" -ForegroundColor Red
    exit 1
}

# Check if Docker is running
$dockerStatus = docker info 2>&1
if ($dockerStatus -like "*error*") {
    Write-Host "Docker is not running. Please start Docker Desktop" -ForegroundColor Red
    exit 1
}

# Check if Docker Compose is available
if (-not (Get-Command "docker-compose" -ErrorAction SilentlyContinue) -and -not (Get-Command "docker" -ArgumentList "compose" -ErrorAction SilentlyContinue)) {
    Write-Host "Docker Compose is not available. Make sure you have Docker Desktop installed with Docker Compose." -ForegroundColor Red
    exit 1
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

# Check if SSL certificates exist and create if needed
if (-not ((Test-Path ".\nginx\ssl\server.crt") -and (Test-Path ".\nginx\ssl\server.key"))) {
    Write-Host "SSL certificates not found. Do you want to create self-signed certificates for testing? (Y/N)" -ForegroundColor Yellow
    $createCerts = Read-Host
    
    if ($createCerts -eq "Y" -or $createCerts -eq "y") {
        # Run certificate creation script
        if (Test-Path ".\create_self_signed_cert.ps1") {
            & .\create_self_signed_cert.ps1
        } else {
            Write-Host "Certificate creation script not found. Please create SSL certificates manually." -ForegroundColor Red
        }
    } else {
        Write-Host "Please add SSL certificates to nginx/ssl directory before using HTTPS." -ForegroundColor Yellow
    }
}

# Check docker-compose.yml
if (-not (Test-Path ".\docker-compose.yml")) {
    Write-Host "docker-compose.yml not found. The service cannot start." -ForegroundColor Red
    exit 1
}

# Prompt user about nginx
Write-Host "Do you want to use Nginx as a reverse proxy with SSL? (Y/N)" -ForegroundColor Yellow
$useNginx = Read-Host

# Edit docker-compose.yml to enable/disable Nginx
$composeContent = Get-Content ".\docker-compose.yml" -Raw
if ($useNginx -eq "Y" -or $useNginx -eq "y") {
    # Uncomment Nginx section
    $composeContent = $composeContent -replace "(?ms)(\s+)# nginx:.+?# networks:", "`$1nginx:`$1  image: nginx:latest`$1  ports:`$1    - `"80:80`"`$1    - `"443:443`"`$1  volumes:`$1    - ./nginx/conf.d:/etc/nginx/conf.d`$1    - ./nginx/ssl:/etc/nginx/ssl`$1  depends_on:`$1    - api`$1  networks:`$1    - integration-network`$1`$1# networks:"
    Set-Content -Path ".\docker-compose.yml" -Value $composeContent
    
    Write-Host "Nginx configuration enabled. The service will be available via HTTPS." -ForegroundColor Green
} else {
    # Ensure Nginx section is commented
    $composeContent = $composeContent -replace "(?ms)(\s+)nginx:.+?# networks:", "`$1# nginx:`$1#   image: nginx:latest`$1#   ports:`$1#     - `"80:80`"`$1#     - `"443:443`"`$1#   volumes:`$1#     - ./nginx/conf.d:/etc/nginx/conf.d`$1#     - ./nginx/ssl:/etc/nginx/ssl`$1#   depends_on:`$1#     - api`$1#   networks:`$1#     - integration-network`$1`$1# networks:"
    Set-Content -Path ".\docker-compose.yml" -Value $composeContent
    
    Write-Host "Running without Nginx. The service will be available via HTTP on port 8000." -ForegroundColor Yellow
}

# Build and start containers
Write-Host "Building and starting Docker containers..." -ForegroundColor Cyan
if (Get-Command "docker-compose" -ErrorAction SilentlyContinue) {
    docker-compose up -d --build
} else {
    docker compose up -d --build
}

if ($?) {
    Write-Host "RSG Integration service started successfully!" -ForegroundColor Green
    
    if ($useNginx -eq "Y" -or $useNginx -eq "y") {
        Write-Host "Service is available at https://localhost/" -ForegroundColor Green
    } else {
        Write-Host "Service is available at http://localhost:8000/" -ForegroundColor Green
    }
    
    Write-Host "Documentation is available at /docs endpoint" -ForegroundColor Green
    Write-Host "To view logs, run: docker-compose logs -f api" -ForegroundColor Cyan
    Write-Host "To stop the service, run: docker-compose down" -ForegroundColor Cyan
} else {
    Write-Host "Failed to start Docker containers. Check the error messages above." -ForegroundColor Red
} 