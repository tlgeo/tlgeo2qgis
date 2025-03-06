import os
import inspect
from PyQt5.QtWidgets import QAction, QMenu, QDialog, QLabel, QPushButton
from PyQt5.QtWidgets import QDockWidget, QVBoxLayout, QWidget
from PyQt5.QtGui import QIcon
from qgis.core import QgsRasterLayer, QgsProject, QgsMessageLog, Qgis, QgsRectangle, QgsCoordinateReferenceSystem, QgsVectorTileLayer, QgsDataSourceUri, QgsVectorLayer, QgsEditorWidgetSetup
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QDesktopServices
from qgis.core import QgsLineSymbol, QgsSingleSymbolRenderer
from PyQt5.QtWebKitWidgets import QWebView
import asyncio
import json

from .ui import qr_code_dialog
from .util import net_util
from .util import fastapi_server
import processing

PORT = 13000
global qgis_plugin
cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]
class TLGeoQGISPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.dock_widget = None

    def initGui(self):
        global qgis_plugin
        qgis_plugin = self
        # start web server
        # web_server.start_web_server(self)
        fastapi_server.start_web_server(self)

        # add toolbar icon
        icon = os.path.join(cmd_folder, 'logo.png')
        self.action = QAction(QIcon(icon), "TLGeo", self.iface.mainWindow())
        self.iface.addToolBarIcon(self.action)
        self.action.triggered.connect(self.show_ip)

        # add the action to menu bar
        menu = QMenu("TLGeo", self.iface.mainWindow())
        if True:
            actionShowIP = QAction(QIcon(icon), "Hiện địa chỉ IP và cổng", self.iface.mainWindow())
            actionShowIP.triggered.connect(self.show_ip)
            menu.addAction(actionShowIP)

        self.iface.mainWindow().menuBar().addMenu(menu)
    def show_ip(self):
        ip_address = net_util.get_lan_ip()
        address = f"{ip_address}:{PORT}"
        hint_text = f"""TLGeo QGIS đang chạy tại địa chỉ {address}"""
        dialog = qr_code_dialog.QRCodeDialog(address, hint_text)
        dialog.exec_()

        
        # self.iface.messageBar().pushMessage(address, hint_text)
        # self.show_dialog(f"Hiện địa chỉ IP và cổng", 
        #     hint_text
        # )
    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        asyncio.run(fastapi_server.stop())
        del self.action
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
    
    def add_geotagged_photos(self, folder_path):
        params = {
            'FOLDER': folder_path,
            'RECURSIVE': False,  # Set to True if you want to scan subfolders
            'OUTPUT': 'TEMPORARY_OUTPUT'  # Use 'memory:' for temporary layer or specify a file path
        }

        result = processing.run("native:importphotos", params)
        layer = result['OUTPUT']
        if True:
            layer.startEditing()  # Enable editing mode
            
            fields = layer.fields()
            field_idx = fields.indexOf('photo')
            
            config = {'DocumentViewer': 1, 'DocumentViewerHeight': 0, 'DocumentViewerWidth': 0, 'FileWidget': True, 'FileWidgetButton': True, 'FileWidgetFilter': '', 'PropertyCollection': {'name': None, 'properties': {}, 'type': 'collection'}, 'RelativeStorage': 0, 'StorageAuthConfigId': None, 'StorageMode': 0, 'StorageType': None}
            
            type = 'ExternalResource'
            widget_setup = QgsEditorWidgetSetup(type,config)
            layer.setEditorWidgetSetup(field_idx, widget_setup)
        QgsProject.instance().addMapLayer(layer)

    # def show_dock(self):
    #     # Create a DockWidget to show the HTML file
    #     if self.dock_widget is None:
    #         self.dock_widget = QDockWidget("TLGeo QGIS", self.iface.mainWindow())
            

    #         # Load the local HTML file
    #         self.web_view = QWebView()
    #         # html_file_path = os.path.join(os.path.dirname(__file__), 'my_gui.html')
    #         url = 'http://localhost:12000'
    #         qurl = QUrl(url)
    #         print("QUrl is valid:", qurl.isValid())
    #         self.web_view.setUrl(qurl)

    #         # Add QWebEngineView to the DockWidget
    #         content_widget = QWidget()
    #         layout = QVBoxLayout()
    #         layout.addWidget(self.web_view)
    #         content_widget.setLayout(layout)
    #         self.dock_widget.setWidget(content_widget)

    #         # Add the DockWidget to QGIS
    #         self.iface.addDockWidget(1, self.dock_widget)

    #     self.dock_widget.show()

