# 🚀 TLGeo2QGIS Product Strategy & Roadmap

**Date:** Jan 24, 2026  
**Status:** Approved  
**Version:** 1.1 (Revised: Client-Side Focus)

This document outlines the strategic direction, product positioning, and development roadmap for the `tlgeo2qgis` plugin. It serves as a guide for technical decisions and feature prioritization.

---

## 1. Product Positioning

`tlgeo2qgis` is the **Edge Publishing Engine** for the TLGeo ecosystem.

**Core Value Proposition:**  
"One-Click to Cloud". Empower GIS specialists to process, package, and publish map data directly from their local QGIS workstation to the GeoCloud. The plugin handles all the heavy lifting (conversion, tiling, packaging) locally, ensuring the server remains lightweight and cost-efficient.

---

## 2. SWOT Analysis

| **Strengths (Internal)** | **Weaknesses (Internal)** |
| :--- | :--- |
| ✅ **Cost Efficiency:** Zero server-side processing costs. Server acts as pure storage.<br>✅ **Privacy:** Raw vector data never leaves the user's machine; only optimized tiles are uploaded.<br>✅ **Scalability:** System scales infinitely with users, as processing power is distributed to clients.<br>✅ **Security:** JWT Auth & Code Obfuscation implemented. | ❌ **Dependency Management:** Heavy reliance on local tools (GDAL/Tippecanoe). Windows environment is challenging.<br>❌ **Client Hardware:** Performance depends on user's PC specs.<br>❌ **One-way Sync:** No real-time bi-directional editing (Publish only). |

| **Opportunities (External)** | **Threats (External)** |
| :--- | :--- |
| 🚀 **Cloud Native Formats:** PMTiles allows serverless hosting and instant viewing.<br>🚀 **Offline Capabilities:** Generated files can be easily shared for offline mobile use.<br>🚀 **Workflow Automation:** Reduce the "GIS to Web" workflow from hours to seconds. | ⚠️ **Tooling Fragmentation:** Different versions of QGIS bundle different GDAL versions.<br>⚠️ **Network Bandwidth:** Uploading large tiled archives requires stable internet. |

---

## 3. Strategic Direction: "Client-Side Edge Processing"

We are adopting a **Thick Client / Thin Server** architecture.

### The Strategy
The QGIS Plugin is the "Factory". The Server is the "Showroom".

1.  **Local Processing:** All data conversion (Vector -> GeoJSON -> PMTiles/MBTiles) happens on the user's machine using local resources.
2.  **Ready-to-View Artifacts:** The plugin produces highly optimized "Cloud Native" artifacts (PMTiles) that require no server-side processing.
3.  **Smart Sync:** The plugin uploads the artifact + metadata. The server simply stores the file and creates a `MapProject` record with a shareable URL.

### Key Logic Flow
1.  **Check:** Does user have `tippecanoe` or `gdal`? (If not, guide/auto-install).
2.  **Convert:** Run background process to generate `.pmtiles`.
3.  **Upload:** Push `.pmtiles` to Storage.
4.  **Link:** Get `https://maps.tlgeo.com/view/123` and open in browser.

---

## 4. Development Roadmap

### Phase 1: Stability & UX (Immediate)
*Goal: Ensure the plugin runs smoothly without freezing QGIS.*

- [ ] **Background Tasks (Critical):** Move all export/upload logic to `QgsTask` to prevent UI freezing. Add progress bars.
- [ ] **Robust Error Handling:** Improve error messages (Network timeouts, Permission issues).
- [ ] **Auto-Update Mechanism:** Notify users when a new plugin version is available.

### Phase 2: The "Local Factory" Engine (Short Term)
*Goal: Enable robust local processing on all platforms.*

- [ ] **Dependency Manager:**
    - Detect local GDAL version.
    - Bundle or auto-download `tippecanoe` binary for Windows/Mac (if feasible) to ensure consistent tiling.
- [ ] **Format Converter:**
    - Implement logic to convert QgsVectorLayer -> PMTiles locally.
    - Fallback to MBTiles or SQLite if PMTiles is not supported.

### Phase 3: "One-Click Publish" (Medium Term)
*Goal: The "Magic Button".*

- [ ] **Publish API Integration:**
    - Upload endpoint (Multipart).
    - Project Creation endpoint.
- [ ] **Result Viewer:**
    - Show QR Code and URL immediately after upload.
    - "Open in Browser" button.
- [ ] **Upload Manager:** Simple list of previously uploaded layers with their links.

---

## 5. Technical Decision Records (ADR)

### ADR-001: Python Minification
*   **Decision:** Use `python-minifier`.
*   **Reason:** Ensures 100% compatibility across all QGIS/OS versions while providing IP protection.

### ADR-002: Background Threading
*   **Decision:** All IO/Processing must use `QgsTask`.
*   **Reason:** Prevents QGIS UI freeze during heavy local processing.

### ADR-003: Client-Side Processing (Edge Computing)
*   **Decision:** Perform all tiling and data conversion on the client.
*   **Reason:**
    1.  **Cost:** Drastically reduces server infrastructure costs (no heavy CPU workers needed).
    2.  **Performance:** PMTiles/MBTiles are optimized for reading; Server just serves byte-ranges.
    3.  **Simplicity:** Server architecture remains simple (CRUD + Storage).

### ADR-004: Tool Bundling Strategy
*   **Decision:** Try to bundle or download portable `tippecanoe`/`gdal` executables for Windows.
*   **Reason:** Windows QGIS environments are inconsistent. Relying on system paths is unreliable.

---

## 6. Action Plan (Next Steps)

1.  **Task 012 (Dependency Manager):** Build the logic to check and acquire necessary tools (tippecanoe/gdal) on the client.
2.  **Task 013 (Background Converter):** Implement the `QgsTask` wrapper for running these tools asynchronously.
3.  **Testing:** Setup Windows VM to test the "Tool Bundling" strategy (critical path).

---
*Authorized by Project Manager*
