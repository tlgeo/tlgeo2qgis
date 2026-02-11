# Layer Upload Guide

## Overview

The TLGeo2QGIS plugin provides multiple methods to upload layers from QGIS to the GEOADMIN backend. This guide covers all available methods, formats, and troubleshooting tips.

## Methods

### Method 1: Right-Click Context Menu (Quick Export)

**Fastest way to upload a single layer**

1. Right-click on a vector layer in the QGIS Layers panel
2. Select `TLGeo > Tải lên` from the context menu
3. Plugin will:
   - Export layer to `~/TLGeo_Exports/{uuid}/`
   - Upload files to GEOADMIN Strapi
   - Show success/error message

**Features:**
- Export format: SQLite (EPSG:4326 + Original), MBTiles, PMTiles, SLD, Metadata
- Automatic upload to server
- UUID-based directory naming for tracking

### Method 2: Publish Widget (Detailed Control)

**Best for monitoring upload progress**

1. Enable TLGeo Panel: `Plugins → TLGeo → Toggle TLGeo Panel`
2. Select a layer in QGIS
3. Click `Làm mới lớp` to check layer info
4. Click `Xuất bản lớp` to start publish task

**Features:**
- Real-time progress bar
- Background task execution (non-blocking)
- Detailed status messages
- Success/error dialogs

### Method 3: Command Line / FastAPI Server

**For integration with external apps**

The plugin runs a FastAPI server on port 13000 that accepts remote commands:

```bash
# Connect to QGIS from mobile app
# QR Code available via: Menu → TLGeo → Show IP
```

**API Endpoints:**
- `POST /api/command` - Execute commands from external apps
- See `src/main.py:process_command()` for available commands

## Export Process

### Background Task (Non-Blocking)

The export now runs as a **QGIS background task** - the UI remains responsive!

**How it works:**

1. User clicks "TLGeo > Tải lên"
2. Plugin shows: "Export started in background..."
3. Progress appears in QGIS Message Bar
4. User can continue working while export runs
5. Final success/error message when complete

**Progress messages:**
```
🔄 Preparing export...
📋 Exporting metadata...
💾 Exporting SQLite (WGS84)...
💾 Exporting SQLite (Original CRS)...
🗺️ Exporting MBTiles...
🎨 Exporting SLD style...
🎨 Exporting QML style...
🗺️ Exporting Mapbox Style...
☁️ Uploading to server...
✅ Complete!
```

**Check progress:**
- QGIS Message Bar (bottom of window)
- QGIS Task Manager: `View → Panels → Task Manager` or `Plugins → TLGeo → Toggle TLGeo Panel`

### Migration from Synchronous Export

| Before | After |
|--------|-------|
| UI frozen during export | ✅ UI responsive |
| Blocking dialog | Background task |
| No progress feedback | Real-time progress |
| Single-threaded | Multi-threaded safe |

### Format Availability

| Format | Required Version | When Unavailable |
|--------|-----------------|-----------------|
| SQLite, SLD, Metadata | Any | Always exported |
| MBTiles | QGIS 3.14+ or GDAL with driver | Skipped with log |
| PMTiles | GDAL 3.8+ | Skipped with log |

### MBTiles Quality

The plugin uses multiple methods to export MBTiles with best available quality:

| Priority | Method | Quality | Zoom Level | Notes |
|----------|--------|---------|------------|-------|
| 1 | **tippecanoe** | ⭐ Highest | Auto (max detail) | Best quality if installed |
| 2 | QGIS native | High | 0-18 | Standard QGIS export |
| 3 | GDAL driver | Standard | Preserved | Fallback |

**Tippecanoe flags** (when available):
- `-zg`: Auto-calculate max zoom level for full detail
- `--drop-densest-as-needed`: Simplify overlapping features
- `--force`: Overwrite output

**QGIS Native improvements**:
- Increased from MAX_ZOOM 14 → **18** for more detail
- Added metadata: name, description, attribution, version

**To install tippecanoe** (recommended for best quality):
```bash
# macOS
brew install tippecanoe

# Linux
git clone https://github.com/felt/tippecanoe.git
cd tippecanoe && make && sudo make install
```

**To verify quality settings**:
Menu → TLGeo → Thông tin phiên bản

### Mapbox Style Export

The plugin can export layer styles as **Mapbox Style (JSON)** format using geostyler-cli.

