#!/bin/bash
# Deploy script for tlgeo2qgis plugin
# Uploads the built package to the server

set -e  # Exit on error

echo "=== TLGeo2QGIS Deploy Script ==="

# Get the project root (one level up from scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Check if dist/tlgeo2qgis.zip exists
if [ ! -f "dist/tlgeo2qgis.zip" ]; then
    echo "❌ Error: dist/tlgeo2qgis.zip not found!"
    echo "Please run ./scripts/build.sh or ./scripts/compile.sh first."
    exit 1
fi

echo "Deploying dist/tlgeo2qgis.zip to server..."
scp dist/tlgeo2qgis.zip luantm@tlgeo.xyz:/home/luantm/tlgeo/geoadmin/geoadmin_strapi/public/uploads/tlgeo2qgis-latest.zip

echo "✓ Deploy complete!"
echo "  Plugin available at: https://tlgeo.xyz/uploads/tlgeo2qgis-latest.zip"
