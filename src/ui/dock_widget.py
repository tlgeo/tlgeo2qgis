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
from ..app.frms_agent.ui.agent_chat_dialog import AgentChatDialog
from ..ui.agent_dock_widget import AgentChatWidget

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
        """
        FRMS (Forest Resource Management System) Ribbon Tab
        4 Groups: Lô rừng, Chủ rừng, Diễn biến, Báo cáo
        """
        frms_tab = self.ribbon.add_tab("FRMS")

        # ========== GROUP 1: Lô rừng (Forest Plots) ==========
        lo_rung_group = frms_tab.add_group("Lô rừng")
        
        # Large button: Tìm kiếm
        icon_search = QgsApplication.getThemeIcon("/mActionSearch.svg")
        if icon_search.isNull():
            icon_search = QApplication.style().standardIcon(QStyle.SP_FileDialogContentsView)
        lo_rung_group.add_large_button("Tìm kiếm", icon_search, self.frms_search_plots)
        
        # Column 1: Tạo mới, Gộp, Tách
        col_plot_1 = lo_rung_group.add_column()
        
        icon_new = QgsApplication.getThemeIcon("/mActionNewAttribute.svg")
        if icon_new.isNull():
            icon_new = QApplication.style().standardIcon(QStyle.SP_FileIcon)
        col_plot_1.add_small_button("Tạo mới", icon_new, self.frms_create_plot)
        
        icon_merge = QgsApplication.getThemeIcon("/mActionMergeFeatures.svg")
        if icon_merge.isNull():
            icon_merge = QApplication.style().standardIcon(QStyle.SP_ArrowRight)
        col_plot_1.add_small_button("Gộp", icon_merge, self.frms_merge_plots)
        
        icon_split = QgsApplication.getThemeIcon("/mActionSplitFeatures.svg")
        if icon_split.isNull():
            icon_split = QApplication.style().standardIcon(QStyle.SP_ArrowLeft)
        col_plot_1.add_small_button("Tách", icon_split, self.frms_split_plot)
        
        # Column 2: Xóa
        col_plot_2 = lo_rung_group.add_column()
        
        icon_delete = QgsApplication.getThemeIcon("/mActionDeleteSelected.svg")
        if icon_delete.isNull():
            icon_delete = QApplication.style().standardIcon(QStyle.SP_TrashIcon)
        col_plot_2.add_small_button("Xóa", icon_delete, self.frms_delete_plot)

        # ========== GROUP 2: Chủ rừng (Forest Owners) ==========
        chu_rung_group = frms_tab.add_group("Chủ rừng")
        
        # Large button: Tìm kiếm
        chu_rung_group.add_large_button("Tìm kiếm", icon_search, self.frms_search_owners)
        
        # Column: Tạo mới, Gộp, Đổi mã
        col_owner = chu_rung_group.add_column()
        col_owner.add_small_button("Tạo mới", icon_new, self.frms_create_owner)
        col_owner.add_small_button("Gộp", icon_merge, self.frms_merge_owners)
        
        icon_rename = QgsApplication.getThemeIcon("/mActionEditTable.svg")
        if icon_rename.isNull():
            icon_rename = QApplication.style().standardIcon(QStyle.SP_FileDialogDetailedView)
        col_owner.add_small_button("Đổi mã", icon_rename, self.frms_change_owner_code)

        # ========== GROUP 3: Diễn biến (Forest Changes/Evolution) ==========
        dien_bien_group = frms_tab.add_group("Diễn biến")
        
        # Large buttons side-by-side
        dien_bien_group.add_large_button("Tìm kiếm", icon_search, self.frms_search_changes)
        
        icon_evolution = QgsApplication.getThemeIcon("/mActionCaptureLine.svg")
        if icon_evolution.isNull():
            icon_evolution = QApplication.style().standardIcon(QStyle.SP_ArrowForward)
        dien_bien_group.add_large_button("Tạo diễn biến", icon_evolution, self.frms_create_change)

# ========== GROUP 4: Báo cáo (Reports) ==========
        bao_cao_group = frms_tab.add_group("Báo cáo")

        icon_print = QApplication.style().standardIcon(QStyle.SP_FileDialogDetailedView)
        bao_cao_group.add_large_button("In báo cáo", icon_print, self.frms_print_report)

        # ========== GROUP 5: FRMS Agent ==========
        agent_group = frms_tab.add_group("Agent")

        icon_agent = QApplication.style().standardIcon(QStyle.SP_CommandLink)
        agent_group.add_large_button("Hỏi Agent", icon_agent, self.open_frms_agent)

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
    
    # --- FRMS Action Handlers ---
    
    def frms_search_plots(self):
        """Search forest plots"""
        QMessageBox.information(
            self,
            "FRMS - Lô rừng",
            "Chức năng Tìm kiếm lô rừng đang phát triển"
        )
    
    def frms_create_plot(self):
        """Create new forest plot"""
        QMessageBox.information(
            self,
            "FRMS - Lô rừng",
            "Chức năng Tạo mới lô rừng đang phát triển"
        )
    
    def frms_merge_plots(self):
        """Merge multiple forest plots"""
        QMessageBox.information(
            self,
            "FRMS - Lô rừng",
            "Chức năng Gộp lô rừng đang phát triển"
        )
    
    def frms_split_plot(self):
        """Split forest plot"""
        QMessageBox.information(
            self,
            "FRMS - Lô rừng",
            "Chức năng Tách lô rừng đang phát triển"
        )
    
    def frms_delete_plot(self):
        """Delete forest plot"""
        QMessageBox.information(
            self,
            "FRMS - Lô rừng",
            "Chức năng Xóa lô rừng đang phát triển"
        )
    
    def frms_search_owners(self):
        """Search forest owners"""
        QMessageBox.information(
            self,
            "FRMS - Chủ rừng",
            "Chức năng Tìm kiếm chủ rừng đang phát triển"
        )
    
    def frms_create_owner(self):
        """Create new forest owner"""
        QMessageBox.information(
            self,
            "FRMS - Chủ rừng",
            "Chức năng Tạo mới chủ rừng đang phát triển"
        )
    
    def frms_merge_owners(self):
        """Merge duplicate forest owner records"""
        # This functionality exists in FRMSToolsWidget, can be extracted later
        QMessageBox.information(
            self,
            "FRMS - Chủ rừng",
            "Chức năng Gộp chủ rừng đang phát triển\n\n"
            "Hiện có trong FRMSToolsWidget tab 'Biên tập'"
        )
    
    def frms_change_owner_code(self):
        """Change forest owner identification code"""
        QMessageBox.information(
            self,
            "FRMS - Chủ rừng",
            "Chức năng Đổi mã chủ rừng đang phát triển"
        )
    
    def frms_search_changes(self):
        """Search forest change history"""
        QMessageBox.information(
            self,
            "FRMS - Diễn biến",
            "Chức năng Tìm kiếm diễn biến đang phát triển"
        )
    
    def frms_create_change(self):
        """Create new forest change event"""
        QMessageBox.information(
            self,
            "FRMS - Diễn biến",
            "Chức năng Tạo diễn biến đang phát triển"
        )
    
    def frms_print_report(self):
        """Generate and print forest management reports"""
        QMessageBox.information(
            self,
            "FRMS - Báo cáo",
            "Chức năng In báo cáo đang phát triển"
        )

    def open_frms_agent(self):
        """Open FRMS Agent chat widget in content dock"""
        widget = AgentChatWidget()
        widget.setObjectName("FRMSAgentChat")
        self.content_dock.open_tab(widget, "FRMS Agent")
