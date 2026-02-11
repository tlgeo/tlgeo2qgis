# Architecture Overview

## System Architecture

TLGeo2QGIS is a QGIS plugin designed to integrate QGIS Desktop with the GEOADMIN ecosystem.

```mermaid
graph TD
    User[User] --> QGIS[QGIS Desktop]
    QGIS --> Plugin[TLGeo2QGIS Plugin]

    subgraph Plugin Components
        UI[User Interface]
        Auth[Auth Service]
        Layer[Layer Provider]
        Net[Network Util]
        FastAPI[FastAPI Server]
    end

    Plugin --> UI
    Plugin --> Auth
    Plugin --> Layer
    Plugin --> FastAPI

    Auth -->|JWT Auth| Strapi[GEOADMIN Strapi]
    Layer -->|Upload/Download| Strapi

    Strapi --> DB[(PostgreSQL)]
    Strapi --> S3[(MinIO/S3 Storage)]
```

## Core Components

### 1. Main Plugin Class (`TLGeoQGISPlugin`)
- **Location**: `src/main.py`
- **Responsibility**:
  - Initializes plugin UI and menus
  - Manages plugin lifecycle (init, unload)
  - Coordinates between Auth and Layer services
  - Handles User Profile display
  - Manages FastAPI server for remote commands

### 2. Authentication Service (`AuthService`)
- **Location**: `src/app/auth/util/auth_service.py`
- **Responsibility**:
  - Manages JWT tokens (Storage in `QSettings`)
  - Handles Login/Logout via `auth-ext` APIs
  - Validates tokens and retrieves user info
  - Provides security checks (HTTPS)

### 3. Layer Menu Provider (`TLGeoProvider`)
- **Location**: `src/layer_menu_provider.py`
- **Responsibility**:
  - Injects context menus into QGIS Layer Tree
  - Handles layer export (SQLite, MBTiles, PMTiles, SLD)
  - Manages file upload to Strapi with Authentication
  - Export location: `~/TLGeo_Exports/{uuid}/`
- **Graceful Fallback**: If MBTiles/PMTiles unavailable:
  - Shows info message (non-blocking)
  - Continues with SQLite/SLD/Metadata export
  - No dialogs interrupt user flow

### 4. Publish Widget (`PublishWidget`)
- **Location**: `src/app/projects/ui/publish_widget.py`
- **Responsibility**:
  - Dock widget for layer publishing
  - Shows layer information before upload
  - Progress tracking with background tasks

### 5. Layer Publish Task (`LayerPublishTask`)
- **Location**: `src/app/projects/tasks/layer_publish_task.py`
- **Responsibility**:
  - Background task for async layer processing
  - GeoJSON export → PMTiles conversion (tippecanoe) → Upload
  - Thread-safe implementation (QgsTask)

### 6. UI Components (`src/ui/`, `src/app/**/ui/`)
- **LoginDialog**: Custom dialog for authentication
- **QRCodeDialog**: For displaying mobile connection info
- **ToolsWidget**: Tools management interface

## Data Flow

### Authentication Flow

```mermaid
sequenceDiagram
    participant User
    participant Plugin
    participant AuthService
    participant Strapi

    User->>Plugin: Load Plugin
    Plugin->>AuthService: Check token
    AuthService->>QSettings: Read token
    alt Token exists
        AuthService->>Strapi: Validate token
        Strapi-->>AuthService: Valid
        Plugin->>User: Show plugin UI
    else No token / Invalid
        Plugin->>Plugin: Show Login Dialog
        User->>Plugin: Enter credentials
        Plugin->>AuthService: Login
        AuthService->>Strapi: POST /auth-ext/login
        Strapi-->>AuthService: JWT Token
        AuthService->>QSettings: Store token
        Plugin->>User: Show plugin UI
    end
```

### Layer Upload Flow (Right-Click Method)

```mermaid
sequenceDiagram
    participant User
    participant LayerTree
    participant TLGeoProvider
    participant ExportUtils
    participant Strapi

    User->>LayerTree: Right-click layer
    User->>LayerTree: Select "TLGeo > Tải lên"
    LayerTree->>TLGeoProvider: export_layer(layer)
    TLGeoProvider->>ExportUtils: Check capabilities
    ExportUtils-->>TLGeoProvider: MBTiles/PMTiles available?
    Note over TLGeoProvider: Graceful fallback: show info message if unavailable
    TLGeoProvider->>ExportUtils: Export SQLite (4326)
    TLGeoProvider->>ExportUtils: Export SQLite (Original)
    TLGeoProvider->>ExportUtils: Export SLD
    TLGeoProvider->>ExportUtils: Export Metadata JSON
    alt MBTiles available
        TLGeoProvider->>ExportUtils: Export MBTiles
    else MBTiles unavailable
        Note over TLGeoProvider: Skip with log message
    end
    alt PMTiles available
        TLGeoProvider->>ExportUtils: Export PMTiles
    else PMTiles unavailable
        Note over TLGeoProvider: Skip with log message
    end
    TLGeoProvider->>Strapi: POST /upload (with JWT)
    Strapi-->>TLGeoProvider: Upload confirmation
    TLGeoProvider->>User: Show success message
```

