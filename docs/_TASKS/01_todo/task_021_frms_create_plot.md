# FRMS: Tạo mới lô rừng (Create Forest Plot)

**Status**: Todo  
**Created**: 2026-02-02  
**Priority**: High  
**Estimated Effort**: 12 hours  
**Dependencies**: Task 020 (Search Plots)

## Description

Implement digitizing tool for creating new forest plot geometries with attribute form entry.

## User Story

> **As a** forest manager  
> **I want to** create new forest plots by drawing on the map  
> **So that** I can add new plots to the forest inventory

## Acceptance Criteria

- [ ] Button click activates QGIS digitizing mode
- [ ] User can draw polygon on map
- [ ] Attribute form dialog opens after geometry completion
- [ ] Form validates required fields
- [ ] New plot saves to layer with geometry and attributes
- [ ] Map refreshes to show new plot
- [ ] Search table updates automatically

## Technical Implementation

### Widget Class

```python
class FRMSCreatePlotWidget(QWidget):
    """
    Forest plot creation tool.
    
    Workflow:
    1. Activate digitizing tool
    2. User draws polygon
    3. Show attribute form
    4. Validate and save
    """
    
    def activate_digitizing(self):
        """Enable QGIS digitizing mode"""
        # iface.actionAddFeature().trigger()
        
    def on_geometry_captured(self, geometry):
        """Handle captured polygon"""
        # Show attribute form
        
    def show_attribute_form(self, geometry):
        """Display form for plot attributes"""
        # Fields: ma_lo, ten_lo, dien_tich, chu_rung, loai_rung, etc.
        
    def validate_form(self):
        """Validate required fields"""
        
    def save_plot(self, geometry, attributes):
        """Save new plot to layer"""
```

### Form Fields

- **Mã lô** (ma_lo) - Auto-generated or manual
- **Tên lô** (ten_lo) - Required
- **Diện tích** (dien_tich) - Auto-calculated from geometry
- **Chủ rừng** (chu_rung) - Dropdown/autocomplete
- **Loại rừng** (loai_rung) - Dropdown: Sản xuất, Phòng hộ, Đặc dụng
- **Ghi chú** (ghi_chu) - Optional

### Integration

```python
# In dock_widget.py
def frms_create_plot(self):
    from ..app.tools.ui.frms_create_plot_widget import FRMSCreatePlotWidget
    self.open_tab_generic(FRMSCreatePlotWidget, "Tạo mới lô rừng")
```

## Related Files

- Widget: `src/app/tools/ui/frms_create_plot_widget.py` (to be created)
- Ribbon: `src/ui/dock_widget.py` (line 349)

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-02
