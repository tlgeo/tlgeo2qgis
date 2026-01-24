# Build Process Documentation

This document explains how to build the TLGeo2QGIS plugin for different environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Build Modes](#build-modes)
- [Development Build](#development-build)
- [Production Build](#production-build)
- [Build Output](#build-output)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)

## Prerequisites

### Required
- **Bash shell** (macOS/Linux native, Windows WSL/Git Bash)
- **Python 3.x** (Python 3.8 or higher recommended)
- **rsync** (usually pre-installed on macOS/Linux)
- **zip** (usually pre-installed)

### Optional (for production builds)
- **PyArmor** - Code obfuscation tool
  ```bash
  pip install pyarmor
  ```

## Build Modes

The build script supports two modes:

| Mode | Command | Use Case | Obfuscation | Source Files |
|------|---------|----------|-------------|--------------|
| **Development** | `./scripts/build.sh` | Testing, debugging | ❌ No | ✅ Included |
| **Production** | `./scripts/build.sh --production` | Distribution, commercial | ✅ Yes (PyArmor) | ❌ Excluded |

## Development Build

### Quick Start

```bash
cd /path/to/tlgeo2qgis
./scripts/build.sh
```

### What It Does

1. **Cleans** previous build artifacts
2. **Copies** Python source files from `src/` to `dist/tlgeo2qgis/`
3. **Includes** all `.py` files (readable source code)
4. **Copies** metadata, logo, and configuration files
5. **Creates** `dist/tlgeo2qgis.zip` archive

### Output Structure

```
dist/
├── tlgeo2qgis/
│   ├── __init__.py           # Source code (readable)
│   ├── main.py               # Source code (readable)
│   ├── layer_menu_provider.py
│   ├── ui/
│   │   ├── login_dialog.py
│   │   └── qr_code_dialog.py
│   ├── util/
│   │   ├── auth_service.py
│   │   ├── fastapi_server.py
│   │   └── net_util.py
│   ├── metadata.txt          # Development metadata
│   ├── logo.png
│   └── .env.example
└── tlgeo2qgis.zip            # Distributable archive
```

### When to Use

- ✅ Local development and testing
- ✅ Debugging issues
- ✅ Contributing to open-source repository
- ✅ Internal team distribution
- ❌ Public distribution (use production mode instead)

## Production Build

### Prerequisites

Install PyArmor (one-time setup):

```bash
pip install pyarmor
```

Verify installation:

```bash
pyarmor --version
```

Expected output:
```
Pyarmor 9.x.x (trial), 000000, non-profits
```

### Build Command

```bash
cd /path/to/tlgeo2qgis
./scripts/build.sh --production
```

### What It Does

1. **Checks** if PyArmor is installed (fails if not)
2. **Cleans** previous build artifacts
3. **Obfuscates** Python source code using PyArmor
4. **Removes** original `.py` source files
5. **Includes** PyArmor runtime (`pyarmor_runtime_000000/`)
6. **Uses** `metadata.prod.txt` if available (falls back to `metadata.txt`)
7. **Creates** `dist/tlgeo2qgis.zip` with obfuscated code

### Output Structure

```
dist/
├── tlgeo2qgis/
│   ├── __init__.py           # Obfuscated (unreadable)
│   ├── main.py               # Obfuscated (unreadable)
│   ├── layer_menu_provider.py # Obfuscated
│   ├── ui/
│   │   ├── login_dialog.py   # Obfuscated
│   │   └── qr_code_dialog.py # Obfuscated
│   ├── util/
│   │   ├── auth_service.py   # Obfuscated
│   │   ├── fastapi_server.py # Obfuscated
│   │   └── net_util.py       # Obfuscated
│   ├── pyarmor_runtime_000000/  # PyArmor runtime
│   │   ├── __init__.py
│   │   └── pyarmor_runtime.so   # Platform-specific binary
│   ├── metadata.txt          # Production metadata
│   ├── logo.png
│   └── .env.example
└── tlgeo2qgis.zip            # Distributable archive
```

### Obfuscated Code Example

**Before (Development)**:
```python
def authenticate(username, password):
    """Authenticate user with GEOADMIN backend"""
    response = requests.post(f"{API_URL}/auth/login", json={
        "identifier": username,
        "password": password
    })
    return response.json()
```

**After (Production)**:
```python
# Pyarmor 9.2.3 (trial), 000000, non-profits, 2026-01-24T10:54:49.609641
from pyarmor_runtime_000000 import __pyarmor__

...68585 bytes of obfuscated binary data...
```

### When to Use

- ✅ Public distribution
- ✅ Commercial plugin releases
- ✅ IP protection (algorithms, business logic)
- ✅ Client delivery
- ❌ Debugging (use development mode)

## Build Output

### Files Generated

| File/Directory | Description | Size (approx) |
|----------------|-------------|---------------|
| `dist/tlgeo2qgis/` | Plugin directory (ready to install) | ~500 KB (dev) / ~800 KB (prod) |
| `dist/tlgeo2qgis.zip` | Distributable archive | ~200 KB (dev) / ~400 KB (prod) |

### Installation

#### Manual Installation (from .zip)

1. Open QGIS
2. Go to **Plugins → Manage and Install Plugins**
3. Click **Install from ZIP**
4. Select `dist/tlgeo2qgis.zip`
5. Click **Install Plugin**
6. Enable the plugin in the list

#### Manual Installation (from directory)

Copy the built plugin to QGIS plugins directory:

**macOS**:
```bash
cp -r dist/tlgeo2qgis ~/Library/Application\ Support/QGIS/QGIS3/profiles/default/python/plugins/
```

**Linux**:
```bash
cp -r dist/tlgeo2qgis ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/
```

**Windows**:
```cmd
xcopy /E /I dist\tlgeo2qgis %APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\tlgeo2qgis
```

Then restart QGIS and enable the plugin.

## Troubleshooting

### PyArmor Not Found

**Error**:
```
Error: PyArmor not found. Install with: pip install pyarmor
       Or run in development mode: ./build.sh
```

**Solution**:
```bash
pip install pyarmor
# or
pip3 install pyarmor
```

Verify:
```bash
which pyarmor
# Should output: /usr/local/bin/pyarmor or similar
```

### Permission Denied

**Error**:
```
./scripts/build.sh: Permission denied
```

**Solution**:
```bash
chmod +x scripts/build.sh
./scripts/build.sh
```

### rsync Not Found

**Error**:
```
rsync: command not found
```

**Solution (macOS/Linux)**:
```bash
# macOS (should be pre-installed, if not):
brew install rsync

# Ubuntu/Debian:
sudo apt-get install rsync

# CentOS/RHEL:
sudo yum install rsync
```

### Build Succeeds But Plugin Won't Load

**Common Issues**:

1. **Missing `metadata.txt` at root**:
   - Check: `dist/tlgeo2qgis/metadata.txt` exists
   - Solution: Ensure `src/metadata.txt` exists before building

2. **Missing `__init__.py` at root**:
   - Check: `dist/tlgeo2qgis/__init__.py` exists
   - Solution: Ensure `src/__init__.py` exists before building

3. **PyArmor runtime missing (production builds)**:
   - Check: `dist/tlgeo2qgis/pyarmor_runtime_000000/` exists
   - Solution: Rebuild with `--production` flag

4. **Python version mismatch**:
   - PyArmor creates platform-specific binaries
   - Build on the same OS as target QGIS installation
   - For cross-platform, build on each platform separately

### Obfuscated Plugin Shows Runtime Errors

**Issue**: Plugin loads but crashes on execution (production build).

**Possible Causes**:
- PyArmor compatibility issue with QGIS Python environment
- Missing PyArmor runtime files
- Platform mismatch (built on macOS, running on Windows)

**Solutions**:
1. Test development build first (without obfuscation)
2. If dev build works but prod doesn't, report PyArmor compatibility issue
3. Ensure PyArmor runtime is included in distribution
4. Build on target platform (or use PyArmor Pro for cross-platform)

## Security Considerations

### What Obfuscation Protects

✅ **Source code structure and algorithms**  
✅ **Implementation details**  
✅ **Comments and documentation in code**  
✅ **Variable and function names** (partially)

### What Obfuscation Does NOT Protect

❌ **API Keys/Secrets** - Never hardcode in source  
❌ **Passwords** - Use environment variables or user input  
❌ **JWT Tokens** - Stored in QSettings, not in code  
❌ **Network traffic** - Can be intercepted regardless of obfuscation

### Best Practices

1. ✅ Use obfuscation for IP protection, not security
2. ✅ Keep secrets in environment variables (`.env`)
3. ✅ Use HTTPS for API communication
4. ✅ Store sensitive data encrypted (e.g., keyring)
5. ✅ Implement proper authentication (JWT-based)

### PyArmor License

**Free Version (Community Edition)**:
- ✅ Open source projects
- ✅ Personal projects
- ✅ Educational use
- ✅ Trial period for commercial projects

**Pro Version Required for**:
- Commercial distribution at scale
- Advanced features (platform binding, expiration dates)
- Cross-platform builds

**Check current license**: https://pyarmor.readthedocs.io/en/latest/licenses.html

## Advanced Configuration

### Custom PyArmor Settings

Edit `pyarmor.toml` to customize obfuscation behavior:

```toml
[project]
name = "tlgeo2qgis"
version = "1.0.0"

[build]
excludes = [
    "*.pyc",
    "__pycache__",
    "tests/*",
]

[runtime]
# Advanced protection (requires PyArmor Pro)
# anti_debug = true
# anti_tamper = true
```

### Dual Metadata Files

The build script supports two metadata files:

- `src/metadata.txt` - Used in development builds
- `src/metadata.prod.txt` - Used in production builds (if exists)

This allows you to:
- Use different version numbers (dev vs prod)
- Include different descriptions
- Set different author/repository links

### Build Script Options

```bash
./scripts/build.sh --help
```

Output:
```
Usage: ./build.sh [OPTIONS]

Options:
  --production, -p    Build with PyArmor obfuscation (production mode)
  --help, -h          Show this help message

Examples:
  ./build.sh                  # Development build (no obfuscation)
  ./build.sh --production     # Production build (obfuscated)
```

## Performance Impact

| Build Mode | Build Time | Plugin Load Time | Runtime Performance |
|------------|------------|------------------|---------------------|
| Development | ~2 seconds | Fast | Normal |
| Production | ~5 seconds | Slightly slower | 5-10% slower |

**Note**: PyArmor adds minimal overhead (~5-10%) which is acceptable for most use cases.

## Cross-Platform Considerations

### Building for Multiple Platforms

PyArmor creates **platform-specific binaries**. To distribute to multiple platforms:

**Option 1: Build on each platform**
```bash
# On macOS
./scripts/build.sh --production
mv dist/tlgeo2qgis.zip dist/tlgeo2qgis-macos.zip

# On Windows
./scripts/build.sh --production
move dist\tlgeo2qgis.zip dist\tlgeo2qgis-windows.zip

# On Linux
./scripts/build.sh --production
mv dist/tlgeo2qgis.zip dist/tlgeo2qgis-linux.zip
```

**Option 2: PyArmor Pro (cross-platform build)**
- Requires PyArmor Pro license
- Can target multiple platforms in single build
- See: https://pyarmor.readthedocs.io/

**Option 3: Development build (no obfuscation)**
- Pure Python source code
- Works on all platforms
- No IP protection

## Continuous Integration (CI)

### GitHub Actions Example

```yaml
name: Build Plugin

on:
  push:
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install PyArmor
        run: pip install pyarmor
      
      - name: Build Production Release
        run: ./scripts/build.sh --production
      
      - name: Upload Artifact
        uses: actions/upload-artifact@v3
        with:
          name: tlgeo2qgis-plugin
          path: dist/tlgeo2qgis.zip
```

## Conclusion

- Use **development mode** for testing and debugging
- Use **production mode** for distribution and IP protection
- Always test obfuscated builds before distribution
- Keep source code in version control (never commit obfuscated code)

For more information:
- PyArmor Documentation: https://pyarmor.readthedocs.io/
- QGIS Plugin Packaging: https://docs.qgis.org/latest/en/docs/pyqgis_developer_cookbook/

---

**Last Updated**: 2026-01-24  
**Build Script Version**: 1.1.0 (with obfuscation support)
