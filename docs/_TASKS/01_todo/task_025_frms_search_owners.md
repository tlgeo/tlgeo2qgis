# FRMS: Tìm kiếm chủ rừng (Search Forest Owners)

**Status**: Todo  
**Created**: 2026-02-02  
**Priority**: High  
**Estimated Effort**: 6 hours  

## Description

Implement search functionality for forest owners with table display and map synchronization.

## User Story

> **As a** forest manager  
> **I want to** search and view forest owner records  
> **So that** I can manage ownership information

## Acceptance Criteria

- [ ] Search widget displays in TLGeo Content Dock
- [ ] Table shows all owner records
- [ ] Search box filters by name, ID, phone, address
- [ ] Click row → Zoom to all plots owned by this owner
- [ ] Right-click → Context menu (Chi tiết, Zoom tới, Tạo mới, Gộp, Đổi mã)
- [ ] Sortable columns

## Technical Implementation

### Widget: `src/app/tools/ui/frms_search_owners_widget.py`

```python
class FRMSSearchOwnersWidget(QWidget):
    """Search forest owners"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def load_owners(self, layer=None):
        """Load owner data from layer"""
        
    def zoom_to_owner_plots(self):
        """Zoom to all plots owned by selected owner"""
        # Find all plots with matching owner ID
        # Select them
        # Zoom to combined extent
```

### Table Columns

- **Mã chủ rừng** (ma_chu_rung)
- **Tên chủ rừng** (ten_chu_rung)
- **Loại chủ** (loai_chu) - Cá nhân, Tổ chức, Nhà nước
- **CMND/CCCD** (cmnd)
- **Địa chỉ** (dia_chi)
- **Điện thoại** (dien_thoai)
- **Số lô sở hữu** (count from plots)

### Context Menu

- Chi tiết
- Zoom tới các lô
- Tạo mới chủ rừng
- Gộp chủ rừng (if multiple selected)
- Đổi mã

### Integration

```python
# In dock_widget.py
def frms_search_owners(self):
    from ..app.tools.ui.frms_search_owners_widget import FRMSSearchOwnersWidget
    self.open_tab_generic(FRMSSearchOwnersWidget, "Tìm kiếm chủ rừng")
```

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-02
