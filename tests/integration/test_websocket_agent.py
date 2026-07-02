import os
import time
import json
import threading
import asyncio
import pytest
import websockets
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import QgsVectorLayer, QgsProject
from tlgeo2qgis.util.qgis_bridge import QGISAgentBridge

class MockWSServer:
    def __init__(self):
        self.port = 13999
        self.received_messages = []
        self.connections = []
        self.server = None
        self.loop = None
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()
        # Wait a bit for the server to start and bind
        time.sleep(0.5)

    def _run_server(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        async def handler(websocket):
            self.connections.append(websocket)
            try:
                async for message in websocket:
                    self.received_messages.append(json.loads(message))
            except websockets.exceptions.ConnectionClosed:
                pass
            finally:
                if websocket in self.connections:
                    self.connections.remove(websocket)

        async def main():
            # In modern websockets, serve takes handler as first argument
            self.server = await websockets.serve(handler, "127.0.0.1", self.port)
            await asyncio.Future()  # run forever

        self.loop.run_until_complete(main())

    def stop(self):
        if self.server and self.loop:
            # Cleanly close all connections
            for conn in list(self.connections):
                self.loop.call_soon_threadsafe(lambda c=conn: asyncio.create_task(c.close()))
            
            self.loop.call_soon_threadsafe(self.server.close)
            self.loop.call_soon_threadsafe(self.loop.stop)
            
        if self.thread:
            self.thread.join(timeout=1.0)

    def send_message(self, message_dict):
        if self.loop and self.connections:
            asyncio.run_coroutine_threadsafe(
                self.connections[0].send(json.dumps(message_dict)),
                self.loop
            )

def test_websocket_agent_tools(qgis_app, qgis_iface):
    """Test successful WebSocket connection and agent tool requests/responses."""
    # 1. Clean up any existing layers
    QgsProject.instance().removeAllMapLayers()

    # 2. Start mock WS server
    server = MockWSServer()
    server.start()
    
    try:
        # Set agent URL env var for the bridge
        os.environ["TLGEO_AGENT_URL"] = "ws://127.0.0.1:13999/ws/qgis"
        
        # 3. Instantiate and start bridge
        bridge = QGISAgentBridge(qgis_iface)
        bridge.start()
        
        # Wait up to 5 seconds for connection
        connected = False
        for _ in range(50):
            QCoreApplication.processEvents()
            time.sleep(0.1)
            if bridge.is_connected:
                connected = True
                break
        
        assert connected, "Bridge failed to connect to mock WebSocket server"
        
        # 4. Add a test layer in QGIS
        layer = QgsVectorLayer("Point?crs=EPSG:4326", "Hà Nội Boundary", "memory")
        QgsProject.instance().addMapLayer(layer)
        
        # 5. Send 'list_layers' request from mock server to plugin
        request_id = "req-123"
        server.send_message({
            "type": "tool_request",
            "id": request_id,
            "action": "list_layers",
            "params": {}
        })
        
        # Wait up to 5 seconds for response to be received by mock server
        response_received = None
        for _ in range(50):
            QCoreApplication.processEvents()
            time.sleep(0.1)
            # Check server.received_messages
            for msg in server.received_messages:
                if msg.get("id") == request_id:
                    response_received = msg
                    break
            if response_received:
                break
                
        assert response_received is not None, "Did not receive response from agent bridge for list_layers"
        assert response_received["status"] == "success"
        
        layers = response_received["result"]
        assert len(layers) == 1
        assert layers[0]["name"] == "Hà Nội Boundary"
        
        # 6. Test 'set_layer_visibility' action
        request_id_2 = "req-456"
        server.send_message({
            "type": "tool_request",
            "id": request_id_2,
            "action": "set_layer_visibility",
            "params": {
                "layer_name": "Hà Nội Boundary",
                "visible": False
            }
        })
        
        # Wait for response
        response_received_2 = None
        for _ in range(50):
            QCoreApplication.processEvents()
            time.sleep(0.1)
            for msg in server.received_messages:
                if msg.get("id") == request_id_2:
                    response_received_2 = msg
                    break
            if response_received_2:
                break
                
        assert response_received_2 is not None, "Did not receive response from agent bridge for set_layer_visibility"
        assert response_received_2["status"] == "success"
        
        # 7. Stop bridge
        bridge.stop()
        
    finally:
        server.stop()
        QgsProject.instance().removeAllMapLayers()
