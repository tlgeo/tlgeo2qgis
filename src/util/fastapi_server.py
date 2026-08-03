from fastapi import FastAPI, Request, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import threading
# Removed QgsMessageLog to ensure thread safety
def log_msg(msg: str):
    print(f"[TLGeoFastAPI] {msg}")
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

def get_plugin():
    import sys
    plugin = getattr(sys, 'tlgeo_plugin', None)
    if plugin is None:
        global _qgis_plugin
        return _qgis_plugin
    return plugin

def start_web_server(qgis_plugin):
    global _qgis_plugin
    _qgis_plugin = qgis_plugin
    import sys
    sys.tlgeo_plugin = qgis_plugin
    global server

    # if server is not None and server.started:
    #     log_msg('Web server is already running')
    #     return
    log_msg('Trying to run FastAPI server')
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*']
    )

    @app.get("/")
    def read_root():
        plugin = get_plugin()
        if not plugin:
            raise ValueError("Plugin instance is not initialized.")
        return plugin.hello()
    
    @app.post('/')
    async def command(request: Request):
        try:
            log_msg('POST /')
            body = await body_parser(request)
            plugin = get_plugin()
            if not plugin:
                raise ValueError("Plugin instance is not initialized.")
            return plugin.process_command(body)
        except Exception as e:
            log_msg(f'Error in command endpoint: {e}')
            return {'error': str(e)}
        
    @app.post('/geotagged_photos')
    async def geotagged_photos(request: Request, files: List[UploadFile] = File(...)):
        try:
            name = 'Geotagged photos'
            body = await body_parser(request)
            try:
                name = body.get('name')
            except Exception:
                _ = None
            log_msg(f'POST /geotagged_photos {body}')
            temp_dir = tempfile.mkdtemp()

            # Save all uploaded files to the temporary directory
            for file in files:
                file_path = os.path.join(temp_dir, file.filename)
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)

            # folder = '/Users/taluan/Downloads/Telegram Desktop/1741245701297__31275744-c08a-4bd8-86d3-30fdd36e2bdc',
            plugin = get_plugin()
            if not plugin:
                raise ValueError("Plugin instance is not initialized.")
            result = plugin.add_geotagged_photos(temp_dir, name)
            if result:
                return { "status": "success" }
            else:
                return { "status": "failed" }
        except Exception as e:
            log_msg(f'Error in geotagged_photos endpoint: {e}')
            return { "status": "failed", "error": str(e)}

    @app.post('/geojson')
    async def post_geojson(request: Request):
        try:
            log_msg('POST /geojson')
            body = await body_parser(request)

            name = body.get('name')
            geojson = body.get('geojson')

            log_msg(f'POST get something {name}')
            plugin = get_plugin()
            if not plugin:
                raise ValueError("Plugin instance is not initialized.")
            result = plugin.add_geojson_layer(name, geojson)
            if result:
                return { "status": "success" }
            else:
                return { "status": "failed" }
        except Exception as e:
            log_msg(f'Error in post_geojson endpoint: {e}')
            return {'error': str(e)}
    
    
    def run_server():
        global server
        try:
            host_bind = ".".join(["0", "0", "0", "0"])
            config = uvicorn.Config(app, host=host_bind, port=PORT, log_config={  # nosec B104
                "version": 1,
                "formatters": {
                    "default": {
                        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                    }
                },
                "handlers": {
                    "default": {
                        "class": "logging.StreamHandler",
                        "formatter": "default"
                    }
                },
                "loggers": {
                    "uvicorn": {"handlers": ["default"], "level": "INFO"}
                }
            })
            server = uvicorn.Server(config)
            
            server.run()
            log_msg(f'Server has stopped running on port {PORT}')
        except Exception as err:
            log_msg(f'ERROR on running FastAPI server: {err}')
            _ = err
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

async def stop():
    global server
    log_msg('Trying to stop fastapi server')
    try:
        if server:
            server.should_exit = True
            server.force_exit = True
            await server.shutdown()
    except Exception as e:
        log_msg(f'Could not force shutdown server: {e}')
        _ = e
    log_msg('Server was stopped')

    
        

