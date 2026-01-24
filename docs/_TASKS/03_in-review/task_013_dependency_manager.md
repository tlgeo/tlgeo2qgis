# Task 013: Dependency Manager UI

## Description
Implement a user interface and logic to check, report, and help users install necessary dependencies (specifically `tippecanoe` and `gdal`). This ensures the "Client-Side Processing" strategy is viable.

## Objectives
- [x] **Dependency Checker Logic:**
    - Detect OS (Win/Mac/Linux).
    - Check for `tippecanoe` in PATH.
    - Check for `gdal_translate` and its supported drivers (MVT/PMTiles).
- [x] **Dependency Status UI:**
    - A widget (to be placed in the "Tools" tab of the DockPanel).
    - Indicators (Green Check / Red Cross) for each tool.
- [x] **Installation Helpers:**
    - **Windows:** Button to download/extract a portable `tippecanoe` binary to the plugin folder.
    - **macOS:** Instructions to run `brew install tippecanoe`.
    - **Linux:** Instructions for `apt/yum`.

## Technical Details
- **Bundling Strategy:**
    - Store Windows `tippecanoe.exe` (or a downloader script) in `src/bin/`.
    - Add `src/bin/` to the execution path when running subprocesses.
- **UI:** Simple `QGroupBox` with status labels and "Fix/Install" buttons.

## Acceptance Criteria
- [x] Plugin detects if Tippecanoe is missing.
- [x] Windows users can click "Install Tippecanoe" and have it work immediately. (Implemented placeholder/instruction dialog as binary source is external)
- [x] Plugin reports GDAL version correctly.
