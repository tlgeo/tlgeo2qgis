"""Tippecanoe Converter - Convert GeoJSON to MBTiles using tippecanoe."""

import os
import shutil
import subprocess
from typing import Optional
from qgis.core import (
   Qgis, QgsVectorFileWriter, QgsProject, QgsVectorLayer
)
from .base_converter import BaseConverter


class TippecanoeConverter(BaseConverter):
    """Convert GeoJSON to MBTiles using tippecanoe."""
    
    def __init__(self):
        super().__init__("TippecanoeConverter")
    
    def _check_availability(self) -> bool:
        """Check if tippecanoe is installed."""
        return shutil.which("tippecanoe") is not None
    
    def convert(self, layer: QgsVectorLayer, output_path: str, 
                geojson_path: Optional[str] = None, **kwargs) -> bool:
        """Convert layer to MBTiles using tippecanoe.
        
        Args:
            layer: Vector layer to convert
            output_path: Destination MBTiles file path
            geojson_path: Optional path for intermediate GeoJSON
        
        Returns:
            True on success
        """
        try:
            # Export to GeoJSON first
            if geojson_path is None:
                geojson_path = output_path.replace('.mbtiles', '.geojson')
            
            geojson_opts = QgsVectorFileWriter.SaveVectorOptions()
            geojson_opts.driverName = "GeoJSON"
            geojson_opts.fileEncoding = "UTF-8"
            
            err = QgsVectorFileWriter.writeAsVectorFormatV3(
                layer, geojson_path,
QgsProject.instance().transformContext(), geojson_opts
            )
            
            if err[0] != QgsVectorFileWriter.NoError:
                self.log_error("GeoJSON export failed")
                return False
            
            # Build tippecanoe command
            cmd = self._build_command(geojson_path, output_path)
            if not cmd:
                self.log_error("Could not build tippecanoe command")
                return False
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.log_success(output_path)
                return True
            else:
                self.log_error(result.stderr[:100] if result.stderr else "unknown")
                return False
                
        except Exception as e:
            self.log_error(str(e))
            return False
    
    def _build_command(self, geojson_path: str, output_path: str):
        """Build tippecanoe command."""
        tippecanoe = shutil.which("tippecanoe")
        if not tippecanoe:
            return None
        
        layer_name = os.path.basename(output_path).replace('.mbtiles', '')
        
        return [
            tippecanoe,
            "-o", output_path,
            "-l", layer_name,
            geojson_path,
            "-zg",  # Auto-calculate max zoom
            "--drop-densest-as-needed",
            "--force"
        ]
