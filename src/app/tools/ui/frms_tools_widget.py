from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QLabel, 
    QPushButton, QComboBox, QLineEdit, QTableView,
    QHBoxLayout, QHeaderView, QMessageBox, QMenu, QAction,
    QListWidget, QFormLayout, QGroupBox, QCheckBox, 
    QAbstractItemView, QListWidgetItem
)
from PyQt5.QtCore import Qt, QSortFilterProxyModel
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from qgis.core import QgsProject, QgsVectorLayer
from qgis.utils import iface

class FRMSToolsWidget(QWidget):
    def __init__(self, parent=None):
        super(FRMSToolsWidget, self).__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_view_tab(), "Tra cứu & Xem")
        self.tabs.addTab(self.create_edit_tab(), "Biên tập")
        self.tabs.addTab(self.create_validate_tab(), "Kiểm tra lỗi")
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)
        
    def create_view_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Controls
        controls = QHBoxLayout()
        self.layer_combo = QComboBox()
        self.layer_combo.currentIndexChanged.connect(self.on_layer_changed)
        controls.addWidget(QLabel("Lớp dữ liệu:"))
        controls.addWidget(self.layer_combo, 1)
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Tìm kiếm (ID, Tên)...")
        self.search_box.textChanged.connect(self.on_search_text_changed)
        controls.addWidget(self.search_box, 1)
        
        layout.addLayout(controls)
        
        # Table
        self.table_view = QTableView()
        self.table_model = QStandardItemModel()
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.table_model)
        self.proxy_model.setFilterKeyColumn(-1) # Filter all columns
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        
        self.table_view.setModel(self.proxy_model)
        self.table_view.setSortingEnabled(True)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        
        # Context Menu & Interaction
        self.table_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.show_context_menu)
        self.table_view.doubleClicked.connect(self.zoom_to_feature)
        
        layout.addWidget(self.table_view)
        
        # Refresh Layers Button
        btn_refresh = QPushButton("Làm mới danh sách lớp")
        btn_refresh.clicked.connect(self.refresh_layers)
        layout.addWidget(btn_refresh)
        
        widget.setLayout(layout)
        
        # Initial load
        self.refresh_layers()
        
        return widget

    def show_context_menu(self, pos):
        menu = QMenu()
        zoom_action = QAction("Zoom tới đối tượng", self)
        zoom_action.triggered.connect(self.zoom_to_feature)
        menu.addAction(zoom_action)
        menu.exec_(self.table_view.viewport().mapToGlobal(pos))

    def zoom_to_feature(self):
        index = self.table_view.currentIndex()
        if not index.isValid():
            return
            
        # Map proxy index to source index
        source_index = self.proxy_model.mapToSource(index)
        row = source_index.row()
        
        # Get feature ID
        item = self.table_model.item(row, 0)
        fid = item.data(Qt.UserRole)
        
        layer = self.layer_combo.currentData()
        if layer and fid is not None:
             layer.selectByIds([fid])
             iface.mapCanvas().zoomToSelected(layer)

    def create_edit_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("<b>Gộp chủ rừng (Merge Forest Owners)</b>"))
        
        # Selection list
        layout.addWidget(QLabel("Chọn các chủ rừng cần gộp (từ lớp đang chọn):"))
        self.merge_list = QListWidget()
        self.merge_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        layout.addWidget(self.merge_list)
        
        btn_load_sel = QPushButton("Lấy từ đang chọn trên bản đồ")
        btn_load_sel.clicked.connect(self.load_selected_owners)
        layout.addWidget(btn_load_sel)
        
        # Target info
        group_target = QGroupBox("Thông tin chủ rừng đích")
        form = QFormLayout()
        self.target_name = QLineEdit()
        form.addRow("Tên chủ rừng:", self.target_name)
        group_target.setLayout(form)
        layout.addWidget(group_target)
        
        btn_merge = QPushButton("Thực hiện gộp")
        btn_merge.clicked.connect(self.execute_merge)
        layout.addWidget(btn_merge)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def load_selected_owners(self):
        self.merge_list.clear()
        layer = iface.activeLayer()
        if not layer:
            QMessageBox.warning(self, "Lỗi", "Vui lòng chọn một lớp dữ liệu.")
            return
            
        selected_features = layer.selectedFeatures()
        if not selected_features:
            QMessageBox.warning(self, "Thông báo", "Chưa có đối tượng nào được chọn trên bản đồ.")
            return

        for feat in selected_features:
            # Simple heuristic for display name
            display = f"ID: {feat.id()}"
            for field_name in ['name', 'ten', 'ten_chu', 'owner', 'Name', 'TEN', 'CHU_RUNG']:
                 idx = layer.fields().indexOf(field_name)
                 if idx != -1:
                     val = feat[field_name]
                     if val:
                        display = f"{val} (ID: {feat.id()})"
                        break
            
            item = QListWidgetItem(display)
            item.setData(Qt.UserRole, feat.id())
            self.merge_list.addItem(item)

    def execute_merge(self):
        QMessageBox.information(self, "Thông báo", "Chức năng đang phát triển")

    def create_validate_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("<b>Kiểm tra dữ liệu (Validation)</b>"))
        
        self.check_missing = QCheckBox("Thuộc tính bắt buộc bị thiếu")
        self.check_duplicate = QCheckBox("Trùng lặp ID")
        self.check_topology = QCheckBox("Lỗi hình học (Topology)")
        self.check_ref = QCheckBox("Toàn vẹn tham chiếu")
        
        # Select defaults
        self.check_missing.setChecked(True)
        self.check_duplicate.setChecked(True)
        
        layout.addWidget(self.check_missing)
        layout.addWidget(self.check_duplicate)
        layout.addWidget(self.check_topology)
        layout.addWidget(self.check_ref)
        
        btn_run = QPushButton("Chạy kiểm tra")
        btn_run.clicked.connect(self.run_validation)
        layout.addWidget(btn_run)
        
        self.error_list = QListWidget()
        layout.addWidget(QLabel("Kết quả:"))
        layout.addWidget(self.error_list)
        
        # layout.addStretch() # Don't stretch if we want list to expand
        widget.setLayout(layout)
        return widget

    def run_validation(self):
        self.error_list.clear()
        self.error_list.addItem("Đang chạy kiểm tra...")
        
        # Mock validation logic
        errors = []
        if self.check_missing.isChecked():
            # Mock check
            pass
        
        if not errors:
             self.error_list.clear()
             self.error_list.addItem("✅ Không phát hiện lỗi (Mock).")
        else:
             for err in errors:
                 self.error_list.addItem(err)

    def refresh_layers(self):
        current_text = self.layer_combo.currentText()
        self.layer_combo.clear()
        
        layers = QgsProject.instance().mapLayers().values()
        sorted_layers = sorted(layers, key=lambda l: l.name())
        
        for layer in sorted_layers:
            if isinstance(layer, QgsVectorLayer):
                self.layer_combo.addItem(layer.name(), layer)
                
        # Restore selection if possible
        index = self.layer_combo.findText(current_text)
        if index >= 0:
            self.layer_combo.setCurrentIndex(index)
                
    def on_layer_changed(self, index):
        layer = self.layer_combo.currentData()
        if not layer:
            self.table_model.clear()
            return
            
        self.load_layer_data(layer)

    def load_layer_data(self, layer):
        self.table_model.clear()
        
        fields = layer.fields()
        headers = [field.name() for field in fields]
        self.table_model.setHorizontalHeaderLabels(headers)
        
        # Limit rows for performance prototype
        MAX_ROWS = 1000 
        
        features = layer.getFeatures()
        
        row_count = 0
        for feature in features:
            if row_count >= MAX_ROWS:
                break
                
            items = []
            first = True
            for field in fields:
                val = feature[field.name()]
                item = QStandardItem(str(val) if val is not None else "")
                
                if first:
                    item.setData(feature.id(), Qt.UserRole)
                    first = False
                    
                items.append(item)
            
            self.table_model.appendRow(items)
            row_count += 1
            
        if row_count >= MAX_ROWS:
             iface.messageBar().pushInfo(
                "FRMS Tools", f"Chỉ hiển thị {MAX_ROWS} dòng đầu tiên."
            )

    def on_search_text_changed(self, text):
        self.proxy_model.setFilterFixedString(text)
