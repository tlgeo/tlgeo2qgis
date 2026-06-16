from qgis.core import (
    QgsProject, 
    QgsMapLayerType, 
    QgsWkbTypes, 
    QgsFeatureRequest, 
    QgsMessageLog, 
    Qgis,
    QgsRectangle
)
import json
import traceback

def log_msg(msg: str, level=Qgis.Info):
    QgsMessageLog.logMessage(msg, 'TLGeoAgentBridge', level=level)

def get_layer_by_name(layer_name: str):
    """Helper to find a loaded vector layer by name (case-insensitive & fuzzy)"""
    layers = QgsProject.instance().mapLayers().values()
    # 1. Exact match
    for layer in layers:
        if layer.name().strip().lower() == layer_name.strip().lower():
            return layer
    # 2. Fuzzy match (contains name)
    for layer in layers:
        if layer_name.strip().lower() in layer.name().strip().lower():
            return layer
    return None

def list_layers(iface) -> list:
    """Returns a list of all loaded map layers"""
    try:
        layers = QgsProject.instance().mapLayers().values()
        layer_list = []
        for layer in layers:
            l_type = "raster" if layer.type() == QgsMapLayerType.RasterLayer else "vector"
            geom_type = "NoGeometry"
            
            if layer.type() == QgsMapLayerType.VectorLayer:
                wkb_type = layer.wkbType()
                geom_type = QgsWkbTypes.geometryDisplayString(QgsWkbTypes.geometryType(wkb_type))
            
            layer_list.append({
                "id": layer.id(),
                "name": layer.name(),
                "type": l_type,
                "geom_type": geom_type
            })
        return layer_list
    except Exception as e:
        log_msg(f"Error listing layers: {e}\n{traceback.format_exc()}", Qgis.Warning)
        raise e

def zoom_to_layer(iface, layer_name: str) -> str:
    """Zooms the map canvas to the extent of the specified layer"""
    layer = get_layer_by_name(layer_name)
    if not layer:
        raise ValueError(f"Không tìm thấy lớp bản đồ có tên '{layer_name}'.")
    
    # Zoom canvas
    extent = layer.extent()
    if extent.isEmpty():
        raise ValueError(f"Lớp bản đồ '{layer.name()}' rỗng, không thể phóng to.")
        
    iface.mapCanvas().setExtent(extent)
    iface.mapCanvas().refresh()
    return f"Đã phóng to tới lớp bản đồ '{layer.name()}'."

def select_features(iface, layer_name: str, query: str) -> str:
    """Selects features in a vector layer matching the QGIS Expression"""
    layer = get_layer_by_name(layer_name)
    if not layer:
        raise ValueError(f"Không tìm thấy lớp bản đồ có tên '{layer_name}'.")
        
    if layer.type() != QgsMapLayerType.VectorLayer:
        raise ValueError(f"Lớp '{layer.name()}' không phải là lớp Vector và không thể thực hiện truy vấn chọn đối tượng.")
        
    # Execute selection using QGIS expression
    layer.selectByExpression(query)
    count = layer.selectedFeatureCount()
    iface.mapCanvas().refresh()
    return f"Đã chọn thành công {count} đối tượng thỏa mãn điều kiện '{query}' trên lớp '{layer.name()}'."

def highlight_features(iface, layer_name: str, query: str) -> str:
    """Flashes features matching the QGIS Expression temporarily"""
    layer = get_layer_by_name(layer_name)
    if not layer:
        raise ValueError(f"Không tìm thấy lớp bản đồ có tên '{layer_name}'.")
        
    if layer.type() != QgsMapLayerType.VectorLayer:
        raise ValueError(f"Lớp '{layer.name()}' không phải là lớp Vector để thực hiện highlight.")

    # Retrieve feature IDs matching expression
    request = QgsFeatureRequest().setFilterExpression(query).setFlags(QgsFeatureRequest.NoGeometry)
    features = list(layer.getFeatures(request))
    feature_ids = [f.id() for f in features]
    
    if not feature_ids:
        return f"Không có đối tượng nào thỏa mãn điều kiện '{query}' trên lớp '{layer.name()}' để highlight."

    # Flash features in QGIS
    iface.flashFeatures(layer, feature_ids)
    return f"Đã thực hiện nhấp nháy làm nổi bật {len(feature_ids)} đối tượng thỏa mãn điều kiện trên lớp '{layer.name()}'."

