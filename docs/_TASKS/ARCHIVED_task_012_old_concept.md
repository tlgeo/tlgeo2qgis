# Task 012: Smart Publishing Workflow (Client-Side Processing)

## Description
Implement a robust "One-Click Publish" workflow that processes data locally on the QGIS client (convert to PMTiles/MBTiles) and uploads the "ready-to-view" artifacts to the server. This moves the processing burden from the server to the client (Edge Computing).

## Objectives
- [ ] **Dependency Check:** Detect if user has necessary tools (GDAL 3.8+ OR Tippecanoe).
- [ ] **Background Processing:** Use `QgsTask` to convert layers without freezing QGIS UI.
- [ ] **Smart Format Selection:** Automatically choose the best format (PMTiles > MBTiles > GeoJSON) based on available tools.
- [ ] **Publish API:** Upload processed files + metadata to create a web map project instantly.

## Workflow

1.  **User Action:** Right-click layer -> "TLGeo > Publish to Cloud".
2.  **Environment Check:** Plugin checks for `gdal_translate` (with PMTiles support) or `tippecanoe`.
3.  **Processing (Background):**
    *   Export Vector Layer -> GeoJSONSeq (Intermediate).
    *   Convert -> PMTiles (using Tippecanoe/GDAL).
    *   *Feedback:* Progress bar in QGIS status bar.
4.  **Upload (Background):** Upload the generated `.pmtiles` file to Strapi.
5.  **Completion:** Show notification with link: "Map published! Click to view."

## Technical Implementation

### 1. Tool Detection (`util/dependency_checker.py`)
Need a robust way to find executables on Windows/Mac/Linux.

```python
def check_capabilities():
    # Check 1: GDAL Version & Drivers
    # Check 2: Tippecanoe (if installed via brew/apt or bundled)
    return {
        "can_generate_pmtiles": bool,
        "tool": "gdal" | "tippecanoe" | None
    }
```

### 2. Background Task (`util/async_processor.py`)
Must subclass `QgsTask` to run subprocesses off the main thread.

```python
class LayerPublishTask(QgsTask):
    def run(self):
        # 1. Export to temp file
        # 2. Run conversion command
        # 3. Upload
        return True
        
    def finished(self, result):
        if result:
            notify_success()
        else:
            notify_error()
```

### 3. Server Integration
*   **Endpoint:** `POST /api/map-projects`
*   **Body:**
    *   `name`: Layer Name
    *   `description`: Abstract
    *   `file`: (Binary attachment)
*   **Response:** `{ "url": "https://geocloud.com/maps/123", "id": 123 }`

## Dependencies
*   **External Tools:** `tippecanoe` (preferred for vector tiles) or `GDAL 3.8+`.
*   **Python Libs:** `requests` (already installed).

## UX Considerations
*   **Windows Users:** Most likely won't have `tippecanoe`. We might need to rely on `gdal_translate` (if QGIS is new enough) or guide them to install a tool.
*   **Large Files:** What if the file is 500MB? Need chunked upload or just standard multipart for now? (Start with standard).

## Acceptance Criteria
- [ ] Plugin correctly identifies if PMTiles generation is possible.
- [ ] Layer export runs in background (QGIS remains responsive).
- [ ] Progress bar updates accurately.
- [ ] Upload succeeds and returns a valid URL.
- [ ] Error handling covers "Missing Tools" and "Network Failures".
