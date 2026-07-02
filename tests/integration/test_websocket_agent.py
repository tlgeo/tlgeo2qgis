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
        # Bind to port 0 to let the OS assign a random free port (prevents 'address already in use' errors)
        self.port = 0
        self.received_messages = []
        self.connections = []
        self.server = None
        self.loop = None
        self.thread = None
        self.started_event = threading.Event()

    def start(self):
        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()
        # Wait until the server has bound and port is resolved
        self.started_event.wait(timeout=5.0)

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
            self.server = await websockets.serve(handler, "127.0.0.1", self.port)
            # Retrieve the dynamically assigned port
            self.port = self.server.sockets[0].getsockname()[1]
            self.started_event.set()
            await asyncio.Future()  # run forever

        try:
            self.loop.run_until_complete(main())
        except RuntimeError as e:
            if "Event loop stopped before Future completed" not in str(e):
                raise

    def stop(self):
        if self.server and self.loop:
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

def wait_for_response(server, request_id, timeout=5.0):
    """Helper to wait for a specific response ID from the mock server."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        QCoreApplication.processEvents()
        time.sleep(0.1)
        for msg in server.received_messages:
            if msg.get("id") == request_id:
                return msg
    return None

@pytest.fixture
def websocket_agent_session(qgis_app, qgis_iface):
    """Fixture to set up a clean Mock WebSocket server and agent bridge for each test."""
    # 1. Clean up project
    QgsProject.instance().removeAllMapLayers()
    
    # 2. Start mock WS server
    server = MockWSServer()
    server.start()
    
    # Set agent URL env var for the bridge using the dynamically assigned port
    os.environ["TLGEO_AGENT_URL"] = f"ws://127.0.0.1:{server.port}/ws/qgis"
    
    # 3. Instantiate and start bridge
    bridge = QGISAgentBridge(qgis_iface)
    bridge.start()
    
    # Wait for connection
    connected = False
    for _ in range(50):
        QCoreApplication.processEvents()
        time.sleep(0.1)
        if bridge.is_connected:
            connected = True
            break
            
    assert connected, "Bridge failed to connect to mock WebSocket server"
    
    yield server, bridge
    
    # Cleanup
    bridge.stop()
    server.stop()
    QgsProject.instance().removeAllMapLayers()

def test_tool_list_layers(websocket_agent_session):
    """Verify that 'list_layers' tool executes correctly and returns loaded layers."""
    server, bridge = websocket_agent_session
    
    # Add a test memory layer
    layer = QgsVectorLayer("Point?crs=EPSG:4326", "Hà Nội Boundary", "memory")
    QgsProject.instance().addMapLayer(layer)
    
    request_id = "req-list-layers"
    server.send_message({
        "type": "tool_request",
        "id": request_id,
        "action": "list_layers",
        "params": {}
    })
    
    response = wait_for_response(server, request_id)
    assert response is not None, "Did not receive response for list_layers"
    assert response["status"] == "success"
    
    layers = response["result"]
    assert len(layers) == 1
    assert layers[0]["name"] == "Hà Nội Boundary"

def test_tool_set_layer_visibility(websocket_agent_session):
    """Verify that 'set_layer_visibility' tool changes layer visibility successfully."""
    server, bridge = websocket_agent_session
    
    # Add a test memory layer
    layer = QgsVectorLayer("Point?crs=EPSG:4326", "Hà Nội Boundary", "memory")
    QgsProject.instance().addMapLayer(layer)
    
    request_id = "req-set-visibility"
    server.send_message({
        "type": "tool_request",
        "id": request_id,
        "action": "set_layer_visibility",
        "params": {
            "layer_name": "Hà Nội Boundary",
            "visible": False
        }
    })
    
    response = wait_for_response(server, request_id)
    assert response is not None, "Did not receive response for set_layer_visibility"
    assert response["status"] == "success"

def test_tool_zoom_to_layer(websocket_agent_session):
    """Verify that 'zoom_to_layer' tool successfully adjusts map canvas extent."""
    server, bridge = websocket_agent_session
    
    # Add a test memory layer
    layer = QgsVectorLayer("Point?crs=EPSG:4326", "Hà Nội Boundary", "memory")
    QgsProject.instance().addMapLayer(layer)
    
    # Add geometry features to ensure layer extent is NOT empty (positive area)
    from qgis.core import QgsFeature, QgsGeometry, QgsPointXY
    layer.startEditing()
    
    feat1 = QgsFeature()
    feat1.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(105.8, 21.0)))
    layer.addFeature(feat1)
    
    feat2 = QgsFeature()
    feat2.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(105.9, 21.1)))
    layer.addFeature(feat2)
    
    layer.commitChanges()
    layer.updateExtents()
    
    assert layer.featureCount() == 2, "Feature count should be 2"
    assert not layer.extent().isEmpty(), "Layer extent should not be empty"
    
    request_id = "req-zoom"
    server.send_message({
        "type": "tool_request",
        "id": request_id,
        "action": "zoom_to_layer",
        "params": {
            "layer_name": "Hà Nội Boundary"
        }
    })
    
    response = wait_for_response(server, request_id)
    assert response is not None, "Did not receive response for zoom_to_layer"
    assert response["status"] == "success"
