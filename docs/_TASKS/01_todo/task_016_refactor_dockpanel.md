# Refactor TLGeo Dockpanel

**Status**: Completed
**Created**: 2026-01-24
**Updated**: 2026-01-24

## Description
Refactor the main TLGeo Dockpanel to replace the current UI with a Ribbon-style interface and a dynamic tabbed content area. This task also involves restructuring the project folder layout to a "Feature-First" (Vertical Slicing) architecture.

## Technical Requirements

### 1. Ribbon Menu System
**Location**: `TLGEO_PROJECTS/tlgeo2qgis/src/components/ribbon/`

Since Qt (PyQt5) does not provide a native Ribbon control, we will implement a custom solution.

**Proposed Components (Classes):**
*   `RibbonWidget` (Inherits `QWidget`): The main container.
    *   Layout: Vertical. Contains a Tab Bar (or QTabWidget) for categories (Home, View, Tools).
*   `RibbonTab` (Inherits `QWidget`): Represents a single category content.
    *   Fixed height (e.g., 90-100px).
    *   Layout: Horizontal (`QHBoxLayout`).
*   `RibbonGroup` (Inherits `QGroupBox` or `QWidget`): Grouping logic within a tab (e.g., "Connection", "Data").
*   `RibbonButton` (Inherits `QToolButton`):
    *   Style: Text under Icon (`ToolButtonTextUnderIcon`).
    *   Size: Large icons for primary actions.

### 2. Content Area & Tab Management
**Location**: `TLGEO_PROJECTS/tlgeo2qgis/src/components/tabs/` (Core logic)

*   **Component**: `QTabWidget` with `setTabsClosable(True)`.
*   **Key Utilities Needed (TabManager):**
    *   `addTab(widget, title, icon=None, closable=True)`: Adds a new tab. If a similar tab exists (optional check), focus on it instead.
    *   `closeTab(index_or_widget)`: Safely closes a tab and performs memory cleanup (`deleteLater`).
    *   `focusOnTab(index_or_widget)`: Sets the current active tab.
    *   **Signal Handling**: Automatically connect `tabCloseRequested` signal to the close utility.

### 3. Project Structure Refactoring
Transition from Layer-based (ui, utils) to **Business-Feature-based** organization.

**New Folder Structure (`src/`):**

```text
src/
├── components/          # Shared Generic UI Components
│   ├── ribbon/          # The new Ribbon system
│   └── tabs/            # The TabManager and generic Tab widgets
├── app/                 # Business Features (Vertical Slices)
│   ├── projects/        # Feature: Project Management
│   │   ├── ui/          # UI specific to Projects (e.g., ProjectList)
│   │   ├── util/        # Utils specific to Projects
│   │   └── tabs/        # Tab contents (e.g., ProjectMapTab)
│   ├── auth/            # Feature: Authentication
│   │   ├── ui/          # Login Dialogs
│   │   └── util/        # Auth logic
│   └── tools/           # Feature: GIS Tools
│       ├── ui/
│       └── tabs/
└── ui/                  # (Legacy/Main) Main application shell/entry points
```

## Architecture Diagram
```
MainDockWidget (QVBoxLayout)
├── RibbonWidget (src/components/ribbon)
│   ├── TabBar (Home, Edit, View)
│   └── StackedWidget (Current RibbonTab)
│       └── RibbonTab (Layout: Horizontal)
│           ├── RibbonGroup (Title: "Project")
│           │   ├── RibbonButton ("New") -> Calls app.projects.ui...
│           │   └── RibbonButton ("Open")
│           └── RibbonGroup (Title: "Data")
│               └── RibbonButton ("Layers")
└── ContentWidget (QTabWidget - Managed by TabManager)
    ├── Tab 1 (Project Map) -> Loaded from src/app/projects/tabs/
    └── Tab 2 (Tool Result) -> Loaded from src/app/tools/tabs/
```
