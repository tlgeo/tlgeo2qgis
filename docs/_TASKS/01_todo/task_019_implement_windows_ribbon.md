# Implement Windows-Style Ribbon Interface

**Status**: Todo
**Created**: 2026-01-24
**Reference**: [Microsoft UX Guide - Ribbons](https://learn.microsoft.com/en-us/windows/win32/uxguide/cmd-ribbons)

## Description
Implement a high-fidelity "Windows Ribbon" interface for the `tlgeo2qgis` plugin, strictly adhering to the UX principles and visual hierarchy defined in the Microsoft Windows User Experience Interaction Guidelines.

## Key Design Principles
*   **Command Exposure**: Replace menus/toolbars with a results-oriented command surface.
*   **Hierarchy**: Application Menu -> Tabs -> Groups -> Controls.
*   **Resizing/Layout**: Dynamic resizing (Flow layout behavior).

## Detailed Technical Implementation

### 1. Core Component Classes
**Location**: `src/components/ribbon/`

| Class Name | Inherits | Responsibility & Implementation Strategy |
| :--- | :--- | :--- |
| **`RibbonWidget`** | `QWidget` | **Root Container**. <br>- **Layout**: `QVBoxLayout`.<br>- **Components**: <br>  1. Top: `RibbonTabBar` (Custom styled QTabBar).<br>  2. Bottom: `QStackedWidget` (Holds the content of active tab).<br>- **Logic**: Manages tab switching, context tab visibility (e.g., show "Map Tools" only when map is selected). |
| **`RibbonTabBar`** | `QTabBar` | **Custom Tab Bar**.<br>- **Style**: Remove bottom border, add top accent color for active tab.<br>- **Features**: <br>  - `addContextTab(title, color)`: Adds tabs with specific background colors (e.g., Orange for "Table Tools").<br>  - `setApplicationButton(btn)`: The "File" menu button on the far left. |
| **`RibbonTabContent`** | `QWidget` | **The Panel Area**.<br>- **Height**: Fixed (e.g., 90px-110px).<br>- **Layout**: `QHBoxLayout` (Left aligned, no spacing between groups).<br>- **Background**: Light gray/gradient to match Windows style. |
| **`RibbonGroup`** | `QFrame` | **Functional Grouping** (e.g., "Clipboard").<br>- **Layout**: `QHBoxLayout` (for internal buttons).<br>- **Visuals**: <br>  - Vertical separator lines on right edge.<br>  - Label at the bottom center (using `QLabel`).<br>  - **OptionButton**: Small icon at bottom-right (Dialog Launcher) implemented as `QToolButton`. |
| **`RibbonButton`** | `QToolButton` | **Action Button**.<br>- **Modes**:<br>  1. `Large`: `ToolButtonTextUnderIcon` (32px icon).<br>  2. `Small`: `ToolButtonTextBesideIcon` (16px icon) - Used in vertical stacks.<br>  3. `Dropdown`: Supports `setMenu(QMenu)`. |
| **`RibbonGallery`** | `QScrollArea` | **Visual Choice List**.<br>- **Usage**: For selecting Map Themes or Styles visually.<br>- **Layout**: Grid of clickable image thumbnails. |

### 2. Layout Strategy (Group Internals)
To achieve the "3 small buttons stack equal 1 large button" look:

*   **`RibbonColumn`** (Helper Class):
    *   Inherits: `QWidget`.
    *   Layout: `QVBoxLayout` (Spacing: 0, Margins: 0).
    *   Usage: Put 2 or 3 `RibbonButton` (Small mode) inside this column, then add the Column to the `RibbonGroup`.

### 3. Styling (QSS)
Create `src/ui/styles/ribbon.qss` to handle:
*   **Gradients**: Subtle vertical gradients on `RibbonTabContent`.
*   **Separators**: 1px solid lines `rgba(0,0,0,0.1)`.
*   **Hover Effects**: Light blue overlay on `RibbonButton` hover.
*   **Typography**: Segoe UI / San Francisco (System font), 11px for Group labels (gray), 12px for Button labels (black).

### 4. Application Menu ("File")
*   **Class**: `RibbonFileMenu` (Inherits `QMenu` or `QWidget` popup).
*   **Trigger**: The first distinct tab/button on the Ribbon.
*   **Content**: Vertical list of commands (New Project, Open, Save As, Settings, Exit).

## Example Usage Code
```python
ribbon = RibbonWidget()

# 1. Create Home Tab
home_tab = ribbon.addTab("Home")

# 2. Add "Project" Group
project_group = home_tab.addGroup("Project")
project_group.addLargeButton("Save", "save_icon.png", callback=save_project)

# 3. Add "Edit" Group with Stacked Buttons
edit_group = home_tab.addGroup("Edit")
edit_group.addLargeButton("Paste", "paste.png")
# Column of small buttons
col = edit_group.addColumn()
col.addSmallButton("Cut", "cut.png")
col.addSmallButton("Copy", "copy.png")

dock_layout.addWidget(ribbon)
```
