import asyncio
import websockets
import json
import ssl
from qgis.PyQt.QtCore import QThread, pyqtSignal
from ....util.i18n import tr

class ChatWSWorker(QThread):
    """
    Background worker thread running an asyncio loop to handle
    the WebSocket client connection to the agent server (/ws/ui).
    """
    connection_changed = pyqtSignal(bool)
    message_received = pyqtSignal(dict) # Contains websocket message payload
    auth_failed = pyqtSignal(str)

    def __init__(self, ws_url, token, thread_id, parent=None):
        super().__init__(parent)
        self.ws_url = ws_url
        self.token = token
        self.thread_id = thread_id
        self.is_running = True
        self.websocket = None
        self.loop = None
        self.send_queue = None

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.send_queue = asyncio.Queue()
        
        try:
            self.loop.run_until_complete(self.ws_lifecycle())
        except Exception as e:
            print(f"[ChatWSWorker] Loop terminated: {e}")
        finally:
            self.loop.close()

    async def ws_lifecycle(self):
        url = self.ws_url
        params = []
        if self.token:
            params.append(f"token={self.token}")
        if params:
            url = f"{url}?{'&'.join(params)}"
            
        print(f"[ChatWSWorker] Connecting to {url}")
        
        while self.is_running:
            try:
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
                async with websockets.connect(url, ssl=ssl_context, ping_interval=20, ping_timeout=10) as ws:
                    self.websocket = ws
                    self.connection_changed.emit(True)
                    
                    receive_task = asyncio.create_task(self.receive_loop())
                    send_task = asyncio.create_task(self.send_loop())
                    
                    done, pending = await asyncio.wait(
                        [receive_task, send_task],
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    for task in pending:
                        task.cancel()
            except websockets.exceptions.ConnectionClosed as e:
                print(f"[ChatWSWorker] Connection closed: {e}")
                if getattr(e, 'code', None) == 1008:
                    self.auth_failed.emit(tr("Phiên đăng nhập hết hạn hoặc không hợp lệ."))
                    self.is_running = False
            except Exception as e:
                print(f"[ChatWSWorker] Error: {e}")
                
            self.websocket = None
            self.connection_changed.emit(False)
            
            if self.is_running:
                await asyncio.sleep(3)

    async def receive_loop(self):
        while self.websocket:
            try:
                message = await self.websocket.recv()
                data = json.loads(message)
                self.message_received.emit(data)
            except Exception as e:
                print(f"[ChatWSWorker] Receive error: {e}")
                break

    async def send_loop(self):
        while self.websocket:
            try:
                payload = await self.send_queue.get()
                await self.websocket.send(json.dumps(payload))
                self.send_queue.task_done()
            except Exception as e:
                print(f"[ChatWSWorker] Send error: {e}")
                break

    def send_message(self, text):
        """Thread-safe method to queue a message for sending."""
        if self.loop and self.send_queue:
            payload = {
                "type": "query",
                "query": text,
                "thread_id": self.thread_id
            }
            asyncio.run_coroutine_threadsafe(self.send_queue.put(payload), self.loop)

    def stop_generation(self):
        """Send stop message to server."""
        if self.loop and self.send_queue:
            payload = {
                "type": "stop"
            }
            asyncio.run_coroutine_threadsafe(self.send_queue.put(payload), self.loop)

    def stop(self):
        self.is_running = False
        if self.websocket and self.loop:
            asyncio.run_coroutine_threadsafe(self.websocket.close(), self.loop)
