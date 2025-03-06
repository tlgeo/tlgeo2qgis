from fastapi import FastAPI, Request, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import threading
from qgis.core import QgsMessageLog, Qgis
import tempfile
from typing import List
import shutil
import os

server = None
_qgis_plugin = None
PORT=13000

async def body_parser(request: Request):
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        body = await request.json()  # Parse JSON
    elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form = await request.form()
        body = dict(form)  # Convert to dictionary
    else:
        body = await request.body()  # Raw body as bytes
    return body

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
            QgsMessageLog.logMessage(f'POST / {request.body()}', 'MyPlugin', level=Qgis.Info)
            body = await body_parser(request)
            return _qgis_plugin.process_command(body)
        except Exception as e:
            QgsMessageLog.logMessage(f'Error', 'MyPlugin', level=Qgis.Info)
            return {'error': str(e)}
        
    @app.post('/geotagged_photos')
    async def geotagged_photos(request: Request, files: List[UploadFile] = File(...)):
        global _qgis_plugin
        try:
            QgsMessageLog.logMessage(f'POST / {request.body()}', 'MyPlugin', level=Qgis.Info)
            temp_dir = tempfile.mkdtemp()

            # Save all uploaded files to the temporary directory
            for file in files:
                file_path = os.path.join(temp_dir, file.filename)
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)

            # folder = '/Users/taluan/Downloads/Telegram Desktop/1741245701297__31275744-c08a-4bd8-86d3-30fdd36e2bdc',
            result = _qgis_plugin.add_geotagged_photos(temp_dir)
            if result:
                return { "status": "success" }
            else:
                return { "status": "failed" }
        except Exception as e:
            QgsMessageLog.logMessage(f'Error', 'MyPlugin', level=Qgis.Info)
            return { "status": "failed", "error": str(e)}

    @app.post('/geojson')
    async def post_geojson(request: Request):
        global _qgis_plugin
        try:
            QgsMessageLog.logMessage(f'POST /geojson {request.body()}', 'MyPlugin', level=Qgis.Info)
            body = await body_parser(request)

            name = body.get('name')
            geojson = body.get('geojson')



            QgsMessageLog.logMessage(f'POST get something {name}', 'MyPlugin', level=Qgis.Info)
            result = _qgis_plugin.add_geojson_layer(name, geojson)
            if result:
                return { "status": "success" }
            else:
                return { "status": "failed" }
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

    
        