def set_layer_visibility(iface, layer_name: str, visible: bool) -> str:
    """Toggles layer visibility"""
    layer = get_layer_by_name(layer_name)
    if not layer:
        raise ValueError(f"Không tìm thấy lớp bản đồ có tên '{layer_name}'.")
        
    node = QgsProject.instance().layerTreeRoot().findLayer(layer.id())
    if not node:
        raise ValueError(f"Không tìm thấy nút quản lý lớp '{layer.name()}' trong danh sách cây thư mục.")
        
    node.setItemVisibilityChecked(visible)
    return f"Đã {'hiển thị' if visible else 'ẩn'} lớp bản đồ '{layer.name()}'."

def get_layer_attributes(iface, layer_name: str, limit: int = 10, query: str = None, selected_only: bool = False) -> list:
    """Retrieves attribute table features up to a limit, optionally filtered by a query or selection status"""
    layer = get_layer_by_name(layer_name)
    if not layer:
        raise ValueError(f"Không tìm thấy lớp bản đồ có tên '{layer_name}'.")
        
    if layer.type() != QgsMapLayerType.VectorLayer:
        raise ValueError(f"Lớp '{layer.name()}' không phải lớp Vector để lấy thuộc tính.")

    fields = [field.name() for field in layer.fields()]
    
    if selected_only:
        features = layer.selectedFeatures()
        # Apply limit to selected features list
        features = features[:limit]
    else:
        request = QgsFeatureRequest()
        if query:
            request.setFilterExpression(query)
        request.setLimit(limit)
        features = layer.getFeatures(request)
    
    result = []
    for f in features:
        attrs = {}
        for field in fields:
            attrs[field] = str(f[field])
        result.append(attrs)
        
    return result

