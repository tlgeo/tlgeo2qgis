# Task 012: UI Modernization (Toolbar & DockPanel)

## Description
Transform the plugin interface from a simple Menu-based system to a modern, integrated QGIS UI using a **Toolbar** for quick actions and a **DockPanel** (QgsDockWidget) for the main workspace.

## Objectives
- [x] **Create TLGeo Toolbar:**
    - Add icons for: Toggle Panel, Publish Active Layer, User Profile.
- [x] **Implement Main DockPanel:**
    - Create `TLGeoDockWidget` class.
    - Dockable on left/right of QGIS.
    - Use `QTabWidget` to organize content:
        - Tab 1: **Projects** (List of cloud projects).
        - Tab 2: **Publish** (Current layer status).
        - Tab 3: **Tools** (Dependency check).
- [x] **Refactor Existing Dialogs:**
    - Move "User Profile" info into the DockPanel (or keep as small popup but triggered from Toolbar).
    - Move "QR Code/Remote IP" to a status area in the DockPanel.

## Technical Details
- **Class:** `TLGeoDockWidget` inherits `QgsDockWidget`.
- **UI File:** Use `.ui` file (Qt Designer) or pure Python code (PyQt5). *Recommendation: Pure Python for easier minification maintenance.*
- **State Persistence:** Save visibility state of DockPanel between QGIS sessions.

## Acceptance Criteria
- [x] Toolbar appears in QGIS toolbar area.
- [x] Clicking main icon toggles the DockPanel.
- [x] DockPanel can be docked/floated.
- [x] Old Menu items still work but delegate to the new UI structure where appropriate.
