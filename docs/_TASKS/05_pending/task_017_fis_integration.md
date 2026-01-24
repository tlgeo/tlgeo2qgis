# FIS Integration (FRMS Input)

**Status**: Pending
**Created**: 2026-01-24

## Description
Integrate `tlgeo2qgis` as an input source for the Forest Information System (FIS).

## Key Features

1.  **FRMS Plugin Detection**:
    - Add a capability (e.g., a button or startup check) to detect if the **FRMS** (Forest Resource Management System) plugin is currently installed and active within QGIS.

2.  **Data Transmission**:
    - If the FRMS plugin is detected, enable functionality to send selected data (layers, projects, or attributes) from `tlgeo2qgis` directly to the FIS system.
    - This creates a bridge where `tlgeo2qgis` prepares/fetches data and passes it to the FRMS workflow.
