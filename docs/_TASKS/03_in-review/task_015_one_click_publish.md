# Task 015: One-Click Publish Workflow (Background Engine)

## Description
Implement the core logic to convert, package, and upload map layers in the background without freezing the QGIS user interface.

## Objectives
- [ ] **Background Task Wrapper (`QgsTask`):**
    - Create `LayerPublishTask` class.
    - Handle threading (no GUI updates from background thread).
    - Signals: `progressChanged`, `taskCompleted`, `taskTerminated`.
- [ ] **Conversion Logic:**
    - Use `subprocess` to call `tippecanoe` or `gdal_translate`.
    - Input: `QgsVectorLayer` -> GeoJSONSeq -> PMTiles.
- [ ] **Upload Logic:**
    - Upload resulting `.pmtiles` file to Strapi (`POST /api/upload`).
    - Create map project (`POST /api/map-projects`).
- [ ] **Notifications:**
    - Show QGIS Message Bar notifications (Success/Fail).
    - Update the "Publish" tab in DockPanel with real-time status.

## Technical Details
- **Threading:** QGIS runs Python plugins in the main thread. Heavy IO/CPU tasks MUST be moved to `QgsTask`.
- **Progress Reporting:** Parse stdout from `tippecanoe` to update progress bar.

## Acceptance Criteria
- [ ] Clicking "Publish" creates a background task.
- [ ] QGIS UI remains responsive during conversion/upload.
- [ ] Progress bar updates in the DockPanel.
- [ ] Success message contains a clickable link to the web map.
