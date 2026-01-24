# Task 011: Python Code Obfuscation in Build Process

## Description
Implement Python code obfuscation in the build script to protect source code when distributing the plugin. The build process should compile `.py` files to `.pyc` (bytecode) and optionally use obfuscation tools to make reverse engineering more difficult.

## Objectives
- [ ] Research Python obfuscation methods suitable for QGIS plugins
- [ ] Implement bytecode compilation (.pyc) in build script
- [ ] Optional: Integrate PyArmor or similar obfuscation tool
- [ ] Ensure obfuscated code works in QGIS environment
- [ ] Update build script to support both dev and production modes
- [ ] Test obfuscated plugin functionality
- [ ] Document obfuscation process

## Background

### Why Code Obfuscation?
- **IP Protection**: Protect proprietary algorithms and business logic
- **Security**: Hide sensitive implementation details (though security by obscurity is not recommended for credentials)
- **Commercial Distribution**: Required for commercial plugins
- **Prevent Tampering**: Make it harder to modify the plugin

### Obfuscation Methods

#### 1. Python Bytecode Compilation (.pyc)
**Pros:**
- Built-in Python feature
- No external dependencies
- Fast execution
- Compatible with all Python environments

**Cons:**
- Easily decompiled using tools like `uncompyle6`
- Minimal protection against determined reverse engineering

**Implementation:**
```python
import py_compile
import compileall

# Compile single file
py_compile.compile('source.py', 'source.pyc')

# Compile directory
compileall.compile_dir('src/', force=True)
```

#### 2. PyArmor (Recommended)
**Pros:**
- Strong obfuscation with runtime protection
- Works with QGIS plugins
- Free for most use cases
- Prevents decompilation

**Cons:**
- External dependency
- License restrictions for commercial use
- Slightly larger file size

**Website:** https://pyarmor.readthedocs.io/

**Installation:**
```bash
pip install pyarmor
```

**Basic Usage:**
```bash
# Obfuscate a package
pyarmor gen --output dist/obfuscated src/

# With runtime package
pyarmor gen -r --output dist/obfuscated src/
```

#### 3. Cython (Advanced)
**Pros:**
- Compiles to C extensions (.so/.pyd)
- Very difficult to reverse engineer
- Performance benefits

**Cons:**
- Platform-specific binaries (need to build for Windows/Mac/Linux)
- Complex build process
- May have compatibility issues with QGIS

## Proposed Solution

### Two-Mode Build System

#### Development Mode (Default)
- No obfuscation
- Source .py files included
- Easy debugging
- Fast build

#### Production Mode (--production flag)
- PyArmor obfuscation
- No source .py files (only obfuscated)
- Optimized for distribution

## Technical Implementation

### 1. Update build.sh Script

**File:** `scripts/build.sh`

```bash
#!/bin/bash
# Build script for tlgeo2qgis plugin with obfuscation support

set -e

PRODUCTION_MODE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --production|-p)
      PRODUCTION_MODE=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: ./build.sh [--production]"
      exit 1
      ;;
  esac
done

echo "=== TLGeo2QGIS Build Script ==="
echo "Mode: $([ "$PRODUCTION_MODE" = true ] && echo "PRODUCTION (Obfuscated)" || echo "DEVELOPMENT")"

# Get project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Clean previous build
echo "Cleaning up previous build..."
rm -rf dist/tlgeo2qgis
rm -f dist/tlgeo2qgis.zip

# Create dist directory
mkdir -p dist/tlgeo2qgis

if [ "$PRODUCTION_MODE" = true ]; then
  echo "Building PRODUCTION version with obfuscation..."
  
  # Check if pyarmor is installed
  if ! command -v pyarmor &> /dev/null; then
    echo "Error: PyArmor not found. Install with: pip install pyarmor"
    exit 1
  fi
  
  # Obfuscate source code
  echo "Obfuscating Python code with PyArmor..."
  pyarmor gen --output dist/tlgeo2qgis src/
  
  # Copy metadata
  cp src/metadata.prod.txt dist/tlgeo2qgis/metadata.txt
  
  # Copy logo
  if [ -f "src/logo.png" ]; then
    cp src/logo.png dist/tlgeo2qgis/
  fi
  
  # Copy .env.example
  cp .env.example dist/tlgeo2qgis/
  
else
  echo "Building DEVELOPMENT version (no obfuscation)..."
  
  # Copy source files (development mode)
  rsync -a --exclude="scripts/" --exclude="__pycache__" --exclude="*.pyc" \
    --include="*/" --include="*.py" --prune-empty-dirs src/ dist/tlgeo2qgis/
  
  # Copy logo
  if [ -f "src/logo.png" ]; then
    cp src/logo.png dist/tlgeo2qgis/
  fi
  
  # Copy metadata
  cp src/metadata.txt dist/tlgeo2qgis/
  
  # Copy .env.example
  cp .env.example dist/tlgeo2qgis/
fi

echo "Build structure:"
ls -R dist/tlgeo2qgis

# Create zip archive
echo "Creating zip archive..."
cd dist
zip -r tlgeo2qgis.zip tlgeo2qgis -x "*.DS_Store" -x "__MACOSX*"
cd ..

echo "✓ Build complete!"
echo "  Output: dist/tlgeo2qgis/"
echo "  Archive: dist/tlgeo2qgis.zip"
echo "  Mode: $([ "$PRODUCTION_MODE" = true ] && echo "PRODUCTION" || echo "DEVELOPMENT")"
```

