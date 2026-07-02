import pytest
from qgis.PyQt.QtCore import QVariant
from qgis.core import (
    QgsVectorLayer, 
    QgsProject, 
    QgsFeature, 
    QgsGeometry, 
    QgsPointXY, 
    QgsField
)
from tlgeo2qgis.util import qgis_tools

@pytest.fixture(autouse=True)
def clean_project():
    """Ensure each test runs with a clean QGIS project layer stack."""
    QgsProject.instance().removeAllMapLayers()
    yield
    QgsProject.instance().removeAllMapLayers()

def test_get_layer_by_name():
    """Verify that get_layer_by_name fuzzy searches and returns the correct layer."""
    layer = QgsVectorLayer("Point?crs=EPSG:4326", "Hà Nội Point", "memory")
    QgsProject.instance().addMapLayer(layer)
    
    # 1. Exact match
    found = qgis_tools.get_layer_by_name("Hà Nội Point")
    assert found is not None
    assert found.id() == layer.id()
    
    # 2. Case-insensitive and fuzzy match
    found_fuzzy = qgis_tools.get_layer_by_name("hà nội")
    assert found_fuzzy is not None
    assert found_fuzzy.id() == layer.id()
    
    # 3. Not found
    assert qgis_tools.get_layer_by_name("Non-existent Layer") is None

def test_list_layers(qgis_iface):
    """Verify that list_layers retrieves the details of all registered layers."""
    layer1 = QgsVectorLayer("Point?crs=EPSG:4326", "Point Layer", "memory")
    layer2 = QgsVectorLayer("LineString?crs=EPSG:4326", "Line Layer", "memory")
    QgsProject.instance().addMapLayers([layer1, layer2])
    
    layers = qgis_tools.list_layers(qgis_iface)
    assert len(layers) == 2
    
    layer_names = [l["name"] for l in layers]
    assert "Point Layer" in layer_names
    assert "Line Layer" in layer_names
    
    point_layer_info = next(l for l in layers if l["name"] == "Point Layer")
    assert point_layer_info["type"] == "vector"
    assert point_layer_info["geom_type"] == "Point"

def test_zoom_to_layer(qgis_iface):
    """Verify that zoom_to_layer executes successfully for non-empty layers."""
    layer = QgsVectorLayer("Point?crs=EPSG:4326", "Zoom Layer", "memory")
    QgsProject.instance().addMapLayer(layer)
    
    # Add two points to make a positive-area bounding box
    layer.startEditing()
    feat1 = QgsFeature()
    feat1.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(105.8, 21.0)))
    layer.addFeature(feat1)
    feat2 = QgsFeature()
    feat2.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(105.9, 21.1)))
    layer.addFeature(feat2)
    layer.commitChanges()
    layer.updateExtents()
    
    result_msg = qgis_tools.zoom_to_layer(qgis_iface, "Zoom Layer")
    assert "Đã phóng to tới lớp bản đồ" in result_msg

def test_select_features(qgis_iface):
    """Verify that select_features selects vector features matching a query expression."""
    layer = QgsVectorLayer("Point?crs=EPSG:4326", "Select Layer", "memory")
    layer.dataProvider().addAttributes([QgsField("val", QVariant.Int)])
    layer.updateFields()
    QgsProject.instance().addMapLayer(layer)
    
    layer.startEditing()
    feat1 = QgsFeature(layer.fields())
    feat1.setAttribute("val", 100)
    feat1.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(105.8, 21.0)))
    layer.addFeature(feat1)
    
    feat2 = QgsFeature(layer.fields())
    feat2.setAttribute("val", 200)
    feat2.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(105.9, 21.1)))
    layer.addFeature(feat2)
    layer.commitChanges()
    
    result_msg = qgis_tools.select_features(qgis_iface, "Select Layer", "val = 200")
    assert "Đã chọn thành công 1 đối tượng" in result_msg
    assert layer.selectedFeatureCount() == 1
    
    # Verify selected feature
    selected_feat = list(layer.selectedFeatures())[0]
    assert selected_feat.attribute("val") == 200

def test_set_layer_visibility(qgis_iface):
    """Verify that set_layer_visibility toggles the layer node visibility in the tree."""
    layer = QgsVectorLayer("Point?crs=EPSG:4326", "Visibility Layer", "memory")
    QgsProject.instance().addMapLayer(layer)
    
    # Hide the layer
    qgis_tools.set_layer_visibility(qgis_iface, "Visibility Layer", False)
    node = QgsProject.instance().layerTreeRoot().findLayer(layer.id())
    assert node is not None
    assert not node.itemVisibilityChecked()
    
    # Show the layer
    qgis_tools.set_layer_visibility(qgis_iface, "Visibility Layer", True)
    assert node.itemVisibilityChecked()

def test_get_layer_attributes(qgis_iface):
    """Verify that get_layer_attributes correctly returns features attribute table."""
    layer = QgsVectorLayer("Point?crs=EPSG:4326", "Attribute Layer", "memory")
    layer.dataProvider().addAttributes([QgsField("name", QVariant.String), QgsField("score", QVariant.Int)])
    layer.updateFields()
    QgsProject.instance().addMapLayer(layer)
    
    layer.startEditing()
    feat = QgsFeature(layer.fields())
    feat.setAttribute("name", "Hanoi")
    feat.setAttribute("score", 95)
    feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(105.8, 21.0)))
    layer.addFeature(feat)
    layer.commitChanges()
    
    attributes = qgis_tools.get_layer_attributes(qgis_iface, "Attribute Layer", limit=5)
    assert len(attributes) == 1
    assert attributes[0]["name"] == "Hanoi"
    assert attributes[0]["score"] == "95"
