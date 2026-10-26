$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

# Antivirus HTTPS scanning (e.g. Norton) re-signs traffic with its own root, set for Node here.
# certs/ is mounted into the container at runtime, never built into the image.
if ($env:NODE_EXTRA_CA_CERTS -and (Test-Path $env:NODE_EXTRA_CA_CERTS)) {
    Copy-Item $env:NODE_EXTRA_CA_CERTS certs/extra-ca.pem
}

docker build -t pm-app .
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
docker rm -f pm-app *> $null
docker run -d --name pm-app --env-file .env -p 8000:8000 -v pm-data:/app/data `
    -v "${PWD}\certs:/app/certs:ro" pm-app
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Running at http://localhost:8000"
