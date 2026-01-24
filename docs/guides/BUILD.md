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
- **python-minifier** - Code obfuscation tool
  ```bash
  pip install python-minifier
  ```

## Build Modes

The build script supports two modes:

| Mode | Command | Use Case | Obfuscation | Source Files |
|------|---------|----------|-------------|--------------|
| **Development** | `./scripts/build.sh` | Testing, debugging | ❌ No | ✅ Readable |
| **Production** | `./scripts/build.sh --production` | Distribution, commercial | ✅ Yes (Minified) | ⚠️ Minified |

## Development Build

### Quick Start

```bash
cd /path/to/tlgeo2qgis
./scripts/build.sh
```

### Output Structure

```
dist/
├── tlgeo2qgis/
│   ├── __init__.py           # Source code (readable)
│   ├── main.py               # Source code (readable)
│   ├── ...
│   └── metadata.txt          # Development metadata
└── tlgeo2qgis.zip            # Distributable archive
```

### When to Use
- ✅ Local development and testing
- ✅ Debugging issues
- ✅ Internal team distribution

## Production Build

### Prerequisites

Install python-minifier:

```bash
pip install python-minifier
```

### Build Command

```bash
cd /path/to/tlgeo2qgis
./scripts/build.sh --production
```

### What It Does
1. **Minifies** Python source code:
   - Removes comments and docstrings
   - Renames local variables (e.g. `user_password` -> `a`)
   - Renames global variables (internal logic only)
   - **Preserves** public API names (e.g. `classFactory`, `TLGeo2QGIS`)
   - **Preserves** line structure (for debugging)
2. **Uses** `metadata.prod.txt` if available
3. **Creates** `dist/tlgeo2qgis.zip`

### Why Minification?
Unlike binary compilation (PyArmor/Cython), minification produces **pure Python code**. This means:
- ✅ **Universal Compatibility**: Works on Windows, macOS, Linux.
- ✅ **Version Independent**: Works on QGIS 3.10, 3.28, 3.34+ (Python 3.7 - 3.12).
- ✅ **Debuggable**: Line numbers in tracebacks match the minified file (thanks to preserved line structure).

### Obfuscated Code Example

**Before (Development)**:
```python
def authenticate(username, password):
    """Authenticate user with GEOADMIN backend"""
    # Send request
    response = requests.post(url, json={"u": username, "p": password})
    return response.json()
```

**After (Production)**:
```python
def authenticate(username,password):
 a=requests.post(url,json={"u":username,"p":password})
 return a.json()
```

### When to Use
- ✅ Public distribution
- ✅ Commercial releases
- ✅ IP protection

## Troubleshooting

### python-minifier Not Found

**Error**:
```
Error: python-minifier not found. Install with: pip install python-minifier
```

**Solution**:
```bash
pip3 install python-minifier
```

### Build Succeeds But Plugin Won't Load

**Common Issues**:
1. **API Name Obfuscation**: If `classFactory` or `initGui` are renamed, QGIS won't find the plugin entry point.
   - **Fix**: Check `scripts/minify_plugin.py` and ensure `PRESERVE_NAMES` list contains all required QGIS hooks.

2. **Import Errors**: If imports are minified incorrectly.
   - **Fix**: The build script uses `combine_imports=False` to prevent this.

## Security Considerations

### What Minification Protects
✅ **Business Logic**: Algorithms are harder to understand.
✅ **Comments/Docs**: All internal documentation is removed.
✅ **Variable Names**: Internal variable names are meaningless (`a`, `b`, `c`).

### What It Does NOT Protect
❌ **API Keys/Secrets**: Never hardcode in source!
❌ **Public Interface**: Class/Function names QGIS needs must remain visible.
❌ **Reverse Engineering**: A determined developer can still prettify the code and understand logic (though it takes effort).

### Best Practices
1. Store secrets in `.env` or environment variables.
2. Use HTTPS for all network communication.
3. Don't rely on client-side code for critical security checks.

---
**Last Updated**: 2026-01-24
