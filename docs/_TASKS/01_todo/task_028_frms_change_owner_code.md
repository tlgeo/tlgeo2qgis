# FRMS: Đổi mã chủ rừng (Change Owner Code)

**Status**: Todo  
**Created**: 2026-02-02  
**Priority**: Low  
**Estimated Effort**: 4 hours  

## Description

Change forest owner identification code with reference updates.

## Acceptance Criteria

- [ ] Works from search context menu
- [ ] Shows current code and new code input
- [ ] Validates new code (unique, format)
- [ ] Updates all plot references
- [ ] Logs code change for audit

## Dialog UI

```
┌───────────────────────────────────────────┐
│ Đổi mã chủ rừng                           │
├───────────────────────────────────────────┤
│ Chủ rừng: Nguyễn Văn A                    │
│                                           │
│ Mã hiện tại: [CR0001  ] (read-only)      │
│                                           │
│ Mã mới:      [CR0001A ] (editable)       │
│                                           │
│ ⚠️ Lưu ý: Sẽ cập nhật 12 lô rừng         │
│                                           │
│ Lý do đổi:                                │
│ [_____________________________________]   │
│                                           │
│ [Hủy]  [Đổi mã]                           │
└───────────────────────────────────────────┘
```

## Implementation

```python
def frms_change_owner_code(self):
    # Get selected owner
    # Show dialog
    # Validate new code
    # Update owner record
    # Update all plot references
    # Log change
```

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-02