### 2. PyArmor Configuration

**File:** `pyarmor.toml` (optional, for advanced config)

```toml
[project]
name = "tlgeo2qgis"
version = "1.0.0"

[build]
# Exclude patterns
excludes = [
    "*.pyc",
    "__pycache__",
    "tests/*",
    "*.md"
]

[runtime]
# Advanced protection features
anti_debug = true
anti_tamper = true
```

### 3. Alternative: Simple Bytecode Compilation

If PyArmor is too complex, use simple .pyc compilation:

**File:** `scripts/compile.sh`

```bash
#!/bin/bash
# Compile Python files to bytecode

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Compiling Python files to bytecode..."

python3 << EOF
import py_compile
import os
import glob

src_dir = "$PROJECT_ROOT/src"
dist_dir = "$PROJECT_ROOT/dist/tlgeo2qgis"

# Create dist directory
os.makedirs(dist_dir, exist_ok=True)

# Compile all .py files
for py_file in glob.glob(f"{src_dir}/**/*.py", recursive=True):
    rel_path = os.path.relpath(py_file, src_dir)
    pyc_path = os.path.join(dist_dir, rel_path + 'c')
    
    # Create subdirectories
    os.makedirs(os.path.dirname(pyc_path), exist_ok=True)
    
    # Compile
    py_compile.compile(py_file, pyc_path, doraise=True)
    print(f"Compiled: {rel_path}")

print("✓ Compilation complete!")
EOF
```

### 4. Update .gitignore

Add obfuscation artifacts:

```gitignore
# PyArmor
.pyarmor/
pyarmor_runtime_*/

# Bytecode
*.pyc
__pycache__/
```

## Testing Checklist

### Development Build
- [ ] Run `./scripts/build.sh`
- [ ] Verify .py files are present in dist/
- [ ] Install and test in QGIS
- [ ] Verify all features work

### Production Build
- [ ] Install PyArmor: `pip install pyarmor`
- [ ] Run `./scripts/build.sh --production`
- [ ] Verify NO .py files in dist/ (only obfuscated)
- [ ] Verify pyarmor_runtime_* folder exists
- [ ] Install and test in QGIS
- [ ] Test authentication flow
- [ ] Test layer upload
- [ ] Test all menu items

### Cross-Platform Testing
- [ ] Test on Windows
- [ ] Test on macOS
- [ ] Test on Linux
- [ ] Verify obfuscated code works on all platforms

## Security Considerations

### What Obfuscation DOES Protect:
✅ Source code structure and algorithms
✅ Implementation details
✅ Comments and documentation in code
✅ Variable and function names (to some extent)

### What Obfuscation DOES NOT Protect:
❌ **API Keys/Secrets** - Never hardcode in source
❌ **Passwords** - Use environment variables or user input
❌ **JWT Tokens** - Stored in QSettings, not in code
❌ Network traffic - Can be intercepted regardless of obfuscation

