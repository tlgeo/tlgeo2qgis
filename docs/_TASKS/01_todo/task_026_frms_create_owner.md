# FRMS: Tạo mới chủ rừng (Create Forest Owner)

**Status**: Todo  
**Created**: 2026-02-02  
**Priority**: Medium  
**Estimated Effort**: 6 hours  

## Description

Implement form-based registration of new forest owners.

## Acceptance Criteria

- [ ] Form displays in TLGeo Content Dock
- [ ] All required fields validated
- [ ] Auto-generate owner ID option
- [ ] Support for individual and organization owners
- [ ] Photo/document upload optional
- [ ] Saves to owner layer

## Form Fields

- **Mã chủ rừng** - Auto or manual
- **Tên chủ rừng** - Required
- **Loại chủ** - Dropdown: Cá nhân, Tổ chức, Nhà nước
- **CMND/CCCD** - For individuals
- **Mã số thuế** - For organizations  
- **Địa chỉ** - Required
- **Điện thoại** - Optional
- **Email** - Optional
- **Ghi chú** - Optional

## Integration

```python
def frms_create_owner(self):
    from ..app.tools.ui.frms_create_owner_widget import FRMSCreateOwnerWidget
    self.open_tab_generic(FRMSCreateOwnerWidget, "Tạo mới chủ rừng")
```

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-02
