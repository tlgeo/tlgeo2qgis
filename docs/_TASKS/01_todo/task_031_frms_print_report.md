# FRMS: In báo cáo (Print Forest Report)

**Status**: Todo  
**Created**: 2026-02-02  
**Priority**: Low  
**Estimated Effort**: 12 hours  

## Description

Generate and print standardized forest management reports with charts and maps.

## Acceptance Criteria

- [ ] Report wizard with template selection
- [ ] Data filter (date range, plots, owners)
- [ ] Preview before print
- [ ] Export to PDF/Excel
- [ ] Multiple report templates
- [ ] Map integration in report

## Report Templates

### 1. Báo cáo tổng hợp lô rừng
- Total plots count
- Total area
- Breakdown by forest type
- Map overview

### 2. Báo cáo chủ rừng
- Owner list
- Plots per owner
- Area per owner

### 3. Báo cáo diễn biến
- Changes by type
- Timeline chart
- Affected area
- Photos

### 4. Báo cáo tùy chỉnh
- User-defined fields
- Custom filters

## Dialog UI

```
┌───────────────────────────────────────────┐
│ In báo cáo rừng                           │
├───────────────────────────────────────────┤
│ Loại báo cáo: [Tổng hợp lô rừng ▼]       │
│                                           │
│ Bộ lọc:                                   │
│ • Từ ngày: [01/01/2024] → [31/12/2024]   │
│ • Lô rừng: [Tất cả ▼]                     │
│ • Chủ rừng: [Tất cả ▼]                    │
│                                           │
│ Tùy chọn:                                 │
│ ☑ Bao gồm bản đồ                          │
│ ☑ Bao gồm biểu đồ                         │
│ ☐ Bao gồm ảnh                             │
│                                           │
│ Định dạng: ⦿ PDF  ○ Excel  ○ Word        │
│                                           │
│ [Xem trước]  [Hủy]  [Xuất báo cáo]       │
└───────────────────────────────────────────┘
```

## Implementation

```python
class FRMSReportWidget(QWidget):
    """Forest report generator"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def generate_plot_summary_report(self):
        """Generate comprehensive plot report"""
        
    def generate_owner_report(self):
        """Generate owner statistics report"""
        
    def generate_changes_report(self):
        """Generate changes timeline report"""
        
    def export_to_pdf(self, report_data):
        """Export report as PDF"""
        # Use QPrinter or ReportLab
        
    def export_to_excel(self, report_data):
        """Export report as Excel"""
        # Use openpyxl or xlsxwriter
```

## Integration

```python
def frms_print_report(self):
    from ..app.tools.ui.frms_report_widget import FRMSReportWidget
    self.open_tab_generic(FRMSReportWidget, "In báo cáo")
```

## Dependencies

- QPrinter for PDF generation
- openpyxl or xlsxwriter for Excel
- matplotlib for charts
- QGIS layout manager for maps

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-02
