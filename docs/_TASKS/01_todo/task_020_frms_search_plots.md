# FRMS: Tìm kiếm lô rừng (Search Forest Plots)

**Status**: Todo  
**Created**: 2026-02-02  
**Priority**: High  
**Estimated Effort**: 8 hours  
**Related**: FRMS Menu Implementation, Task 018

## Description

Implement advanced search functionality for forest plots (Lô rừng) with interactive table display, map synchronization, and context menu operations.

## User Story

> **As a** forest manager  
> **I want to** search and filter forest plots by various criteria  
> **So that** I can quickly find specific plots and view them on the map

## Acceptance Criteria

- [ ] Search widget displays in TLGeo Content Dock when "Tìm kiếm" button clicked
- [ ] Table shows all forest plot records from active layer
- [ ] Search box filters data in real-time (ID, name, area, owner, etc.)
- [ ] Click on table row → Map zooms to selected plot
- [ ] Double-click row → Opens detail dialog
- [ ] Right-click row → Shows context menu with actions
- [ ] Table is sortable by all columns
- [ ] Performance: Handles 10,000+ records smoothly

## Technical Implementation

### 1. File Structure

**Create**: `src/app/tools/ui/frms_search_plots_widget.py`

```python
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView,
    QLineEdit, QLabel, QComboBox, QPushButton, QMenu, QAction,
    QMessageBox, QHeaderView
)
from PyQt5.QtCore import Qt, QSortFilterProxyModel
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from qgis.core import QgsProject, QgsVectorLayer, QgsFeature
from qgis.utils import iface

class FRMSSearchPlotsWidget(QWidget):
    """
    Search and display forest plots with map synchronization.
    
    Features:
    - Real-time search filtering
    - Click row → Zoom to feature
    - Context menu with plot actions
    - Sortable columns
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.current_layer = None
        
    def init_ui(self):
        """Initialize the user interface"""
        # Main layout
        # Search controls
        # Table view with proxy model
        # Status label
        
    def load_plots(self, layer=None):
        """Load forest plot data from layer"""
        # Auto-detect layer if not provided
        # Populate table model
        # Update status
        
    def on_search_text_changed(self, text):
        """Filter table data"""
        self.proxy_model.setFilterFixedString(text)
        
    def on_row_clicked(self, index):
        """Zoom to feature on map"""
        # Get feature ID from UserRole
        # Select feature on layer
        # Zoom map canvas
        
    def on_row_double_clicked(self, index):
        """Show detailed information"""
        # Open detail dialog
        
    def show_context_menu(self, pos):
        """Display context menu on right-click"""
        # Create menu with actions:
        # - Chi tiết (Detail)
        # - Zoom tới (Zoom to)
        # - Tạo mới (Create new)
        # - Gộp (Merge)
        # - Tách (Split)
        # - Xóa (Delete)
        
    def zoom_to_feature(self):
        """Zoom map to selected feature"""
        # Pattern from frms_tools_widget.py:
        # index = self.table_view.currentIndex()
        # source_index = self.proxy_model.mapToSource(index)
        # item = self.table_model.item(row, 0)
        # fid = item.data(Qt.UserRole)
        # layer.selectByIds([fid])
        # iface.mapCanvas().zoomToSelected(layer)
        
    def show_detail_dialog(self):
        """Show detailed attribute form"""
        
    def create_new_plot(self):
        """Launch plot creation tool"""
        # Open frms_create_plot_widget
        
    def merge_plots(self):
        """Launch merge plots tool"""
        # Check multiple selection
        # Open frms_merge_plots_widget
        
    def split_plot(self):
        """Launch split plot tool"""
        # Open frms_split_plot_widget
        
    def delete_plot(self):
        """Delete selected plot(s)"""
        # Confirmation dialog
        # Check references
        # Delete from layer
```

### 2. Integration Points

**In**: `src/ui/dock_widget.py`

```python
# Replace placeholder method:
def frms_search_plots(self):
    """Search forest plots"""
    from ..app.tools.ui.frms_search_plots_widget import FRMSSearchPlotsWidget
    self.open_tab_generic(FRMSSearchPlotsWidget, "Tìm kiếm lô rừng")
```

### 3. UI Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Tìm kiếm lô rừng                                      [X]    │
├─────────────────────────────────────────────────────────────┤
│ Lớp: [Dropdown: lo_rung] [🔄 Làm mới]                      │
│ Tìm: [________________________] 🔍                           │
├─────────────────────────────────────────────────────────────┤
│ ID      │ Tên lô    │ Diện tích │ Chủ rừng      │ Loại...   │
├─────────┼───────────┼───────────┼───────────────┼──────...  │
│ LR0001  │ Lô A1     │ 12.5 ha   │ Nguyễn Văn A  │ Sản xuất  │
│ LR0002  │ Lô B2     │ 8.3 ha    │ Trần Thị B    │ Phòng hộ  │
│ LR0003  │ Lô C3     │ 15.7 ha   │ Lê Văn C      │ Đặc dụng  │
│ ...                                                          │
├─────────────────────────────────────────────────────────────┤
│ Tổng: 1,234 lô rừng | Đã lọc: 3 lô                          │
└─────────────────────────────────────────────────────────────┘

Right-click menu:
  ✓ Chi tiết
  ✓ Zoom tới
  ─────────
  ✓ Tạo mới
  ✓ Gộp (nếu chọn nhiều)
  ✓ Tách
  ✓ Xóa
