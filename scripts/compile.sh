#!/bin/bash
# Compile script for tlgeo2qgis plugin
# Compiles Python files to .pyc for optimized distribution

set -e  # Exit on error

echo "=== TLGeo2QGIS Compile Script ==="

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

# Compile Python files from src/
echo "Compiling Python files..."
python3 -m compileall -b -f -d dist/tlgeo2qgis src/

# Move all .pyc files to dist preserving structure
echo "Copying compiled files..."
rsync -a --exclude="scripts/" --exclude="__pycache__" --include="*/" --include="*.pyc" --prune-empty-dirs src/ dist/tlgeo2qgis/

# Remove empty __pycache__ directories in src/
find src -type d -name "__pycache__" -empty -delete

# Copy assets
echo "Copying assets..."
if [ -f "src/logo.png" ]; then
    cp src/logo.png dist/tlgeo2qgis/
fi
cp src/metadata.txt dist/tlgeo2qgis/

# Copy .env.example
cp .env.example dist/tlgeo2qgis/

echo "Build structure:"
ls -R dist/tlgeo2qgis

# Create zip file
echo "Creating zip archive..."
cd dist
zip -r tlgeo2qgis.zip tlgeo2qgis -x "*.DS_Store" -x "__MACOSX*"
cd ..

echo "✓ Compile complete!"
echo "  Output: dist/tlgeo2qgis/"
echo "  Archive: dist/tlgeo2qgis.zip"
