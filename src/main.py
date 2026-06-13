import os
import inspect
from PyQt5.QtWidgets import QAction, QMenu, QDialog, QLabel, QPushButton, QMessageBox, QApplication, QStyle, QTextEdit
from PyQt5.QtWidgets import QDockWidget, QVBoxLayout, QWidget
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from qgis.core import QgsRasterLayer, QgsProject, QgsMessageLog, Qgis, QgsRectangle, QgsCoordinateReferenceSystem, QgsVectorTileLayer, QgsDataSourceUri, QgsVectorLayer, QgsEditorWidgetSetup, QgsApplication, QgsVectorFileWriter
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QDesktopServices
from qgis.core import QgsLineSymbol, QgsSingleSymbolRenderer
from PyQt5.QtWebKitWidgets import QWebView
import asyncio
import json

from .app.tools.ui import qr_code_dialog
from .app.auth.ui.login_dialog import LoginDialog
# Updated import for split docks
from .ui.dock_widget import TLGeoContentDock, TLGeoRibbonDock
from .util import net_util
from .util import fastapi_server
from .util import agent_client
from .app.auth.util.auth_service import AuthService
from . import layer_menu_provider
from .util.qgis_bridge import QGISAgentBridge
import processing

PORT = 13000
global qgis_plugin
cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]
class TLGeoQGISPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.content_dock = None
        self.ribbon_dock = None
        self.menu = None
        self.toolbar = None
        self.actions = []
        self.auth_service = AuthService()
        self.is_authenticated = False
        self.agent_bridge = None

    def initGui(self):
        global qgis_plugin
        qgis_plugin = self
        
        # Check authentication before initializing plugin
        if not self.check_authentication():
            return  # Don't initialize if authentication fails
        
        # start web server
        # web_server.start_web_server(self)
        fastapi_server.start_web_server(self)
        
        # start agent client
        # agent_client.start_agent_client(self)

        # Initialize Docks
        # 1. Content Dock (Bottom)
        self.content_dock = TLGeoContentDock(self.iface.mainWindow())
        self.iface.addDockWidget(Qt.BottomDockWidgetArea, self.content_dock)
        self.content_dock.hide()
        
        # 2. Ribbon Dock (Top) - Passes reference to content_dock
        self.ribbon_dock = TLGeoRibbonDock(self.content_dock, self.iface.mainWindow())
        self.iface.addDockWidget(Qt.TopDockWidgetArea, self.ribbon_dock)
        self.ribbon_dock.hide()

        # Initialize Toolbar
        self.toolbar = self.iface.addToolBar("TLGeo Toolbar")
        self.toolbar.setObjectName("TLGeoToolbar")

        # Icon path
        icon_path = os.path.join(cmd_folder, 'logo.png')
        default_icon = QIcon(icon_path)

        # 1. Toggle Dock Action
        self.action_toggle = QAction(default_icon, "Toggle TLGeo Panel", self.iface.mainWindow())
        self.action_toggle.setCheckable(True)
        self.action_toggle.triggered.connect(self.toggle_dock)
        self.toolbar.addAction(self.action_toggle)
        self.actions.append(self.action_toggle)
        
        # Connect dock visibility change to action state
        # Logic: If ribbon is visible, button is checked
        self.ribbon_dock.visibilityChanged.connect(self.action_toggle.setChecked)

        # 2. Publish Action
        publish_icon = QgsApplication.getThemeIcon('/mActionShowAllLayers.svg') # Placeholder
        if publish_icon.isNull():
            publish_icon = default_icon
        self.action_publish = QAction(publish_icon, "Publish Active Layer", self.iface.mainWindow())
        self.action_publish.triggered.connect(self.publish_layer)
        self.toolbar.addAction(self.action_publish)
        self.actions.append(self.action_publish)

        # 3. User Profile Action
        user_icon = QgsApplication.getThemeIcon('/user.svg')
        if user_icon.isNull():
            user_icon = default_icon
        self.action_profile = QAction(user_icon, "User Profile", self.iface.mainWindow())
        self.action_profile.triggered.connect(self.show_user_profile)
        self.toolbar.addAction(self.action_profile)
        self.actions.append(self.action_profile)

        # add the action to menu bar
        self.menu = QMenu("TLGeo", self.iface.mainWindow())
        if True:
            # Add user profile action
            self.menu.addAction(self.action_profile)
            
            # Add version info action
            # Use standard information icon from QStyle
            info_icon = QApplication.style().standardIcon(QStyle.SP_MessageBoxInformation)
            actionVersionInfo = QAction(info_icon, "Thông tin phiên bản", self.iface.mainWindow())
            actionVersionInfo.triggered.connect(self.show_version_info)
            self.menu.addAction(actionVersionInfo)
            
            # Add logout action
            self.menu.addSeparator()
            # Use standard close/logout icon
            logout_icon = QgsApplication.getThemeIcon('/mActionFileExit.svg')
            if logout_icon.isNull():
                 logout_icon = QApplication.style().standardIcon(QStyle.SP_DialogCloseButton)
                 
            actionLogout = QAction(logout_icon, "Đăng xuất", self.iface.mainWindow())
            actionLogout.triggered.connect(self.logout)
            self.menu.addAction(actionLogout)

        self.iface.mainWindow().menuBar().addMenu(self.menu)
        
        # Initialize layer context menu provider (right-click on layer)
        layer_menu_provider.init_provider(self.iface, self)
        
        # Initialize Agent WebSocket Bridge
        try:
            self.agent_bridge = QGISAgentBridge(self.iface, auth_service=self.auth_service)
            self.agent_bridge.start()
        except Exception as e:
            QgsMessageLog.logMessage(f"Failed to start QGISAgentBridge: {e}", 'TLGeo2QGIS', level=Qgis.Warning)

    def toggle_dock(self):
        # Logic: if ribbon is visible, hide ALL. If hidden, show ALL.
        if self.ribbon_dock.isVisible():
            self.ribbon_dock.hide()
            self.content_dock.hide()
        else:
            self.ribbon_dock.show()
            self.content_dock.show()

    def publish_layer(self):
        # Switch to Publish tab in dock
        self.ribbon_dock.show()
        self.content_dock.show()
        # Ribbon dock has the logic to open tabs, let's use it
        self.ribbon_dock.open_publish()
        QMessageBox.information(self.iface.mainWindow(), "Publish", "Selected active layer for publishing.")

    def show_ip(self):
        ip_address = net_util.get_lan_ip()
        address = f"{ip_address}:{PORT}"
        hint_text = f"""TLGeo QGIS đang chạy tại địa chỉ {address}"""
        dialog = qr_code_dialog.QRCodeDialog(address, hint_text)
        dialog.exec_()
    
    def show_version_info(self):
        """Show QGIS, GDAL version and export capabilities"""
        from osgeo import gdal
        
        # Get QGIS version
        qgis_version = Qgis.QGIS_VERSION
        qgis_version_int = Qgis.QGIS_VERSION_INT
        
        # Get GDAL version
        gdal_version = gdal.VersionInfo("RELEASE_NAME")
        gdal_version_num = gdal.VersionInfo("VERSION_NUM")
        
        # Check export capabilities
        capabilities = self.check_export_capabilities()
        
        # Build info message
        info = f"""
<h3>TLGeo2QGIS - Thông tin phiên bản</h3>

<b>QGIS:</b><br/>
• Version: {qgis_version}<br/>
• Version Int: {qgis_version_int}<br/>
<br/>

<b>GDAL/OGR:</b><br/>
• Version: {gdal_version}<br/>
• Version Number: {gdal_version_num}<br/>
<br/>

<b>Khả năng xuất dữ liệu:</b><br/>
• SQLite: ✅ Có sẵn<br/>
• SLD Style: ✅ Có sẵn<br/>
• MBTiles (Processing): {'✅ Có sẵn' if capabilities['mbtiles_processing'] else '❌ Không có'}<br/>
• MBTiles (GDAL): {'✅ Có sẵn' if capabilities['mbtiles_gdal'] else '❌ Không có'}<br/>
• PMTiles: {'✅ Có sẵn (GDAL 3.8+)' if capabilities['pmtiles'] else '❌ Không có (cần GDAL 3.8+)'}<br/>
<br/>

<b>Ghi chú:</b><br/>
• MBTiles cần QGIS 3.14+ hoặc GDAL có driver MBTiles<br/>
• PMTiles cần GDAL 3.8.0 trở lên<br/>
• Nếu không có MBTiles/PMTiles, vui lòng nâng cấp QGIS lên phiên bản mới nhất<br/>
"""
        
        # Create dialog with scrollable text
        dialog = QDialog(self.iface.mainWindow())
        dialog.setWindowTitle("Thông tin phiên bản")
        dialog.resize(600, 500)
        
        layout = QVBoxLayout()
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setHtml(info)
        layout.addWidget(text_edit)
        
        close_button = QPushButton("Đóng")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def check_export_capabilities(self):
        """Check which export formats are available"""
        capabilities = {
            "mbtiles_processing": False,
            "mbtiles_gdal": False,
            "pmtiles": False
        }
        
        # Check processing algorithms
        try:
            import processing
            try:
                processing.algorithmHelp('native:writevectortiles_mbtiles')
                capabilities["mbtiles_processing"] = True
            except:
                pass
        except:
            pass
        
        # Check GDAL drivers
        try:
            drivers = QgsVectorFileWriter.ogrDriverList()
            for driver in drivers:
                driver_name = driver.driverName if hasattr(driver, 'driverName') else driver.longName
                if "MBTiles" in driver_name:
                    capabilities["mbtiles_gdal"] = True
                if "PMTiles" in driver_name:
                    capabilities["pmtiles"] = True
        except:
            pass
        
        return capabilities

    def check_authentication(self) -> bool:
        """
        Check if user is authenticated, show login dialog if not
        
        Returns:
            bool: True if authenticated, False if user cancelled login
        """
        # Check if token exists
        if not self.auth_service.is_authenticated():
            return self.show_login_dialog()
        
        # Validate existing token
        if not self.auth_service.validate_token():
            # Token is invalid/expired, show login again
            QMessageBox.warning(
                self.iface.mainWindow(),
                "Phiên đăng nhập hết hạn",
                "Phiên đăng nhập của bạn đã hết hạn.\nVui lòng đăng nhập lại."
            )
            return self.show_login_dialog()
        
        # Token is valid
        self.is_authenticated = True
        user_info = self.auth_service.get_user_info()
        if user_info:
            QgsMessageLog.logMessage(
                f"Đăng nhập thành công: {user_info.get('email')}",
                'TLGeo2QGIS',
                level=Qgis.Info
            )
        return True
    
    def show_login_dialog(self) -> bool:
        """
        Show login dialog and handle result
        
        Returns:
            bool: True if login successful, False if cancelled
        """
        dialog = LoginDialog(self.iface.mainWindow())
        if dialog.exec_() == QDialog.Accepted:
            # User logged in successfully
            self.is_authenticated = True
            user_info = self.auth_service.get_user_info()
            if user_info:
                self.iface.messageBar().pushSuccess(
                    "TLGeo2QGIS",
                    f"Đăng nhập thành công! Xin chào {user_info.get('email', 'user')}"
                )
            return True
        else:
            # User cancelled login
            QMessageBox.warning(
                self.iface.mainWindow(),
                "TLGeo2QGIS",
                "Bạn cần đăng nhập để sử dụng plugin này.\n"
                "Plugin sẽ không được khởi tạo."
            )
            return False
    
    def logout(self):
        """Handle logout action"""
        reply = QMessageBox.question(
            self.iface.mainWindow(),
            "Xác nhận đăng xuất",
            "Bạn có chắc chắn muốn đăng xuất?\n"
            "Bạn sẽ cần đăng nhập lại khi khởi động lại plugin.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.auth_service.logout()
            self.is_authenticated = False
            self.iface.messageBar().pushInfo(
                "TLGeo2QGIS",
                "Đăng xuất thành công. Vui lòng khởi động lại plugin để đăng nhập lại."
            )
    
    def show_user_profile(self):
        """Show user profile information in DockWidget"""
        if not self.is_authenticated:
            QMessageBox.warning(
                self.iface.mainWindow(),
                "TLGeo2QGIS",
                "Bạn cần đăng nhập để xem thông tin cá nhân."
            )
            return
        
        # Show dock widgets
        self.ribbon_dock.show()
        self.content_dock.show()
        
        # Switch to Profile tab using RibbonDock's method
        self.ribbon_dock.open_profile()

        
        # self.iface.messageBar().pushMessage(address, hint_text)
        # self.show_dialog(f"Hiện địa chỉ IP và cổng", 
        #     hint_text
        # )
    def unload(self):
        # Stop Agent WebSocket Bridge
        if self.agent_bridge:
            try:
                self.agent_bridge.stop()
            except Exception as e:
                QgsMessageLog.logMessage(f"Failed to stop QGISAgentBridge: {e}", 'TLGeo2QGIS', level=Qgis.Warning)
            del self.agent_bridge

        # Unload layer context menu provider
        layer_menu_provider.unload()
        
        # Remove DockWidgets
        # Attempt to remove by object name first (catch orphans)
        try:
             # Find all dock widgets in main window
             docks = self.iface.mainWindow().findChildren(QDockWidget)
             for dock in docks:
                 if dock.objectName() in ["TLGeoContentDock", "TLGeoRibbonDock"]:
                     self.iface.removeDockWidget(dock)
                     dock.close()
                     dock.deleteLater()
        except Exception as e:
             QgsMessageLog.logMessage(f"Error cleaning up docks: {e}", 'TLGeo2QGIS', level=Qgis.Warning)

        # Remove explicit references if they still exist
        if self.content_dock:
            try:
                self.content_dock.close()
                self.iface.removeDockWidget(self.content_dock)
            except: pass
            del self.content_dock
            
        if self.ribbon_dock:
            try:
                self.ribbon_dock.close()
                self.iface.removeDockWidget(self.ribbon_dock)
            except: pass
            del self.ribbon_dock

        # Remove Toolbar
        if self.toolbar:
            try:
                self.iface.mainWindow().removeToolBar(self.toolbar)
            except: pass
            del self.toolbar
            
        # Clean up actions
        if self.actions:
            for action in self.actions:
                try:
                    self.iface.removeToolBarIcon(action)
                except: pass

        # Remove menu from menubar
        if self.menu:
            try:
                self.iface.mainWindow().menuBar().removeAction(self.menu.menuAction())
            except: pass
            del self.menu
        
        # Stop Agent Client
        # agent_client.stop_agent_client()
        
        # Stop FastAPI server
        asyncio.run(fastapi_server.stop())
    def show_dialog(self, title, message):
        dialog = QDialog(self.iface.mainWindow())
        dialog.setWindowTitle(title)

        layout = QVBoxLayout()
        
        label = QLabel(message)
        layout.addWidget(label)
        
        close_button = QPushButton("Xác nhận")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        dialog.setLayout(layout)
        dialog.exec_()
    def open_web_page(self):
        # url = 'http://localhost:12000/connect/remote-image'
        # QDesktopServices.openUrl(QUrl(url))
        pass

    def set_crs(self):
        # Set project CRS to EPSG:3857
        crs = QgsCoordinateReferenceSystem("EPSG:3857")
        QgsProject.instance().setCrs(crs)
        print(f"Project CRS set to: {QgsProject.instance().crs().authid()}")
    
    def start_web_server(self):
        global qgis_plugin
    
    def hello(self):
        return "Hello from TLGeoQGIS plugin reload is working"
    def process_command(self, data):
        try:
            message = '' + str(data)
            QgsMessageLog.logMessage('Get an command', 'MyPlugin', level=Qgis.Info)
            QgsMessageLog.logMessage(message, 'MyPlugin', level=Qgis.Info)

            is_vector = False
            zmin = 0
            zmax = 22
            if True:
                try:
                    if 'source_type' in data:
                        is_vector = data['source_type'] == 'vector'
                    if 'zmin' in data:
                        zmin = int(data['zmin'])
                    if 'zmax' in data:
                        zmax = int(data['zmax'])
                except:
                    QgsMessageLog.logMessage(f'ERROR', 'MyPlugin', level=Qgis.Info)    


            if is_vector:
                # basemap_url = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
                crs = 'EPSG:3857'
                encode_url = data['url'].replace('&', '%26')
                uri = f"styleUrl=https://raw.githubusercontent.com/thangqd/vstyles/main/esri/esri_dark.json&type=xyz&zmin={zmin}&zmax={zmax}&url={encode_url}" #&zmin={zmin}&zmax={zmax}&crs={crs}&bbox={data['bbox']}
                name = data['name']
                
                layer = QgsVectorTileLayer(uri, name)

                if layer.isValid():
                    QgsProject.instance().addMapLayer(layer)
                    # bbox_splited = data['bbox'].split(',')
                    
                    # bbox = QgsRectangle( float(bbox_splited[0]), float(bbox_splited[1]), float(bbox_splited[2]), float(bbox_splited[3]))
                    # if qgis_plugin:
                    #     # qgis_plugin.iface.mapCanvas().setExtent(bbox)
                    #     # # qgis_plugin.iface.mapCanvas().refresh()
                    #     qgis_plugin.iface.messageBar().pushSuccess("Success", "Layer added")
                    # else:
                    #     QgsMessageLog.logMessage("qgis_plugin None", 'MyPlugin', level=Qgis.Info)
                else:
                    QgsMessageLog.logMessage(f'Invalid layer', 'MyPlugin', level=Qgis.Info)
                    qgis_plugin.iface.messageBar().pushCritical("Error", "Layer not valid")
            else:
                # basemap_url = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
                crs = 'EPSG:3857'
                encode_url = data['url'].replace('&', '%26')
                uri = f"http-header:referer=&type=xyz&zmin={zmin}&zmax={zmax}&url={encode_url}" #&zmin={zmin}&zmax={zmax}&crs={crs}&bbox={data['bbox']}
                name = data['name']
                layer = QgsRasterLayer(uri, name, 'wms')

                if layer.isValid():
                    QgsProject.instance().addMapLayer(layer)
                    # bbox_splited = data['bbox'].split(',')
                    
                    # bbox = QgsRectangle( float(bbox_splited[0]), float(bbox_splited[1]), float(bbox_splited[2]), float(bbox_splited[3]))
                    # if qgis_plugin:
                    #     # qgis_plugin.iface.mapCanvas().setExtent(bbox)
                    #     # # qgis_plugin.iface.mapCanvas().refresh()
                    #     qgis_plugin.iface.messageBar().pushSuccess("Success", "Layer added")
                    # else:
                    #     QgsMessageLog.logMessage("qgis_plugin None", 'MyPlugin', level=Qgis.Info)
                else:
                    qgis_plugin.iface.messageBar().pushCritical("Error", "Layer not valid")
            return { "status": "ok" }
        except Exception as e:
            QgsMessageLog.logMessage(f'Exception {e}', 'MyPlugin', level=Qgis.Info)
            return 'failed'

    def add_geojson_layer(self, name, geojson_str):
        # geojson_str = json.dumps(geojson)

        # Load GeoJSON as an in-memory layer
        layer = QgsVectorLayer(f"GeoJSON:{geojson_str}", name, "ogr")

        # Check if the layer is valid
        if not layer.isValid():
            return False
        else:
            QgsProject.instance().addMapLayer(layer)
            # symbol = QgsLineSymbol.createSimple({'width': '1', 'color': 'blue'})  # Adjust width and color
            # renderer = QgsSingleSymbolRenderer(symbol)
            # layer.setRenderer(renderer)
            return True
    
    def add_geotagged_photos(self, folder_path, name = 'Geotagged Photos'):
        params = {
            'FOLDER': folder_path,
            'RECURSIVE': False,  # Set to True if you want to scan subfolders
            'OUTPUT': 'TEMPORARY_OUTPUT'  # Use 'memory:' for temporary layer or specify a file path
        }

        result = processing.run("native:importphotos", params)
        layer = result['OUTPUT']
        layer.setName(name)
        if True:
            layer.startEditing()  # Enable editing mode
            
            fields = layer.fields()
            field_idx = fields.indexOf('photo')
            
            config = {'DocumentViewer': 1, 'DocumentViewerHeight': 0, 'DocumentViewerWidth': 0, 'FileWidget': True, 'FileWidgetButton': True, 'FileWidgetFilter': '', 'PropertyCollection': {'name': None, 'properties': {}, 'type': 'collection'}, 'RelativeStorage': 0, 'StorageAuthConfigId': None, 'StorageMode': 0, 'StorageType': None}
            
            type = 'ExternalResource'
            widget_setup = QgsEditorWidgetSetup(type,config)
            layer.setEditorWidgetSetup(field_idx, widget_setup)
        QgsProject.instance().addMapLayer(layer)

    def show_gdal_update_prompt(self):
        """Show GDAL update dialog"""
        from osgeo import gdal
        from .app.tools.ui.gdal_update_dialog import GDALUpdateDialog
        from .app.tools.util.gdal_installer import GDALInstaller
        
        gdal_version = gdal.VersionInfo("RELEASE_NAME")
        
        dialog = GDALUpdateDialog(gdal_version, self.iface.mainWindow())
        
        if dialog.exec_() == QDialog.Accepted:
            choice = dialog.get_choice()
            
            if choice == "auto_install":
                # Auto install GDAL
                installer = GDALInstaller(self.iface)
                if installer.install_gdal():
                    QMessageBox.information(
                        self.iface.mainWindow(),
                        "Cài đặt thành công",
                        "GDAL 3.8.3 đã được cài đặt!\n\n"
                        "Vui lòng khởi động lại QGIS để sử dụng GDAL mới."
                    )
                # Note: install_gdal shows its own error dialogs
            
            elif choice == "download_qgis_ltr":
                # Open QGIS download page
                QDesktopServices.openUrl(QUrl("https://qgis.org/en/site/forusers/download.html"))
            
            elif choice == "download_qgis_latest":
                # Open QGIS latest download
                QDesktopServices.openUrl(QUrl("https://qgis.org/en/site/forusers/download.html"))
            
            elif choice == "use_sqlite":
                # Show SQLite guide
                self.show_sqlite_conversion_guide()

    def show_sqlite_conversion_guide(self):
        """Show guide for converting SQLite to MBTiles/PMTiles"""
        guide = """
<h3>Hướng dẫn chuyển đổi SQLite sang MBTiles/PMTiles</h3>

<h4>Bước 1: Export sang SQLite</h4>
<p>Plugin đã export layer sang SQLite (EPSG:4326). File này hoạt động trên mọi version QGIS.</p>

<h4>Bước 2: Cài đặt công cụ chuyển đổi</h4>

<b>Tippecanoe (SQLite → MBTiles):</b>
<pre>
# macOS (Homebrew)
brew install tippecanoe

# Linux (build from source)
git clone https://github.com/felt/tippecanoe.git
cd tippecanoe && make && sudo make install
</pre>

<b>pmtiles (MBTiles → PMTiles):</b>
<pre>
# Download từ GitHub
https://github.com/protomaps/go-pmtiles/releases
</pre>

<h4>Bước 3: Chuyển đổi</h4>
<pre>
# SQLite → MBTiles
tippecanoe -o output.mbtiles -l layer_name input_4326.sqlite

# MBTiles → PMTiles
pmtiles convert output.mbtiles output.pmtiles
</pre>

<h4>Tài liệu tham khảo:</h4>
<ul>
<li><a href="https://github.com/felt/tippecanoe">Tippecanoe Documentation</a></li>
<li><a href="https://github.com/protomaps/PMTiles">PMTiles Documentation</a></li>
</ul>
"""
        
        dialog = QDialog(self.iface.mainWindow())
        dialog.setWindowTitle("Hướng dẫn chuyển đổi")
        dialog.resize(700, 500)
        
        layout = QVBoxLayout()
        
        text = QTextEdit()
        text.setReadOnly(True)
        text.setHtml(guide)
        layout.addWidget(text)
        
        btn_close = QPushButton("Đóng")
        btn_close.clicked.connect(dialog.accept)
        layout.addWidget(btn_close)
        
        dialog.setLayout(layout)
        dialog.exec_()
