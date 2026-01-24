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
  - Exports to: SQLite (4326), SQLite (original), MBTiles*, PMTiles*, SLD, metadata.json
  - UUID-based export directory: `~/TLGeo_Exports/{uuid}/`
  - *MBTiles requires QGIS 3.14+, PMTiles requires GDAL 3.8+
✅ **Version Info**: Menu → TLGeo → Thông tin phiên bản (shows QGIS/GDAL version and export capabilities)
✅ **Auto-Dependency Install**: Automatically installs required packages on first load
✅ **Windows Support**: Shows helpful error message if needs admin rights
✅ **Authentication**: JWT-based authentication with GEOADMIN backend

### Checking Export Capabilities

To check which export formats are available on your QGIS installation:

1. **In QGIS**: Menu → **TLGeo → Thông tin phiên bản**
2. The dialog shows:
   - QGIS version
   - GDAL version  
   - Which export formats are available (MBTiles, PMTiles)

For detailed information about QGIS versions and export support, see:
📖 **[QGIS Versions & Export Capabilities Guide](docs/QGIS_VERSIONS.md)**

### Build & Deploy

The build system supports two modes:

#### Development Mode (Default)
Build with source code (no obfuscation) - for testing and debugging:

```bash
./scripts/build.sh
```

Output: `dist/tlgeo2qgis.zip` with readable Python source files.

#### Production Mode (Obfuscated)
Build with PyArmor obfuscation - for distribution and IP protection:

```bash
# Install PyArmor (one-time setup)
pip install pyarmor

# Build with obfuscation
./scripts/build.sh --production
```

Output: `dist/tlgeo2qgis.zip` with obfuscated Python files (no readable source code).

**Note**: Production builds use `metadata.prod.txt` if available.

For detailed build instructions and troubleshooting, see [docs/BUILD.md](docs/BUILD.md).

#### Deploy to Server

```bash
# Deploy built plugin to server
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

### Active Tasks

📋 **Current Development:**
- ✅ **Task 010**: JWT Authentication (COMPLETED - moved to `docs/04_completed/`)
- 🔄 **Task 012**: MBTiles/PMTiles Support & GDAL Auto-Update (IN PROGRESS)
  - Auto-detect GDAL version
  - Offer to download and install GDAL 3.8.3
  - Guide users to upgrade QGIS
  - Provide SQLite conversion alternatives
  - See: [docs/02_in-progress/task_012_mbtiles_pmtiles_support.md](docs/02_in-progress/task_012_mbtiles_pmtiles_support.md)

### Roadmap

**v1.1.0 (Next Release)**:
- [ ] GDAL auto-installer (macOS + Windows)
- [ ] GDAL update dialog with multiple options
- [ ] SQLite → MBTiles/PMTiles conversion guide
- [ ] Bundle conversion tools (tippecanoe, pmtiles)

**v1.2.0 (Future)**:
- [ ] Cloud-based layer conversion service
- [ ] Batch export multiple layers
- [ ] Custom export templates
- [ ] Plugin auto-update mechanism

### Next Steps

- [x] Test plugin in QGIS
- [x] Implement Task 010 (Authentication) ✅
- [x] Add version info dialog ✅
- [ ] Implement Task 012 (GDAL Auto-installer) 🔄
- [ ] Add comprehensive documentation

---

**Last Updated**: 2026-01-24  
**Status**: ✅ Ready to use | 🔄 Task 012 in progress