def set_layer_style(iface, layer_name: str, fill_color: str = None, stroke_color: str = None, stroke_width: float = None, opacity: float = None) -> str:
    """Sets style properties of a vector layer such as fill color, outline (stroke) color, outline width, and opacity."""
    from PyQt5.QtGui import QColor
    from PyQt5.QtCore import Qt
    
    layer = get_layer_by_name(layer_name)
    if not layer:
        raise ValueError(f"Không tìm thấy lớp bản đồ có tên '{layer_name}'.")
        
    if layer.type() != QgsMapLayerType.VectorLayer:
        raise ValueError(f"Lớp '{layer.name()}' không phải là lớp Vector và không thể thay đổi style.")

    renderer = layer.renderer()
    if not renderer:
        raise ValueError(f"Không lấy được renderer của lớp '{layer.name()}'.")
        
    # Get symbols
    symbol = renderer.symbol()
    if not symbol:
        symbols = []
        if hasattr(renderer, 'categories'):
            symbols = [cat.symbol() for cat in renderer.categories()]
        elif hasattr(renderer, 'ranges'):
            symbols = [r.symbol() for r in renderer.ranges()]
    else:
        symbols = [symbol]
        
    if not symbols or all(s is None for s in symbols):
        if hasattr(renderer, 'sourceSymbol') and renderer.sourceSymbol():
            symbols = [renderer.sourceSymbol()]

    if not symbols or all(s is None for s in symbols):
        raise ValueError(f"Không thể truy cập symbol của lớp '{layer.name()}'.")

    modified = False
    
    # Iterate and apply styling to each symbol
    for sym in symbols:
        if not sym:
            continue
            
        # 1. Fill color
        if fill_color is not None:
            if fill_color.lower() in ('transparent', 'none'):
                for i in range(sym.symbolLayerCount()):
                    layer_sym = sym.symbolLayer(i)
                    if hasattr(layer_sym, 'setFillColor'):
                        layer_sym.setFillColor(QColor(0, 0, 0, 0))
                    if hasattr(layer_sym, 'setBrushStyle'):
                        layer_sym.setBrushStyle(Qt.NoBrush)
            else:
                color = QColor(fill_color)
                if color.isValid():
                    sym.setColor(color)
                    for i in range(sym.symbolLayerCount()):
                        layer_sym = sym.symbolLayer(i)
                        if hasattr(layer_sym, 'setFillColor'):
                            layer_sym.setFillColor(color)
                        if hasattr(layer_sym, 'setBrushStyle'):
                            layer_sym.setBrushStyle(Qt.SolidPattern)
            modified = True
            
        # 2. Stroke color (Border color)
        if stroke_color is not None:
            color = QColor(stroke_color)
            if color.isValid():
                for i in range(sym.symbolLayerCount()):
                    layer_sym = sym.symbolLayer(i)
                    if hasattr(layer_sym, 'setStrokeColor'):
                        layer_sym.setStrokeColor(color)
                    elif hasattr(layer_sym, 'setLineColor'):
                        layer_sym.setLineColor(color)
                    elif hasattr(layer_sym, 'setColor'):
                        layer_sym.setColor(color)
                modified = True
                
        # 3. Stroke width (Border width)
        if stroke_width is not None:
            for i in range(sym.symbolLayerCount()):
                layer_sym = sym.symbolLayer(i)
                if hasattr(layer_sym, 'setStrokeWidth'):
                    layer_sym.setStrokeWidth(float(stroke_width))
                elif hasattr(layer_sym, 'setWidth'):
                    layer_sym.setWidth(float(stroke_width))
            modified = True
            
    # 4. Layer Opacity
    if opacity is not None:
        val = float(opacity)
        if val > 1.0:
            val = val / 100.0
        val = max(0.0, min(1.0, val))
        layer.setOpacity(val)
        modified = True

    if modified:
        layer.triggerRepaint()
        iface.layerTreeView().refreshLayerSymbology(layer.id())
        iface.mapCanvas().refresh()
        
        msg_parts = []
        if fill_color is not None: msg_parts.append(f"màu tô '{fill_color}'")
        if stroke_color is not None: msg_parts.append(f"màu viền '{stroke_color}'")
        if stroke_width is not None: msg_parts.append(f"độ dày viền {stroke_width}")
        if opacity is not None: msg_parts.append(f"độ trong suốt {opacity}")
        
        return f"Đã cập nhật style cho lớp '{layer.name()}': " + ", ".join(msg_parts) + "."
    else:
        return "Không có thay đổi style nào được thực hiện."

def reorder_layer(iface, layer_name: str, target_layer_name: str, position: str = 'below') -> str:
    """Reorders map layers by moving one layer above or below another layer in the QGIS Layer Tree."""
    layer = get_layer_by_name(layer_name)
    target_layer = get_layer_by_name(target_layer_name)
    
    if not layer:
        raise ValueError(f"Không tìm thấy lớp bản đồ cần di chuyển có tên '{layer_name}'.")
    if not target_layer:
        raise ValueError(f"Không tìm thấy lớp bản đồ đích có tên '{target_layer_name}'.")
        
    root = QgsProject.instance().layerTreeRoot()
    node_layer = root.findLayer(layer.id())
    node_target = root.findLayer(target_layer.id())
    
    if not node_layer:
        raise ValueError(f"Không tìm thấy nút của lớp '{layer.name()}' trong cây lớp bản đồ.")
    if not node_target:
        raise ValueError(f"Không tìm thấy nút của lớp '{target_layer.name()}' trong cây lớp bản đồ.")
        
    parent_layer = node_layer.parent()
    parent_target = node_target.parent()
    
    # Clone the node to move
    node_clone = node_layer.clone()
    
    # Get index of target node
    try:
        idx_target = parent_target.children().index(node_target)
    except ValueError:
        raise ValueError(f"Không xác định được vị trí của lớp '{target_layer.name()}'.")
        
    # Calculate insert index
    if position.lower() == 'above':
        insert_idx = idx_target
    else: # below
        insert_idx = idx_target + 1
        
    # Insert cloned node
    parent_target.insertChildNode(insert_idx, node_clone)
    
    # Remove original node
    parent_layer.removeChildNode(node_layer)
    
    # Refresh map canvas to reflect layer order changes
    iface.mapCanvas().refresh()
    
    pos_str = "dưới" if position.lower() == 'below' else "trên"
    return f"Đã di chuyển lớp '{layer.name()}' xuống {pos_str} lớp '{target_layer.name()}' thành công."