**Requirements:**
- geostyler-cli installed: `npm install -g geostyler-cli`
- OR npx available (comes with Node.js)

**Command:**
```bash
# With geostyler-cli installed
geostyler-cli -s sld -t mapbox -o output.json input.sld

# With npx (no install)
npx geostyler-cli -s sld -t mapbox -o output.json input.sld
```

**Auto-detection:**
The plugin automatically detects if geostyler-cli or npx is available and exports Mapbox Style format automatically.

### Example Flow

```
1. User right-clicks layer → "TLGeo > Tải lên"
2. Plugin exports:
   - ✅ SQLite (EPSG:4326)
   - ✅ SQLite (Original)
   - ✅ SLD Style
   - ✅ Metadata JSON
   - ℹ️ MBTiles: Skipped (QGIS version)
   - ℹ️ PMTiles: Skipped (GDAL 3.8+ required)
3. Info message shown
4. Upload to GEOADMIN proceeds
5. Done!
```

### Check Available Formats

Menu → TLGeo → Thông tin phiên bản

This dialog shows which formats are available on your system.

## Export Directory

**Location**: `~/TLGeo_Exports/{UUID}/`

Example:
```
~/TLGeo_Exports/abc123-def456/
├── my_layer.metadata.json
├── my_layer_sqlite_4326.sqlite
├── my_layer_sqlite.sqlite
├── my_layer.sld
├── my_layer.mbtiles     (if supported)
└── my_layer.pmtiles    (if GDAL 3.8+)
```

## Troubleshooting

### Layer Not Uploaded

**Problem**: "TLGeo > Tải lên" doesn't appear in context menu

**Solutions**:
1. Verify plugin is activated: `Plugins → Manage and Install Plugins`
2. Check layer is a VectorLayer (raster layers not supported)
3. Restart QGIS

### Authentication Errors

| Error | Solution |
|-------|----------|
| "Bạn cần đăng nhập" | Restart plugin, login dialog appears |
| "401 Unauthorized" | Token expired, login again |
| "Upload failed" | Check network, verify GEOADMIN server running |

### MBTiles/PMTiles Not Exported

**Symptom**: Info message shows "Chưa hỗ trợ: MBTiles, PMTiles"

**Meaning**: Graceful fallback - plugin works normally

**What to do**:
- ✅ Nothing required - SQLite/SLD still exported and uploaded
- ℹ️ To enable: Upgrade QGIS or GDAL (see below)

### Format Availability

**Check which formats are available**:

```bash
# In QGIS, go to:
Menu → TLGeo → Thông tin phiên bản
```

This shows:
- QGIS version
- GDAL version
- Available export formats

### Upgrade for Advanced Formats

| Format | Upgrade Path |
|--------|--------------|
| MBTiles | Update to QGIS 3.14+ OR install GDAL with MBTiles driver |
| PMTiles | Upgrade to GDAL 3.8+ |

See [GDAL Upgrade Guide](GDAL_UPGRADE_GUIDE.md) for detailed instructions.

## API Reference

### Upload Endpoint

```
POST {STRAPI_URL}/api/upload
Headers: {
  "Authorization": "Bearer {JWT_TOKEN}"
}
Body: multipart/form-data {
  files: [file1, file2, ...],
  uuid: "{EXPORT_UUID}",
  layer_name: "{LAYER_NAME}"
}
Response: {
  "id": file_id,
  "url": "/uploads/..."
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `files` | File[] | Files to upload |
| `uuid` | String | Export UUID (for tracking) |
| `layer_name` | String | Original layer name |

## Related Documentation

- [Authentication Guide](AUTHENTICATION.md)
- [GDAL Upgrade Guide](GDAL_UPGRADE_GUIDE.md)
- [QGIS Versions & Export Capabilities](QGIS_VERSIONS.md)
- [Task 010: JWT Authentication](../_TASKS/04_completed/task_010_authentication_jwt.md)
- [Task 012: MBTiles/PMTiles Support](../_TASKS/02_in-progress/task_012_mbtiles_pmtiles_support.md)

## Source Code

| Component | File |
|-----------|------|
| Context Menu Provider | `src/layer_menu_provider.py` |
| Publish Widget | `src/app/projects/ui/publish_widget.py` |
| Background Task | `src/app/projects/tasks/layer_publish_task.py` |
| Main Plugin | `src/main.py` |
| Auth Service | `src/app/auth/util/auth_service.py` |
