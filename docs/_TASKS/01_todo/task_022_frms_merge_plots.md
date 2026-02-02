# FRMS: Gộp lô rừng (Merge Forest Plots)

**Status**: Todo  
**Created**: 2026-02-02  
**Priority**: Medium  
**Estimated Effort**: 10 hours  
**Dependencies**: Task 020 (Search Plots)

## Description

Implement tool to merge multiple forest plots into a single plot with geometry union and attribute resolution.

## User Story

> **As a** forest manager  
> **I want to** merge multiple adjacent plots into one  
> **So that** I can consolidate plot boundaries

## Acceptance Criteria

- [ ] Works from search table multi-selection
- [ ] Shows merge dialog with preview
- [ ] Unions geometries automatically
- [ ] Allows attribute selection/resolution
- [ ] Updates references in related tables
- [ ] Deletes source plots after merge
- [ ] Transaction support (rollback on error)

## Technical Implementation

### Widget Class

```python
class FRMSMergePlotsWidget(QWidget):
    """
    Merge multiple forest plots.
    
    Workflow:
    1. Select 2+ plots from search table
    2. Click "Gộp" in context menu
    3. Show merge dialog
    4. Choose target attributes
    5. Merge geometries
    6. Save and update
    """
    
    def __init__(self, plot_features, layer):
        # Initialize with selected features
        
    def show_merge_dialog(self):
        """Display merge options dialog"""
        # Target plot ID
        # Attribute resolution (keep first, last, sum, concat)
        # Geometry union options
        
    def merge_geometries(self, features):
        """Union all plot geometries"""
        # Use QgsGeometry.unaryUnion()
        
    def resolve_attributes(self, features, rules):
        """Resolve conflicting attributes"""
        # Apply user-selected rules
        
    def execute_merge(self):
        """Perform the merge operation"""
        # Start transaction
        # Create new merged feature
        # Delete source features
        # Update references
        # Commit transaction
```

### Merge Dialog UI

```
┌───────────────────────────────────────────┐
│ Gộp lô rừng (3 lô được chọn)              │
├───────────────────────────────────────────┤
│ Mã lô đích: [LR0001      ▼]              │
│                                           │
│ Thuộc tính:                               │
│ • Diện tích:  ☑ Tính tổng (35.5 ha)      │
│ • Chủ rừng:   ⦿ Giữ từ LR0001            │
│               ○ Chọn mới                  │
│ • Loại rừng:  ⦿ Sản xuất (từ LR0001)     │
│                                           │
│ Hình học:                                 │
│ ☑ Gộp thành đa giác đơn                  │
│ ☐ Giữ các phần tách biệt                 │
│                                           │
│ [Xem trước]  [Hủy]  [Thực hiện gộp]      │
└───────────────────────────────────────────┘
```

## Integration

```python
# Called from search context menu
def merge_plots(self):
    selected_rows = self.table_view.selectionModel().selectedRows()
    features = [self.get_feature_from_row(row) for row in selected_rows]
    
    from ..app.tools.ui.frms_merge_plots_widget import FRMSMergePlotsWidget
    widget = FRMSMergePlotsWidget(features, self.current_layer)
    widget.exec_()  # Modal dialog
```

## Related Files

- Widget: `src/app/tools/ui/frms_merge_plots_widget.py` (to be created)
- Ribbon: `src/ui/dock_widget.py` (line 357)
- Context menu: Called from `frms_search_plots_widget.py`

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-02