def zoom_to_features(iface, layer_name: str, query: str = None, selected_only: bool = False) -> str:
    """Zooms the map canvas to the bounding box of features matching a query or current selection."""
    layer = get_layer_by_name(layer_name)
    if not layer:
        raise ValueError(f"Không tìm thấy lớp bản đồ có tên '{layer_name}'.")
        
    if layer.type() != QgsMapLayerType.VectorLayer:
        raise ValueError(f"Lớp '{layer.name()}' không phải là lớp Vector và không thể thực hiện phóng tới đối tượng.")
        
    features = []
    
    if selected_only:
        features = layer.selectedFeatures()
        if not features:
            raise ValueError(f"Không có đối tượng nào đang được chọn trên lớp '{layer.name()}' để phóng tới.")
    elif query:
        request = QgsFeatureRequest().setFilterExpression(query)
        features = list(layer.getFeatures(request))
        if not features:
            raise ValueError(f"Không tìm thấy đối tượng nào thỏa mãn điều kiện '{query}' trên lớp '{layer.name()}' để phóng tới.")
    else:
        # Fallback to zooming to the whole layer extent
        extent = layer.extent()
        if extent.isEmpty():
            raise ValueError(f"Lớp bản đồ '{layer.name()}' rỗng, không thể phóng to.")
        iface.mapCanvas().setExtent(extent)
        iface.mapCanvas().refresh()
        return f"Đã phóng tới toàn bộ lớp bản đồ '{layer.name()}'."
        
    # Calculate bounding box of features
    extent = None
    
    for f in features:
        if f.hasGeometry():
            bbox = f.geometry().boundingBox()
            if extent is None:
                extent = QgsRectangle(bbox)
            else:
                extent.combineExtentWith(bbox)
            
    if extent is None or extent.isEmpty() or extent.isNull():
        raise ValueError("Vùng hiển thị (extent) của các đối tượng chọn/lọc bị rỗng hoặc không hợp lệ.")
        
    # Zoom canvas to extent
    iface.mapCanvas().setExtent(extent)
    
    # Adjust zoom scale if it's a single point (width/height is 0) to avoid extreme zoom in
    if extent.width() == 0 or extent.height() == 0:
        iface.mapCanvas().zoomScale(5000)
    else:
        # Scale out slightly (10%) to provide context margins
        iface.mapCanvas().zoomByFactor(1.1)
        
    iface.mapCanvas().refresh()
    
    source_str = "các đối tượng đang được chọn" if selected_only else f"các đối tượng thỏa mãn điều kiện '{query}'"
    return f"Đã phóng tới {source_str} trên lớp '{layer.name()}' thành công."

