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

# 1. Copy src/ content to dist preserving structure
echo "Copying source files to dist..."
rsync -a --exclude="__pycache__" src/ dist/tlgeo2qgis/

# 2. Compile Python files directly inside dist
echo "Compiling Python files inside dist..."
python3 -m compileall -b -f -q dist/tlgeo2qgis/

# 3. Remove original .py source files from dist (leaving only .pyc)
echo "Removing source .py files from dist..."
find dist/tlgeo2qgis -name "*.py" -delete

# 4. Clean up any remaining __pycache__ directories in dist
find dist/tlgeo2qgis -type d -name "__pycache__" -delete

# 5. Configure production metadata (use metadata.prod.txt as metadata.txt)
echo "Configuring production metadata..."
if [ -f "dist/tlgeo2qgis/metadata.prod.txt" ]; then
    mv dist/tlgeo2qgis/metadata.prod.txt dist/tlgeo2qgis/metadata.txt
fi

# 6. Ensure no development environment files are included in production build
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

echo "✓ Compile complete!"
echo "  Output: dist/tlgeo2qgis/"
echo "  Archive: dist/tlgeo2qgis.zip"
