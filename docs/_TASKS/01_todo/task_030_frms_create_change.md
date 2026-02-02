# FRMS: Tạo diễn biến (Create Forest Change Event)

**Status**: Todo  
**Created**: 2026-02-02  
**Priority**: Medium  
**Estimated Effort**: 8 hours  

## Description

Record new forest change/evolution event with affected plot selection.

## Acceptance Criteria

- [ ] Form displays in TLGeo Content Dock
- [ ] Select affected plots on map
- [ ] Choose change type from list
- [ ] Date picker with validation
- [ ] Area calculation from selection
- [ ] Photo/document upload
- [ ] Saves to changes layer

## Form Fields

- **Mã diễn biến** - Auto-generated
- **Mã lô** - From selection or dropdown
- **Ngày diễn biến** - Date picker (required)
- **Loại diễn biến** - Dropdown (required):
  - Trồng mới
  - Khai thác gỗ
  - Tỉa thưa
  - Cháy rừng
  - Sâu bệnh
  - Thiên tai
  - Chuyển đổi mục đích
  - Khác
- **Diện tích ảnh hưởng** - Number (ha)
- **Mức độ** - Dropdown: Nhẹ, Trung bình, Nặng
- **Mô tả** - Text area
- **Ảnh đính kèm** - File upload
- **Người ghi nhận** - Auto from user

## Integration

```python
def frms_create_change(self):
    from ..app.tools.ui.frms_create_change_widget import FRMSCreateChangeWidget
    self.open_tab_generic(FRMSCreateChangeWidget, "Tạo diễn biến")
```

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-02