### Best Practices:
1. ✅ Use obfuscation for IP protection, not security
2. ✅ Keep secrets in environment variables (.env)
3. ✅ Use HTTPS for API communication
4. ✅ Store sensitive data encrypted (e.g., keyring)
5. ✅ Implement proper authentication (already done)

## Acceptance Criteria

### Build Script
- [ ] `./scripts/build.sh` creates development build (no obfuscation)
- [ ] `./scripts/build.sh --production` creates production build (obfuscated)
- [ ] Build script checks for PyArmor in production mode
- [ ] Build script shows clear mode indication
- [ ] Both modes create valid .zip file

### Obfuscated Plugin
- [ ] No .py files visible in production build
- [ ] pyarmor_runtime folder included
- [ ] All plugin features work correctly
- [ ] Authentication works
- [ ] Layer upload works
- [ ] No runtime errors
- [ ] Performance is acceptable

### Documentation
- [ ] README updated with build instructions
- [ ] Production build process documented
- [ ] PyArmor installation instructions included
- [ ] Troubleshooting guide added

## Implementation Plan

### Phase 1: Research & Setup (Priority: High)
1. Test PyArmor with simple QGIS plugin
2. Verify compatibility with QGIS Python environment
3. Document any issues or limitations

### Phase 2: Build Script Update (Priority: High)
1. Update `build.sh` to support `--production` flag
2. Add PyArmor obfuscation in production mode
3. Test both dev and production builds

### Phase 3: Testing (Priority: High)
1. Test development build (existing functionality)
2. Test production build (obfuscated)
3. Cross-platform testing
4. Performance testing

### Phase 4: Documentation (Priority: Medium)
1. Update README.md with build instructions
2. Add troubleshooting guide
3. Document deployment process

## Files to Create/Modify

### New Files
- `pyarmor.toml` (optional) - PyArmor configuration
- `docs/BUILD.md` - Build process documentation

### Modified Files
- `scripts/build.sh` - Add production mode with obfuscation
- `README.md` - Add build instructions
- `.gitignore` - Exclude obfuscation artifacts

## Dependencies

**Required:**
- Python 3.x (already available)
- bash shell (already available)

**Optional (for production):**
- PyArmor: `pip install pyarmor`
  - Free for non-commercial use
  - License required for commercial distribution

## PyArmor License Considerations

**Free Version (Community Edition):**
- ✅ Open source projects
- ✅ Personal projects
- ✅ Educational use
- ✅ Trial period for commercial projects

**Pro Version Required for:**
- Commercial distribution
- Large scale deployment
- Advanced features (like platform binding)

**Check current license:** https://pyarmor.readthedocs.io/en/latest/licenses.html

## Alternative Solutions

If PyArmor is not suitable:

1. **py_compile (Basic)**
   - Use Python's built-in bytecode compilation
   - Minimal protection but better than nothing

2. **Nuitka (Advanced)**
   - Compile to standalone C
   - Very strong protection
   - Complex setup, platform-specific

3. **pyminifier (Deprecated)**
   - Code minification and obfuscation
   - No longer maintained

4. **Custom Obfuscator**
   - Write custom obfuscation script
   - Variable/function name randomization
   - Code restructuring

## References

- PyArmor Documentation: https://pyarmor.readthedocs.io/
- Python py_compile: https://docs.python.org/3/library/py_compile.html
- QGIS Plugin Packaging: https://docs.qgis.org/latest/en/docs/pyqgis_developer_cookbook/
- Code Obfuscation Best Practices: https://owasp.org/www-community/controls/Code_Obfuscation

## Status
- **Current**: Planning
- **Started**: Not yet
- **Target Completion**: TBD

## Related Tasks
- Task 010: Authentication (completed) - Secrets must not be in source code
- Future: Commercial distribution preparation

## Notes

### Performance Impact
- PyArmor: ~5-10% performance overhead (acceptable for most cases)
- Bytecode: Minimal to no performance impact

### Reversibility
- No obfuscation is 100% secure
- Determined attackers can reverse engineer
- Goal is to raise the difficulty level, not make it impossible

### Maintenance
- Obfuscated code cannot be debugged easily
- Always keep unobfuscated source in version control
- Use production build only for distribution