def query_gis_data(iface, sql_query: str) -> list:
    """Executes a virtual SQL query (SQLite/SpatiaLite) on loaded map layers and returns results as a list of dicts."""
    from qgis.core import QgsVectorLayer
    
    # QGIS Virtual Layers automatically register all loaded layers as SQL tables.
    # We create a temporary virtual layer to execute the query.
    uri = f"?query={sql_query}"
    vlayer = QgsVectorLayer(uri, "temp_query_layer", "virtual")
    
    if not vlayer.isValid():
        provider = vlayer.dataProvider()
        err_details = ""
        if provider:
            errors = provider.errors()
            if errors:
                err_details = "\nChi tiết lỗi từ QGIS: " + "; ".join(errors)
            elif hasattr(provider, 'error') and provider.error().message():
                err_details = "\nChi tiết lỗi từ QGIS: " + provider.error().message()
        err = f"Câu lệnh SQL không hợp lệ hoặc tên lớp bản đồ (bảng) không đúng. Đảm bảo tên bảng khớp chính xác với tên lớp bản đồ đang mở.{err_details}"
        raise ValueError(err)

    fields = [field.name() for field in vlayer.fields()]
    features = vlayer.getFeatures()
    
    result = []
    for f in features:
        attrs = {}
        for field in fields:
            attrs[field] = str(f[field])
        result.append(attrs)
        
    # Check if there were runtime errors during execution
    provider = vlayer.dataProvider()
    if provider:
        errors = provider.errors()
        if errors:
            err_details = "; ".join(errors)
            raise ValueError(f"Lỗi SQLite trong quá trình thực thi: {err_details}")
        
    return result


def set_layer_style_rule(iface, layer_name: str, rule_name: str, expression: str, fill_color: str = None, stroke_color: str = None, stroke_width: float = None, opacity: float = None) -> str:
    """Sets a rule-based style for a vector layer by creating/updating a specific rule."""
    from PyQt5.QtGui import QColor
    from PyQt5.QtCore import Qt
    from qgis.core import QgsRuleBasedRenderer, QgsSymbol, QgsMapLayerType
    
    layer = get_layer_by_name(layer_name)
    if not layer:
        raise ValueError(f"Không tìm thấy lớp bản đồ có tên '{layer_name}'.")
        
    if layer.type() != QgsMapLayerType.VectorLayer:
        raise ValueError(f"Lớp '{layer.name()}' không phải là lớp Vector và không thể thiết lập quy tắc style.")

    renderer = layer.renderer()
    if not renderer:
        raise ValueError(f"Không lấy được renderer của lớp '{layer.name()}'.")
        
    # Check if renderer is RuleBased, if not, convert it
    if not isinstance(renderer, QgsRuleBasedRenderer):
        # Create a new root rule
        root_rule = QgsRuleBasedRenderer.Rule(None)
        
        # Add default/original style as fallback rule
        default_symbol = renderer.symbol().clone() if renderer.symbol() else QgsSymbol.defaultSymbol(layer.geometryType())
        default_rule = QgsRuleBasedRenderer.Rule(default_symbol)
        default_rule.setLabel("Mặc định")
        root_rule.appendChild(default_rule)
        
        new_renderer = QgsRuleBasedRenderer(root_rule)
        layer.setRenderer(new_renderer)
        renderer = new_renderer
        
    root_rule = renderer.rootRule()
    
    # Search for existing rule with matching label/name
    target_rule = None
    for rule in root_rule.children():
        if rule.label() == rule_name:
            target_rule = rule
            break
            
    if target_rule:
        symbol = target_rule.symbol()
    else:
        # Clone default symbol from default rule, or create generic default
        default_rule = root_rule.children()[0] if root_rule.children() else None
        if default_rule and default_rule.symbol():
            symbol = default_rule.symbol().clone()
        else:
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            
    # Apply style modifications
    modified = False
    
    # Style modifying logic for symbol layers:
    if symbol:
        symbols = [symbol]
        for sym in symbols:
            # 1. Fill color
            if fill_color is not None:
                if fill_color.lower() in ('transparent', 'none'):
                    for i in range(sym.symbolLayerCount()):
                        layer_sym = sym.symbolLayer(i)
                        if hasattr(layer_sym, 'setFillColor'):
                            layer_sym.setFillColor(QColor(0, 0, 0, 0))
                        if hasattr(layer_sym, 'setBrushStyle'):
                            layer_sym.setBrushStyle(Qt.NoBrush)
                else:
                    color = QColor(fill_color)
                    if color.isValid():
                        sym.setColor(color)
                        for i in range(sym.symbolLayerCount()):
                            layer_sym = sym.symbolLayer(i)
                            if hasattr(layer_sym, 'setFillColor'):
                                layer_sym.setFillColor(color)
                            if hasattr(layer_sym, 'setBrushStyle'):
                                layer_sym.setBrushStyle(Qt.SolidPattern)
                modified = True
                
            # 2. Stroke color (Border color)
            if stroke_color is not None:
                color = QColor(stroke_color)
                if color.isValid():
                    for i in range(sym.symbolLayerCount()):
                        layer_sym = sym.symbolLayer(i)
                        if hasattr(layer_sym, 'setStrokeColor'):
                            layer_sym.setStrokeColor(color)
                        elif hasattr(layer_sym, 'setLineColor'):
                            layer_sym.setLineColor(color)
                        elif hasattr(layer_sym, 'setColor'):
                            layer_sym.setColor(color)
                    modified = True
                    
            # 3. Stroke width (Border width)
            if stroke_width is not None:
                for i in range(sym.symbolLayerCount()):
                    layer_sym = sym.symbolLayer(i)
                    if hasattr(layer_sym, 'setStrokeWidth'):
                        layer_sym.setStrokeWidth(float(stroke_width))
                    elif hasattr(layer_sym, 'setWidth'):
                        layer_sym.setWidth(float(stroke_width))
                modified = True
                
    # 4. Opacity
    if opacity is not None:
        val = float(opacity)
        if val > 1.0:
            val = val / 100.0
        val = max(0.0, min(1.0, val))
        layer.setOpacity(val)
        modified = True
        
    if not target_rule:
        # Create new rule and append
        new_rule = QgsRuleBasedRenderer.Rule(symbol, filterExp=expression, label=rule_name)
        root_rule.appendChild(new_rule)
    else:
        # Update existing rule
        target_rule.setFilterExpression(expression)
        target_rule.setSymbol(symbol)
        
    layer.triggerRepaint()
    iface.layerTreeView().refreshLayerSymbology(layer.id())
    iface.mapCanvas().refresh()
    
    msg_parts = []
    if fill_color is not None: msg_parts.append(f"màu tô '{fill_color}'")
    if stroke_color is not None: msg_parts.append(f"màu viền '{stroke_color}'")
    if stroke_width is not None: msg_parts.append(f"độ dày viền {stroke_width}")
    if opacity is not None: msg_parts.append(f"độ trong suốt {opacity}")
    
    return f"Đã thiết lập quy tắc hiển thị '{rule_name}' với điều kiện '{expression}' cho lớp '{layer.name()}': " + ", ".join(msg_parts) + "."

