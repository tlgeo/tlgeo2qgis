# FRMS: Tìm kiếm diễn biến (Search Forest Changes)

**Status**: Todo  
**Created**: 2026-02-02  
**Priority**: Medium  
**Estimated Effort**: 6 hours  

## Description

Search and view forest change/evolution history records.

## Acceptance Criteria

- [ ] Table shows all change records
- [ ] Filter by date range, plot, change type
- [ ] Click row → Zoom to related plot
- [ ] Timeline view option
- [ ] Export change history

## Table Columns

- **Mã diễn biến** (ma_dien_bien)
- **Mã lô** (ma_lo)
- **Ngày diễn biến** (ngay_dien_bien)
- **Loại diễn biến** (loai_dien_bien) - Trồng mới, Khai thác, Cháy rừng, etc.
- **Diện tích ảnh hưởng** (dien_tich_anh_huong)
- **Mô tả** (mo_ta)

## Context Menu

- Chi tiết
- Zoom tới lô
- Tạo diễn biến mới
- Xem timeline

## Integration

```python
def frms_search_changes(self):
    from ..app.tools.ui.frms_search_changes_widget import FRMSSearchChangesWidget
    self.open_tab_generic(FRMSSearchChangesWidget, "Tìm kiếm diễn biến")
```

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-02
