# Get script and project root dirs
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path "$ScriptDir\.."
Set-Location $ProjectRoot

Write-Host "=== TLGeo2QGIS Packaging Script (PowerShell) ==="

# Clean up previous build
Write-Host "Cleaning up previous build..."
if (Test-Path "dist\tlgeo2qgis") {
    Remove-Item -Recurse -Force "dist\tlgeo2qgis"
}
if (Test-Path "dist\tlgeo2qgis.zip") {
    Remove-Item -Force "dist\tlgeo2qgis.zip"
}
New-Item -ItemType Directory -Force -Path "dist\tlgeo2qgis" | Out-Null

# 1. Run syntax verification using compileall (fails build if syntax errors are found)
Write-Host "Verifying Python syntax..."
python -m compileall -q -f src
if ($LASTEXITCODE -ne 0) {
    Write-Error "Error: Python syntax verification failed!"
    exit 1
}

# 2. Clean up temporary syntax verification files from src/
Get-ChildItem -Path "src" -Recurse -Include "*.pyc" | Remove-Item -Force
Get-ChildItem -Path "src" -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force

# 3. Copy src/ content (only .py files and assets) to dist
Write-Host "Copying source files to dist..."
Get-ChildItem -Path "src" -Recurse | Where-Object {
    $_.FullName -notmatch "__pycache__" -and $_.Extension -ne ".pyc"
} | ForEach-Object {
    $RelativePath = $_.FullName.Substring((Resolve-Path "src").Path.Length + 1)
    $DestPath = Join-Path "dist\tlgeo2qgis" $RelativePath
    if ($_.PSIsContainer) {
        if (!(Test-Path $DestPath)) {
            New-Item -ItemType Directory -Path $DestPath -Force | Out-Null
        }
    } else {
        $ParentDir = Split-Path -Parent $DestPath
        if (!(Test-Path $ParentDir)) {
            New-Item -ItemType Directory -Path $ParentDir -Force | Out-Null
        }
        Copy-Item $_.FullName $DestPath -Force
    }
}

# 4. Configure production metadata (use metadata.prod.txt as metadata.txt)
Write-Host "Configuring production metadata..."
if (Test-Path "dist\tlgeo2qgis\metadata.prod.txt") {
    Move-Item "dist\tlgeo2qgis\metadata.prod.txt" "dist\tlgeo2qgis\metadata.txt" -Force
}

# 5. Ensure no development environment files are included in production build
Write-Host "Removing environment config files from production build..."
if (Test-Path "dist\tlgeo2qgis\.env") {
    Remove-Item "dist\tlgeo2qgis\.env" -Force
}
if (Test-Path "dist\tlgeo2qgis\.env.example") {
    Remove-Item "dist\tlgeo2qgis\.env.example" -Force
}

# Create zip file
Write-Host "Creating zip archive..."
Compress-Archive -Path "dist\tlgeo2qgis" -DestinationPath "dist\tlgeo2qgis.zip" -Force

Write-Host "OK: Packaging complete!"
Write-Host "  Output: dist\tlgeo2qgis\"
Write-Host "  Archive: dist\tlgeo2qgis.zip"
