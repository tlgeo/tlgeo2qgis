from qgis.PyQt.QtCore import QObject, pyqtSignal, QThread, Qt, QCoreApplication
from qgis.core import Qgis
import asyncio
import websockets
import json
import logging
import traceback
import threading
from . import qgis_tools

logger = logging.getLogger("qgis.agent_bridge")

def log_msg(msg: str, level=Qgis.Info):
    # Log to python standard logging (always thread-safe)
    if level == Qgis.Info:
        logger.info(msg)
    elif level == Qgis.Warning:
        logger.warning(msg)
    elif level == Qgis.Critical:
        logger.error(msg)
    print(f"[TLGeoAgentBridge] {msg}")

def get_plugin_version():
    import os
    try:
        metadata_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "metadata.txt")
        if os.path.exists(metadata_path):
            with open(metadata_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("version="):
                        return line.split("=")[1].strip()
    except Exception as e:
        log_msg(f"Error reading plugin version: {e}", Qgis.Warning)
    return "1.0.1"

def get_qgis_version():
    try:
        return getattr(Qgis, "QGIS_VERSION", None)
    except Exception:
        return None

class WSClientWorker(QThread):
    """
    Background worker thread running an asyncio loop to handle
    the persistent WebSocket client connection to the agent server.
    """
    command_received = pyqtSignal(str, dict, str) # action, params, request_id
    connection_changed = pyqtSignal(bool)
    auth_failed = pyqtSignal(str)

    def __init__(self, ws_url=None, auth_service=None, parent=None):
        super().__init__(parent)
        import os
        if ws_url is None:
            agent_url = os.getenv("TLGEO_AGENT_URL", "wss://agent.tlgeo.net").rstrip("/")
            if agent_url.endswith("/ws/qgis"):
                agent_url = agent_url[:-8]
            elif agent_url.endswith("/ws/ui"):
                agent_url = agent_url[:-6]
            ws_url = f"{agent_url}/ws/qgis"
        self.ws_url = ws_url
        self.auth_service = auth_service
        self.is_running = True
        self.websocket = None
        self.loop = None
        self.send_queue = None

    def run(self):
        """Starts the background asyncio event loop"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        # Create the Queue inside the correct event loop of the background thread
        self.send_queue = asyncio.Queue()
        
        try:
            self.loop.run_until_complete(self.ws_lifecycle())
        except Exception as e:
            log_msg(f"Async loop terminated with error: {e}", Qgis.Warning)
        finally:
            self.loop.close()
            log_msg("Async loop closed.")

    async def ws_lifecycle(self):
        """WebSocket connection lifecycle with auto-reconnect logic"""
        import urllib.parse
        while self.is_running:
            try:
                # Dynamically retrieve the latest token before connecting
                token = self.auth_service.get_token() if self.auth_service else None
                version = get_plugin_version()
                qgis_ver = get_qgis_version()
                url = self.ws_url
                
                params = []
                if token:
                    params.append(f"token={urllib.parse.quote(token)}")
                if version:
                    params.append(f"version={urllib.parse.quote(version)}")
                if qgis_ver:
                    params.append(f"qgis_version={urllib.parse.quote(qgis_ver)}")
                if params:
                    url = f"{self.ws_url}?{'&'.join(params)}"
                
                log_msg(f"Attempting to connect to Agent Server: {url}")
                if url.startswith("wss://"):
                    import ssl
                    ssl_context = ssl.create_default_context()
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                    connect_args = {"ssl": ssl_context}
                else:
                    connect_args = {}
                    
                async with websockets.connect(url, ping_interval=20, ping_timeout=10, **connect_args) as ws:
                    self.websocket = ws
                    log_msg("WebSocket connected successfully to Agent Server.")
                    self.connection_changed.emit(True)
                    
                    # Run send and receive loops concurrently, cancelling the other when one exits
                    receive_task = asyncio.create_task(self.receive_loop())
                    send_task = asyncio.create_task(self.send_loop())
                    
                    done, pending = await asyncio.wait(
                        [receive_task, send_task],
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    for task in pending:
                        task.cancel()
            except websockets.exceptions.ConnectionClosed as e:
                log_msg(f"WebSocket connection closed by server. Code: {getattr(e, 'code', 'unknown')}", Qgis.Warning)
                if getattr(e, 'code', None) == 1008:
                    self.auth_failed.emit("Phiên đăng nhập hết hạn hoặc không hợp lệ.")
                    self.is_running = False
            except Exception as e:
                log_msg(f"WebSocket client error: {e}", Qgis.Warning)
                
            self.websocket = None
            self.connection_changed.emit(False)
            
            if self.is_running:
                log_msg("Retrying WebSocket connection in 5 seconds...")
                await asyncio.sleep(5)

    async def receive_loop(self):
        """Listens for tool execution requests from the Agent server"""
        while self.websocket:
            try:
                message = await self.websocket.receive_text() if hasattr(self.websocket, 'receive_text') else await self.websocket.recv()
                data = json.loads(message)
                
                # Check if it is a tool request
                if data.get("type") == "tool_request":
                    request_id = data.get("id")
                    action = data.get("action")
                    params = data.get("params", {})
                    
                    # Emit PyQt signal to execute safely on the main thread
                    self.command_received.emit(action, params, request_id)
                elif data.get("type") == "auth_error":
                    self.auth_failed.emit(data.get("content", "Xác thực thất bại"))
                    self.is_running = False
                    break
            except asyncio.CancelledError:
                break
            except Exception as e:
                log_msg(f"Error in receive loop: {e}", Qgis.Warning)
                break

    async def send_loop(self):
        """Listens to the local asyncio queue and sends outgoing responses"""
        while self.websocket:
            try:
                payload = await self.send_queue.get()
                await self.websocket.send(json.dumps(payload))
                self.send_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                log_msg(f"Error in send loop: {e}", Qgis.Warning)
                break

    def queue_send(self, payload: dict):
        """Thread-safe call to schedule a send message in the asyncio queue"""
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self.send_queue.put(payload), self.loop)

    def stop(self):
        """Stops the worker thread and connection lifecycle"""
        self.is_running = False
        if self.websocket and self.loop and not self.loop.is_closed():
            # Schedule closing the websocket cleanly
            try:
                future = asyncio.run_coroutine_threadsafe(self.websocket.close(), self.loop)
                # Wait up to 1 second for the socket to cleanly disconnect
                future.result(timeout=1.0)
            except Exception:
                _ = None
        
        # Stop loop thread-safely
        if self.loop and not self.loop.is_closed():
            try:
                self.loop.call_soon_threadsafe(self.loop.stop)
            except RuntimeError:
                _ = None
        
        self.quit()
        self.wait(1000) # Wait up to 1 second for thread to exit
        log_msg("WSClientWorker thread stopped.")


class QGISAgentBridge(QObject):
    """
    Main Bridge QObject running on the QGIS main thread.
    Coordinates between the background WS Client Thread and QGIS Core UI.
    """
    def __init__(self, iface, auth_service=None, plugin=None, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.auth_service = auth_service
        self.plugin = plugin
        self.worker = None
        self.is_connected = False

    def start(self):
        """Launches the background WebSocket client thread"""
        log_msg("Starting QGISAgentBridge...")
        self.worker = WSClientWorker(auth_service=self.auth_service)
        self.worker.command_received.connect(self.on_command_received, Qt.QueuedConnection)
        self.worker.connection_changed.connect(self.on_connection_changed, Qt.QueuedConnection)
        self.worker.auth_failed.connect(self.on_auth_failed, Qt.QueuedConnection)
        self.worker.start()

    def stop(self):
        """Stops the bridge and background threads"""
        log_msg("Stopping QGISAgentBridge...")
        if self.worker:
            self.worker.stop()
            self.worker = None

    def on_connection_changed(self, connected: bool):
        self.is_connected = connected
        if connected:
            self.iface.messageBar().pushSuccess("TLGeo Agent", "Đã kết nối thành công với Trợ lý Deep Agent!")
        else:
            self.iface.messageBar().pushInfo("TLGeo Agent", "Mất kết nối với Trợ lý Deep Agent. Đang tự động kết nối lại...")

    def on_auth_failed(self, reason: str):
        log_msg(f"Authentication failed: {reason}", Qgis.Warning)
        self.iface.messageBar().pushCritical("TLGeo Agent", "Hãy đăng nhập lại, token không hợp lệ")
        if self.plugin:
            self.plugin.is_authenticated = False
            self.plugin.auth_service.logout()
            # Stop the bridge cleanly as token is invalid
            self.stop()

    def on_command_received(self, action: str, params: dict, request_id: str):
        """
        Executed on the QGIS Main Thread.
        Invokes corresponding QGIS API actions safely.
        """
        log_msg(f"Main thread executing command: {action} (ID: {request_id})")
        
        try:
            result = None
            if action == "list_layers":
                result = qgis_tools.list_layers(self.iface)
            elif action == "zoom_to_layer":
                result = qgis_tools.zoom_to_layer(self.iface, params.get("layer_name"))
            elif action == "select_features":
                result = qgis_tools.select_features(self.iface, params.get("layer_name"), params.get("query"))
            elif action == "highlight_features":
                result = qgis_tools.highlight_features(self.iface, params.get("layer_name"), params.get("query"))
            elif action == "set_layer_visibility":
                result = qgis_tools.set_layer_visibility(self.iface, params.get("layer_name"), params.get("visible"))
            elif action == "get_layer_attributes":
                result = qgis_tools.get_layer_attributes(
                    self.iface, 
                    params.get("layer_name"), 
                    params.get("limit", 10),
                    params.get("query"),
                    params.get("selected_only", False)
                )
            elif action == "set_layer_style":
                result = qgis_tools.set_layer_style(
                    self.iface,
                    params.get("layer_name"),
                    params.get("fill_color"),
                    params.get("stroke_color"),
                    params.get("stroke_width"),
                    params.get("opacity")
                )
            elif action == "reorder_layer":
                result = qgis_tools.reorder_layer(
                    self.iface,
                    params.get("layer_name"),
                    params.get("target_layer_name"),
                    params.get("position", "below")
                )
            elif action == "zoom_to_features":
                result = qgis_tools.zoom_to_features(
                    self.iface,
                    params.get("layer_name"),
                    params.get("query"),
                    params.get("selected_only", False)
                )
            elif action == "query_gis_data":
                result = qgis_tools.query_gis_data(
                    self.iface,
                    params.get("sql_query")
                )
            elif action == "set_layer_style_rule":
                result = qgis_tools.set_layer_style_rule(
                    self.iface,
                    params.get("layer_name"),
                    params.get("rule_name"),
                    params.get("expression"),
                    params.get("fill_color"),
                    params.get("stroke_color"),
                    params.get("stroke_width"),
                    params.get("opacity")
                )
            elif action == "execute_python_script":
                result = qgis_tools.execute_python_script(
                    self.iface,
                    params.get("script")
                )
            elif action == "execute_processing":
                result = qgis_tools.execute_processing(
                    self.iface,
                    params.get("algorithm"),
                    params.get("parameters")
                )
            elif action == "capture_map_canvas":
                result = qgis_tools.capture_map_canvas(self.iface)
            elif action == "list_dir":
                result = qgis_tools.list_dir(
                    params.get("directory_path")
                )
            elif action == "read_file":
                result = qgis_tools.read_file(
                    params.get("file_path")
                )
            elif action == "grep_search":
                result = qgis_tools.grep_search(
                    params.get("directory_path"),
                    params.get("pattern")
                )
            elif action == "find_file":
                result = qgis_tools.find_file(
                    params.get("filename")
                )
            else:
                raise NotImplementedError(f"Công cụ '{action}' chưa được triển khai trong QGIS Plugin.")

            # Send successful response
            response = {
                "type": "tool_response",
                "id": request_id,
                "status": "success",
                "result": result
            }
            log_msg(f"Command executed successfully: {action}")
            self.worker.queue_send(response)

        except Exception as e:
            err_msg = f"{str(e)}\n{traceback.format_exc()}"
            log_msg(f"Error executing command {action} on main thread: {err_msg}", Qgis.Warning)
            # Send error response
            response = {
                "type": "tool_response",
                "id": request_id,
                "status": "error",
                "error": str(e)
            }
            self.worker.queue_send(response)
