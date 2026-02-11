"""SLD Converter - Export layers to OGC SLD format."""

import os
from qgis.core import Qgis, QgsVectorLayer
from .base_converter import BaseConverter


class SLDConverter(BaseConverter):
    """Export layer styles to OGC SLD format."""
    
    def __init__(self):
        super().__init__("SLDConverter")
    
    def _check_availability(self) -> bool:
        """SLD export is always available."""
        return True
    
    def _get_geometry_sld(self, layer: QgsVectorLayer) -> str:
        """Generate minimal SLD based on geometry type."""
        name = layer.name()
        
        # Default to polygon if we can't determine geometry type
        geom_type = -1  # Unknown
        try:
            geom_type = layer.geometryType()
        except:
            pass
        
        if geom_type == 0:  # PointGeometry
            return f'''<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" version="1.1.0">
  <NamedLayer>
    <Name>{name}</Name>
    <UserStyle>
      <Title>{name}</Title>
      <FeatureTypeStyle>
        <Rule>
          <PointSymbolizer>
            <Graphic>
              <Mark>
                <WellKnownName>circle</WellKnownName>
                <Fill>
                  <CssParameter name="fill">#00ff00</CssParameter>
                </Fill>
              </Mark>
              <Size>8</Size>
            </Graphic>
          </PointSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>'''
        elif geom_type == 1:  # LineGeometry
            return f'''<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" version="1.1.0">
  <NamedLayer>
    <Name>{name}</Name>
    <UserStyle>
      <Title>{name}</Title>
      <FeatureTypeStyle>
        <Rule>
          <LineSymbolizer>
            <Stroke>
              <CssParameter name="stroke">#0000ff</CssParameter>
              <CssParameter name="stroke-width">2</CssParameter>
            </Stroke>
          </LineSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>'''
        else:  # PolygonGeometry, Unknown, or error
            return f'''<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" version="1.1.0">
  <NamedLayer>
    <Name>{name}</Name>
    <UserStyle>
      <Title>{name}</Title>
      <FeatureTypeStyle>
        <Rule>
          <PolygonSymbolizer>
            <Fill>
              <CssParameter name="fill">#ff0000</CssParameter>
              <CssParameter name="fill-opacity">0.5</CssParameter>
            </Fill>
            <Stroke>
              <CssParameter name="stroke">#ff0000</CssParameter>
              <CssParameter name="stroke-width">1</CssParameter>
            </Stroke>
          </PolygonSymbolizer>
        </Rule>
      </FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>'''
    
    def convert(self, layer: QgsVectorLayer, output_path: str, **kwargs) -> bool:
        """Export layer style to SLD.
        
        Args:
            layer: Vector layer with style
            output_path: Destination file path
        
        Returns:
            True on success
        """
        fallback_reason = None
        
        try:
            # Try saveSldStyle first (for layers with native style)
            self.log_info(f"Trying saveSldStyle for {layer.name()}...")
            result = layer.saveSldStyle(output_path)
            self.log_info(f"saveSldStyle returned: {result}")
            
            # Check if file exists and has actual style content
            if os.path.exists(output_path):
                with open(output_path, 'r') as f:
                    content = f.read()
                
                # Check for QGIS placeholder comment (no actual renderer export)
                if 'embeddedSymbol not implemented' in content:
                    fallback_reason = "QGIS saveSldStyle returned placeholder (no renderer export)"
                elif content.count('<se:Rule>') < 1 and content.count('<Rule>') < 1:
                    fallback_reason = "SLD has no style rules"
                elif len(content.strip()) < 200:
                    fallback_reason = f"SLD too short ({len(content)} bytes)"
                else:
                    # Valid SLD with style content
                    self.log_success(output_path)
                    return True
            
            if fallback_reason:
                self.log_info(f"saveSldStyle invalid: {fallback_reason}")
            else:
                self.log_info("saveSldStyle didn't create file")
            
        except Exception as e:
            self.log_error(f"saveSldStyle exception: {str(e)[:100]}")
        
        # Fallback: Create SLD based on geometry type
        try:
            self.log_info(f"Creating fallback SLD for geometry type {layer.geometryType()}")
            sld_content = self._get_geometry_sld(layer)
            with open(output_path, 'w') as f:
                f.write(sld_content)
            self.log_success(f"Created fallback SLD: {output_path}")
            return True
        except Exception as e2:
            self.log_error(f"Failed to create fallback SLD: {str(e2)[:100]}")
            return False
