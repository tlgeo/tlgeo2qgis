#!/bin/bash
# Build script for tlgeo2qgis plugin
# Creates a distributable package in dist/ directory

set -e  # Exit on error

echo "=== TLGeo2QGIS Build Script ==="

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

# Copy source files to dist
echo "Copying source files..."
rsync -a --exclude="scripts/" --exclude="__pycache__" --exclude="*.pyc" --include="*/" --include="*.py" --prune-empty-dirs src/ dist/tlgeo2qgis/

# Copy logo (create placeholder if not exists)
if [ -f "src/logo.png" ]; then
    cp src/logo.png dist/tlgeo2qgis/
else
    echo "Warning: logo.png not found, plugin may not display icon"
fi

# Copy metadata
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

echo "✓ Build complete!"
echo "  Output: dist/tlgeo2qgis/"
echo "  Archive: dist/tlgeo2qgis.zip"
