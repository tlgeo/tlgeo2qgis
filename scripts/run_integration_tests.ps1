param (
    [string]$QgisVersion = "release-3_28"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path "$ScriptDir\.."
Set-Location $ProjectRoot

Write-Host "================================================================="
Write-Host "Running integration tests on QGIS Docker image: qgis/qgis:$QgisVersion"
Write-Host "================================================================="

# Start QGIS container and run tests
docker run --rm `
  -v "${ProjectRoot}:/usr/src/tlgeo2qgis" `
  -w /usr/src/tlgeo2qgis `
  qgis/qgis:$QgisVersion `
  sh -c "
    echo 'Installing system packages (QtWebSockets) inside container...' &&
    apt-get update &&
    (apt-get install -y python3-pyqt5.qtwebsockets || true) &&
    (apt-get install -y python3-pyqt6.qtwebsockets || true) &&
    echo 'Installing test dependencies inside container...' &&
    (pip3 install pytest pytest-qgis requests fastapi uvicorn qrcode python-multipart python-dotenv psycopg2-binary websockets --break-system-packages --ignore-installed 2>/dev/null ||
     pip3 install pytest pytest-qgis requests fastapi uvicorn qrcode python-multipart python-dotenv psycopg2-binary websockets --ignore-installed) &&
    echo 'Setting up QGIS plugin path...' &&
    mkdir -p /root/.local/share/QGIS/QGIS3/profiles/default/python/plugins &&
    ln -snf /usr/src/tlgeo2qgis/src /root/.local/share/QGIS/QGIS3/profiles/default/python/plugins/tlgeo2qgis &&
    echo 'Running pytest under xvfb...' &&
    export QGIS_INTEGRATION_TEST=1 &&
    export PYTHONPATH=\"/root/.local/share/QGIS/QGIS3/profiles/default/python/plugins:\`$PYTHONPATH\" &&
    xvfb-run -s '+extension GLX -screen 0 1024x768x24' pytest tests/integration -v --junitxml=integration_report.xml | tee integration_report.txt
  "
