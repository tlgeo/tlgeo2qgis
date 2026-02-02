# FRMS Tasks Index

**Created**: 2026-02-02  
**Total Tasks**: 12  
**Location**: `docs/_TASKS/01_todo/`

## Overview

This index tracks all FRMS (Forest Resource Management System) implementation tasks created for the TLGeo2QGIS plugin.

---

## Task Breakdown by Feature Group

### 🌲 Lô rừng (Forest Plots) - 5 Tasks

| Task ID | Title | Priority | Effort | Status |
|---------|-------|----------|--------|--------|
| **020** | [Tìm kiếm lô rừng](01_todo/task_020_frms_search_plots.md) | High | 8h | Todo |
| **021** | [Tạo mới lô rừng](01_todo/task_021_frms_create_plot.md) | High | 12h | Todo |
| **022** | [Gộp lô rừng](01_todo/task_022_frms_merge_plots.md) | Medium | 10h | Todo |
| **023** | [Tách lô rừng](01_todo/task_023_frms_split_plot.md) | Medium | 12h | Todo |
| **024** | [Xóa lô rừng](01_todo/task_024_frms_delete_plot.md) | Low | 4h | Todo |

**Subtotal**: 46 hours

---

### 👤 Chủ rừng (Forest Owners) - 4 Tasks

| Task ID | Title | Priority | Effort | Status |
|---------|-------|----------|--------|--------|
| **025** | [Tìm kiếm chủ rừng](01_todo/task_025_frms_search_owners.md) | High | 6h | Todo |
| **026** | [Tạo mới chủ rừng](01_todo/task_026_frms_create_owner.md) | Medium | 6h | Todo |
| **027** | [Gộp chủ rừng](01_todo/task_027_frms_merge_owners.md) | Medium | 8h | Todo |
| **028** | [Đổi mã chủ rừng](01_todo/task_028_frms_change_owner_code.md) | Low | 4h | Todo |

**Subtotal**: 24 hours

---

### 📊 Diễn biến (Forest Changes) - 2 Tasks

| Task ID | Title | Priority | Effort | Status |
|---------|-------|----------|--------|--------|
| **029** | [Tìm kiếm diễn biến](01_todo/task_029_frms_search_changes.md) | Medium | 6h | Todo |
| **030** | [Tạo diễn biến](01_todo/task_030_frms_create_change.md) | Medium | 8h | Todo |

**Subtotal**: 14 hours

---

### 🖨️ Báo cáo (Reports) - 1 Task

| Task ID | Title | Priority | Effort | Status |
|---------|-------|----------|--------|--------|
| **031** | [In báo cáo](01_todo/task_031_frms_print_report.md) | Low | 12h | Todo |

**Subtotal**: 12 hours

---

## Grand Total

| Metric | Value |
|--------|-------|
| **Total Tasks** | 12 |
| **Total Estimated Effort** | **96 hours** (~12 working days) |
| **High Priority** | 3 tasks (28 hours) |
| **Medium Priority** | 6 tasks (52 hours) |
| **Low Priority** | 3 tasks (20 hours) |

---

## Implementation Phases

### Phase 1: Core Search (High Priority)
**Duration**: ~4 days  
**Tasks**: 020, 025

Focus on search functionality as it's used by all other tasks.

- ✅ Task 020: Search Plots (8h)
- ✅ Task 025: Search Owners (6h)

**Deliverable**: Users can search and view plots/owners in tables, click to zoom.

---

### Phase 2: CRUD Operations (High + Medium Priority)
**Duration**: ~7 days  
**Tasks**: 021, 022, 023, 026, 027, 029, 030

Implement create/update/delete operations for all entities.

- ✅ Task 021: Create Plot (12h)
- ✅ Task 022: Merge Plots (10h)
- ✅ Task 023: Split Plot (12h)
- ✅ Task 026: Create Owner (6h)
- ✅ Task 027: Merge Owners (8h)
- ✅ Task 029: Search Changes (6h)
- ✅ Task 030: Create Change (8h)

**Deliverable**: Full CRUD functionality for plots, owners, and changes.

---

### Phase 3: Utilities (Low Priority)
**Duration**: ~2 days  
**Tasks**: 024, 028, 031

Additional utilities and reporting.

- ✅ Task 024: Delete Plot (4h)
- ✅ Task 028: Change Owner Code (4h)
- ✅ Task 031: Print Report (12h)

**Deliverable**: Complete FRMS feature set with reporting.

---

## Key Features by Task

### Search Tasks (3)
- **020**: Forest Plot Search - Interactive table, zoom, context menu
- **025**: Owner Search - Owner records, plot relationships
- **029**: Change History Search - Timeline, filtering

**Common Features**:
- QTableView with QStandardItemModel
- QSortFilterProxyModel for search
- Click row → Zoom to map
- Right-click → Context menu (Chi tiết, Zoom tới, actions...)
- Multi-column sort

---

