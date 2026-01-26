from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QApplication, QStyle
from qgis.gui import QgsDockWidget
from qgis.core import QgsApplication
from ..components.ribbon.ribbon_widget import RibbonWidget, RibbonGroup, RibbonButton
from ..components.tabs.tab_manager import TabManager

# Feature Widgets
from ..app.projects.ui.project_list_widget import ProjectListWidget
from ..app.projects.ui.publish_widget import PublishWidget
from ..app.tools.ui.tools_widget import ToolsWidget
from ..app.tools.ui.frms_tools_widget import FRMSToolsWidget
from ..app.auth.ui.profile_widget import ProfileWidget
from ..app.auth.ui.login_dialog import LoginDialog
from ..app.auth.util.auth_service import AuthService

class TLGeoContentDock(QgsDockWidget):
    """
    Bottom Dock Widget: Contains the dynamic tabs (TabManager).
    Behaves like the QGIS 'Log Messages' panel.
    """
    def __init__(self, parent=None):
        super(TLGeoContentDock, self).__init__("TLGeo Content", parent)
        self.setObjectName("TLGeoContentDock")
        
        # Main content widget
        self.main_widget = QWidget()
        self.setWidget(self.main_widget)
        
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.main_widget.setLayout(self.layout)
        
        # Tab Manager
        self.tab_manager = TabManager()
        self.layout.addWidget(self.tab_manager)
    
    def open_tab(self, widget, title):
        """Adds a widget as a new tab"""
        self.tab_manager.add_tab(widget, title)

    def find_tab_by_key(self, key):
        """Finds a tab widget by its objectName"""
        for i in range(self.tab_manager.tabs.count()):
             w = self.tab_manager.tabs.widget(i)
             if w.objectName() == key:
                 self.tab_manager.tabs.setCurrentIndex(i)
                 return w
        return None
    
    def refresh_active_tab_if_needed(self):
        """Helper to refresh content of active tab"""
        # Iterate all tabs and call 'load_...' or 'refresh'
        for i in range(self.tab_manager.tabs.count()):
            w = self.tab_manager.tabs.widget(i)
            if isinstance(w, ProjectListWidget):
                w.load_projects()
            elif isinstance(w, ProfileWidget):
                w.load_profile()


