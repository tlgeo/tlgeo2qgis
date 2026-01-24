# TLGeo2QGIS Operational Workflow

This document describes the end-to-end workflow of the plugin, from user interaction to cloud publication.

## 1. High-Level Architecture

```
[ QGIS Client ]  ---(Upload PMTiles)-->  [ Strapi Server ]  ---(Serve Tiles)-->  [ Web/Mobile Apps ]
      |                                         |
(Local Processing)                         (Storage Only)
      |                                         |
   GDAL/Tippecanoe                          File System / S3
```

## 2. User Journey: "One-Click Publish"

### Step 1: Preparation
1.  User loads a Vector Layer in QGIS.
2.  User styles the layer (Symbology, Labels).
3.  User opens **TLGeo DockPanel**.

### Step 2: Environment Check (Automatic)
1.  Plugin checks: "Is `tippecanoe` or `gdal` available?"
2.  **Case A (Available):** "Ready to publish".
3.  **Case B (Missing):** Show "Install Tools" button in the DockPanel.
    *   *Action:* User clicks "Install", plugin downloads portable binary to `~/.qgis/tlgeo/bin/`.

### Step 3: Publishing
1.  User clicks **"Publish Layer"** button.
2.  **Background Process (QgsTask):**
    *   **Export:** QGIS Vector Layer -> GeoJSONSeq (Temp file).
    *   **Convert:** `tippecanoe -o output.pmtiles input.geojson`.
    *   **Metadata:** Extract Layer Name, Abstract, Extent.
3.  **Upload:**
    *   Plugin POSTs `.pmtiles` file to `/api/upload`.
    *   Plugin POSTs project data to `/api/map-projects`.

### Step 4: Result
1.  Server returns a unique URL (e.g., `https://maps.tlgeo.com/v/123`).
2.  Plugin displays success notification with:
    *   **QR Code** (for mobile scanning).
    *   **Clickable Link** (for browser).

## 3. Detailed Data Flow

### A. Local Conversion Strategy (Edge Computing)

| Input Format | Intermediate | Tool | Output Format | Notes |
| :--- | :--- | :--- | :--- | :--- |
| Shapefile | GeoJSONSeq | Tippecanoe | PMTiles | Best for large datasets, creates vector tiles. |
| PostGIS | GeoJSONSeq | Tippecanoe | PMTiles | Handles complex geometries well. |
| Raster (Tiff) | VRT | GDAL | MBTiles | (Future) For raster/orthophoto support. |

### B. Server Handling

The server (Strapi) acts as a **Passive Host**.
1.  Receive `multipart/form-data` upload.
2.  Store file in public uploads directory (or S3).
3.  Create DB record linking `MapProject` -> `Media File`.
4.  No background processing triggers on the server.

## 4. Error Handling

| Phase | Error | Recovery Action |
| :--- | :--- | :--- |
| **Check** | Tool missing | Guide user to "Tools" tab to install. |
| **Convert** | Disk full | Notify user to free space (check temp folder). |
| **Convert** | Invalid geometry | Tippecanoe auto-cleans simple errors; report fatal ones. |
| **Upload** | Network timeout | Retry mechanism (3 times) with exponential backoff. |
| **Upload** | Auth token expired | Trigger re-login flow automatically. |

## 5. Security Model

1.  **Authentication:**
    *   JWT Token obtained via Login.
    *   Token stored in `QgsSettings` (encrypted if possible, otherwise standard QGIS storage).
2.  **Data Privacy:**
    *   Raw data (GeoJSON) exists ONLY in temp folder during processing.
    *   Temp folder is securely deleted after upload (or failure).
3.  **Code Security:**
    *   Plugin logic is obfuscated (minified) in production builds.

---
**Last Updated:** Jan 24, 2026
