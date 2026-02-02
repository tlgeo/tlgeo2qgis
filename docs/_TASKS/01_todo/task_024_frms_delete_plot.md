# FRMS: Xóa lô rừng (Delete Forest Plot)

**Status**: Todo  
**Created**: 2026-02-02  
**Priority**: Low  
**Estimated Effort**: 4 hours  
**Dependencies**: Task 020 (Search Plots)

## Description

Implement safe deletion of forest plots with reference checking and confirmation.

## User Story

> **As a** forest manager  
> **I want to** delete incorrect or obsolete plots  
> **So that** I can maintain data accuracy

## Acceptance Criteria

- [ ] Works from search context menu
- [ ] Shows confirmation dialog with plot details
- [ ] Checks for references in other tables (owners, changes)
- [ ] Warns if references exist
- [ ] Supports soft delete (mark as deleted) or hard delete
- [ ] Logs deletion for audit trail
- [ ] Batch delete for multiple selections

## Technical Implementation

### Delete Confirmation Dialog

```python
def delete_plot(self):
    """Delete selected plot(s) with confirmation"""
    selected_rows = self.table_view.selectionModel().selectedRows()
    if not selected_rows:
        QMessageBox.warning(self, "Lỗi", "Chưa chọn lô rừng nào")
        return
    
    features = [self.get_feature_from_row(row) for row in selected_rows]
    
    # Check references
    references = self.check_references(features)
    
    # Confirm dialog
    msg = f"Bạn có chắc chắn muốn xóa {len(features)} lô rừng?\n\n"
    
    if references:
        msg += "⚠️ CẢNH BÁO: Các lô này có tham chiếu:\n"
        for ref in references[:5]:  # Show first 5
            msg += f"  • {ref}\n"
    
    reply = QMessageBox.question(
        self, 
        "Xác nhận xóa", 
        msg,
        QMessageBox.Yes | QMessageBox.No
    )
    
    if reply == QMessageBox.Yes:
        self.execute_delete(features)
```

### Reference Checking

```python
def check_references(self, features):
    """Check if plots are referenced elsewhere"""
    references = []
    
    for feature in features:
        plot_id = feature['ma_lo']
        
        # Check in chu_rung table
        owner_layer = self.find_layer('chu_rung')
        if owner_layer:
            expr = f"ma_lo = '{plot_id}'"
            matches = owner_layer.getFeatures(QgsFeatureRequest().setFilterExpression(expr))
            if len(list(matches)) > 0:
                references.append(f"{plot_id}: Liên kết với chủ rừng")
        
        # Check in dien_bien table
        changes_layer = self.find_layer('dien_bien')
        if changes_layer:
            expr = f"ma_lo = '{plot_id}'"
            matches = changes_layer.getFeatures(QgsFeatureRequest().setFilterExpression(expr))
            count = len(list(matches))
            if count > 0:
                references.append(f"{plot_id}: {count} diễn biến")
    
    return references
```

### Delete Options Dialog

```
┌───────────────────────────────────────────┐
│ Xóa lô rừng                               │
├───────────────────────────────────────────┤
│ Chọn loại xóa:                            │
│                                           │
│ ⦿ Xóa mềm (đánh dấu đã xóa)              │
│   Lô sẽ được ẩn nhưng vẫn giữ lại        │
│   trong cơ sở dữ liệu                    │
│                                           │
│ ○ Xóa cứng (xóa vĩnh viễn)               │
│   ⚠️ Không thể khôi phục                 │
│                                           │
│ Lý do xóa:                                │
│ [_____________________________________]   │
│                                           │
│ [Hủy]  [Xóa]                              │
└───────────────────────────────────────────┘
```

## Integration

```python
# Called from search context menu
def delete_plot(self):
    # Implementation as shown above
```

## Related Files

- Implementation: In `src/app/tools/ui/frms_search_plots_widget.py`
- Ribbon: `src/ui/dock_widget.py` (line 373)

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-02