def execute_python_script(iface, script: str) -> dict:
    """
    Executes a Python script dynamically in the QGIS Desktop environment.
    Provides context objects like `iface`, `QgsProject`, and core classes.
    """
    import sys
    import io
    import traceback
    
    # Redirect stdout to capture print statements
    old_stdout = sys.stdout
    redirected_output = io.StringIO()
    sys.stdout = redirected_output
    
    # Setup execution context variables
    from qgis.core import (
        QgsProject, QgsVectorLayer, QgsRasterLayer, QgsFeature, 
        QgsGeometry, QgsPointXY, QgsRectangle, QgsCoordinateReferenceSystem
    )
    import processing
    
    locs = {
        "iface": iface,
        "QgsProject": QgsProject,
        "QgsVectorLayer": QgsVectorLayer,
        "QgsRasterLayer": QgsRasterLayer,
        "QgsFeature": QgsFeature,
        "QgsGeometry": QgsGeometry,
        "QgsPointXY": QgsPointXY,
        "QgsRectangle": QgsRectangle,
        "QgsCoordinateReferenceSystem": QgsCoordinateReferenceSystem,
        "processing": processing,
        "result": None
    }
    
    try:
        # Execute the script in safe scopes
        exec(script, globals(), locs)
        sys.stdout = old_stdout
        
        captured_print = redirected_output.getvalue()
        return {
            "status": "success",
            "stdout": captured_print,
            "result": str(locs.get("result")) if locs.get("result") is not None else None
        }
    except Exception as e:
        sys.stdout = old_stdout
        err_msg = f"{str(e)}\n{traceback.format_exc()}"
        return {
            "status": "error",
            "error": err_msg,
            "stdout": redirected_output.getvalue()
        }


