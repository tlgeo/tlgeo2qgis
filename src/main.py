import os
import inspect
from qgis.PyQt.QtWidgets import QAction, QMenu, QDialog, QLabel, QPushButton, QMessageBox, QApplication, QStyle, QTextEdit, QDockWidget, QVBoxLayout, QWidget
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import Qt, QTimer
from qgis.core import QgsRasterLayer, QgsProject, QgsMessageLog, Qgis, QgsRectangle, QgsCoordinateReferenceSystem, QgsVectorTileLayer, QgsDataSourceUri, QgsVectorLayer, QgsEditorWidgetSetup, QgsApplication, QgsVectorFileWriter
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QDesktopServices
from qgis.core import QgsLineSymbol, QgsSingleSymbolRenderer
import asyncio
import json

from .app.tools.ui import qr_code_dialog
from .app.auth.ui.login_dialog import LoginDialog
# Updated import for split docks
from .ui.dock_widget import TLGeoContentDock, TLGeoRibbonDock
from .ui.agent_dock import TLGeoAgentDock
from .util import net_util
from .util import fastapi_server
from .util import agent_client
from .app.auth.util.auth_service import AuthService
from . import layer_menu_provider
from .util.qgis_bridge import QGISAgentBridge
import processing

from .util.i18n import init_i18n, tr

