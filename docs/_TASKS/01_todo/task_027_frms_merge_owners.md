# FRMS: Gộp chủ rừng (Merge Forest Owners)

**Status**: Todo  
**Created**: 2026-02-02  
**Priority**: Medium  
**Estimated Effort**: 8 hours  

## Description

Merge duplicate or related forest owner records with plot reference updates.

## Acceptance Criteria

- [ ] Works from search table multi-selection
- [ ] Shows merge dialog with owner details
- [ ] Allows target owner selection
- [ ] Updates all plot references to new owner
- [ ] Deletes source owner records
- [ ] Transaction support

## Implementation Note

**Existing code** in `frms_tools_widget.py` (lines 104-164) has basic merge logic. Extract and enhance.

## Dialog UI

```
┌───────────────────────────────────────────┐
│ Gộp chủ rừng (3 chủ rừng được chọn)      │
├───────────────────────────────────────────┤
│ Chủ rừng đích: [Nguyễn Văn A ▼]          │
│                                           │
│ Thông tin:                                │
│ • CMND: [từ chủ A]                        │
│ • Địa chỉ: [từ chủ A]                     │
│ • Điện thoại: [từ chủ A]                  │
│                                           │
│ Số lô rừng sẽ chuyển: 15 lô              │
│                                           │
│ [Hủy]  [Thực hiện gộp]                    │
└───────────────────────────────────────────┘
```

## Integration

```python
def frms_merge_owners(self):
    from ..app.tools.ui.frms_merge_owners_widget import FRMSMergeOwnersWidget
    selected_rows = self.table_view.selectionModel().selectedRows()
    features = [self.get_feature_from_row(row) for row in selected_rows]
    widget = FRMSMergeOwnersWidget(features, self.current_layer)
    widget.exec_()
```

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-02
