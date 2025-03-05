import os
import inspect
from PyQt5.QtWidgets import QAction, QMenu, QDialog, QLabel, QPushButton
from PyQt5.QtWidgets import QDockWidget, QVBoxLayout, QWidget
from PyQt5.QtGui import QIcon
from qgis.core import QgsRasterLayer, QgsProject, QgsMessageLog, Qgis, QgsRectangle, QgsCoordinateReferenceSystem
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QDesktopServices
from PyQt5.QtWebKitWidgets import QWebView
from flask import Flask, jsonify
import threading
from flask import request
from flask_cors import CORS, cross_origin
from .util import net_util

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]
PORT=13000

# Create Flask app
app = Flask(__name__)
cors = CORS(app) # allow CORS for all domains on all routes.
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route('/')
def home():
    return "Hello, QGIS!"

# Function to shut down Flask server gracefully
def shutdown_server():
    try:
        func = request.environ.get('werkzeug.server.shutdown')
        if func:
            func()
    except RuntimeError:
        pass

@app.route('/', methods = ['POST'])
@cross_origin()
def command():
    global qgis_plugin
    try:
        data = request.form.to_dict()
        message = '' + str(data)
        QgsMessageLog.logMessage('Get an command', 'MyPlugin', level=Qgis.Info)
        QgsMessageLog.logMessage(message, 'MyPlugin', level=Qgis.Info)
        if True:
            # basemap_url = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
            zmin = 0
            zmax = 19
            crs = 'EPSG:3857'
            encode_url = data['url'].replace('&', '%26')
            uri = f"http-header:referer=&type=xyz&url={encode_url}" #&zmin={zmin}&zmax={zmax}&crs={crs}&bbox={data['bbox']}
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
        return "ok"
    except Exception as e:
        print(e)
        return 'failed'

# Function to run Flask app
def run_flask():
    app.run(host='0.0.0.0', port=PORT, threaded=True)

class TLGeoQGISPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.dock_widget = None
        self.flask_thread = None

    def initGui(self):
        self.iface.messageBar().pushMessage("TLGeoQGIS plugin is running")

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
        # run
        self.run()
    def show_ip(self):
        ip_address = net_util.get_lan_ip()
        address = f"{ip_address}:{PORT}"
        self.iface.messageBar().pushMessage(address)
        self.show_dialog(f"Hiện địa chỉ IP và cổng", 
            f"""    TLGeo QGIS đang chạy tại địa chỉ {address}
Có thể sử dụng địa chỉ này để kết nối Geocollect mobile tới QGIS của bạn
            """
        )
    def unload(self):
        self.iface.removeToolBarIcon(self.action)
        shutdown_server()
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

        # Start Flask app in a separate thread
        self.flask_thread = threading.Thread(target=run_flask, daemon=True)
        self.flask_thread.start()
        qgis_plugin = self

    def run(self):
        self.start_web_server()
        self.open_web_page()

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

