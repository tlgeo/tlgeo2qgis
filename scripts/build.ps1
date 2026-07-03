param (
    [switch]$Production,
    [switch]$Release,
    [switch]$Help
)

if ($Help) {
    Write-Host "=== TLGeo2QGIS Build Script (PowerShell) ==="
    Write-Host "Usage: .\build.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Production, -p     Build with Python Minification (production mode)"
    Write-Host "  -Release, -r        Build with production metadata but no obfuscation"
    Write-Host "  -Help, -h           Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\build.ps1                  # Development build (no obfuscation)"
    Write-Host "  .\build.ps1 -Release        # Release build (production metadata, source code)"
    Write-Host "  .\build.ps1 -Production     # Production build (minified)"
    exit 0
}

Write-Host "=== TLGeo2QGIS Build Script ==="
if ($Production) {
    Write-Host "Mode: PRODUCTION (Minified)"
} elseif ($Release) {
    Write-Host "Mode: RELEASE (Production Metadata, Source Code)"
} else {
    Write-Host "Mode: DEVELOPMENT"
}

# Get script and project root dirs
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path "$ScriptDir\.."
Set-Location $ProjectRoot

# Clean up previous build
Write-Host "Cleaning up previous build..."
if (Test-Path "dist\tlgeo2qgis") {
    Remove-Item -Recurse -Force "dist\tlgeo2qgis"
}
if (Test-Path "dist\tlgeo2qgis.zip") {
    Remove-Item -Force "dist\tlgeo2qgis.zip"
}

# Create dist directory
New-Item -ItemType Directory -Force -Path "dist\tlgeo2qgis" | Out-Null

if ($Production) {
    Write-Host "Building PRODUCTION version with obfuscation..."
    
    # Check if python-minifier is installed
    python -c "import python_minifier" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Error: python-minifier not found. Install with: pip install python-minifier"
        Write-Error "       Or run in development mode: .\build.ps1"
        exit 1
    }
    
    Write-Host "Minifying Python code..."
    python scripts\minify_plugin.py src/ dist/tlgeo2qgis/
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Error: Minification failed!"
        exit 1
    }
    
    # Copy metadata (production version if exists, otherwise default)
    if (Test-Path "src\metadata.prod.txt") {
        Write-Host "Using production metadata..."
        Copy-Item "src\metadata.prod.txt" "dist\tlgeo2qgis\metadata.txt" -Force
    } else {
        Copy-Item "src\metadata.txt" "dist\tlgeo2qgis\metadata.txt" -Force
    }
    
    # Copy logo
    if (Test-Path "src\logo.png") {
        Copy-Item "src\logo.png" "dist\tlgeo2qgis\" -Force
    } else {
        Write-Warning "logo.png not found, plugin may not display icon"
    }
    
    # Copy .env.example
    Copy-Item ".env.example" "dist\tlgeo2qgis\" -Force
    
} elseif ($Release) {
    Write-Host "Building RELEASE version (no obfuscation, production metadata)..."
    
    # Copy source files (excluding __pycache__ and *.pyc)
    Write-Host "Copying source files..."
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
    
    # Clean up duplicate metadata files copied from src/
    if (Test-Path "dist\tlgeo2qgis\metadata.prod.txt") {
        Remove-Item "dist\tlgeo2qgis\metadata.prod.txt" -Force
    }
    if (Test-Path "dist\tlgeo2qgis\metadata.txt") {
        Remove-Item "dist\tlgeo2qgis\metadata.txt" -Force
    }
    
    # Copy logo
    if (Test-Path "src\logo.png") {
        Copy-Item "src\logo.png" "dist\tlgeo2qgis\" -Force
    } else {
        Write-Warning "logo.png not found, plugin may not display icon"
    }
    
    # Copy metadata (production version if exists, otherwise default)
    if (Test-Path "src\metadata.prod.txt") {
        Write-Host "Using production metadata..."
        Copy-Item "src\metadata.prod.txt" "dist\tlgeo2qgis\metadata.txt" -Force
    } else {
        Copy-Item "src\metadata.txt" "dist\tlgeo2qgis\metadata.txt" -Force
    }
    
    # Copy .env.example
    Copy-Item ".env.example" "dist\tlgeo2qgis\" -Force
    
} else {
    Write-Host "Building DEVELOPMENT version (no obfuscation)..."
    
    # Copy source files (excluding __pycache__ and *.pyc)
    Write-Host "Copying source files..."
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
    
    # Clean up duplicate metadata files copied from src/
    if (Test-Path "dist\tlgeo2qgis\metadata.prod.txt") {
        Remove-Item "dist\tlgeo2qgis\metadata.prod.txt" -Force
    }
    if (Test-Path "dist\tlgeo2qgis\metadata.txt") {
        Remove-Item "dist\tlgeo2qgis\metadata.txt" -Force
    }
    
    # Copy logo
    if (Test-Path "src\logo.png") {
        Copy-Item "src\logo.png" "dist\tlgeo2qgis\" -Force
    } else {
        Write-Warning "logo.png not found, plugin may not display icon"
    }
    
    # Copy metadata
    Copy-Item "src\metadata.txt" "dist\tlgeo2qgis\metadata.txt" -Force
    
    # Copy .env.example
    Copy-Item ".env.example" "dist\tlgeo2qgis\" -Force
}