```

### 4. Data Model

**Table Columns**:
1. **ID** (ma_lo) - Plot identification code
2. **Tên lô** (ten_lo) - Plot name
3. **Diện tích** (dien_tich) - Area in hectares
4. **Chủ rừng** (chu_rung) - Owner name
5. **Loại rừng** (loai_rung) - Forest type (Sản xuất, Phòng hộ, Đặc dụng)
6. **Trạng thái** (trang_thai) - Status
7. **Ghi chú** (ghi_chu) - Notes

**Storage in Model**:
```python
# Store feature ID in first column's UserRole
item = QStandardItem(plot_id)
item.setData(feature.id(), Qt.UserRole)  # Store FID for zoom
self.table_model.setItem(row, 0, item)
```

### 5. Layer Detection

**Auto-detect layer by name patterns**:
```python
def find_plot_layer(self):
    """Find forest plot layer in project"""
    patterns = [
        'lo_rung', 'lo rung', 'forest_plot', 
        'khoảnh', 'khoành', 'compartment'
    ]
    
    for layer in QgsProject.instance().mapLayers().values():
        if isinstance(layer, QgsVectorLayer):
            name_lower = layer.name().lower()
            if any(p in name_lower for p in patterns):
                return layer
    
    return None
```

### 6. Performance Optimization

**For large datasets**:
```python
# Limit initial load
MAX_ROWS = 5000

# Virtual scrolling with QTableView (built-in)

# Incremental loading
def load_plots_incremental(self, layer):
    """Load features in batches"""
    batch_size = 1000
    features = layer.getFeatures()
    
    for i, feature in enumerate(features):
        if i >= MAX_ROWS:
            break
        # Add to model
        if i % batch_size == 0:
            QApplication.processEvents()  # Keep UI responsive
```

### 7. Context Menu Actions

**Full implementation**:
```python
def show_context_menu(self, pos):
    """Display context menu"""
    if not self.table_view.currentIndex().isValid():
        return
        
    menu = QMenu(self)
    
    # Detail action
    act_detail = QAction("📋 Chi tiết", self)
    act_detail.triggered.connect(self.show_detail_dialog)
    menu.addAction(act_detail)
    
    # Zoom action
    act_zoom = QAction("🔍 Zoom tới", self)
    act_zoom.triggered.connect(self.zoom_to_feature)
    menu.addAction(act_zoom)
    
    menu.addSeparator()
    
    # Create action
    act_create = QAction("➕ Tạo mới", self)
    act_create.triggered.connect(self.create_new_plot)
    menu.addAction(act_create)
    
    # Merge action (if multiple selected)
    selected_rows = self.table_view.selectionModel().selectedRows()
    if len(selected_rows) > 1:
        act_merge = QAction("🔗 Gộp lô rừng", self)
        act_merge.triggered.connect(self.merge_plots)
        menu.addAction(act_merge)
    
    # Split action
    act_split = QAction("✂️ Tách lô rừng", self)
    act_split.triggered.connect(self.split_plot)
    menu.addAction(act_split)
    
    menu.addSeparator()
    
    # Delete action
    act_delete = QAction("🗑️ Xóa", self)
    act_delete.triggered.connect(self.delete_plot)
    menu.addAction(act_delete)
    
    # Show menu at cursor position
    menu.exec_(self.table_view.viewport().mapToGlobal(pos))
```

## Testing Checklist

### Unit Tests
- [ ] Load empty layer
- [ ] Load layer with 1 plot
- [ ] Load layer with 10,000 plots
- [ ] Search filter with various keywords
- [ ] Sort by each column

### Integration Tests
- [ ] Click row → Map zooms correctly
- [ ] Right-click → Menu appears with correct actions
- [ ] Context menu actions trigger correctly
- [ ] Multi-row selection enables merge action

### Manual Tests
- [ ] Open search widget from FRMS ribbon
- [ ] Select different layers from dropdown
- [ ] Type in search box → Table filters
- [ ] Click row → Map zooms smoothly
- [ ] Double-click row → Detail dialog opens
- [ ] Right-click → Menu shows all actions
- [ ] Test each context menu action

## Dependencies

**Requires**:
- Task 019: Windows Ribbon implementation (✅ Complete)
- FRMS Menu structure (✅ Complete)

**Blocks**:
- Task 021: Create plot (uses layer reference)
- Task 022: Merge plots (uses selection)
- Task 023: Split plot (uses selection)
- Task 024: Delete plot (uses selection)

## Reference Implementation

**Pattern Source**: `src/app/tools/ui/frms_tools_widget.py` (lines 79-102)

```python
# Existing zoom_to_feature implementation to follow:
def zoom_to_feature(self):
    index = self.table_view.currentIndex()
    if not index.isValid():
        return
        
    source_index = self.proxy_model.mapToSource(index)
    row = source_index.row()
    
    item = self.table_model.item(row, 0)
    fid = item.data(Qt.UserRole)
    
    layer = self.layer_combo.currentData()
    if layer and fid is not None:
         layer.selectByIds([fid])
         iface.mapCanvas().zoomToSelected(layer)
```

## Notes

- Use `QSortFilterProxyModel` for search filtering
- Store feature ID in `Qt.UserRole` for zoom operations
- Follow existing QGIS plugin patterns
- Vietnamese UI labels throughout
- Handle edge cases (no layer, empty layer, invalid selection)

## Related Files

- Widget: `src/app/tools/ui/frms_search_plots_widget.py` (to be created)
- Ribbon: `src/ui/dock_widget.py` (line 341: `frms_search_plots()`)
- Reference: `src/app/tools/ui/frms_tools_widget.py` (existing patterns)

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-02