### Create Tasks (3)
- **021**: Create Plot - Digitize polygon, attribute form
- **026**: Create Owner - Registration form, validation
- **030**: Create Change - Event recording, photo upload

**Common Features**:
- Validated forms
- Auto-ID generation
- Save to layer
- Refresh search tables

---

### Edit Tasks (4)
- **022**: Merge Plots - Geometry union, attribute resolution
- **023**: Split Plot - Line split, attribute distribution
- **027**: Merge Owners - Reference updates
- **028**: Change Owner Code - Code validation, reference updates

**Common Features**:
- Transaction support
- Reference integrity checks
- Confirmation dialogs
- Audit logging

---

### Delete Tasks (1)
- **024**: Delete Plot - Soft/hard delete, reference checking

---

### Report Tasks (1)
- **031**: Print Report - Multiple templates, PDF/Excel export

---

## Technical Patterns

### Table View Pattern
**Used in**: Tasks 020, 025, 029

```python
# Pattern from frms_tools_widget.py
class SearchWidget(QWidget):
    def __init__(self):
        self.table_view = QTableView()
        self.table_model = QStandardItemModel()
        self.proxy_model = QSortFilterProxyModel()
        
    def zoom_to_feature(self):
        index = self.table_view.currentIndex()
        source_index = self.proxy_model.mapToSource(index)
        item = self.table_model.item(row, 0)
        fid = item.data(Qt.UserRole)
        layer.selectByIds([fid])
        iface.mapCanvas().zoomToSelected(layer)
```

### Context Menu Pattern
**Used in**: All search tasks

```python
def show_context_menu(self, pos):
    menu = QMenu()
    menu.addAction("📋 Chi tiết", self.show_detail)
    menu.addAction("🔍 Zoom tới", self.zoom_to_feature)
    menu.addSeparator()
    menu.addAction("➕ Tạo mới", self.create_new)
    # ... more actions
    menu.exec_(self.table_view.viewport().mapToGlobal(pos))
```

### Form Validation Pattern
**Used in**: Tasks 021, 026, 030

```python
def validate_form(self):
    errors = []
    if not self.field_name.text():
        errors.append("Tên không được để trống")
    if not self.field_area.value() > 0:
        errors.append("Diện tích phải lớn hơn 0")
    
    if errors:
        QMessageBox.warning(self, "Lỗi", "\n".join(errors))
        return False
    return True
```

---

## Dependencies

### External Libraries
- PyQt5 (already in QGIS)
- QGIS API (qgis.core, qgis.gui, qgis.utils)

### Optional (for Phase 3)
- **openpyxl** or **xlsxwriter** - Excel export
- **reportlab** or **QPrinter** - PDF generation
- **matplotlib** - Charts for reports

### Internal Dependencies
- Task 020 (Search Plots) → Blocks: 021, 022, 023, 024
- Task 025 (Search Owners) → Blocks: 026, 027, 028
- Task 029 (Search Changes) → Blocks: 030

---

## Testing Strategy

### Per-Task Testing

Each task file includes:
- Unit test checklist
- Integration test scenarios
- Manual test steps

### Integration Testing

After Phase 2, test complete workflows:
1. **Plot Lifecycle**: Create → Edit → Merge/Split → Delete
2. **Owner Management**: Create → Assign to plots → Merge duplicates
3. **Change Tracking**: Create plot → Record changes → Generate timeline
4. **Cross-Entity**: Search plot → View owner → See change history

### Performance Testing

- Load 10,000+ plots in search table
- Test zoom with 1,000+ selected plots
- Merge 100+ plots at once

---

## Related Documentation

- [FRMS Menu Design](../features/FRMS_MENU_DESIGN.md) - Overall design specification
- [FRMS Implementation Summary](../features/FRMS_IMPLEMENTATION_SUMMARY.md) - Ribbon implementation
- [Task 018: FRMS Advanced Tools](05_pending/task_018_frms_advanced_tools.md) - Original feature request
- [Ribbon Widget API](../../src/components/ribbon/ribbon_widget.py) - UI framework

---

## Progress Tracking

### Completed
- [x] FRMS Ribbon Menu Structure (13 buttons)
- [x] Action handler placeholders (13 methods)
- [x] Documentation (2 design docs + 12 task files)

### In Progress
- [ ] None

### Todo
- [ ] All 12 tasks (96 hours estimated)

---

## Notes for Implementers

1. **Start with Search**: Tasks 020 and 025 are foundational. All other tasks reference them.

2. **Follow Existing Patterns**: Use `frms_tools_widget.py` as reference for table views and zoom functionality.

3. **Test Incrementally**: After each task, test integration with ribbon button and search context menu.

4. **Vietnamese UI**: All user-facing text must be in Vietnamese.

5. **Reference Integrity**: Always check and update references when modifying owners or plots.

6. **Transaction Support**: Use QGIS transactions for multi-step operations (merge, split).

7. **Audit Trail**: Log significant changes (delete, merge, code changes) for compliance.

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-02  
**Maintained by**: TLGeo Development Team
