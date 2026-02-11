"""SLD Converter - Export layers to SLD format."""

import os
from qgis.core import QgsVectorLayer
from .base_converter import BaseConverter


class SLDConverter(BaseConverter):
    """Export layer styles to OGC SLD format."""
    
    def __init__(self):
        super().__init__("SLDConverter")
    
    def _check_availability(self) -> bool:
        """SLD export is always available."""
        return True
    
    def convert(self, layer:QgsVectorLayer, output_path: str, **kwargs) -> bool:
        """Export layer style to SLD.
        
        Args:
            layer: Vector layer with style
            output_path: Destination file path
        
        Returns:
            True on success
        """
        try:
            layer.saveSldStyle(output_path, "")
            self.log_success(output_path)
            return True
        except Exception as e:
            self.log_error(str(e))
            return False
