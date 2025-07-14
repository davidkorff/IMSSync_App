# PowerShell script to create self-signed certificates for testing
# This should NOT be used in production environments

# Configuration
$domain = "api.local" # Change this to your domain
$outputDir = ".\nginx\ssl"
$certName = "server"
$validityPeriod = 365 # days

# Create output directory if it doesn't exist
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    Write-Host "Created directory: $outputDir"
}

# Create self-signed certificate
$cert = New-SelfSignedCertificate -DnsName $domain -CertStoreLocation "cert:\LocalMachine\My" -NotAfter (Get-Date).AddDays($validityPeriod) -KeyAlgorithm RSA -KeyLength 2048

# Export certificate to PFX
$password = ConvertTo-SecureString -String "password" -Force -AsPlainText
$pfxPath = Join-Path $outputDir "$certName.pfx"
Export-PfxCertificate -Cert $cert -FilePath $pfxPath -Password $password | Out-Null

# Export certificate and key for Nginx
$certPath = Join-Path $outputDir "$certName.crt"
$keyPath = Join-Path $outputDir "$certName.key"

# Export certificate
$certData = [System.Convert]::ToBase64String($cert.RawData)
$certData = "-----BEGIN CERTIFICATE-----`r`n" + ($certData -replace '.{64}', '$0`r`n') + "`r`n-----END CERTIFICATE-----"
Set-Content -Path $certPath -Value $certData

# Export private key using OpenSSL (needs to be installed)
$opensslExists = $null -ne (Get-Command "openssl" -ErrorAction SilentlyContinue)
if ($opensslExists) {
    Write-Host "Exporting private key using OpenSSL..."
    & openssl pkcs12 -in $pfxPath -nocerts -out $keyPath -nodes -password pass:password
} else {
    Write-Host "WARNING: OpenSSL not found. Cannot export private key."
    Write-Host "Please install OpenSSL and run: openssl pkcs12 -in $pfxPath -nocerts -out $keyPath -nodes -password pass:password"
}

# Clean up
Remove-Item -Path "cert:\LocalMachine\My\$($cert.Thumbprint)" -Force
Write-Host "Self-signed certificate for $domain created successfully!"
Write-Host "Certificate file: $certPath"
Write-Host "Key file: $keyPath"
Write-Host ""
Write-Host "NOTE: These certificates are for testing only and should not be used in production." 