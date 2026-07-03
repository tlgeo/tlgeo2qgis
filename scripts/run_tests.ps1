$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path "$ScriptDir\.."
Set-Location $ProjectRoot
$VenvDir = Join-Path $ProjectRoot ".venv_test"

# Setup Virtual Environment if not exists
if (!(Test-Path $VenvDir)) {
    Write-Host "Creating virtual environment for testing..."
    python -m venv $VenvDir
    
    # Activate virtual environment
    . (Join-Path $VenvDir "Scripts\activate.ps1")
    
    Write-Host "Installing test dependencies..."
    python -m pip install --upgrade pip
    python -m pip install pytest pytest-mock python-dotenv requests PyQt5-stubs fastapi uvicorn qrcode python-multipart
} else {
    . (Join-Path $VenvDir "Scripts\activate.ps1")
}

# Debug environment
Write-Host "Python: $(Get-Command python | Select-Object -ExpandProperty Source)"
python -m pip list | Select-String "qrcode"
python -c "import qrcode; print('qrcode imported successfully')"

# Add project root and src to PYTHONPATH
$env:PYTHONPATH = "$ProjectRoot;$ProjectRoot\src;$env:PYTHONPATH"
$env:PYTEST_CURRENT_TEST = "1"

# Run tests
Write-Host "Running Unit Tests..."
Write-Host "====================="
pytest tests/unit -v --junitxml=unit_report.xml

# Deactivate
deactivate
