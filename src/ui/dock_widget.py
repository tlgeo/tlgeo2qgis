from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QLabel, 
    QPushButton, QListWidget, QProgressBar, QHBoxLayout,
    QGroupBox, QMessageBox, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMenu, QAction, QInputDialog
)
from qgis.gui import QgsDockWidget
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices
from ..util.dependency_checker import DependencyChecker
from ..util.project_service import ProjectService
import webbrowser
import platform

class TLGeoDockWidget(QgsDockWidget):
    def __init__(self, parent=None):
        super(TLGeoDockWidget, self).__init__("TLGeo Workspace", parent)
        self.setObjectName("TLGeoDockWidget")
        
        self.dep_checker = DependencyChecker()
        self.project_service = ProjectService()

        # Main content widget
        self.main_widget = QWidget()
        self.setWidget(self.main_widget)
        
        # Layout
        self.layout = QVBoxLayout()
        self.main_widget.setLayout(self.layout)
        
        # Tabs
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)
        
        # Tab 1: Projects
        self.projects_tab = QWidget()
        self.setup_projects_tab()
        self.tabs.addTab(self.projects_tab, "Projects")
        
        # Tab 2: Publish
        self.publish_tab = QWidget()
        self.setup_publish_tab()
        self.tabs.addTab(self.publish_tab, "Publish")
        
        # Tab 3: Tools
        self.tools_tab = QWidget()
        self.setup_tools_tab()
        self.tabs.addTab(self.tools_tab, "Tools")
        
    def setup_projects_tab(self):
        layout = QVBoxLayout()
        
        # Project Table
        self.project_table = QTableWidget()
        self.project_table.setColumnCount(4)
        self.project_table.setHorizontalHeaderLabels(["Name", "Date", "Status", "Link"])
        self.project_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.project_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.project_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.project_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.project_table.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(QLabel("Cloud Projects:"))
        layout.addWidget(self.project_table)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Projects")
        refresh_btn.clicked.connect(self.load_projects)
        layout.addWidget(refresh_btn)
        
        self.projects_tab.setLayout(layout)
        
        # Initial load
        # We delay initial load slightly or just call it. 
        # Ideally we only load if logged in.
        if self.project_service.auth_service.is_authenticated():
            self.load_projects()

    def load_projects(self):
        """Fetch and display projects"""
        result = self.project_service.get_projects()
        
        if not result.get('success'):
            if "User not authenticated" not in result.get('error', ''):
                 # Only show error if it's not just an auth issue (which might happen on startup)
                 QMessageBox.warning(self, "Error", result.get('error', 'Unknown error'))
            self.project_table.setRowCount(0)
            return

        projects = result.get('data', [])
        self.project_table.setRowCount(len(projects))
        
        for row, project in enumerate(projects):
            # Helper to get attribute safely handling flat or nested structure
            def get_attr(p, key):
                if 'attributes' in p and isinstance(p['attributes'], dict):
                    return p['attributes'].get(key)
                return p.get(key)
                
            name = get_attr(project, 'name') or get_attr(project, 'title') or f"Project {project.get('id')}"
            date_str = get_attr(project, 'createdAt')
            date = date_str[:10] if date_str else ""
            status = get_attr(project, 'status') or "Unknown"
            
            # Construct link
            slug = get_attr(project, 'slug')
            link = ""
            if slug:
                 # Assuming a standard public URL structure
                 base_url = self.project_service.strapi_url.replace("11000", "5173").replace("api", "") # heuristic for dev
                 # But better to just show the slug or wait for real config
                 link = slug

            # Name Item
            name_item = QTableWidgetItem(str(name))
            name_item.setData(Qt.UserRole, project) # Store full object
            self.project_table.setItem(row, 0, name_item)
            
            # Date Item
            self.project_table.setItem(row, 1, QTableWidgetItem(str(date)))
            
            # Status Item
            self.project_table.setItem(row, 2, QTableWidgetItem(str(status)))
            
            # Link Item
            self.project_table.setItem(row, 3, QTableWidgetItem(str(link)))

    def show_context_menu(self, position):
        menu = QMenu()
        
        view_action = QAction("View in Browser", self)
        view_action.triggered.connect(self.open_project_url)
        menu.addAction(view_action)
        
        edit_action = QAction("Edit Metadata", self)
        edit_action.triggered.connect(self.edit_project_metadata)
        menu.addAction(edit_action)
        
        delete_action = QAction("Delete Project", self)
        delete_action.triggered.connect(self.delete_project)
        menu.addAction(delete_action)
        
        menu.exec_(self.project_table.viewport().mapToGlobal(position))

    def get_selected_project(self):
        rows = self.project_table.selectionModel().selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        item = self.project_table.item(row, 0)
        return item.data(Qt.UserRole)

    def open_project_url(self):
        project = self.get_selected_project()
        if not project:
            return
            
        def get_attr(p, key):
            if 'attributes' in p and isinstance(p['attributes'], dict):
                return p['attributes'].get(key)
            return p.get(key)

        slug = get_attr(project, 'slug')
        if slug:
             # Construct URL. Assuming MapStore or generic viewer.
             # For now, let's guess standard public URL
             # If strapi is localhost:11000, maybe public is localhost:5173/map/{slug}
             # But let's just use what we have or a placeholder
             url_str = f"http://localhost:5173/map/{slug}" # TODO: Get from config
             QDesktopServices.openUrl(QUrl(url_str))
        else:
             QMessageBox.information(self, "Info", "No URL available for this project")

    def delete_project(self):
        project = self.get_selected_project()
        if not project:
            return
            
        confirm = QMessageBox.question(
            self, "Confirm Delete", 
            "Are you sure you want to delete this project?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            res = self.project_service.delete_project(project.get('id'))
            if res.get('success'):
                self.load_projects()
            else:
                QMessageBox.warning(self, "Error", res.get('error'))

    def edit_project_metadata(self):
        project = self.get_selected_project()
        if not project:
            return
            
        def get_attr(p, key):
            if 'attributes' in p and isinstance(p['attributes'], dict):
                return p['attributes'].get(key)
            return p.get(key)
            
        current_name = get_attr(project, 'name') or get_attr(project, 'title') or ""
        
        new_name, ok = QInputDialog.getText(
            self, "Edit Project", "Project Name:", text=str(current_name)
        )
        
        if ok and new_name:
            res = self.project_service.update_project(project.get('id'), {"name": new_name})
            if res.get('success'):
                self.load_projects()
            else:
                QMessageBox.warning(self, "Error", res.get('error'))

    def setup_publish_tab(self):
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Active Layer Status:"))
        
        # Placeholder status
        self.status_label = QLabel("No active layer selected")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("border: 1px dashed gray; padding: 20px;")
        layout.addWidget(self.status_label)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        self.publish_btn = QPushButton("Publish Layer")
        self.publish_btn.setEnabled(False)
        btn_layout.addWidget(self.publish_btn)
        
        layout.addLayout(btn_layout)
        layout.addStretch()
        
        self.publish_tab.setLayout(layout)
        
    def setup_tools_tab(self):
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("System Check:"))
        
        # Dependency list
        self.dep_list = QListWidget()
        self.dep_list.addItem("QGIS Version: Checking...")
        self.dep_list.addItem("GDAL Version: Checking...")
        layout.addWidget(self.dep_list)
        
        check_btn = QPushButton("Re-check Dependencies")
        layout.addWidget(check_btn)
        
        layout.addStretch()
        self.tools_tab.setLayout(layout)