Write-Host ""
Write-Host "Build structure:"
Get-ChildItem -Path "dist\tlgeo2qgis" -Recurse | Select-Object Name

# Create zip archive
Write-Host ""
Write-Host "Creating zip archive..."
Compress-Archive -Path "dist\tlgeo2qgis" -DestinationPath "dist\tlgeo2qgis.zip" -Force

Write-Host ""
Write-Host "OK: Build complete!"
Write-Host "  Output:  dist\tlgeo2qgis\"
Write-Host "  Archive: dist\tlgeo2qgis.zip"
if ($Production) {
    Write-Host "  Mode:    PRODUCTION (Minified)"
} elseif ($Release) {
    Write-Host "  Mode:    RELEASE (Production Metadata, Source Code)"
} else {
    Write-Host "  Mode:    DEVELOPMENT"
}
Write-Host ""
if ($Production) {
    Write-Host "Note: This is a production build with minified code."
    Write-Host "      Source code is obfuscated for IP protection."
} elseif ($Release) {
    Write-Host "Note: This is a release build with readable source code and production metadata."
    Write-Host "      Ready for distribution."
} else {
    Write-Host "Note: This is a development build with source code and dev metadata."
    Write-Host "      For production release, use: .\build.ps1 -Release"
}

# Link/Copy to QGIS plugin directory (Optional, for local dev)
$QgisPluginDir = "$env:APPDATA\QGIS\QGIS3\profiles\default\python\plugins"

if (Test-Path $QgisPluginDir) {
    Write-Host ""
    Write-Host "---------------------------------------------------"
    Write-Host "Detected QGIS plugin directory: $QgisPluginDir"
    
    $TargetDir = Join-Path $QgisPluginDir "tlgeo2qgis"
    
    if ($Production -or $Release) {
        # For production/release: COPY the built files (simulate user install)
        Write-Host "Deploying built plugin to QGIS..."
        if (Test-Path $TargetDir) {
            Remove-Item -Recurse -Force $TargetDir
        }
        # Copy built folder
        Copy-Item -Path "dist\tlgeo2qgis" -Destination $QgisPluginDir -Recurse -Force
        Write-Host "OK: Deployed (Copied built package)"
    } else {
        # For development: SYMLINK for live editing
        Write-Host "Deploying DEVELOPMENT build to QGIS..."
        
        if (Test-Path $TargetDir) {
            Remove-Item -Recurse -Force $TargetDir
        }
        
        Write-Host "Attempting to create symlink (requires admin rights)..."
        try {
            New-Item -ItemType SymbolicLink -Path $TargetDir -Value "$ProjectRoot\src" -ErrorAction Stop | Out-Null
            Write-Host "OK: Deployed (Symlinked to src/ for live updates)"
        } catch {
            Write-Host "Failed to create symlink (no admin rights). Falling back to COPYing src..."
            New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
            Get-ChildItem -Path "src" -Recurse | Where-Object {
                $_.FullName -notmatch "__pycache__" -and $_.Extension -ne ".pyc"
            } | ForEach-Object {
                $RelativePath = $_.FullName.Substring((Resolve-Path "src").Path.Length + 1)
                $DestPath = Join-Path $TargetDir $RelativePath
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
            Write-Host "OK: Deployed (Copied src/ for development)"
        }
    }
    Write-Host "Restart QGIS to apply changes."
}
