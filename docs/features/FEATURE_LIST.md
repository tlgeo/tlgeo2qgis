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

- **Export Layers**:
  - Export vector layers to SQLite (both EPSG:4326 and original CRS).
  - Export Metadata (JSON format).
  - Export SLD Styles.
- **Cloud Upload**:
  - Direct upload of exported layers to GEOADMIN Cloud.
  - Authentication integration for secure uploads.
- **Format Support**:
  - **Vector**: SQLite, GeoJSON.
  - **Tiles**: MBTiles, PMTiles (via GDAL/Processing).

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