class TLGeoRibbonDock(QgsDockWidget):
    """
    Top Dock Widget: Contains the Ribbon Menu.
    Controls the Content Dock.
    """
    def __init__(self, content_dock, parent=None):
        super(TLGeoRibbonDock, self).__init__("TLGeo Ribbon", parent)
        self.setObjectName("TLGeoRibbonDock")
        
        self.content_dock = content_dock # Reference to the bottom dock
        self.auth_service = AuthService()

        # Main content widget
        self.main_widget = QWidget()
        self.setWidget(self.main_widget)
        
        # Layout
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.main_widget.setLayout(self.layout)
        
        # Ribbon
        self.ribbon = RibbonWidget()
        self.layout.addWidget(self.ribbon)
        
        # Setup Ribbon Tabs
        self.setup_home_ribbon()
        self.setup_frms_ribbon()
        self.setup_example_ribbon()
        self.setup_tools_ribbon()
        
        # Open Project List by default on startup
        self.open_project_list()

    def setup_home_ribbon(self):
        home_tab = self.ribbon.add_tab("Geocollect")
        
        # Group: Projects
        project_group = home_tab.add_group("Dự án")
        
        icon_project = QgsApplication.getThemeIcon("/mIconFolder.svg")
        if icon_project.isNull():
            icon_project = QApplication.style().standardIcon(QStyle.SP_DirIcon)
            
        project_group.add_large_button("Quản lý", icon_project, self.open_project_list)
        
        # Group: Publish
        publish_group = home_tab.add_group("Xuất bản")
        
        icon_publish = QgsApplication.getThemeIcon("/mActionSharing.svg")
        if icon_publish.isNull():
             icon_publish = QApplication.style().standardIcon(QStyle.SP_DialogSaveButton)

        publish_group.add_large_button("Xuất bản lớp", icon_publish, self.open_publish)
        
        # Group: Auth/Profile
        auth_group = home_tab.add_group("Cá nhân")
        
        icon_profile = QgsApplication.getThemeIcon("/user.svg")
        if icon_profile.isNull():
             icon_profile = QApplication.style().standardIcon(QStyle.SP_ComputerIcon)

        auth_group.add_large_button("Thông tin", icon_profile, self.open_profile)
        
        icon_login = QgsApplication.getThemeIcon("/mActionStart.svg")
        if icon_login.isNull():
             icon_login = QApplication.style().standardIcon(QStyle.SP_DialogYesButton)

        auth_group.add_large_button("Đăng nhập", icon_login, self.show_login)
        
        home_tab.add_stretch()

    def setup_frms_ribbon(self):
        frms_tab = self.ribbon.add_tab("FRMS")

        # Group: FRMS
        frms_group = frms_tab.add_group("Chức năng")
        
        icon_frms = QgsApplication.getThemeIcon("/mActionDbManager.svg") 
        if icon_frms.isNull():
             icon_frms = QApplication.style().standardIcon(QStyle.SP_DirHomeIcon)

        frms_group.add_large_button("Dữ liệu & Biên tập", icon_frms, self.open_frms_tools)
        
        frms_tab.add_stretch()

    def setup_example_ribbon(self):
        """
        Example Ribbon Tab to demonstrate features.
        """
        ex_tab = self.ribbon.add_tab("Example")

        # 1. Group with Large Buttons
        grp_main = ex_tab.add_group("Main Actions")
        
        icon_save = QApplication.style().standardIcon(QStyle.SP_DriveFDIcon)
        grp_main.add_large_button("Save", icon_save, lambda: QMessageBox.information(self, "Demo", "Save Clicked"))
        
        icon_open = QApplication.style().standardIcon(QStyle.SP_DialogOpenButton)
        grp_main.add_large_button("Open", icon_open, lambda: QMessageBox.information(self, "Demo", "Open Clicked"))

        # 2. Group with Mixed Layout (Column of Small Buttons)
        grp_edit = ex_tab.add_group("Editing")
        
        # Large Button
        icon_paste = QApplication.style().standardIcon(QStyle.SP_BrowserReload)
        grp_edit.add_large_button("Paste", icon_paste)
        
        # Column of Small Buttons
        col1 = grp_edit.add_column()
        col1.add_small_button("Cut", QApplication.style().standardIcon(QStyle.SP_TrashIcon), lambda: print("Cut"))
        col1.add_small_button("Copy", QApplication.style().standardIcon(QStyle.SP_FileIcon), lambda: print("Copy"))
        col1.add_small_button("Format", QApplication.style().standardIcon(QStyle.SP_DialogHelpButton))

        # 3. Group with Option Button
        grp_opts = ex_tab.add_group("Options")
        grp_opts.add_large_button("Settings", QApplication.style().standardIcon(QStyle.SP_MessageBoxInformation))
        grp_opts.enable_option_button(lambda: QMessageBox.information(self, "Options", "Launch Dialog!"))

        # 4. Group with Gallery (Visual List)
        grp_gallery = ex_tab.add_group("Styles")
        gallery = grp_gallery.add_gallery()
        
        # Add some dummy items to gallery
        for i in range(5):
            btn = RibbonButton(f"Style {i+1}", mode="large")
            btn.setFixedSize(60, 60)
            btn.setStyleSheet("background-color: #eee; border: 1px solid #ccc;")
            gallery.add_item(btn)
            
        ex_tab.add_stretch()

    def setup_tools_ribbon(self):
        tools_tab = self.ribbon.add_tab("Công cụ")
        
        # Group: System
        sys_group = tools_tab.add_group("Hệ thống")
        
        icon_tools = QgsApplication.getThemeIcon("/mActionOptions.svg")
        if icon_tools.isNull():
             icon_tools = QApplication.style().standardIcon(QStyle.SP_ToolBarHorizontalExtensionButton)

        sys_group.add_large_button("Tiện ích", icon_tools, self.open_tools)
        
        tools_tab.add_stretch()

    # --- Actions ---

    def ensure_content_visible(self):
        if self.content_dock and not self.content_dock.isVisible():
            self.content_dock.show()

    def open_tab_generic(self, widget_class, title, unique_key=None):
        """
        Generic method to open a tab in the Content Dock.
        """
        if not self.content_dock: return
        
        self.ensure_content_visible()

        key = unique_key or widget_class.__name__
        
        # Check existing in content dock
        existing = self.content_dock.find_tab_by_key(key)
        if existing:
            return existing
        
        # Create new
        widget = widget_class()
        widget.setObjectName(key)
        
        # Connect signals if needed
        if isinstance(widget, ProfileWidget):
            widget.user_logged_out.connect(self.on_user_logged_out)
            
        self.content_dock.open_tab(widget, title)
        return widget

    def open_project_list(self):
        self.open_tab_generic(ProjectListWidget, "Dự án")

    def open_publish(self):
        self.open_tab_generic(PublishWidget, "Xuất bản")

    def open_tools(self):
        self.open_tab_generic(ToolsWidget, "Tiện ích")

    def open_frms_tools(self):
        self.open_tab_generic(FRMSToolsWidget, "FRMS Tools")

    def open_profile(self):
        widget = self.open_tab_generic(ProfileWidget, "Cá nhân")
        # Force reload if needed
        if hasattr(widget, 'load_profile') and self.auth_service.is_authenticated():
            widget.load_profile()

    def show_login(self):
        if self.auth_service.is_authenticated():
            QMessageBox.information(self, "Thông báo", "Bạn đã đăng nhập rồi.")
            return
            
        dlg = LoginDialog(self)
        if dlg.exec_():
            QMessageBox.information(self, "Thành công", "Đăng nhập thành công!")
            if self.content_dock:
                self.content_dock.refresh_active_tab_if_needed()

    def on_user_logged_out(self):
        if self.content_dock:
            self.content_dock.refresh_active_tab_if_needed()