def capture_map_canvas(iface) -> dict:
    """Captures the current map canvas, compresses as JPEG, encodes in Base64, and returns it."""
    import base64
    import tempfile
    import os
    
    try:
        canvas = iface.mapCanvas()
        if not canvas:
            raise ValueError("Không thể truy cập QGIS map canvas.")
            
        # Create temp file path
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, "qgis_canvas_capture.jpg")
        
        # Grab map canvas pixmap
        pixmap = canvas.grab()
        
        # Save as JPG with compression to reduce payload size (quality 85)
        success = pixmap.save(temp_file, "JPG", 85)
        if not success:
            raise IOError("Không thể lưu ảnh chụp canvas ra file tạm.")
            
        # Read and base64-encode
        with open(temp_file, "rb") as f:
            encoded_data = base64.b64encode(f.read()).decode('utf-8')
            
        # Clean up temp file
        try:
            os.remove(temp_file)
        except Exception:
            pass
            
        return {
            "mime_type": "image/jpeg",
            "base64_data": encoded_data
        }
    except Exception as e:
        err_msg = f"{str(e)}\n{traceback.format_exc()}"
        log_msg(f"Error capturing map canvas: {err_msg}", Qgis.Warning)
        raise e


def list_dir(directory_path: str) -> list:
    """Lists the files and subdirectories of directory_path on the local machine (QGIS environment)."""
    import os
    
    path = os.path.expanduser(directory_path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Thư mục '{directory_path}' không tồn tại.")
    if not os.path.isdir(path):
        raise ValueError(f"Đường dẫn '{directory_path}' không phải là thư mục.")
        
    items = []
    for item in os.listdir(path):
        full_path = os.path.join(path, item)
        is_dir = os.path.isdir(full_path)
        size = os.path.getsize(full_path) if not is_dir else 0
        items.append({"name": item, "is_dir": is_dir, "size": size})
    return items


def read_file(file_path: str) -> str:
    """Reads the contents of file_path on the local machine (QGIS environment)."""
    import os
    
    path = os.path.expanduser(file_path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Tệp tin '{file_path}' không tồn tại.")
    if not os.path.isfile(path):
        raise ValueError(f"Đường dẫn '{file_path}' không phải là một tệp tin.")
        
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read(50000)  # Max 50k characters


def grep_search(directory_path: str, pattern: str) -> str:
    """Searches for pattern in text files within directory_path (QGIS environment)."""
    import os
    import re
    
    dir_path = os.path.expanduser(directory_path)
    if not os.path.exists(dir_path):
        raise FileNotFoundError(f"Thư mục '{directory_path}' không tồn tại.")
    if not os.path.isdir(dir_path):
        raise ValueError(f"Đường dẫn '{directory_path}' không phải là thư mục.")
        
    matches = []
    for root, dirs, files in os.walk(dir_path):
        # Limit search depth to 2 to prevent freezing QGIS
        depth = root[len(dir_path):].count(os.sep)
        if depth > 1:
            dirs.clear()
            continue
            
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in [".txt", ".md", ".csv", ".json", ".xml", ".html", ".py"]:
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        for i, line in enumerate(f):
                            if re.search(pattern, line, re.IGNORECASE):
                                matches.append(f"{file} (dòng {i+1}): {line.strip()}")
                                if len(matches) >= 30:
                                    break
                except Exception:
                    pass
            if len(matches) >= 30:
                break
        if len(matches) >= 30:
            break
            
    return "\n".join(matches) if matches else "Không tìm thấy kết quả trùng khớp."