**Key Points:**
- **No blocking dialogs** when formats unavailable
- **Info message** shown in QGIS message bar
- **Continues seamlessly** with available formats
- **Upload proceeds** regardless of format availability

### Publish Widget Flow (Background Task)

```mermaid
sequenceDiagram
    participant User
    participant PublishWidget
    participant LayerPublishTask
    participant Tippecanoe
    participant Strapi

    User->>PublishWidget: Click "Xuất bản lớp"
    PublishWidget->>LayerPublishTask: Start task (layer, token, url)
    LayerPublishTask->>LayerPublishTask: Export GeoJSON
    LayerPublishTask->>Tippecanoe: Convert to PMTiles
    Tippecanoe-->>LayerPublishTask: PMTiles file
    LayerPublishTask->>Strapi: Upload PMTiles
    Strapi-->>LayerPublishTask: File ID
    LayerPublishTask->>Strapi: Create Map Project
    Strapi-->>LayerPublishTask: Project ID
    LayerPublishTask-->>PublishWidget: Complete signal
    PublishWidget->>User: Show success dialog
```

## Export Formats & Requirements

| Format | File Extension | Driver/Method | Minimum Version |
|--------|---------------|---------------|-----------------|
| SQLite | `.sqlite` | `QgsVectorFileWriter` | Any |
| SLD | `.sld` | `layer.saveSldStyle()` | Any |
| MBTiles | `.mbtiles` | `native:writevectortiles_mbtiles` | QGIS 3.14 |
| MBTiles (GDAL) | `.mbtiles` | `QgsVectorFileWriter` | GDAL with driver |
| PMTiles | `.pmtiles` | `QgsVectorFileWriter` | GDAL 3.8 |

## File Structure

```
src/
├── __init__.py                    # Plugin entry point
├── main.py                        # TLGeoQGISPlugin class
├── layer_menu_provider.py         # TLGeoProvider (context menu)
├── logo.png                       # Plugin icon
├── metadata.txt                   # QGIS plugin metadata
│
├── app/
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── ui/
│   │   │   ├── __init__.py
│   │   │   ├── login_dialog.py    # Login dialog
│   │   │   └── profile_widget.py  # User profile
│   │   └── util/
│   │       ├── __init__.py
│   │       └── auth_service.py    # JWT management
│   │
│   ├── projects/
│   │   ├── __init__.py
│   │   ├── ui/
│   │   │   ├── __init__.py
│   │   │   ├── publish_widget.py  # Publish dock widget
│   │   │   └── project_list_widget.py
│   │   ├── tasks/
│   │   │   ├── __init__.py
│   │   │   └── layer_publish_task.py  # Background task
│   │   └── util/
│   │       ├── __init__.py
│   │       └── project_service.py
│   │
│   └── tools/
│       ├── __init__.py
│       ├── ui/
│       │   ├── __init__.py
│       │   ├── tools_widget.py
│       │   ├── qr_code_dialog.py   # QR for mobile connect
│       │   └── gdal_update_dialog.py
│       └── util/
│           ├── __init__.py
│           ├── dependency_checker.py
│           └── gdal_installer.py
│
├── components/
│   ├── tabs/
│   │   └── tab_manager.py
│   └── ribbon/
│       └── ribbon_widget.py
│
├── ui/
│   ├── __init__.py
│   └── dock_widget.py             # TLGeoContentDock, TLGeoRibbonDock
│
└── util/
    ├── __init__.py
    ├── fastapi_server.py          # Remote control server
    └── net_util.py                # Network utilities
```

## Tech Stack

- **Language**: Python 3.9+ (QGIS environment)
- **UI Framework**: PyQt5
- **Networking**: `requests` library
- **GIS Core**: `qgis.core`, `qgis.gui`
- **Build System**: Bash scripts + python-minifier (for production)
- **Task Management**: `QgsTask` for background operations
- **Web Server**: FastAPI + Uvicorn (for remote commands)

## Related Documentation

- [Layer Upload Guide](../guides/LAYER_UPLOAD.md)
- [Authentication Guide](../guides/AUTHENTICATION.md)
- [GDAL Upgrade Guide](../guides/GDAL_UPGRADE_GUIDE.md)
- [QGIS Versions & Export Capabilities](../guides/QGIS_VERSIONS.md)
