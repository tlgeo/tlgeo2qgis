# FRMS Menu Design

**Status**: Implemented  
**Created**: 2026-02-02  
**Version**: 1.0

## Overview

The FRMS (Forest Resource Management System) menu provides a comprehensive ribbon interface for managing forest data within QGIS. It follows the Windows Ribbon design pattern implemented in the TLGeo2QGIS plugin.

## Menu Structure

The FRMS ribbon tab contains **4 functional groups**:

### 1. Lô rừng (Forest Plots)
Management of forest plot boundaries and attributes.

| Button | Icon | Function | Description |
|--------|------|----------|-------------|
| **Tìm kiếm** | 🔍 Search | `frms_search_plots` | Search and filter forest plots by ID, name, attributes |
| Tạo mới | ➕ New | `frms_create_plot` | Create new forest plot geometry and attributes |
| Gộp | 🔗 Merge | `frms_merge_plots` | Merge multiple plots into one |
| Tách | ✂️ Split | `frms_split_plot` | Split one plot into multiple plots |
| Xóa | 🗑️ Delete | `frms_delete_plot` | Delete selected forest plots |

**Layout**:
- 1 Large Button: Tìm kiếm
- 2 Columns of Small Buttons:
  - Column 1: Tạo mới, Gộp, Tách
  - Column 2: Xóa

### 2. Chủ rừng (Forest Owners)
Management of forest ownership records.

| Button | Icon | Function | Description |
|--------|------|----------|-------------|
| **Tìm kiếm** | 🔍 Search | `frms_search_owners` | Search and filter forest owners |
| Tạo mới | ➕ New | `frms_create_owner` | Register new forest owner |
| Gộp | 🔗 Merge | `frms_merge_owners` | Merge duplicate owner records |
| Đổi mã | 🏷️ Rename | `frms_change_owner_code` | Change owner identification code |

**Layout**:
- 1 Large Button: Tìm kiếm
- 1 Column of Small Buttons: Tạo mới, Gộp, Đổi mã

### 3. Diễn biến (Forest Changes/Evolution)
Track changes in forest status over time.

| Button | Icon | Function | Description |
|--------|------|----------|-------------|
| **Tìm kiếm** | 🔍 Search | `frms_search_changes` | Search historical changes |
| **Tạo diễn biến** | 📊 Evolution | `frms_create_change` | Record new forest status change event |

**Layout**:
- 2 Large Buttons side-by-side

### 4. Báo cáo (Reports)
Generate and print forest management reports.

| Button | Icon | Function | Description |
|--------|------|----------|-------------|
| **In báo cáo** | 🖨️ Print | `frms_print_report` | Generate and print standard reports |

**Layout**:
- 1 Large Button

## Implementation Details

### File Locations

| Component | File Path |
|-----------|-----------|
| Ribbon Setup | `src/ui/dock_widget.py` → `TLGeoRibbonDock.setup_frms_ribbon()` |
| Action Handlers | `src/ui/dock_widget.py` → `TLGeoRibbonDock.frms_*()` methods |
| Widget Components | `src/app/tools/ui/frms_*.py` (to be created) |
| Ribbon Base Classes | `src/components/ribbon/ribbon_widget.py` |

### Code Pattern

```python
def setup_frms_ribbon(self):
    frms_tab = self.ribbon.add_tab("FRMS")
    
    # Group 1: Lô rừng
    lo_rung_group = frms_tab.add_group("Lô rừng")
    lo_rung_group.add_large_button("Tìm kiếm", icon, callback)
    col = lo_rung_group.add_column()
    col.add_small_button("Tạo mới", icon, callback)
    # ... more buttons
    
    frms_tab.add_stretch()
```

### Action Handler Pattern

Each ribbon button triggers an action method that:
1. Ensures content dock is visible
2. Opens appropriate widget in tab panel
3. Initializes widget with context (selected layer, features, etc.)

```python
def frms_search_plots(self):
    """Search forest plots"""
    self.ensure_content_visible()
    widget = self.open_tab_generic(FRMSSearchPlotsWidget, "Tìm kiếm lô rừng")
    widget.load_data()
```

