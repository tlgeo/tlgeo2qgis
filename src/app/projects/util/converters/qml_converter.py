"""QML Converter - Export layers to QML format."""

import os
from qgis.core import (
   Qgis, QgsVectorFileWriter, QgsProject, QgsVectorLayer
)
from .base_converter import BaseConverter


class QMLConverter(BaseConverter):
    """Export layer styles to QGIS QML format."""
    
    def __init__(self):
        super().__init__("QMLConverter")
    
    def _check_availability(self) -> bool:
        """QML driver is always available."""
        return True
    
    def convert(self, layer:QgsVectorLayer, output_path: str, **kwargs) -> bool:
        """Export layer style to QML.
        
        Args:
            layer: Vector layer with style
            output_path: Destination file path
        
        Returns:
            True on success
        """
        try:
            # Try writeAsVectorFormatV3 with QML driver
            opts = QgsVectorFileWriter.SaveVectorOptions()
            opts.driverName = "QML"
            opts.fileEncoding = "UTF-8"
            
            err = QgsVectorFileWriter.writeAsVectorFormatV3(
                layer, output_path,
QgsProject.instance().transformContext(), opts
            )
            
            if err[0] == QgsVectorFileWriter.NoError:
                self.log_success(output_path)
                return True
            else:
                self.log_error(f"Export failed: {err}")
                return False
                
        except Exception as e:
            self.log_error(str(e))
            return False
