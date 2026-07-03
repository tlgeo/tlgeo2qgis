$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path "$ScriptDir\.."
Set-Location $ProjectRoot

Write-Host "=== TLGeo2QGIS Deploy Script (PowerShell) ==="

# Check if dist/tlgeo2qgis.zip exists
if (!(Test-Path "dist\tlgeo2qgis.zip")) {
    Write-Error "Error: dist\tlgeo2qgis.zip not found!"
    Write-Host "Please run .\scripts\build.ps1 or .\scripts\compile.ps1 first."
    exit 1
}

Write-Host "Deploying dist/tlgeo2qgis.zip to server..."
scp dist/tlgeo2qgis.zip tlgeo@tlgeo.net:/home/tlgeo/tlgeo/PRODUCTION/geoadmin_strapi/public/uploads/tlgeo2qgis-latest.zip
if ($LASTEXITCODE -ne 0) {
    Write-Error "Error: scp upload failed!"
    exit 1
}

Write-Host "OK: Deploy complete!"
Write-Host "  Plugin available at: https://strapi.admin.tlgeo.xyz/uploads/tlgeo2qgis-latest.zip"
