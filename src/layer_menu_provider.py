from qgis.gui import QgsLayerTreeView
from qgis.PyQt.QtWidgets import QAction, QMenu, QMessageBox
from qgis.core import QgsProject, QgsVectorLayer, QgsVectorFileWriter, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsMessageLog, Qgis
from qgis.PyQt.QtGui import QIcon
try:
    import processing
except:
    pass
import os
import uuid
import json
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Global reference to provider
_provider = None

class TLGeoProvider:
    def __init__(self, iface):
        self.iface = iface
        self.strapi_url = os.getenv("GEOADMIN_STRAPI_URL", "http://localhost:1337")
        
    def init_menu(self):
        """Initialize layer tree context menu"""
        layer_tree_view = self.iface.layerTreeView()
        if layer_tree_view:
            layer_tree_view.contextMenuAboutToShow.connect(self.add_context_menu)
    
    def add_context_menu(self, menu):
        """Add TLGeo export menu to layer context menu"""
        layer = self.iface.activeLayer()
        if not layer or not isinstance(layer, QgsVectorLayer):
            return
        
        # Get icon path
        plugin_dir = os.path.dirname(__file__)
        icon_path = os.path.join(plugin_dir, 'logo.png')
        icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()
        
        # Create single action
        action = QAction(icon, "TLGeo > Tải lên", menu)
        action.triggered.connect(lambda: self.export_layer(layer))
        menu.addAction(action)
    
    def collect_layer_metadata(self, layer):
        """Collect comprehensive metadata about the layer"""
        metadata = {
            "name": layer.name(),
            "type": "vector",
            "crs": layer.crs().authid(),
            "crs_description": layer.crs().description(),
            "extent": {
                "xmin": layer.extent().xMinimum(),
                "ymin": layer.extent().yMinimum(),
                "xmax": layer.extent().xMaximum(),
                "ymax": layer.extent().yMaximum()
            },
            "feature_count": layer.featureCount(),
            "geometry_type": layer.geometryType(),
            "geometry_type_name": ["Point", "Line", "Polygon"][layer.geometryType()] if layer.geometryType() < 3 else "Unknown",
            "fields": []
        }
        
        # Collect field information
        for field in layer.fields():
            metadata["fields"].append({
                "name": field.name(),
                "type": field.typeName(),
                "length": field.length(),
                "precision": field.precision()
            })
        
        # Add custom metadata if available
        if hasattr(layer, 'metadata'):
            layer_metadata = layer.metadata()
            metadata["title"] = layer_metadata.title()
            metadata["abstract"] = layer_metadata.abstract()
            metadata["keywords"] = layer_metadata.keywords()
            metadata["rights"] = layer_metadata.rights()
        
        return metadata
    
    def export_layer(self, layer):
        """Export layer to multiple formats in UUID-based directory"""
        if not isinstance(layer, QgsVectorLayer):
            QMessageBox.warning(None, "TLGeo", "Chỉ hỗ trợ vector layer!")
            return
        
        try:
            # Create UUID-based export directory
            export_uuid = str(uuid.uuid4())
            home_dir = os.path.expanduser("~")
            export_base = os.path.join(home_dir, "TLGeo_Exports")
            export_dir = os.path.join(export_base, export_uuid)
            os.makedirs(export_dir, exist_ok=True)
            
            layer_name = layer.name()
            safe_name = "".join(c for c in layer_name if c.isalnum() or c in (' ', '_', '-')).strip()
            
            # Show progress message
            self.iface.messageBar().pushMessage(
                "TLGeo", 
                f"Đang xuất layer '{layer_name}'...", 
                level=Qgis.Info,
                duration=3
            )
            
            # 1. Export metadata.json
            metadata = self.collect_layer_metadata(layer)
            metadata["export_uuid"] = export_uuid
            metadata_path = os.path.join(export_dir, f"{safe_name}.metadata.json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            QgsMessageLog.logMessage(f"✓ Exported metadata: {metadata_path}", "TLGeo", Qgis.Info)
            
            # 2. Export SQLite (EPSG:4326)
            sqlite_4326_path = os.path.join(export_dir, f"{safe_name}_sqlite_4326.sqlite")
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = "SQLite"
            options.fileEncoding = "UTF-8"
            
            # Set destination CRS to EPSG:4326
            target_crs = QgsCoordinateReferenceSystem("EPSG:4326")
            options.destCrs = target_crs
            
            error = QgsVectorFileWriter.writeAsVectorFormatV3(
                layer,
                sqlite_4326_path,
                QgsProject.instance().transformContext(),
                options
            )
            
            if error[0] == QgsVectorFileWriter.NoError:
                QgsMessageLog.logMessage(f"✓ Exported SQLite (4326): {sqlite_4326_path}", "TLGeo", Qgis.Info)
            else:
                QgsMessageLog.logMessage(f"✗ SQLite (4326) export error: {error}", "TLGeo", Qgis.Warning)
            
            # 3. Export SQLite (Original CRS)
            sqlite_path = os.path.join(export_dir, f"{safe_name}_sqlite.sqlite")
            options_orig = QgsVectorFileWriter.SaveVectorOptions()
            options_orig.driverName = "SQLite"
            options_orig.fileEncoding = "UTF-8"
            
            error = QgsVectorFileWriter.writeAsVectorFormatV3(
                layer,
                sqlite_path,
                QgsProject.instance().transformContext(),
                options_orig
            )
            
            if error[0] == QgsVectorFileWriter.NoError:
                QgsMessageLog.logMessage(f"✓ Exported SQLite (original CRS): {sqlite_path}", "TLGeo", Qgis.Info)
            else:
                QgsMessageLog.logMessage(f"✗ SQLite (original) export error: {error}", "TLGeo", Qgis.Warning)
            
            # 4. Export MBTiles
            mbtiles_path = os.path.join(export_dir, f"{safe_name}_mbtiles.mbtiles")
            try:
                processing.run("native:writevectortiles_mbtiles", {
                    'INPUT': layer,
                    'MIN_ZOOM': 0,
                    'MAX_ZOOM': 14,
                    'OUTPUT': mbtiles_path
                })
                QgsMessageLog.logMessage(f"✓ Exported MBTiles: {mbtiles_path}", "TLGeo", Qgis.Info)
            except Exception as e:
                QgsMessageLog.logMessage(f"✗ MBTiles export error: {str(e)}", "TLGeo", Qgis.Warning)
            
            # 5. Export PMTiles
            pmtiles_path = os.path.join(export_dir, f"{safe_name}_pmtiles.pmtiles")
            try:
                options_pmtiles = QgsVectorFileWriter.SaveVectorOptions()
                options_pmtiles.driverName = "PMTiles"
                options_pmtiles.fileEncoding = "UTF-8"
                
                error = QgsVectorFileWriter.writeAsVectorFormatV3(
                    layer,
                    pmtiles_path,
                    QgsProject.instance().transformContext(),
                    options_pmtiles
                )
                
                if error[0] == QgsVectorFileWriter.NoError:
                    QgsMessageLog.logMessage(f"✓ Exported PMTiles: {pmtiles_path}", "TLGeo", Qgis.Info)
                else:
                    QgsMessageLog.logMessage(f"✗ PMTiles export error: {error}", "TLGeo", Qgis.Warning)
            except Exception as e:
                QgsMessageLog.logMessage(f"✗ PMTiles export error: {str(e)}", "TLGeo", Qgis.Warning)
            
            # 6. Export SLD style
            sld_path = os.path.join(export_dir, f"{safe_name}.sld")
            try:
                layer.saveSldStyle(sld_path)
                QgsMessageLog.logMessage(f"✓ Exported SLD: {sld_path}", "TLGeo", Qgis.Info)
            except Exception as e:
                QgsMessageLog.logMessage(f"✗ SLD export error: {str(e)}", "TLGeo", Qgis.Warning)
            
            # Success message
            self.iface.messageBar().pushMessage(
                "TLGeo", 
                f"✓ Đã xuất layer thành công vào: {export_dir}\nUUID: {export_uuid}", 
                level=Qgis.Success,
                duration=10
            )
            
            # Optional: Upload to Strapi (currently disabled)
            # self.upload_to_strapi(export_dir, export_uuid, layer_name)
            
        except Exception as e:
            QgsMessageLog.logMessage(f"Export error: {str(e)}", "TLGeo", Qgis.Critical)
            self.iface.messageBar().pushMessage(
                "TLGeo", 
                f"Lỗi khi xuất layer: {str(e)}", 
                level=Qgis.Critical,
                duration=10
            )
    
    def upload_to_strapi(self, export_dir, export_uuid, layer_name):
        """Upload exported files to GEOADMIN Strapi"""
        try:
            # Prepare multipart upload
            files = []
            for filename in os.listdir(export_dir):
                filepath = os.path.join(export_dir, filename)
                if os.path.isfile(filepath):
                    files.append(('files', (filename, open(filepath, 'rb'))))
            
            # Upload to Strapi
            upload_url = f"{self.strapi_url}/api/upload"
            data = {
                'uuid': export_uuid,
                'layer_name': layer_name
            }
            
            # Uncomment to enable upload
            # response = requests.post(upload_url, files=files, data=data)
            # if response.status_code == 200:
            #     QgsMessageLog.logMessage(f"✓ Uploaded to Strapi: {upload_url}", "TLGeo", Qgis.Success)
            # else:
            #     QgsMessageLog.logMessage(f"✗ Upload failed: {response.text}", "TLGeo", Qgis.Warning)
            
            QgsMessageLog.logMessage(f"Upload to Strapi is disabled. Files ready at: {export_dir}", "TLGeo", Qgis.Info)
            
        except Exception as e:
            QgsMessageLog.logMessage(f"Upload error: {str(e)}", "TLGeo", Qgis.Warning)
    
    def unload(self):
        """Clean up menu connections"""
        layer_tree_view = self.iface.layerTreeView()
        if layer_tree_view:
            try:
                layer_tree_view.contextMenuAboutToShow.disconnect(self.add_context_menu)
            except:
                pass

def init_provider(iface):
    """Initialize the layer menu provider"""
    global _provider
    _provider = TLGeoProvider(iface)
    _provider.init_menu()

def unload():
    """Unload the layer menu provider"""
    global _provider
    if _provider:
        _provider.unload()
        _provider = None
