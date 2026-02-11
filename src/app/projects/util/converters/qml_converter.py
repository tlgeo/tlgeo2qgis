"""QML Converter - Export layers to QML format."""

import os
from qgis.core import Qgis, QgsVectorFileWriter, QgsProject, QgsVectorLayer
from .base_converter import BaseConverter


class QMLConverter(BaseConverter):
    """Export layer styles to QGIS QML format."""
    
    def __init__(self):
        super().__init__("QMLConverter")
    
    def _check_availability(self) -> bool:
        """QML driver is always available."""
        return True
    
    def _get_minimal_qml(self, layer: QgsVectorLayer) -> str:
        """Generate minimal QML based on geometry type."""
        name = layer.name()
        
        # Default to polygon if we can't determine geometry type
        geom_type = -1  # Unknown
        try:
            geom_type = layer.geometryType()
        except:
            pass
        
        if geom_type == 0:
            symbol = '''    <symbol alpha="1" type="marker" name="symbol_0_0">
      <layer pass="0" class="SimpleMarker" locked="0">
        <prop k="angle" v="0"/>
        <prop k="color" v="0,128,0,255"/>
        <prop k="name" v="circle"/>
        <prop k="offset" v="0,0"/>
        <prop k="size" v="4"/>
        <prop k="vertical_anchor_point" v="0"/>
      </layer>
    </symbol>'''
        elif geom_type == 1:
            symbol = '''    <symbol alpha="1" type="line" name="symbol_0_0">
      <layer pass="0" class="SimpleLine" locked="0">
        <prop k="capstyle" v="square"/>
        <prop k="joinstyle" v="bevel"/>
        <prop k="line_color" v="0,0,255,255"/>
        <prop k="line_style" v="solid"/>
        <prop k="line_width" v="0.6"/>
        <prop k="use_custom_dash" v="0"/>
      </layer>
    </symbol>'''
        else:  # PolygonGeometry or Unknown
            symbol = '''    <symbol alpha="1" type="fill" name="symbol_0_0">
      <layer pass="0" class="SimpleFill" locked="0">
        <prop k="color" v="255,0,0,255"/>
        <prop k="outline_color" v="255,0,0,255"/>
        <prop k="outline_style" v="solid"/>
        <prop k="outline_width" v="0.26"/>
        <prop k="style" v="solid"/>
      </layer>
    </symbol>'''
        
        return f'''<!DOCTYPE qgisstyles>
<qgis_style version="2">
  <symbols name="{name}">
{symbol}
  </symbols>
</qgis_style>'''
    
    def convert(self, layer: QgsVectorLayer, output_path: str, **kwargs) -> bool:
        """Export layer style to QML.
        
        Args:
            layer: Vector layer with style
            output_path: Destination file path
        
        Returns:
            True on success
        """
        try:
            # Try writeAsVectorFormatV3 with QML driver
            self.log_info(f"Trying QML export for {layer.name()}...")
            opts = QgsVectorFileWriter.SaveVectorOptions()
            opts.driverName = "QML"
            opts.fileEncoding = "UTF-8"
            
            err = QgsVectorFileWriter.writeAsVectorFormatV3(
                layer, output_path,
                QgsProject.instance().transformContext(), opts
            )
            self.log_info(f"QML export returned: {err[0]}")
            
            if err[0] == QgsVectorFileWriter.NoError:
                self.log_success(output_path)
                return True
            
            # Check if file was created anyway
            if os.path.exists(output_path) and os.path.getsize(output_path) > 100:
                self.log_info(f"QML file created despite warning: {output_path}")
                return True
            
        except Exception as e:
            self.log_error(f"QML export exception: {str(e)[:100]}")
        
        # Fallback: Always try to create QML based on geometry type
        try:
            self.log_info(f"Creating fallback QML for geometry type {layer.geometryType()}")
            qml_content = self._get_minimal_qml(layer)
            with open(output_path, 'w') as f:
                f.write(qml_content)
            self.log_success(f"Created fallback QML: {output_path}")
            return True
        except Exception as e2:
            self.log_error(f"Failed to create fallback QML: {str(e2)[:100]}")
            return False
