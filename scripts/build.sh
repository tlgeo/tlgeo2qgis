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
      echo "  --production, -p    Build with Python Minification (production mode)"
      echo "  --help, -h          Show this help message"
      echo ""
      echo "Examples:"
      echo "  ./build.sh                  # Development build (no obfuscation)"
      echo "  ./build.sh --production     # Production build (minified)"
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
echo "Mode: $([ "$PRODUCTION_MODE" = true ] && echo "PRODUCTION (Minified)" || echo "DEVELOPMENT")"

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
  
  # Check if python-minifier is installed
  if ! python3 -c "import python_minifier" &> /dev/null; then
    echo "Error: python-minifier not found. Install with: pip install python-minifier"
    echo "       Or run in development mode: ./build.sh"
    exit 1
  fi
  
  # Minify source code using custom script
  echo "Minifying Python code..."
  python3 scripts/minify_plugin.py src/ dist/tlgeo2qgis/
  
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
echo "  Mode:    $([ "$PRODUCTION_MODE" = true ] && echo "PRODUCTION (Minified)" || echo "DEVELOPMENT")"
echo ""
if [ "$PRODUCTION_MODE" = true ]; then
  echo "Note: This is a production build with minified code."
  echo "      Source code is obfuscated for IP protection."
else
  echo "Note: This is a development build with source code."
  echo "      For production, use: ./build.sh --production"
fi

# Link/Copy to QGIS plugin directory (Optional, for local dev)
# Detect OS and set QGIS plugin path
QGIS_PLUGIN_DIR=""
if [[ "$OSTYPE" == "darwin"* ]]; then
  # macOS
  QGIS_PLUGIN_DIR="$HOME/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
  # Linux
  QGIS_PLUGIN_DIR="$HOME/.local/share/QGIS/QGIS3/profiles/default/python/plugins"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
  # Windows (Git Bash / Cygwin)
  QGIS_PLUGIN_DIR="$APPDATA/QGIS/QGIS3/profiles/default/python/plugins"
fi

if [ -d "$QGIS_PLUGIN_DIR" ]; then
  echo ""
  echo "---------------------------------------------------"
  echo "Detected QGIS plugin directory: $QGIS_PLUGIN_DIR"
  
  TARGET_DIR="$QGIS_PLUGIN_DIR/tlgeo2qgis"
  
  if [ "$PRODUCTION_MODE" = true ]; then
    # For production: COPY the built files (simulate user install)
    echo "Deploying PRODUCTION build to QGIS..."
    rm -rf "$TARGET_DIR"
    cp -r "dist/tlgeo2qgis" "$TARGET_DIR"
    echo "✓ Deployed (Copied)"
  else
    # For development: SYMLINK for live editing
    # Only symlink if src is what we want, but build.sh creates dist structure.
    # Actually, for QGIS to pick up changes in src/ immediately, we should symlink src/ to plugin dir,
    # BUT src/ structure (with metadata.txt inside) might not match what QGIS expects if metadata is not at root of src.
    # In this project, metadata.txt IS at src/metadata.txt, so symlinking src/ works!
    
    echo "Deploying DEVELOPMENT build to QGIS..."
    
    # Check if it's already a symlink to src
    if [ -L "$TARGET_DIR" ] && [ "$(readlink "$TARGET_DIR")" == "$PROJECT_ROOT/src" ]; then
      echo "✓ Already symlinked to src/"
    else
      rm -rf "$TARGET_DIR"
      ln -s "$PROJECT_ROOT/src" "$TARGET_DIR"
      echo "✓ Deployed (Symlinked to src/ for live updates)"
    fi
  fi
  echo "Restart QGIS to apply changes."
fi

