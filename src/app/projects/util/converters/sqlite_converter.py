"""SQLite Converter - Export layers to SQLite format."""

import os
from qgis.core import (
   Qgis,QgsVectorLayer,QgsProject,
   QgsVectorFileWriter,QgsCoordinateReferenceSystem
)
from .base_converter import BaseConverter


class SQLiteConverter(BaseConverter):
    """Export vector layers to SQLite format."""
    
    def __init__(self):
        super().__init__("SQLiteConverter")
    
    def _check_availability(self) -> bool:
        """SQLite driver is always available."""
        return True
    
    def convert(self, layer:QgsVectorLayer, output_path: str, 
                dest_crs: str = None, **kwargs) -> bool:
        """Export layer to SQLite.
        
        Args:
            layer: Vector layer to export
            output_path: Destination file path
            dest_crs: Optional CRS for reprojection (e.g., "EPSG:4326")
        
        Returns:
            True on success
        """
        try:
            opts =QgsVectorFileWriter.SaveVectorOptions()
            opts.driverName = "SQLite"
            opts.fileEncoding = "UTF-8"
            
            if dest_crs:
                opts.destCrs =QgsCoordinateReferenceSystem(dest_crs)
            
            err =QgsVectorFileWriter.writeAsVectorFormatV3(
                layer, output_path,
QgsProject.instance().transformContext(), opts
            )
            
            if err[0] ==QgsVectorFileWriter.NoError:
                self.log_success(output_path)
                return True
            else:
                self.log_error(f"Export failed: {err}")
                return False
                
        except Exception as e:
            self.log_error(str(e))
            return False
