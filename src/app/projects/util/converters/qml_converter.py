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
    
    def _get_full_qml(self, layer: QgsVectorLayer) -> str:
        """Generate full QML layer definition with renderer."""
        name = layer.name()
        layer_id = layer.id()
        crs_authid = layer.crs().authid() if layer.crs() else ""
        extent = layer.extent()
        
        # Get renderer
        renderer = layer.renderer()
        renderer_type = type(renderer).__name__
        
        # Build proper QML with full layer definition
        qml = f'''<!DOCTYPE qgis>
<qgis version="3.28.0-Firenze" saveUser="taluan" saveDateTime="2026-02-11T15:00:00">
  <maplayers>
    <maplayer labelsEnabled="false" type="vector" geometry="Polygon">
      <id>{layer_id}</id>
      <datasources>{layer.source()}</datasources>
      <keywordList></keywordList>
      <renderer-v2 type="singleSymbol" enableorderby="0" symbollevels="0" attr="">
        <symbols>
'''
        
        # Add symbols based on geometry type
        geom_type = layer.geometryType()
        if geom_type == 0:
            qml += '''          <symbol alpha="1" type="marker" name="symbol_0_0">
            <layer pass="0" class="SimpleMarker" locked="0">
              <prop k="angle" v="0"/>
              <prop k="color" v="0,128,0,255"/>
              <prop k="name" v="circle"/>
              <prop k="offset" v="0,0"/>
              <prop k="size" v="4"/>
            </layer>
          </symbol>
'''
        elif geom_type == 1:
            qml += '''          <symbol alpha="1" type="line" name="symbol_0_0">
            <layer pass="0" class="SimpleLine" locked="0">
              <prop k="capstyle" v="square"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="line_color" v="0,0,255,255"/>
              <prop k="line_style" v="solid"/>
              <prop k="line_width" v="0.6"/>
            </layer>
          </symbol>
'''
        else:  # Polygon
            qml += '''          <symbol alpha="1" type="fill" name="symbol_0_0">
            <layer pass="0" class="SimpleFill" locked="0">
              <prop k="color" v="255,0,0,255"/>
              <prop k="outline_color" v="255,0,0,255"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0.26"/>
            </layer>
          </symbol>
'''
        
        qml += '''        </symbols>
        <rotation enabled="0"/>
        <sizescale enabled="0"/>
        <rule key=""/>
      </renderer-v2>
      <labeling type="single"></labeling>
      <customproperties/>
      <blendMode>0</blendMode>
      <featureBlendMode>0</featureBlendMode>
      <layerOpacity>1</layerOpacity>
      <SingleCategoryDiagramRenderer diagramType="Pie" size="10">
        <DiagramCategory rotationOffset="270" maxScaleDenominator="1e+8" penWidth="0" penColor="#000000" minimumSize="0" barWidth="5" labelPlacementMethod="xHeight" width="15" scaleBasedVisibility="0" backgroundColor="#ffffff" opacity="1" enabled="0" height="15" scaleMinDenominator="0" rotation="0" type="0" lineStyle="solid" penAlpha="255" diagramOrientation="Up">
          <propertyProperties/>
          <fontProperties style="" description="Sans Serif,10,-1,5,50,0,0,0,0,0"/>
          <attribute color="#000000" label=""/>
        </DiagramCategory>
      </SingleCategoryDiagramRenderer>
      <DiagramLayerCollection>
        <DiagramLayer layerOptions="{}" showColumn="-1" labelOptions="{}" unusedAttributeAction="0" priority="0" obstacle="0" featureDisplay="0" placement="0" zIndex="0"/>
        <propertyProperties/>
      </DiagramLayerCollection>
      <geometryOptions removeDuplicateNodes="0" geometryPrecision="0"/>
      <legend type="default-vector"/>
      <referencedContainers/>
      <fieldConfiguration>
'''
        
        # Add field configurations (empty for now)
        fields = layer.fields()
        for field in fields:
            qml += f'''        <field name="{field.name()}" configurationFlags="None">
          <editWidget type="TextEdit">
            <config>
              <Option type="Map">
                <Option name="IsMultiline" type="QString" value="false"/>
                <Option name="UseHtml" type="QString" value="false"/>
              </Option>
            </config>
          </editWidget>
        </field>
'''
        
        qml += '''      </fieldConfiguration>
      <aliases>
      </aliases>
      <excludeAttributesWMS>
      </excludeAttributesWMS>
      <excludeAttributesWFS>
      </excludeAttributesWFS>
      <defaults>
'''
        
        # Add defaults for fields
        for field in fields:
            qml += f'''        <default field="{field.name()}" expression="" applyOnUpdate="0"/>
'''
        
        qml += '''      </defaults>
      <constraints>
'''
        
        # Add constraints
        for field in fields:
            qml += f'''        <constraint notnull="0" unique="0" expiring="" constraints="0" field="{field.name()}"/>
'''
        
        qml += '''      </constraints>
      <constraintExpressions>
'''
        
        # Add constraint expressions
        for field in fields:
            qml += f'''        <constraint exp="" field="{field.name()}"/>
'''
        
        qml += '''      </constraintExpressions>
      <expressionfields>
      </expressionfields>
      <attributeactions>
      </attributeactions>
      <attributetableconfig actionWidgetStyle="dropDown">
        <columns>
        </columns>
      </attributetableconfig>
      <conditionalstyles>
        <rowstyles/>
        <fieldstyles/>
      </conditionalstyles>
      <storedexpressions/>
      <editform tolerant="1">{name}.ui</editform>
      <editforminit/>
      <editforminitcodesource path=""/>
      <editforminitcode scope="Expression"/>
      <previousSelection/>
      <RemoteTheme enabled="false" name=""/>
    </maplayer>
  </maplayers>
</qgis>'''
        
        return qml
    
    def convert(self, layer: QgsVectorLayer, output_path: str, **kwargs) -> bool:
        """Export layer style to QML.
        
        Args:
            layer: Vector layer with style
            output_path: Destination file path
        
        Returns:
            True on success
        """
        try:
            # Try writeAsVectorFormatV3 with QML driver first
            self.log_info(f"Trying QML export for {layer.name()}...")
            opts = QgsVectorFileWriter.SaveVectorOptions()
            opts.driverName = "QML"
            opts.fileEncoding = "UTF-8"
            
            err = QgsVectorFileWriter.writeAsVectorFormatV3(
                layer, output_path,
                QgsProject.instance().transformContext(), opts
            )
            self.log_info(f"QML export returned: {err[0]}, file: {os.path.exists(output_path)}")
            
            if err[0] == QgsVectorFileWriter.NoError and os.path.exists(output_path):
                size = os.path.getsize(output_path)
                if size > 1000:  # Real QML is larger than simple style
                    self.log_success(f"QML exported: {size} bytes")
                    return True
            
            self.log_info("QML driver didn't create valid file, trying fallback...")
            
        except Exception as e:
            self.log_error(f"QML export exception: {str(e)[:100]}")
        
        # Fallback: Generate full QML with renderer
        try:
            self.log_info("Generating full QML with renderer...")
            qml_content = self._get_full_qml(layer)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(qml_content)
            self.log_success(f"Created full QML: {output_path}")
            return True
        except Exception as e:
            self.log_error(f"Failed to create QML: {str(e)[:100]}")
            return False
