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

## Graceful Fallback

When MBTiles/PMTiles formats are not available (due to older QGIS/GDAL versions), the plugin handles it gracefully:

1. **Info message** appears: "Đã xuất SQLite/SLD. (Chưa hỗ trợ: MBTiles, PMTiles)"
2. **SQLite, SLD, Metadata** are exported normally
3. **Upload proceeds** to GEOADMIN as usual
4. **No blocking dialogs** - user flow continues seamlessly

### Format Availability

| Format | Required Version | When Unavailable |
|--------|-----------------|-----------------|
| SQLite, SLD, Metadata | Any | Always exported |
| MBTiles | QGIS 3.14+ or GDAL with driver | Skipped with log |
| PMTiles | GDAL 3.8+ | Skipped with log |

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
