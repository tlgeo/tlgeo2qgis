from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QTableWidget, 
    QTableWidgetItem, QHeaderView, QPushButton, QMessageBox, 
    QMenu, QAction, QInputDialog
)
from qgis.PyQt.QtCore import Qt, QUrl
from qgis.PyQt.QtGui import QDesktopServices
from ..util.project_service import ProjectService

class ProjectListWidget(QWidget):
    def __init__(self, parent=None):
        super(ProjectListWidget, self).__init__(parent)
        self.project_service = ProjectService()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Sub-tabs for My Projects / Shared Projects
        self.project_subtabs = QTabWidget()
        layout.addWidget(self.project_subtabs)
        
        # --- Tab: My Projects ---
        my_projects_widget = QWidget()
        my_layout = QVBoxLayout()
        
        self.my_project_table = QTableWidget()
        self.setup_project_table(self.my_project_table)
        my_layout.addWidget(self.my_project_table)
        
        my_projects_widget.setLayout(my_layout)
        self.project_subtabs.addTab(my_projects_widget, "Của tôi")
        
        # --- Tab: Shared Projects ---
        shared_projects_widget = QWidget()
        shared_layout = QVBoxLayout()
        
        self.shared_project_table = QTableWidget()
        self.setup_project_table(self.shared_project_table)
        shared_layout.addWidget(self.shared_project_table)
        
        shared_projects_widget.setLayout(shared_layout)
        self.project_subtabs.addTab(shared_projects_widget, "Được chia sẻ")

        # Global Refresh Button
        refresh_btn = QPushButton("Làm mới danh sách")
        refresh_btn.clicked.connect(self.load_projects)
        layout.addWidget(refresh_btn)
        
        self.setLayout(layout)
        
        # Initial load if authenticated
        if self.project_service.auth_service.is_authenticated():
            self.load_projects()

    def setup_project_table(self, table):
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Tên", "Ngày tạo", "Trạng thái", "Liên kết"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setContextMenuPolicy(Qt.CustomContextMenu)
        table.customContextMenuRequested.connect(lambda pos: self.show_context_menu(pos, table))

    def load_projects(self):
        """Fetch and display projects (both My and Shared)"""
        if not self.project_service.auth_service.is_authenticated():
             return

        # 1. Load My Projects
        result_my = self.project_service.get_projects()
        if result_my.get('success'):
            self.populate_table(self.my_project_table, result_my.get('data', []))
        else:
            QMessageBox.warning(self, "Lỗi tải dự án", result_my.get('error', 'Lỗi không xác định'))
            
        # 2. Load Shared Projects
        result_shared = self.project_service.get_shared_projects()
        if result_shared.get('success'):
            self.populate_table(self.shared_project_table, result_shared.get('data', []))
        else:
            print(f"Failed to load shared projects: {result_shared.get('error')}")

    def populate_table(self, table, projects):
        table.setRowCount(len(projects))
        for row, project in enumerate(projects):
            def get_attr(p, key):
                if not p: return None
                if 'attributes' in p and isinstance(p['attributes'], dict):
                    return p['attributes'].get(key)
                return p.get(key)
                
            name = get_attr(project, 'name') or get_attr(project, 'title') or f"Dự án {project.get('id')}"
            date_str = get_attr(project, 'createdAt')
            date = date_str[:10] if date_str else ""
            
            slug = get_attr(project, 'slug')
            uuid = get_attr(project, 'uuid')
            link = ""
            identifier = slug or uuid or str(get_attr(project, 'id'))
            if identifier:
                 link = identifier

            name_item = QTableWidgetItem(str(name))
            name_item.setData(Qt.UserRole, project)
            table.setItem(row, 0, name_item)
            
            table.setItem(row, 1, QTableWidgetItem(str(date)))
            
            status_val = "Hoạt động"
            if get_attr(project, 'is_deleted'):
                status_val = "Đã xóa"
            table.setItem(row, 2, QTableWidgetItem(status_val))
            
            table.setItem(row, 3, QTableWidgetItem(str(link)))

    def show_context_menu(self, position, table):
        menu = QMenu()
        
        view_action = QAction("Xem trên trình duyệt", self)
        view_action.triggered.connect(lambda: self.open_project_url(table))
        menu.addAction(view_action)
        
        if table == self.my_project_table:
            edit_action = QAction("Chỉnh sửa Metadata", self)
            edit_action.triggered.connect(lambda: self.edit_project_metadata(table))
            menu.addAction(edit_action)
            
            delete_action = QAction("Xóa dự án", self)
            delete_action.triggered.connect(lambda: self.delete_project(table))
            menu.addAction(delete_action)
        
        menu.exec_(table.viewport().mapToGlobal(position))

    def get_selected_project(self, table):
        rows = table.selectionModel().selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        item = table.item(row, 0)
        return item.data(Qt.UserRole)

    def open_project_url(self, table):
        project = self.get_selected_project(table)
        if not project: return
            
        def get_attr(p, key):
            if 'attributes' in p and isinstance(p['attributes'], dict):
                return p['attributes'].get(key)
            return p.get(key)

        slug = get_attr(project, 'slug')
        uuid = get_attr(project, 'uuid')
        identifier = slug or uuid or str(get_attr(project, 'id'))

        if identifier:
             # TODO: Config URL properly
             url_str = f"http://localhost:5173/map/{identifier}" 
             QDesktopServices.openUrl(QUrl(url_str))
        else:
             QMessageBox.information(self, "Thông báo", "Không tìm thấy URL")

    def delete_project(self, table):
        project = self.get_selected_project(table)
        if not project: return
            
        confirm = QMessageBox.question(self, "Xác nhận xóa", "Bạn có chắc chắn muốn xóa dự án này không?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            res = self.project_service.delete_project(project.get('id'))
            if res.get('success'):
                self.load_projects()
            else:
                QMessageBox.warning(self, "Lỗi", res.get('error'))

    def edit_project_metadata(self, table):
        project = self.get_selected_project(table)
        if not project: return
        
        def get_attr(p, key):
            if 'attributes' in p and isinstance(p['attributes'], dict):
                return p['attributes'].get(key)
            return p.get(key)
            
        current_name = get_attr(project, 'name') or get_attr(project, 'title') or ""
        new_name, ok = QInputDialog.getText(self, "Chỉnh sửa dự án", "Tên dự án:", text=str(current_name))
        
        if ok and new_name:
            res = self.project_service.update_project(project.get('id'), {"name": new_name})
            if res.get('success'):
                self.load_projects()
            else:
                QMessageBox.warning(self, "Lỗi", res.get('error'))
