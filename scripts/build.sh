#!/bin/bash
# Build script for tlgeo2qgis plugin with obfuscation support
# Creates a distributable package in dist/ directory

set -e  # Exit on error

PRODUCTION_MODE=false
RELEASE_MODE=false
DEVELOPMENT_MODE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --production|-p)
      PRODUCTION_MODE=true
      shift
      ;;
    --release|-r)
      RELEASE_MODE=true
      shift
      ;;
    --development|-d)
      DEVELOPMENT_MODE=true
      shift
      ;;
    --help|-h)
      echo "Usage: ./build.sh [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --release, -r       Build with production metadata (default)"
      echo "  --production, -p    Build with Python Minification (production mode)"
      echo "  --development, -d   Build with development metadata"
      echo "  --help, -h          Show this help message"
      echo ""
      echo "Examples:"
      echo "  ./build.sh                  # Release build (production metadata, source code)"
      echo "  ./build.sh --production     # Production build (minified)"
      echo "  ./build.sh --development    # Development build (dev metadata)"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: ./build.sh [--production|--release|--development]"
      echo "Run './build.sh --help' for more information"
      exit 1
      ;;
  esac
done

# Set default mode to RELEASE if no mode is explicitly set
if [ "$PRODUCTION_MODE" = false ] && [ "$RELEASE_MODE" = false ] && [ "$DEVELOPMENT_MODE" = false ]; then
  RELEASE_MODE=true
fi

echo "=== TLGeo2QGIS Build Script ==="
if [ "$PRODUCTION_MODE" = true ]; then
  echo "Mode: PRODUCTION (Minified)"
elif [ "$DEVELOPMENT_MODE" = true ]; then
  echo "Mode: DEVELOPMENT"
else
  echo "Mode: RELEASE (Production Metadata, Source Code)"
fi

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
  
  # Copy LICENSE
  if [ -f "src/LICENSE" ]; then
    cp src/LICENSE dist/tlgeo2qgis/
  fi
  
elif [ "$DEVELOPMENT_MODE" = true ]; then
  echo "Building DEVELOPMENT version (no obfuscation)..."
  
  # Copy source files (development mode)
  echo "Copying source files..."
  rsync -a --exclude="scripts/" --exclude="__pycache__" --exclude="*.pyc" --exclude=".env" --exclude=".env.production" \
    --include="*/" --include="*.py" --prune-empty-dirs src/ dist/tlgeo2qgis/
  
  # Clean up duplicate metadata files copied from src/
  rm -f dist/tlgeo2qgis/metadata.prod.txt
  rm -f dist/tlgeo2qgis/metadata.txt
  
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

else
  echo "Building RELEASE version (no obfuscation, production metadata)..."
  
  # Copy source files (development mode but with production metadata)
  echo "Copying source files..."
  rsync -a --exclude="scripts/" --exclude="__pycache__" --exclude="*.pyc" --exclude=".env" --exclude=".env.production" \
    --include="*/" --include="*.py" --prune-empty-dirs src/ dist/tlgeo2qgis/
  
  # Clean up duplicate metadata files copied from src/
  rm -f dist/tlgeo2qgis/metadata.prod.txt
  rm -f dist/tlgeo2qgis/metadata.txt
  
  # Copy logo
  if [ -f "src/logo.png" ]; then
    cp src/logo.png dist/tlgeo2qgis/
  else
    echo "Warning: logo.png not found, plugin may not display icon"
  fi
  
  # Copy metadata (production version if exists, otherwise default)
  if [ -f "src/metadata.prod.txt" ]; then
    echo "Using production metadata..."
    cp src/metadata.prod.txt dist/tlgeo2qgis/metadata.txt
  else
    cp src/metadata.txt dist/tlgeo2qgis/metadata.txt
  fi
  
  # Copy .env.example
  cp .env.example dist/tlgeo2qgis/
fi

# Copy .env.production as the default .env in the build package
if [ -f "src/.env.production" ]; then
  echo "Packaging .env.production as .env..."
  cp src/.env.production dist/tlgeo2qgis/.env
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
if [ "$PRODUCTION_MODE" = true ]; then
  echo "  Mode:    PRODUCTION (Minified)"
elif [ "$RELEASE_MODE" = true ]; then
  echo "  Mode:    RELEASE (Production Metadata, Source Code)"
else
  echo "  Mode:    DEVELOPMENT"
fi
echo ""
if [ "$PRODUCTION_MODE" = true ]; then
  echo "Note: This is a production build with minified code."
  echo "      Source code is obfuscated for IP protection."
elif [ "$RELEASE_MODE" = true ]; then
  echo "Note: This is a release build with readable source code and production metadata."
  echo "      Ready for distribution."
else
  echo "Note: This is a development build with source code and dev metadata."
  echo "      For production release, use: ./build.sh --release"
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
  
  if [ "$PRODUCTION_MODE" = true ] || [ "$RELEASE_MODE" = true ]; then
    # For production/release: COPY the built files (simulate user install)
    echo "Deploying built plugin to QGIS..."
    rm -rf "$TARGET_DIR"
    cp -r "dist/tlgeo2qgis" "$TARGET_DIR"
    echo "✓ Deployed (Copied built package)"
  else
    # For development: SYMLINK for live editing
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