## Icon Mapping

### QGIS Theme Icons Used

```python
# Search operations
"/mActionSearch.svg"

# Create/New operations
"/mActionNewAttribute.svg"
"/mActionAdd.svg"

# Merge operations
"/mActionMergeFeatures.svg"

# Split operations
"/mActionSplitFeatures.svg"

# Delete operations
"/mActionDeleteSelected.svg"

# Edit/Rename operations
"/mActionEditTable.svg"
"/mActionToggleEditing.svg"

# Evolution/Timeline
"/mActionCaptureLine.svg"
"/mActionHistory.svg"

# Print/Report
"/mActionFilePrint.svg"
"/mActionNewReport.svg"
```

### Fallback Pattern

```python
icon = QgsApplication.getThemeIcon("/mActionSearch.svg")
if icon.isNull():
    icon = QApplication.style().standardIcon(QStyle.SP_FileDialogContentsView)
```

## User Workflow

### Typical Forest Plot Management Flow

1. **Search** → Click "Tìm kiếm" in Lô rừng group
   - Opens search panel in bottom dock
   - Filter by ID, name, area, owner
   - Results shown in table
   - Double-click to zoom to feature

2. **Create** → Click "Tạo mới"
   - Activates digitizing mode
   - User draws polygon on map
   - Attribute form opens
   - Save to layer

3. **Merge** → Select plots → Click "Gộp"
   - Shows merge dialog
   - Choose target attributes
   - Merges geometries
   - Updates references

4. **Split** → Select plot → Click "Tách"
   - Activates split tool
   - User draws split line
   - Attribute distribution dialog
   - Creates new plots

5. **Delete** → Select plots → Click "Xóa"
   - Confirmation dialog
   - Checks references
   - Soft delete or hard delete option

## Integration with Existing Components

### FRMSToolsWidget

The existing `FRMSToolsWidget` contains:
- Tab 1: "Tra cứu & Xem" → Search functionality
- Tab 2: "Biên tập" → Merge owners functionality
- Tab 3: "Kiểm tra lỗi" → Validation

**Migration Strategy**:
- Extract search logic → `FRMSSearchPlotsWidget`, `FRMSSearchOwnersWidget`
- Extract merge logic → `FRMSMergeOwnersWidget`
- Keep validation tab as separate utility

### New Widgets to Create

1. `frms_search_plots_widget.py` - Forest plot search
2. `frms_search_owners_widget.py` - Owner search
3. `frms_search_changes_widget.py` - Change history search
4. `frms_merge_plots_widget.py` - Plot merge dialog
5. `frms_merge_owners_widget.py` - Owner merge dialog (extracted)
6. `frms_split_plot_widget.py` - Plot split tool
7. `frms_create_plot_widget.py` - Plot creation form
8. `frms_create_owner_widget.py` - Owner registration form
9. `frms_create_change_widget.py` - Change event form
10. `frms_report_widget.py` - Report generation

## Future Enhancements

### Phase 2 Features

- **Batch Operations**: Select multiple features for bulk edit
- **Import/Export**: Import plots from CAD/Shapefile
- **Validation Rules**: Real-time data validation
- **Workflow Approval**: Multi-step approval process
- **History Tracking**: Full audit trail
- **Map Integration**: Highlight features on map when selected in table

### Phase 3 Features

- **Mobile Sync**: Sync with mobile field data collection
- **3D Visualization**: Show forest plots in 3D
- **Analytics Dashboard**: Statistical reports and charts
- **AI Assistance**: Auto-detect topology errors
- **Cloud Backup**: Auto-backup to GEOADMIN cloud

## References

- [Microsoft Ribbon UX Guide](https://learn.microsoft.com/en-us/windows/win32/uxguide/cmd-ribbons)
- [Task 019: Implement Windows Ribbon](../docs/_TASKS/01_todo/task_019_implement_windows_ribbon.md)
- [Task 018: FRMS Advanced Tools](../docs/_TASKS/05_pending/task_018_frms_advanced_tools.md)
- [Ribbon Widget Implementation](../../src/components/ribbon/ribbon_widget.py)

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-02  
**Author**: TLGeo Development Team
