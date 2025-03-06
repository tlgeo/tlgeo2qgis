from fastapi import FastAPI, Request, Form, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import threading
from PyQt5.QtWidgets import QAction, QMenu, QDialog, QLabel, QPushButton
from PyQt5.QtWidgets import QDockWidget, QVBoxLayout, QWidget
from PyQt5.QtGui import QIcon
from qgis.core import QgsRasterLayer, QgsProject, QgsMessageLog, Qgis, QgsRectangle, QgsCoordinateReferenceSystem, QgsVectorTileLayer, QgsDataSourceUri
from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QDesktopServices
from PyQt5.QtWebKitWidgets import QWebView
server = None
_qgis_plugin = None
PORT=13000

def start_web_server(qgis_plugin):
    global _qgis_plugin
    _qgis_plugin = qgis_plugin
    global server

    # if server is not None and server.started:
    #     QgsMessageLog.logMessage('Web server is already running', 'MyPlugin', level=Qgis.Info)
    #     return
    QgsMessageLog.logMessage('Trying to running', 'MyPlugin', level=Qgis.Info)
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*']
    )

    @app.get("/")
    def read_root():
        global _qgis_plugin
        return _qgis_plugin.hello()
    
    @app.post('/')
    async def command(request: Request):
        global _qgis_plugin
        try:
            QgsMessageLog.logMessage('POST get something aa', 'MyPlugin', level=Qgis.Info)
            form_data = await request.form()

            QgsMessageLog.logMessage(f'POST get something {form_data}', 'MyPlugin', level=Qgis.Info)
            return _qgis_plugin.process_command(dict(form_data))
        except Exception as e:
            QgsMessageLog.logMessage(f'Error', 'MyPlugin', level=Qgis.Info)
            return {'error': str(e)}
    
    def run_server():
        global server
        config = uvicorn.Config(app, host="0.0.0.0", port=PORT)
        server = uvicorn.Server(config)
        
        server.run()
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    QgsMessageLog.logMessage(f'Server is running on port {PORT}', 'MyPlugin', level=Qgis.Info)

async def stop():
    global server
    QgsMessageLog.logMessage('Trying to stop fastapi server', 'MyPlugin', level=Qgis.Info)
    try:
        server.should_exit = True
        server.force_exit = True
        await server.shutdown()
    except:
        QgsMessageLog.logMessage('Could not force shutdown server', 'MyPlugin', level=Qgis.Info)
        pass
    QgsMessageLog.logMessage('Server was stopped', 'MyPlugin', level=Qgis.Info)

    
        

