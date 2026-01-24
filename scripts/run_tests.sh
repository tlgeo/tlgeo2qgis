#!/bin/bash
# Run unit tests for tlgeo2qgis

# Get project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv_test"

# Setup Virtual Environment if not exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment for testing..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    echo "Installing test dependencies..."
    python3 -m pip install --upgrade pip
    python3 -m pip install pytest pytest-mock python-dotenv requests PyQt5-stubs fastapi uvicorn qrcode python-multipart
else
    source "$VENV_DIR/bin/activate"
fi

# Debug environment
echo "Python: $(which python3)"
python3 -m pip list | grep qrcode
python3 -c "import qrcode; print('qrcode imported successfully')" || echo "Failed to import qrcode"

# Add project root and src to PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/src:$PYTHONPATH"
export PYTEST_CURRENT_TEST="1"

# Run tests
echo "Running Unit Tests..."
echo "====================="
cd "$PROJECT_ROOT"
pytest tests/unit -v

# Deactivate (optional in script, but good practice)
deactivate
