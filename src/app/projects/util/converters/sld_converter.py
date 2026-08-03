"""SLD Converter - Export layers to OGC SLD format."""

import os
from .base_converter import BaseConverter


class SLDConverter(BaseConverter):
    """Export layer styles to OGC SLD format.
    
    NOTE: This converter does NOT create fallback SLD.
    If saveSldStyle() returns a placeholder, we return False.
    User wants ONLY real layer style - no generic fallbacks.
    """

    def __init__(self):
        super().__init__("SLDConverter")

    def _check_availability(self) -> bool:
        """SLD export is always available."""
        return True

    def convert(self, layer: "QgsVectorLayer", output_path: str, **kwargs) -> bool:
        """Export layer style to SLD.
        
        Args:
            layer: Vector layer with style
            output_path: Destination file path
        
        Returns:
            True on success, False if real SLD cannot be exported
        """
        self.log_info("Trying saveSldStyle()...")

        try:
            result = layer.saveSldStyle(output_path)
            self.log_info(f"saveSldStyle returned: {result}")

            if os.path.exists(output_path):
                with open(output_path, 'r') as f:
                    content = f.read()

                # Check if it's valid SLD (not placeholder)
                if 'embeddedSymbol' not in content and ('<Rule>' in content or '<se:Rule>' in content) and len(content) > 200:
                    self.log_success(output_path)
                    return True
                else:
                    self.log_info("saveSldStyle returned placeholder - no real SLD available")
                    # Clean up placeholder file
                    try:
                        os.remove(output_path)
                    except Exception:
                        _ = None
                    return False

            self.log_info("saveSldStyle did not create file")
            return False

        except Exception as e:
            self.log_error(f"saveSldStyle exception: {str(e)[:100]}")
            return False
