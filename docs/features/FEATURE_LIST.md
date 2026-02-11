# Features List

## 🔐 Authentication & Security

- **Secure Login**: JWT-based authentication with GEOADMIN Strapi.
- **Session Management**: Persistent login sessions across QGIS restarts.
- **User Profile**: View authenticated user information directly in QGIS.
- **Security**:
  - HTTPS support (with warnings for HTTP).
  - Credentials masking (passwords not stored).
  - Token-based API access.

## 🗺️ Layer Management

### Export Formats

| Format | Type | Description | Availability | Behavior When Unavailable |
|--------|------|-------------|--------------|--------------------------|
| **SQLite (EPSG:4326)** | Vector | Geopackage-compatible SQLite with WGS84 CRS | ✅ Always available | Background task, non-blocking UI |
| **SQLite (Original)** | Vector | SQLite with original layer CRS | ✅ Always available | Background task, non-blocking UI |
| **SLD Style** | Style | OGC SLD styling export | ✅ Always available | N/A |
| **QML Style** | Style | QGIS Layer Style format | ✅ Always available | N/A |
| **Mapbox Style** | Style | Mapbox GL JSON style format | ⚠️ geostyler-cli required | Auto-export after SLD if available |
| **Metadata JSON** | Config | Layer metadata (name, CRS, fields, extent) | ✅ Always available | N/A |
| **GeoJSON** | Vector | Standard GeoJSON format (via Publish Widget) | ✅ Always available | N/A |
| **MBTiles** | Vector Tiles | Vector tile format for web mapping | ⚠️ QGIS 3.14+ or GDAL driver | ⭐ tippecanoe fallback for best quality, MAX_ZOOM 18 |
| **PMTiles** | Vector Tiles | Cloud-optimized vector tiles | ⚠️ GDAL 3.8+ required | ℹ️ Skip with log message |

### Graceful Fallback Behavior

When advanced formats (MBTiles/PMTiles) are not available:

1. **Info message** appears in QGIS message bar (non-blocking)
2. **SQLite, SLD, Metadata** are still exported normally
3. **Upload proceeds** to GEOADMIN as usual
4. **QGIS Log** shows which formats were skipped

No dialogs interrupt the user flow. The plugin continues seamlessly.

### Layer Upload Methods

#### Method 1: Right-Click Context Menu
- **Location**: QGIS Layer Tree → Right-click on layer
- **Menu Item**: `TLGeo > Tải lên`
- **Flow**: Export → Upload automatically
- **Export Location**: `~/TLGeo_Exports/{uuid}/`
- **Graceful Fallback**: If MBTiles/PMTiles unavailable:
  - Shows simple info message
  - Continues with SQLite/SLD/Metadata export
  - No blocking dialogs

#### Method 2: Publish Widget (Dock Panel)
- **Location**: TLGeo Panel → Publish Tab
- **Features**:
  - View selected layer info
  - Progress bar with real-time status
  - Background task execution (non-blocking)
  - Success/error feedback

#### Method 3: Background Task (LayerPublishTask)
- **Location**: `src/app/projects/tasks/layer_publish_task.py`
- **Flow**: GeoJSON → PMTiles (via tippecanoe) → Upload
- **Used by**: Publish Widget for async processing

## 🔌 Integration

- **QGIS Integration**:
  - Seamless menu integration (Layer Tree context menu, Main Menu).
  - Uses QGIS Network Access Manager and Proxy settings.
- **Web Server**:
  - Embedded FastAPI server for receiving commands from external apps (e.g., Mobile App).
  - QR Code generation for easy mobile connection.

## 🛠️ Developer Tools

- **Build System**:
  - Automated build scripts (`build.sh`).
  - Support for Development (source) and Production (obfuscated) builds.
- **Obfuscation**:
  - PyArmor integration for IP protection.

## 📁 File Outputs

### Export Directory Structure

```
~/TLGeo_Exports/{uuid}/
├── {layer_name}.metadata.json      # Layer metadata
├── {layer_name}_sqlite_4326.sqlite  # SQLite (WGS84)
├── {layer_name}_sqlite.sqlite       # SQLite (Original CRS)
├── {layer_name}.sld                 # SLD Style
├── {layer_name}.mbtiles             # Vector Tiles (if supported)
└── {layer_name}.pmtiles             # PMTiles (if GDAL 3.8+)
```

### Metadata Schema

```json
{
  "name": "Layer Name",
  "type": "vector",
  "crs": "EPSG:4326",
  "crs_description": "WGS 84",
  "extent": {
    "xmin": -180,
    "ymin": -90,
    "xmax": 180,
    "ymax": 90
  },
  "feature_count": 1500,
  "geometry_type": 2,
  "geometry_type_name": "Polygon",
  "fields": [
    {
      "name": "id",
      "type": "integer",
      "length": 10,
      "precision": 0
    }
  ],
  "export_uuid": "uuid-string"
}
```
