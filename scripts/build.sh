#!/bin/bash
# Build script for tlgeo2qgis plugin with obfuscation support
# Creates a distributable package in dist/ directory

set -e  # Exit on error

PRODUCTION_MODE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --production|-p)
      PRODUCTION_MODE=true
      shift
      ;;
    --help|-h)
      echo "Usage: ./build.sh [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --production, -p    Build with PyArmor obfuscation (production mode)"
      echo "  --help, -h          Show this help message"
      echo ""
      echo "Examples:"
      echo "  ./build.sh                  # Development build (no obfuscation)"
      echo "  ./build.sh --production     # Production build (obfuscated)"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: ./build.sh [--production]"
      echo "Run './build.sh --help' for more information"
      exit 1
      ;;
  esac
done

echo "=== TLGeo2QGIS Build Script ==="
echo "Mode: $([ "$PRODUCTION_MODE" = true ] && echo "PRODUCTION (Obfuscated)" || echo "DEVELOPMENT")"

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

if [ "$PRODUCTION_MODE" = true ]; then
  echo "Building PRODUCTION version with obfuscation..."
  
  # Detect QGIS Python (for compatible obfuscation)
  QGIS_PYARMOR="/Applications/QGIS.app/Contents/MacOS/bin/pyarmor"
  if [ -f "$QGIS_PYARMOR" ]; then
    PYARMOR_CMD="$QGIS_PYARMOR"
    echo "Using QGIS PyArmor (Python 3.9 compatible)"
  elif command -v pyarmor &> /dev/null; then
    PYARMOR_CMD="pyarmor"
    echo "Warning: Using system PyArmor (may not be compatible with QGIS Python 3.9)"
  else
    echo "Error: PyArmor not found"
    echo "       Install with: pip install pyarmor"
    echo "       Or for QGIS compatibility: /Applications/QGIS.app/Contents/MacOS/bin/python3.9 -m pip install pyarmor"
    echo "       Or run in development mode: ./build.sh"
    exit 1
  fi
  
  # Verify PyArmor works
  if ! $PYARMOR_CMD --version &> /dev/null; then
    echo "Error: PyArmor command failed"
    exit 1
  fi
  
  # Obfuscate source code to temp directory
  echo "Obfuscating Python code with PyArmor..."
  echo "Targeting platforms: Windows (x86_64), macOS (Intel/Silicon), Linux (x86_64)"
  
  mkdir -p dist/temp_obfuscated
  
  # Generate for multiple platforms
  # Note: This matches the CURRENT Python version (e.g. 3.9). 
  # If users have QGIS with Python 3.12, you must build with Python 3.12.
  $PYARMOR_CMD gen \
    --platform windows.x86_64,darwin.x86_64,darwin.arm64,linux.x86_64 \
    --output dist/temp_obfuscated \
    src/
  
  # Move obfuscated files from src/ subdirectory to dist/tlgeo2qgis/
  
  # Move obfuscated files from src/ subdirectory to dist/tlgeo2qgis/
  if [ -d "dist/temp_obfuscated/src" ]; then
    mv dist/temp_obfuscated/src/* dist/tlgeo2qgis/
  else
    mv dist/temp_obfuscated/* dist/tlgeo2qgis/
  fi
  
  # Move pyarmor_runtime to root
  if [ -d "dist/temp_obfuscated/pyarmor_runtime_"* ]; then
    mv dist/temp_obfuscated/pyarmor_runtime_* dist/tlgeo2qgis/
  fi
  
  # Clean up temp directory
  rm -rf dist/temp_obfuscated
  
  # Copy metadata (production version if exists, otherwise default)
  if [ -f "src/metadata.prod.txt" ]; then
    echo "Using production metadata..."
    cp src/metadata.prod.txt dist/tlgeo2qgis/metadata.txt
  else
    cp src/metadata.txt dist/tlgeo2qgis/metadata.txt
  fi
  
  # Copy logo
  if [ -f "src/logo.png" ]; then
    cp src/logo.png dist/tlgeo2qgis/
  else
    echo "Warning: logo.png not found, plugin may not display icon"
  fi
  
  # Copy .env.example
  cp .env.example dist/tlgeo2qgis/
  
else
  echo "Building DEVELOPMENT version (no obfuscation)..."
  
  # Copy source files (development mode)
  echo "Copying source files..."
  rsync -a --exclude="scripts/" --exclude="__pycache__" --exclude="*.pyc" \
    --include="*/" --include="*.py" --prune-empty-dirs src/ dist/tlgeo2qgis/
  
  # Copy logo
  if [ -f "src/logo.png" ]; then
    cp src/logo.png dist/tlgeo2qgis/
  else
    echo "Warning: logo.png not found, plugin may not display icon"
  fi
  
  # Copy metadata
  cp src/metadata.txt dist/tlgeo2qgis/metadata.txt
  
  # Copy .env.example
  cp .env.example dist/tlgeo2qgis/
fi

echo ""
echo "Build structure:"
ls -R dist/tlgeo2qgis

# Create zip archive
echo ""
echo "Creating zip archive..."
cd dist
zip -r tlgeo2qgis.zip tlgeo2qgis -x "*.DS_Store" -x "__MACOSX*"
cd ..

echo ""
echo "✓ Build complete!"
echo "  Output:  dist/tlgeo2qgis/"
echo "  Archive: dist/tlgeo2qgis.zip"
echo "  Mode:    $([ "$PRODUCTION_MODE" = true ] && echo "PRODUCTION (Obfuscated)" || echo "DEVELOPMENT")"
echo ""
if [ "$PRODUCTION_MODE" = true ]; then
  echo "Note: This is a production build with obfuscated code."
  echo "      Source .py files are not included for security."
else
  echo "Note: This is a development build with source code."
  echo "      For production, use: ./build.sh --production"
fi


# Link to QGIS plugin directory
rm -rf "/Users/taluan/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/tlgeo2qgis"
ln -s /Users/taluan/Workshop/TLGeo/GEOADMIN_WORKSPACE/TLGEO_PROJECTS/tlgeo2qgis/dist/tlgeo2qgis "/Users/taluan/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/tlgeo2qgis"