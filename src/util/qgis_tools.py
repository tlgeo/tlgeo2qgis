from qgis.core import (
    QgsProject, 
    QgsMapLayerType, 
    QgsWkbTypes, 
    QgsFeatureRequest, 
    QgsMessageLog, 
    Qgis
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

def get_layer_attributes(iface, layer_name: str, limit: int = 10) -> list:
    """Retrieves attribute table features up to a limit"""
    layer = get_layer_by_name(layer_name)
    if not layer:
        raise ValueError(f"Không tìm thấy lớp bản đồ có tên '{layer_name}'.")
        
    if layer.type() != QgsMapLayerType.VectorLayer:
        raise ValueError(f"Lớp '{layer.name()}' không phải lớp Vector để lấy thuộc tính.")

    fields = [field.name() for field in layer.fields()]
    request = QgsFeatureRequest().setLimit(limit)
    features = layer.getFeatures(request)
    
    result = []
    for f in features:
        attrs = {}
        for field in fields:
            attrs[field] = str(f[field])
        result.append(attrs)
        
    return result
