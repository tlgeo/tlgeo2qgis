import pytest
from qgis.core import QgsProject

def test_plugin_loading(qgis_app, qgis_iface):
    """Test that the plugin can be successfully imported and initialized in a QGIS environment."""
    import tlgeo2qgis
    
    # Initialize the plugin with the mock QGIS interface
    plugin = tlgeo2qgis.classFactory(qgis_iface)
    assert plugin is not None
    
    # Verify basic plugin metadata and capabilities check logic works
    capabilities = plugin.check_export_capabilities()
    assert isinstance(capabilities, dict)
    assert "mbtiles_processing" in capabilities
    assert "mbtiles_gdal" in capabilities
    assert "pmtiles" in capabilities
