# FRMS: Tách lô rừng (Split Forest Plot)

**Status**: Todo  
**Created**: 2026-02-02  
**Priority**: Medium  
**Estimated Effort**: 12 hours  
**Dependencies**: Task 020 (Search Plots)

## Description

Implement tool to split a forest plot into multiple plots using a split line, with attribute distribution.

## User Story

> **As a** forest manager  
> **I want to** split a large plot into smaller plots  
> **So that** I can subdivide forest areas

## Acceptance Criteria

- [ ] Activates split tool from search context menu
- [ ] User draws line to split plot
- [ ] Shows resulting polygons preview
- [ ] Allows attribute distribution to new plots
- [ ] Generates new plot IDs automatically
- [ ] Updates original plot or creates new ones
- [ ] Validates split geometry (no gaps, overlaps)

## Technical Implementation

### Widget Class

```python
class FRMSSplitPlotWidget(QWidget):
    """
    Split forest plot into multiple plots.
    
    Workflow:
    1. Select plot from search table
    2. Click "Tách" in context menu
    3. Draw split line on map
    4. Show split result dialog
    5. Distribute attributes
    6. Save new plots
    """
    
    def __init__(self, plot_feature, layer):
        # Initialize with selected feature
        
    def activate_split_tool(self):
        """Enable line drawing tool"""
        # iface.actionSplitFeatures().trigger()
        
    def on_line_drawn(self, line_geometry):
        """Handle split line drawn by user"""
        # Split plot geometry
        # Show preview
        
    def split_geometry(self, polygon, line):
        """Split polygon by line"""
        # Use QgsGeometry.splitGeometry()
        # Return list of resulting polygons
        
    def show_split_dialog(self, result_polygons):
        """Display split configuration dialog"""
        # Show preview of new plots
        # Attribute distribution form
        # ID generation
        
    def distribute_attributes(self, original_attrs, result_polygons):
        """Distribute attributes to new plots"""
        # Area: Calculate proportional
        # Owner: Copy to all
        # Type: Copy to all or customize
        
    def execute_split(self):
        """Perform split operation"""
        # Start transaction
        # Create new features
        # Delete or update original
        # Commit transaction
```

### Split Dialog UI

```
┌───────────────────────────────────────────┐
│ Tách lô rừng: LR0001                      │
├───────────────────────────────────────────┤
│ Tách thành: 2 lô mới                      │
│                                           │
│ Lô 1:                                     │
│ • Mã: [LR0001A  ] (tự động)              │
│ • Diện tích: 7.2 ha (58%)                │
│ • Chủ rừng: [Giống gốc ▼]                │
│ • Loại: [Sản xuất ▼]                     │
│                                           │
│ Lô 2:                                     │
│ • Mã: [LR0001B  ] (tự động)              │
│ • Diện tích: 5.3 ha (42%)                │
│ • Chủ rừng: [Giống gốc ▼]                │
│ • Loại: [Sản xuất ▼]                     │
│                                           │
│ ☑ Xóa lô gốc sau khi tách                │
│                                           │
│ [Xem trước]  [Hủy]  [Thực hiện tách]     │
└───────────────────────────────────────────┘
```

## Integration

```python
# Called from search context menu
def split_plot(self):
    index = self.table_view.currentIndex()
    feature = self.get_feature_from_index(index)
    
    from ..app.tools.ui.frms_split_plot_widget import FRMSSplitPlotWidget
    widget = FRMSSplitPlotWidget(feature, self.current_layer)
    widget.exec_()  # Modal dialog
```

## Related Files

- Widget: `src/app/tools/ui/frms_split_plot_widget.py` (to be created)
- Ribbon: `src/ui/dock_widget.py` (line 365)
- Context menu: Called from `frms_search_plots_widget.py`

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-02