PORT = 13000
global qgis_plugin
cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]
class TLGeoQGISPlugin:
    def __init__(self, iface):
        self.iface = iface
        # Initialize translations
        init_i18n()
        
        self.content_dock = None
        self.ribbon_dock = None
        self.agent_dock = None
        self.menu = None
        self.toolbar = None
        self.actions = []
        self.auth_service = AuthService()
        self.is_authenticated = False
        self.agent_bridge = None

    def initGui(self):
        global qgis_plugin
        qgis_plugin = self
        
        # Check authentication status (non-blocking, checks if token exists)
        self.is_authenticated = self.auth_service.is_authenticated()
        
        # Initialize Docks - Temporarily disabled
        self.content_dock = None
        self.ribbon_dock = None

        # Initialize Agent Dock on the right side
        self.agent_dock = TLGeoAgentDock(self.iface.mainWindow())
        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.agent_dock)

        # Initialize Toolbar
        self.toolbar = self.iface.addToolBar(tr("TLGeo Toolbar"))
        self.toolbar.setObjectName("TLGeoToolbar")

        # Icon path
        icon_path = os.path.join(cmd_folder, 'logo.png')
        default_icon = QIcon(icon_path)

        # Single Connection Action (QR Code) - Replaces the old Toggle Dock action, uses main logo icon
        self.action_qr = QAction(default_icon, tr("Connect mobile device (QR Code)"), self.iface.mainWindow())
        self.action_qr.triggered.connect(self.show_ip)
        self.toolbar.addAction(self.action_qr)
        self.actions.append(self.action_qr)

        # add the action to menu bar (rebuilt dynamically when shown)
        self.menu = QMenu("TLGeo", self.iface.mainWindow())
        self.menu.aboutToShow.connect(self.rebuild_menu)
        self.rebuild_menu()  # Pre-populate so it is not empty and renders on the menu bar
        self.iface.mainWindow().menuBar().addMenu(self.menu)
        
        # Initialize layer context menu provider (right-click on layer)
        layer_menu_provider.init_provider(self.iface, self)
        
        # Defer starting background services to allow QGIS to finish its own startup sequence
        QTimer.singleShot(1000, self.deferred_start_services)

    def deferred_start_services(self):
        # start web server
        fastapi_server.start_web_server(self)
        
        # Initialize Agent WebSocket Bridge if authenticated
        if self.is_authenticated:
            self.start_bridge()
            
            # Fetch user profile details in the background if they are incomplete in cache
            user_info = self.auth_service.get_user_info()
            if user_info and (not user_info.get('fullname') or not user_info.get('phone')):
                import threading
                def fetch_profile_bg():
                    try:
                        self.auth_service.validate_token()
                    except Exception:
                        _ = None
                threading.Thread(target=fetch_profile_bg, daemon=True).start()

    def start_bridge(self):
        """Starts the Agent WebSocket Bridge"""
        if self.agent_bridge:
            try:
                self.agent_bridge.stop()
            except Exception:
                _ = None
            self.agent_bridge = None
            
        try:
            self.agent_bridge = QGISAgentBridge(self.iface, auth_service=self.auth_service, plugin=self)
            self.agent_bridge.start()
        except Exception as e:
            QgsMessageLog.logMessage(f"Failed to start QGISAgentBridge: {e}", 'TLGeo2QGIS', level=Qgis.Warning)

    def toggle_dock(self):
        if not self.ensure_authenticated():
            return
        # Logic: if ribbon is visible, hide ALL. If hidden, show ALL.
        if self.ribbon_dock.isVisible():
            self.ribbon_dock.hide()
            if self.content_dock:
                self.content_dock.hide()
        else:
            self.ribbon_dock.show()
            if self.content_dock:
                self.content_dock.show()

    def publish_layer(self):
        if not self.ensure_authenticated():
            return
        # Switch to Publish tab in dock
        self.ribbon_dock.show()
        if self.content_dock:
            self.content_dock.show()
        # Ribbon dock has the logic to open tabs, let's use it
        self.ribbon_dock.open_publish()
        QMessageBox.information(self.iface.mainWindow(), "Publish", "Selected active layer for publishing.")

    def show_ip(self):
        ip_address = net_util.get_lan_ip()
        address = f"{ip_address}:{PORT}"
        hint_text = tr("TLGeo QGIS is running at {}").format(address)
        dialog = qr_code_dialog.QRCodeDialog(address, hint_text)
        dialog.exec_()
    
    def show_version_info(self):
        """Show QGIS, GDAL version and export capabilities"""
        from osgeo import gdal
        
        # Read plugin version from metadata.txt
        plugin_version = "Unknown"
        try:
            metadata_path = os.path.join(os.path.dirname(__file__), "metadata.txt")
            if os.path.exists(metadata_path):
                with open(metadata_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("version="):
                            plugin_version = line.split("=")[-1].strip()
                            break
        except Exception:
            _ = None

        # Get QGIS version
        qgis_version = Qgis.QGIS_VERSION
        qgis_version_int = Qgis.QGIS_VERSION_INT
        
        # Get GDAL version
        gdal_version = gdal.VersionInfo("RELEASE_NAME")
        gdal_version_num = gdal.VersionInfo("VERSION_NUM")
        
        # Check export capabilities
        capabilities = self.check_export_capabilities()
        
        # Build translated status strings
        avail_str = tr("Available")
        not_avail_str = tr("Not available")
        pmtiles_avail_str = tr("Available (GDAL 3.8+)")
        pmtiles_not_avail_str = tr("Not available (GDAL 3.8+ required)")
        
        mbtiles_proc = avail_str if capabilities['mbtiles_processing'] else not_avail_str
        mbtiles_gdal = avail_str if capabilities['mbtiles_gdal'] else not_avail_str
        pmtiles_status = pmtiles_avail_str if capabilities['pmtiles'] else pmtiles_not_avail_str
        
        # Build info message
        info = f"""
<h3>{tr("TLGeo2QGIS - Version Info")}</h3>

<b>{tr("Plugin Version:")}</b> {plugin_version}<br/>
<br/>

<b>QGIS:</b><br/>
• Version: {qgis_version}<br/>
• Version Int: {qgis_version_int}<br/>
<br/>

<b>GDAL/OGR:</b><br/>
• Version: {gdal_version}<br/>
• Version Number: {gdal_version_num}<br/>
<br/>

<b>{tr("Export Capabilities:")}</b><br/>
• SQLite: ✅ {avail_str}<br/>
• SLD Style: ✅ {avail_str}<br/>
• MBTiles (Processing): {mbtiles_proc}<br/>
• MBTiles (GDAL): {mbtiles_gdal}<br/>
• PMTiles: {pmtiles_status}<br/>
<br/>

<b>{tr("Notes:")}</b><br/>
• {tr("MBTiles requires QGIS 3.14+ or GDAL with MBTiles driver")}<br/>
• {tr("PMTiles requires GDAL 3.8.0 or newer")}<br/>
• {tr("If MBTiles/PMTiles are unavailable, please upgrade QGIS to the newest version")}<br/>
"""
        
        # Create dialog with scrollable text
        dialog = QDialog(self.iface.mainWindow())
        dialog.setWindowTitle(tr("Version Info"))
        dialog.resize(600, 500)
        
        layout = QVBoxLayout()
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setHtml(info)
        layout.addWidget(text_edit)
        
        close_button = QPushButton(tr("Close"))
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
            except Exception:
                _ = None
        except Exception:
            _ = None
        
        # Check GDAL drivers
        try:
            drivers = QgsVectorFileWriter.ogrDriverList()
            for driver in drivers:
                driver_name = driver.driverName if hasattr(driver, 'driverName') else driver.longName
                if "MBTiles" in driver_name:
                    capabilities["mbtiles_gdal"] = True
                if "PMTiles" in driver_name:
                    capabilities["pmtiles"] = True
        except Exception:
            _ = None
        
        return capabilities

    def ensure_authenticated(self) -> bool:
        """
        Ensure the user is authenticated. If not, show login dialog.
        If authenticated but token validation fails, show warning and login.
        
        Returns:
            bool: True if authenticated, False if user cancelled login
        """
        if self.is_authenticated:
            # Dynamically check if token is valid
            if self.auth_service.validate_token():
                return True
            else:
                QMessageBox.warning(
                    self.iface.mainWindow(),
                    tr("Session Expired"),
                    tr("Your session has expired.\nPlease log in again.")
                )
                self.is_authenticated = False
                if self.agent_bridge:
                    try:
                        self.agent_bridge.stop()
                    except Exception:
                        _ = None
                    self.agent_bridge = None
        
        # Show login dialog
        if self.show_login_dialog():
            self.is_authenticated = True
            # Start/Restart bridge
            self.start_bridge()
            return True
        return False
    
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
                    tr("Login successful! Welcome {}").format(user_info.get('email', 'user'))
                )
            return True
        else:
            return False
            
    def rebuild_menu(self):
        """Rebuilds the TLGeo menu dynamically based on auth status"""
        self.menu.clear()
        
        # 1. QR Code Action
        self.menu.addAction(self.action_qr)
        
        # 2. Version Info Action
        info_icon = QApplication.style().standardIcon(QStyle.SP_MessageBoxInformation)
        actionVersionInfo = QAction(info_icon, tr("Version Info"), self.iface.mainWindow())
        actionVersionInfo.triggered.connect(self.show_version_info)
        self.menu.addAction(actionVersionInfo)
        
        # 3. Settings Action
        settings_icon = QgsApplication.getThemeIcon('/mActionOptions.svg')
        if settings_icon.isNull():
             settings_icon = QApplication.style().standardIcon(QStyle.SP_FileDialogListView)
        actionSettings = QAction(settings_icon, tr("Settings"), self.iface.mainWindow())
        actionSettings.triggered.connect(self.show_settings_dialog)
        self.menu.addAction(actionSettings)
        
        self.menu.addSeparator()
        
        # 3. Dynamic Login/Logout Action based on authentication state
        if self.is_authenticated:
            user_info = self.auth_service.get_user_info()
            if user_info:
                fullname = user_info.get('fullname') or "N/A"
                email = user_info.get('email') or "N/A"
                phone = user_info.get('username') or "N/A"
                
                actionFullname = QAction(tr("Fullname: {}").format(fullname), self.iface.mainWindow())
                actionFullname.setEnabled(False)
                self.menu.addAction(actionFullname)
                
                actionEmail = QAction(tr("Email: {}").format(email), self.iface.mainWindow())
                actionEmail.setEnabled(False)
                self.menu.addAction(actionEmail)
                
                actionPhone = QAction(tr("Phone: {}").format(phone), self.iface.mainWindow())
                actionPhone.setEnabled(False)
                self.menu.addAction(actionPhone)
                
                self.menu.addSeparator()
                
            logout_icon = QgsApplication.getThemeIcon('/mActionFileExit.svg')
            if logout_icon.isNull():
                 logout_icon = QApplication.style().standardIcon(QStyle.SP_DialogCloseButton)
            actionLogout = QAction(logout_icon, tr("Logout"), self.iface.mainWindow())
            actionLogout.triggered.connect(self.logout)
            self.menu.addAction(actionLogout)
        else:
            login_icon = QApplication.style().standardIcon(QStyle.SP_DialogOpenButton)
            actionLogin = QAction(login_icon, tr("Login"), self.iface.mainWindow())
            actionLogin.triggered.connect(self.login)
            self.menu.addAction(actionLogin)
 
    def login(self):
        """Handle login action"""
        if self.is_authenticated and self.auth_service.validate_token():
            user_info = self.auth_service.get_user_info()
            email = user_info.get("email") if user_info else "chưa rõ"
            QMessageBox.information(
                self.iface.mainWindow(),
                "TLGeo",
                tr("You are logged in as:\n{}").format(email)
            )
        else:
            self.ensure_authenticated()
 
    def logout(self):
        """Handle logout action"""
        reply = QMessageBox.question(
            self.iface.mainWindow(),
            tr("Confirm Logout"),
            tr("Are you sure you want to logout?\nSyncing with Agent will pause until you log in again."),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.auth_service.logout()
            self.is_authenticated = False
            if self.agent_bridge:
                try:
                    self.agent_bridge.stop()
                except Exception:
                    _ = None
                self.agent_bridge = None
            self.iface.messageBar().pushInfo(
                "TLGeo2QGIS",
                tr("Logout successful")
            )
    
    def show_user_profile(self):
        """Show user profile information in DockWidget"""
        if not self.ensure_authenticated():
            return
        
        # Show dock widgets
        self.ribbon_dock.show()
        if self.content_dock:
            self.content_dock.show()
        
        # Switch to Profile tab using RibbonDock's method
        self.ribbon_dock.open_profile()

    def show_settings_dialog(self):
        """Show settings dialog to configure language preference"""
        from tlgeo2qgis.ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self.iface.mainWindow())
        dialog.exec_()

        
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
                 if dock.objectName() in ["TLGeoContentDock", "TLGeoRibbonDock", "TLGeoAgentDock"]:
                     self.iface.removeDockWidget(dock)
                     dock.setParent(None)
                     dock.close()
                     dock.deleteLater()
        except Exception as e:
             QgsMessageLog.logMessage(f"Error cleaning up docks: {e}", 'TLGeo2QGIS', level=Qgis.Warning)

        # Remove explicit references if they still exist
        if self.agent_dock:
            try:
                self.iface.removeDockWidget(self.agent_dock)
                self.agent_dock.setParent(None)
                self.agent_dock.close()
                self.agent_dock.deleteLater()
            except Exception: _ = None
            self.agent_dock = None
            
        if self.content_dock:
            try:
                self.iface.removeDockWidget(self.content_dock)
                self.content_dock.setParent(None)
                self.content_dock.close()
                self.content_dock.deleteLater()
            except Exception: _ = None
            self.content_dock = None
            
        if self.ribbon_dock:
            try:
                self.iface.removeDockWidget(self.ribbon_dock)
                self.ribbon_dock.setParent(None)
                self.ribbon_dock.close()
                self.ribbon_dock.deleteLater()
            except Exception: _ = None
            self.ribbon_dock = None

        # Remove Toolbar
        if self.toolbar:
            try:
                self.iface.mainWindow().removeToolBar(self.toolbar)
            except Exception: _ = None
            del self.toolbar
            
        # Clean up actions
        if self.actions:
            for action in self.actions:
                try:
                    self.iface.removeToolBarIcon(action)
                except Exception: _ = None

        # Remove menu from menubar
        if self.menu:
            try:
                self.iface.mainWindow().menuBar().removeAction(self.menu.menuAction())
            except Exception: _ = None
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
                except Exception:
                    QgsMessageLog.logMessage(f'ERROR', 'MyPlugin', level=Qgis.Info)    


            # Get stored JWT token to authorize remote tile server requests
            token = self.auth_service.get_token()

            # Decode URL-encoded placeholders (e.g., %7Bz%7D -> {z}) and detect external tile servers
            raw_url = data.get('url', '')
            if raw_url:
                raw_url = raw_url.replace('%7Bz%7D', '{z}').replace('%7Bx%7D', '{x}').replace('%7By%7D', '{y}')
                raw_url = raw_url.replace('%7BZ%7D', '{z}').replace('%7BX%7D', '{x}').replace('%7BY%7D', '{y}')
            
            url_lower = raw_url.lower() if raw_url else ''
            is_external = any(domain in url_lower for domain in [
                'googleapis.com', 'google.com', 'openstreetmap.org', 'mapbox.com', 
                'arcgisonline.com', 'cartocdn.com', 'stamen.com'
            ])

            auth_header = ""
            if token and not is_external:
                auth_header = f"&http-header:Authorization=Bearer {token}"

            encode_url = raw_url.replace('&', '%26') if raw_url else ''

            if is_vector:
                # basemap_url = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
                crs = 'EPSG:3857'
                uri = f"styleUrl=https://raw.githubusercontent.com/thangqd/vstyles/main/esri/esri_dark.json&type=xyz&zmin={zmin}&zmax={zmax}&url={encode_url}{auth_header}" #&zmin={zmin}&zmax={zmax}&crs={crs}&bbox={data['bbox']}
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
                uri = f"http-header:referer=&type=xyz&zmin={zmin}&zmax={zmax}&url={encode_url}{auth_header}" #&zmin={zmin}&zmax={zmax}&crs={crs}&bbox={data['bbox']}
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
