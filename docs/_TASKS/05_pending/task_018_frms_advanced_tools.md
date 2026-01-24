# FRMS Advanced Data Tools

**Status**: Pending
**Created**: 2026-01-24

## Description
Develop advanced data management and validation tools within `tlgeo2qgis` to supplement and enhance existing FRMS Desktop workflows. These tools focus on data viewing, searching, and fixing common issues that are currently difficult to handle in the standard FRMS Desktop application.

## Key Features

### 1. Advanced Data View (Tabular)
Implement high-performance table views for core datasets:
*   **Target Data**:
    *   **Lô rừng (Forest Plots)**
    *   **Chủ rừng (Forest Owners)**
*   **Features**:
    *   **Search Bar**: Real-time filtering and searching capabilities (by ID, Name, Location).
    *   **Sort & Filter**: Advanced sorting and multi-column filtering.

### 2. Data Editing Tools
*   **Merge Forest Owners (Gộp chủ rừng)**:
    *   UI to select multiple owner records.
    *   Logic to merge attributes and geometry (if applicable) into a single unique owner.
    *   Update references in related tables (e.g., Lô rừng linked to these owners).

### 3. Data Validation
*   **Validation Suite**: A set of automated checks to ensure data integrity.
*   **Common Checks**:
    *   Missing mandatory attributes.
    *   Duplicate IDs.
    *   Topology errors (overlaps, gaps) in Forest Plots.
    *   Reference integrity (e.g., Forest Plot referencing a non-existent Owner).
