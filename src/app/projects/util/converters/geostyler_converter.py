"""Geostyler Converter - Convert SLD/QML to Mapbox Style using geostyler-cli."""

import os
import subprocess
from .base_converter import BaseConverter


class GeostylerConverter(BaseConverter):
    """Convert SLD or QML to Mapbox Style using geostyler-cli."""
    
    # Common installation paths
    NODE_PATHS = [
        "/Users/taluan/.nvm/versions/node/v22.14.0/bin/node",
        "/usr/local/bin/node",
        "/usr/bin/node",
    ]
    
    GEOSTYLER_PATHS = [
        "/Users/taluan/.nvm/versions/node/v22.14.0/bin/geostyler-cli",
        "/Users/taluan/.npm-global/bin/geostyler-cli",
        "/usr/local/bin/geostyler-cli",
    ]
    
    def __init__(self):
        super().__init__("GeostylerConverter")
        self._node_exe = None
        self._geostyler_exe = None
    
    def _check_availability(self) -> bool:
        """Check if geostyler-cli is available."""
        # Find node executable
        for path in self.NODE_PATHS:
            if os.path.exists(path):
                self._node_exe = path
                break
        
        # Find geostyler-cli executable
        for path in self.GEOSTYLER_PATHS:
            if os.path.exists(path):
                self._geostyler_exe = path
                break
        
        return self._geostyler_exe is not None or self._node_exe is not None
    
    def convert(self, layer, output_path: str, **kwargs) -> bool:
        """Convert SLD or QML to Mapbox Style.
        
        Args:
            layer: Path to input SLD or QML file
            output_path: Path for output Mapbox JSON
        
        Returns:
            True on success
        """
        if not os.path.exists(layer):
            self.log_error(f"Input file not found: {layer}")
            return False
        
        # Detect format from extension
        ext = os.path.splitext(layer)[1].lower()
        if ext == '.qml':
            input_format = 'qml'
        else:
            input_format = 'sld'  # Default to SLD
        
        self.log_info(f"Converting {input_format.upper()} to Mapbox Style...")
        
        try:
            cmd = self._build_command(layer, output_path, input_format)
            if not cmd:
                self.log_error("Could not build geostyler command")
                return False
            
            # Run with environment
            env = os.environ.copy()
            if self._node_exe:
                env["PATH"] = f"{os.path.dirname(self._node_exe)}:{env.get('PATH', '')}"
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                env=env
            )
            
            if result.returncode == 0 and os.path.exists(output_path):
                self.log_success(output_path)
                return True
            else:
                error_msg = result.stderr or result.stdout or "unknown"
                self.log_error(error_msg[:200])
                return False
                
        except subprocess.TimeoutExpired:
            self.log_error("Conversion timeout")
            return False
        except Exception as e:
            self.log_error(str(e))
            return False
    
    def _build_command(self, layer: str, output_path: str, input_format: str = 'sld'):
        """Build the geostyler-cli command."""
        cmd = None
        
        if self._geostyler_exe:
            cmd = [
                self._geostyler_exe,
                "-s", input_format,
                "-t", "mapbox",
                "-o", output_path,
                layer
            ]
        elif self._node_exe:
            npx_path = os.path.join(os.path.dirname(self._node_exe), "npx")
            if os.path.exists(npx_path):
                cmd = [
                    npx_path, "-y", "geostyler-cli",
                    "-s", input_format,
                    "-t", "mapbox",
                    "-o", output_path,
                    layer
                ]
        
        return cmd
