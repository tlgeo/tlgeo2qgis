import os
import inspect
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QDockWidget, QVBoxLayout, QWidget
from PyQt5.QtGui import QIcon
from qgis.core import QgsRasterLayer, QgsProject, QgsMessageLog, Qgis
from qgis.PyQt.QtCore import QUrl
from PyQt5.QtWebKitWidgets import QWebView
from flask import Flask, jsonify
import threading
from flask import request
import time

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

# Create Flask app
app = Flask(__name__)

# Event to signal Flask to stop
shutdown_event = threading.Event()
@app.route('/')
def home():
    command: str = ""
    return "Hello, QGIS!"

# Function to shut down Flask server gracefully
def shutdown_server():
    try:
        func = request.environ.get('werkzeug.server.shutdown')
        if func:
            func()
    except RuntimeError:
        pass

@app.route('/shutdown')
def shutdown():
    shutdown_server()
    return "Server shutting down..."

@app.route('/', methods = ['POST'])
def command():
    data = request.form.to_dict()
    message = '' + str(data)
    QgsMessageLog.logMessage('Get an command', 'MyPlugin', level=Qgis.Info)
    QgsMessageLog.logMessage(message, 'MyPlugin', level=Qgis.Info)
    if True:
        # basemap_url = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
        zmin = 0
        zmax = 19
        crs = 'EPSG:3857'
        uri = f"type=xyz&url={data['url']}&zmin={zmin}&zmax={zmax}&crs={crs}"
        layer = QgsRasterLayer(uri, data['name'], 'wms')

        if layer.isValid():
            QgsProject.instance().addMapLayer(layer)
            qgis_plugin.iface.messageBar().pushSuccess("Success", "OSM layer added")
        else:
            qgis_plugin.iface.messageBar().pushCritical("Error", "OSM layer not valid")
    return "ok"

# Function to run Flask app
def run_flask():
    while not shutdown_event.is_set():
        app.run(port=13000, threaded=True)
        time.sleep(1)  # Allow the thread to exit and check the shutdown event

class TLGeoQGISPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.dock_widget = None
        self.flask_thread = None

    def initGui(self):
        self.iface.messageBar().pushMessage("TLGeoQGIS plugin is running")
        icon = os.path.join(cmd_folder, 'logo.png')
        self.action = QAction(QIcon(icon), "TLGeo", self.iface.mainWindow())
        self.iface.addToolBarIcon(self.action)
        self.action.triggered.connect(self.run)
    
    def unload(self):
        self.iface.removeToolBarIcon(self.action)

        shutdown_server()

        # Signal Flask thread to stop by setting the shutdown event
        shutdown_event.set()

        # if self.flask_thread and self.flask_thread.is_alive():
        #     self.flask_thread.join()
        del self.action

    def show_dock(self):
        # Create a DockWidget to show the HTML file
        if self.dock_widget is None:
            self.dock_widget = QDockWidget("TLGeo QGIS", self.iface.mainWindow())
            

            # Load the local HTML file
            self.web_view = QWebView()
            # html_file_path = os.path.join(os.path.dirname(__file__), 'my_gui.html')
            url = 'http://localhost:12000'
            qurl = QUrl(url)
            print("QUrl is valid:", qurl.isValid())
            self.web_view.setUrl(qurl)

            # Add QWebEngineView to the DockWidget
            content_widget = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(self.web_view)
            content_widget.setLayout(layout)
            self.dock_widget.setWidget(content_widget)

            # Add the DockWidget to QGIS
            self.iface.addDockWidget(1, self.dock_widget)

        self.dock_widget.show()
    
    def start_web_server(self):
        # Start Flask app in a separate thread
        self.flask_thread = threading.Thread(target=run_flask, daemon=True)
        self.flask_thread.start()
        qgis_plugin = self

    def stop_flask_server(self):
        if self.is_flask_running:
            try:
                # Send a request to the Flask shutdown endpoint
                requests.get("http://localhost:5000/shutdown")
            except requests.RequestException:
                pass
            self.is_flask_running = False
            print("Flask server shut down.")

    def run(self):
        self.show_dock()
        self.start_web_server()

qgis_plugin: TLGeoQGISPlugin = None