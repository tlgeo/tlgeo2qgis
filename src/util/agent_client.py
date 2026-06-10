import json
import os
from PyQt5.QtCore import QObject, QUrl, QTimer, Qt, QDate, QDateTime, QTime
from PyQt5.QtGui import QColor
from PyQt5.QtWebSockets import QWebSocket
from qgis.core import QgsProject, QgsMessageLog, Qgis, QgsFeatureRequest, QgsRectangle

def serialize_value(val):
    if isinstance(val, (QDate, QDateTime, QTime)):
        return val.toString(Qt.ISODate)
    try:
        json.dumps(val)
        return val
    except TypeError:
        return str(val)

class QGISAgentClient(QObject):
    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.ws = QWebSocket()
        self.ws.connected.connect(self.on_connected)
        self.ws.disconnected.connect(self.on_disconnected)
        self.ws.textMessageReceived.connect(self.on_message_received)
        
        self.reconnect_timer = QTimer()
        self.reconnect_timer.setInterval(5000)  # Reconnect every 5 seconds
        self.reconnect_timer.timeout.connect(self.connect_to_server)
        
        self.url = QUrl("")
        self.is_running = False

    def start(self):
        self.is_running = True
        self.connect_to_server()

    def stop(self):
        self.is_running = False
        self.reconnect_timer.stop()
        self.ws.close()

    def connect_to_server(self):
        if self.ws.state() == 0:  # UnconnectedState
            token = ""
            if self.plugin and hasattr(self.plugin, "auth_service"):
                token = self.plugin.auth_service.get_token() or ""
            server_url = os.getenv("AGENT_SERVER_URL", "ws://localhost:13001/ws/qgis")
            self.url = QUrl(f"{server_url}?token={token}")
            
            QgsMessageLog.logMessage(f"Connecting to TLGeo Agent Server ({server_url})...", "TLGeo2QGIS", level=Qgis.Info)
            self.ws.open(self.url)

    def on_connected(self):
        QgsMessageLog.logMessage("Successfully connected to TLGeo Agent Server!", "TLGeo2QGIS", level=Qgis.Info)
        self.reconnect_timer.stop()

    def on_disconnected(self):
        QgsMessageLog.logMessage("Disconnected from TLGeo Agent Server.", "TLGeo2QGIS", level=Qgis.Warning)
        if self.is_running:
            self.reconnect_timer.start()

    def on_message_received(self, message):
        try:
            data = json.loads(message)
            if data.get("type") == "tool_request":
                request_id = data.get("id")
                action = data.get("action")
                params = data.get("params", {})
                
                QgsMessageLog.logMessage(f"Received agent tool request: {action}", "TLGeo2QGIS", level=Qgis.Info)
                
                # Execute tool and get response
                result = self.execute_tool(action, params)
                
                # Send response back
                response = {
                    "type": "tool_response",
                    "id": request_id,
                }
                if isinstance(result, dict) and result.get("status") == "error":
                    response["status"] = "error"
                    response["error"] = result.get("error", "Unknown error")
                else:
                    response["status"] = "success"
                    response["result"] = result
                    
                self.ws.sendTextMessage(json.dumps(response))
        except Exception as e:
            QgsMessageLog.logMessage(f"Error handling agent message: {e}", "TLGeo2QGIS", level=Qgis.Critical)

    def execute_tool(self, action, params):
        try:
            if action == "list_layers":
                return self.list_layers()
            elif action == "zoom_to_layer":
                return self.zoom_to_layer(params)
            elif action == "select_features":
                return self.select_features(params)
            elif action == "highlight_features":
                return self.highlight_features(params)
            elif action == "set_layer_visibility":
                return self.set_layer_visibility(params)
            elif action == "get_layer_attributes":
                return self.get_layer_attributes(params)
            elif action == "set_layer_style":
                return self.set_layer_style(params)
            elif action == "reorder_layer":
                return self.reorder_layer(params)
            elif action == "zoom_to_features":
                return self.zoom_to_features(params)
            else:
                return {"status": "error", "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # --- Tool Implementations ---

    def list_layers(self):
        layers = []
        for layer in QgsProject.instance().mapLayers().values():
            ltype = "vector" if layer.type() == 0 else "raster" if layer.type() == 1 else "other"
            geom_type = "NoGeometry"
            if ltype == "vector":
                g = layer.geometryType()
                if g == 0: geom_type = "Point"
                elif g == 1: geom_type = "Line"
                elif g == 2: geom_type = "Polygon"
            layers.append({
                "name": layer.name(),
                "id": layer.id(),
                "type": ltype,
                "geometry_type": geom_type
            })
        return layers

    def zoom_to_layer(self, params):
        layer_name = params.get("layer_name")
        matching_layers = QgsProject.instance().mapLayersByName(layer_name)
        if not matching_layers:
            return {"status": "error", "error": f"Layer '{layer_name}' not found."}
        layer = matching_layers[0]
        if self.plugin and self.plugin.iface:
            canvas = self.plugin.iface.mapCanvas()
            canvas.setExtent(layer.extent())
            canvas.refresh()
            return f"Zoomed to layer '{layer_name}' successfully."
        return {"status": "error", "error": "QGIS map interface is not available."}

    def select_features(self, params):
        layer_name = params.get("layer_name")
        query = params.get("query")
        matching_layers = QgsProject.instance().mapLayersByName(layer_name)
        if not matching_layers:
            return {"status": "error", "error": f"Layer '{layer_name}' not found."}
        layer = matching_layers[0]
        if layer.type() != 0:
            return {"status": "error", "error": f"Layer '{layer_name}' is not a vector layer."}

        request = QgsFeatureRequest().setFilterExpression(query)
        features = list(layer.getFeatures(request))
        ids = [f.id() for f in features]
        layer.selectByIds(ids)
        if self.plugin and self.plugin.iface:
            self.plugin.iface.mapCanvas().refresh()
        return f"Selected {len(ids)} features matching query '{query}' in layer '{layer_name}'."

    def highlight_features(self, params):
        layer_name = params.get("layer_name")
        query = params.get("query")
        matching_layers = QgsProject.instance().mapLayersByName(layer_name)
        if not matching_layers:
            return {"status": "error", "error": f"Layer '{layer_name}' not found."}
        layer = matching_layers[0]
        if layer.type() != 0:
            return {"status": "error", "error": f"Layer '{layer_name}' is not a vector layer."}

        if self.plugin and self.plugin.iface:
            request = QgsFeatureRequest().setFilterExpression(query)
            features = list(layer.getFeatures(request))
            ids = [f.id() for f in features]
            self.plugin.iface.mapCanvas().flashFeatures(layer, ids)
            return f"Highlighted {len(ids)} features in layer '{layer_name}'."
        return {"status": "error", "error": "QGIS map interface is not available."}

    def set_layer_visibility(self, params):
        layer_name = params.get("layer_name")
        visible = params.get("visible")
        matching_layers = QgsProject.instance().mapLayersByName(layer_name)
        if not matching_layers:
            return {"status": "error", "error": f"Layer '{layer_name}' not found."}
        layer = matching_layers[0]
        node = QgsProject.instance().layerTreeRoot().findLayer(layer.id())
        if node:
            node.setItemVisibilityChecked(visible)
            return f"Layer '{layer_name}' visibility set to {visible}."
        return {"status": "error", "error": "Could not find layer node in project tree."}

    def get_layer_attributes(self, params):
        layer_name = params.get("layer_name")
        limit = params.get("limit", 10)
        query = params.get("query")
        selected_only = params.get("selected_only", False)

        matching_layers = QgsProject.instance().mapLayersByName(layer_name)
        if not matching_layers:
            return {"status": "error", "error": f"Layer '{layer_name}' not found."}
        layer = matching_layers[0]
        if layer.type() != 0:
            return {"status": "error", "error": f"Layer '{layer_name}' is not a vector layer."}

        request = QgsFeatureRequest()
        if query:
            request.setFilterExpression(query)
        if selected_only:
            selected_ids = layer.selectedFeatureIds()
            request.setFilterFids(selected_ids)

        features = []
        fields = [field.name() for field in layer.fields()]
        for f in layer.getFeatures(request):
            attrs = {}
            for field in fields:
                val = f[field]
                if val is None or str(val) == "NULL":
                    val = ""
                else:
                    val = serialize_value(val)
                attrs[field] = val
            features.append(attrs)
            if len(features) >= limit:
                break
        return features

    def set_layer_style(self, params):
        layer_name = params.get("layer_name")
        fill_color = params.get("fill_color")
        stroke_color = params.get("stroke_color")
        stroke_width = params.get("stroke_width")
        opacity = params.get("opacity")

        matching_layers = QgsProject.instance().mapLayersByName(layer_name)
        if not matching_layers:
            return {"status": "error", "error": f"Layer '{layer_name}' not found."}
        layer = matching_layers[0]
        if layer.type() != 0:
            return {"status": "error", "error": f"Layer '{layer_name}' is not a vector layer."}

        renderer = layer.renderer()
        if not renderer:
            return {"status": "error", "error": "Layer does not have a valid renderer."}

        symbol = renderer.symbol()
        if not symbol:
            return {"status": "error", "error": "Layer renderer does not have a symbol."}

        if fill_color:
            if fill_color.lower() in ['none', 'transparent']:
                symbol.setColor(QColor(0, 0, 0, 0))
            else:
                symbol.setColor(QColor(fill_color))

        if stroke_color:
            if hasattr(symbol, 'setOutlineColor'):
                symbol.setOutlineColor(QColor(stroke_color))
            elif hasattr(symbol, 'setLineColor'):
                symbol.setLineColor(QColor(stroke_color))
            else:
                symbol.setColor(QColor(stroke_color))

        if stroke_width is not None:
            if hasattr(symbol, 'setStrokeWidth'):
                symbol.setStrokeWidth(float(stroke_width))
            elif hasattr(symbol, 'setWidth'):
                symbol.setWidth(float(stroke_width))

        if opacity is not None:
            op = float(opacity)
            if op > 1.0:
                op = op / 100.0
            layer.setOpacity(op)

        layer.triggerRepaint()
        if self.plugin and self.plugin.iface:
            self.plugin.iface.mapCanvas().refresh()
        return f"Successfully updated style of layer '{layer_name}'."

    def reorder_layer(self, params):
        layer_name = params.get("layer_name")
        target_layer_name = params.get("target_layer_name")
        position = params.get("position", "below")

        matching_layers = QgsProject.instance().mapLayersByName(layer_name)
        matching_targets = QgsProject.instance().mapLayersByName(target_layer_name)
        if not matching_layers or not matching_targets:
            return {"status": "error", "error": "One or both layers not found."}

        layer = matching_layers[0]
        target = matching_targets[0]

        root = QgsProject.instance().layerTreeRoot()
        node_layer = root.findLayer(layer.id())
        node_target = root.findLayer(target.id())

        if not node_layer or not node_target:
            return {"status": "error", "error": "Could not find layer nodes in project layer tree."}

        parent_target = node_target.parent()
        parent_layer = node_layer.parent()

        clone = node_layer.clone()
        idx = parent_target.children().index(node_target)

        if position == 'above':
            parent_target.insertChildNode(idx, clone)
        else:
            parent_target.insertChildNode(idx + 1, clone)

        parent_layer.removeChildNode(node_layer)
        return f"Reordered layer '{layer_name}' {position} '{target_layer_name}' successfully."

    def zoom_to_features(self, params):
        layer_name = params.get("layer_name")
        query = params.get("query")
        selected_only = params.get("selected_only", False)

        matching_layers = QgsProject.instance().mapLayersByName(layer_name)
        if not matching_layers:
            return {"status": "error", "error": f"Layer '{layer_name}' not found."}
        layer = matching_layers[0]
        if layer.type() != 0:
            return {"status": "error", "error": f"Layer '{layer_name}' is not a vector layer."}

        request = QgsFeatureRequest()
        if query:
            request.setFilterExpression(query)
        if selected_only:
            selected_ids = layer.selectedFeatureIds()
            request.setFilterFids(selected_ids)

        rect = QgsRectangle()
        rect.setMinimal()
        count = 0
        for f in layer.getFeatures(request):
            if f.hasGeometry():
                rect.combineExtentWith(f.geometry().boundingBox())
                count += 1

        if count > 0 and self.plugin and self.plugin.iface:
            canvas = self.plugin.iface.mapCanvas()
            canvas.setExtent(rect)
            canvas.refresh()
            return f"Zoomed to {count} features in layer '{layer_name}'."
        return {"status": "error", "error": "No features matching conditions were found or they have no geometry."}

_client = None

def start_agent_client(plugin):
    global _client
    if _client is None:
        _client = QGISAgentClient(plugin)
        _client.start()

def stop_agent_client():
    global _client
    if _client is not None:
        _client.stop()
        _client = None
