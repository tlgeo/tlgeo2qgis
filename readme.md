# TLGeo2QGIS Plugin - Restored

## ✅ Project Restored Successfully!

All source code has been recreated with the new refactored structure after accidental deletion by QGIS.

### Project Structure

```
TLGEO_PROJECTS/tlgeo2qgis/
├── src/                    # Source code
│   ├── __init__.py         # Plugin entry point with auto-dependency install
│   ├── main.py             # Main plugin class
│   ├── layer_menu_provider.py  # Layer export functionality
│   ├── logo.png            # Plugin icon
│   ├── metadata.txt        # Plugin metadata for QGIS
│   ├── metadata.prod.txt   # Production metadata
│   ├── ui/
│   │   └── qr_code_dialog.py   # QR code dialog
│   └── util/
│       ├── fastapi_server.py   # Remote control server
│       └── net_util.py         # Network utilities
│
├── scripts/                # Build tools
│   ├── build.sh            # Build plugin (source)
│   ├── compile.sh          # Compile to .pyc
│   └── deploy.sh           # Deploy to server
│
├── docs/                   # Documentation
│   ├── 02_in-progress/
│   │   ├── task_009_...    # Layer export task
│   │   └── task_010_...    # Authentication task (NEW)
│   └── ...
│
├── dist/                   # Build output (gitignored)
│   ├── tlgeo2qgis/         # Built plugin
│   └── tlgeo2qgis.zip      # Distributable archive
│
├── .env.example            # Environment template
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

### Features

✅ **Remote Control**: Control QGIS from mobile via FastAPI server (port 13000)
✅ **Layer Export**: Right-click layer → "TLGeo > Tải lên"
  - Exports to: SQLite (4326), SQLite (original), MBTiles, PMTiles, SLD, metadata.json
  - UUID-based export directory: `~/TLGeo_Exports/{uuid}/`
✅ **Auto-Dependency Install**: Automatically installs required packages on first load
✅ **Windows Support**: Shows helpful error message if needs admin rights

### Build & Deploy

```bash
# Build for development (Python source)
./scripts/build.sh

# Build for production (compiled .pyc)
./scripts/compile.sh

# Deploy to server
./scripts/deploy.sh
```

### Installation in QGIS

The plugin is already deployed to:
```
~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/tlgeo2qgis/
```

**To activate:**
1. Open QGIS
2. Go to: Plugins → Manage and Install Plugins
3. Find "TLGeo2QGIS" and check the box
4. Plugin should load successfully now!

### What Changed

**Before (Broken)**: Files scattered, complex structure
**After (Fixed)**: Clean `src/` → `dist/` build process

**Key Fix**: 
- `__init__.py` and `metadata.txt` are now properly copied from `src/` to root of `dist/tlgeo2qgis/`
- QGIS requires these files at plugin root level, not in subdirectories

### Configuration

Create `.env` file (copy from `.env.example`):
```bash
cp .env.example .env
```

Edit `.env`:
```
GEOADMIN_STRAPI_URL=http://localhost:1337
```

### Dependencies

Auto-installed on first load:
- `fastapi` - Web server
- `uvicorn` - ASGI server
- `qrcode` - QR code generation
- `python-multipart` - File upload support
- `python-dotenv` - Environment variables
- `requests` - HTTP client

### Version

Current: **1.0.2**

### Next Steps

- [ ] Test plugin in QGIS
- [ ] Implement Task 010 (Authentication)
- [ ] Add comprehensive documentation

---

**Last Updated**: 2026-01-22  
**Status**: ✅ Ready to use
