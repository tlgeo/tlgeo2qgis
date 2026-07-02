#!/bin/bash
# Compile and packaging script for tlgeo2qgis plugin
# Verifies Python syntax and packages original .py files for universal cross-platform compatibility

set -e  # Exit on error

echo "=== TLGeo2QGIS Packaging Script ==="

# Get the project root (one level up from scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Clean up previous build
echo "Cleaning up previous build..."
rm -rf dist/tlgeo2qgis
rm -f dist/tlgeo2qgis.zip

# Create dist directory
mkdir -p dist/tlgeo2qgis

# 1. Run syntax verification using compileall (fails build if syntax errors are found)
echo "Verifying Python syntax..."
python3 -m compileall -q -f src/

# 2. Clean up temporary syntax verification files from src/
find src -name "*.pyc" -delete
find src -type d -name "__pycache__" -delete

# 3. Copy src/ content (only .py files and assets) to dist
echo "Copying source files to dist..."
rsync -a --exclude="__pycache__" --exclude="*.pyc" src/ dist/tlgeo2qgis/

# 4. Configure production metadata (use metadata.prod.txt as metadata.txt)
echo "Configuring production metadata..."
if [ -f "dist/tlgeo2qgis/metadata.prod.txt" ]; then
    mv dist/tlgeo2qgis/metadata.prod.txt dist/tlgeo2qgis/metadata.txt
fi

# 5. Ensure no development environment files are included in production build
echo "Removing environment config files from production build..."
rm -f dist/tlgeo2qgis/.env
rm -f dist/tlgeo2qgis/.env.example

echo "Build structure:"
ls -R dist/tlgeo2qgis

# Create zip file
echo "Creating zip archive..."
cd dist
zip -r tlgeo2qgis.zip tlgeo2qgis -x "*.DS_Store" -x "__MACOSX*"
cd ..

echo "✓ Packaging complete!"
echo "  Output: dist/tlgeo2qgis/"
echo "  Archive: dist/tlgeo2qgis.zip"
