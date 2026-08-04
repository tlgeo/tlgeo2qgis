from qgis.gui import QgsLayerTreeView
from qgis.PyQt.QtWidgets import QAction, QMenu, QMessageBox
from qgis.core import QgsProject, QgsVectorLayer, QgsVectorFileWriter, QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsMessageLog, Qgis, QgsApplication
from qgis.PyQt.QtGui import QIcon
try:
    import processing
except Exception:
    _ = None
import os
import uuid
import json
from dotenv import load_dotenv
import requests
from .app.auth.util.auth_service import AuthService
from .layer_export_task import LayerExportTask

# Load environment variables
plugin_root = os.path.dirname(os.path.abspath(__file__))
_env_path = os.path.join(plugin_root, ".env")
if os.path.exists(_env_path):
    load_dotenv(_env_path)
else:
    load_dotenv()

# Global reference to provider
_provider = None

class TLGeoProvider:
    def __init__(self, iface, plugin_instance=None):
        self.iface = iface
        self.plugin = plugin_instance
        self.strapi_url = os.getenv("GEOADMIN_STRAPI_URL", "http://localhost:11000")
        self.auth_service = AuthService()
        
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
        action.triggered.connect(lambda: self.start_export_task(layer))
        menu.addAction(action)
    

    def start_export_task(self, layer):
        """Start background export task - non-blocking UI."""
        if not isinstance(layer,QgsVectorLayer):
            QMessageBox.warning(None, "TLGeo", "Chỉ hỗ trợ vector layer!")
            return
        
        # Check authentication
        token = self.auth_service.get_token()
        if not token:
            QMessageBox.warning(None, "TLGeo", "Vui lòng đăng nhập trước!")
            return
        
        # Create background task
        task = LayerExportTask(layer, self.strapi_url, self.auth_service)
        
        # Connect signals for progress feedback
        task.progress_changed.connect(
            lambda msg: self.iface.messageBar().pushMessage("TLGeo", msg,Qgis.Info, 3)
        )
        task.export_complete.connect(
            lambda dir, uuid: self.iface.messageBar().pushSuccess("TLGeo", f"Export complete!")
        )
        task.export_failed.connect(
            lambda err: self.iface.messageBar().pushWarning("TLGeo", f"Export failed: {err}")
        )
        
        # Add to QGIS task manager
        QgsApplication.taskManager().addTask(task)
        
        # Initial feedback
        self.iface.messageBar().pushMessage(
            "TLGeo", 
            f"Export started in background...",
            Qgis.Info,
            5
        )

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
    
    def check_export_capabilities(self):
        """Check which export formats are available"""
        capabilities = {
            "mbtiles_processing": False,
            "mbtiles_gdal": False,
            "pmtiles": False
        }
        
        # Check processing algorithms  
        try:
            import processing
            # Try to get algorithm
            try:
                alg = processing.algorithmHelp('native:writevectortiles_mbtiles')
                capabilities["mbtiles_processing"] = True
            except Exception:
                _ = None
        except Exception:
            _ = None
        
        # Check GDAL drivers
        try:
            drivers = QgsVectorFileWriter.ogrDriverList()
            for driver in drivers:
                driver_name = driver.driverName if hasattr(driver, 'driverName') else driver.longName
                if "MBTiles" in driver_name:
                    capabilities["mbtiles_gdal"] = True
                if "PMTiles" in driver_name:
                    capabilities["pmtiles"] = True
        except Exception:
            _ = None
        
        return capabilities
    
    def export_layer(self, layer):
        """Export layer to multiple formats in UUID-based directory"""
        if not isinstance(layer, QgsVectorLayer):
            QMessageBox.warning(None, "TLGeo", "Chỉ hỗ trợ vector layer!")
            return
        
        try:
            # Check export capabilities
            capabilities = self.check_export_capabilities()
            QgsMessageLog.logMessage(f"Export capabilities: {capabilities}", "TLGeo", Qgis.Info)
            
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
            
            # Check capabilities for advanced formats (MBTiles/PMTiles)
            has_mbtiles = capabilities['mbtiles_processing'] or capabilities['mbtiles_gdal']
            has_pmtiles = capabilities['pmtiles']
            
            if (not has_mbtiles or not has_pmtiles) and self.plugin:
                QgsMessageLog.logMessage("GDAL version insufficient for MBTiles/PMTiles", "TLGeo", Qgis.Warning)
                
                # Show update prompt
                self.plugin.show_gdal_update_prompt()
                
                # Stop advanced export but report partial success
                self.iface.messageBar().pushMessage(
                    "TLGeo", 
                    f"✓ Đã xuất SQLite thành công.\n(Bỏ qua MBTiles/PMTiles do phiên bản GDAL cũ)", 
                    level=Qgis.Warning,
                    duration=8
                )
                
                # Upload what we have
                self.upload_to_strapi(export_dir, export_uuid, layer_name)
                return

            # 4. Export MBTiles (Vector Tiles format)
            mbtiles_path = os.path.join(export_dir, f"{safe_name}.mbtiles")
            try:
                # QGIS 3.14+ has native vector tiles export
                import processing
                processing.run("native:writevectortiles_mbtiles", {
                    'INPUT': layer,
                    'MIN_ZOOM': 0,
                    'MAX_ZOOM': 14,
                    'EXTENT': layer.extent(),
                    'OUTPUT': mbtiles_path
                })
                QgsMessageLog.logMessage(f"✓ Exported MBTiles: {mbtiles_path}", "TLGeo", Qgis.Info)
            except Exception as e:
                # Fallback: Try using GDAL MBTiles driver directly
                try:
                    options_mbtiles = QgsVectorFileWriter.SaveVectorOptions()
                    options_mbtiles.driverName = "MBTiles"
                    options_mbtiles.fileEncoding = "UTF-8"
                    
                    error = QgsVectorFileWriter.writeAsVectorFormatV3(
                        layer,
                        mbtiles_path,
                        QgsProject.instance().transformContext(),
                        options_mbtiles
                    )
                    
                    if error[0] == QgsVectorFileWriter.NoError:
                        QgsMessageLog.logMessage(f"✓ Exported MBTiles (via GDAL): {mbtiles_path}", "TLGeo", Qgis.Info)
                    else:
                        QgsMessageLog.logMessage(f"✗ MBTiles not available. Error: {error[1] if len(error) > 1 else str(error)}", "TLGeo", Qgis.Warning)
                except Exception as e2:
                    QgsMessageLog.logMessage(f"✗ MBTiles export not supported in this QGIS version. Processing: {str(e)}, GDAL: {str(e2)}", "TLGeo", Qgis.Warning)
            
            # 5. Export PMTiles (requires GDAL 3.8+ with PMTiles driver)
            pmtiles_path = os.path.join(export_dir, f"{safe_name}.pmtiles")
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
                    QgsMessageLog.logMessage(f"✗ PMTiles driver not available (requires GDAL 3.8+). Error: {error[1] if len(error) > 1 else str(error)}", "TLGeo", Qgis.Warning)
            except Exception as e:
                QgsMessageLog.logMessage(f"✗ PMTiles export not supported (requires GDAL 3.8+): {str(e)}", "TLGeo", Qgis.Warning)
            
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
            
            # Upload to Strapi with authentication
            self.upload_to_strapi(export_dir, export_uuid, layer_name)
            
        except Exception as e:
            QgsMessageLog.logMessage(f"Export error: {str(e)}", "TLGeo", Qgis.Critical)
            self.iface.messageBar().pushMessage(
                "TLGeo", 
                f"Lỗi khi xuất layer: {str(e)}", 
                level=Qgis.Critical,
                duration=10
            )
    
    def upload_to_strapi(self, export_dir, export_uuid, layer_name):
        """Upload exported files to GEOADMIN Strapi with JWT authentication"""
        try:
            # Get JWT token
            token = self.auth_service.get_token()
            if not token:
                QMessageBox.warning(
                    None,
                    "TLGeo",
                    "Bạn cần đăng nhập để tải file lên server.\n"
                    "Vui lòng khởi động lại plugin để đăng nhập."
                )
                QgsMessageLog.logMessage("Upload failed: No authentication token", "TLGeo", Qgis.Warning)
                return
            
            # Prepare multipart upload
            files = []
            file_handles = []  # Keep track of file handles to close later
            for filename in os.listdir(export_dir):
                filepath = os.path.join(export_dir, filename)
                if os.path.isfile(filepath):
                    fh = open(filepath, 'rb')
                    file_handles.append(fh)
                    files.append(('files', (filename, fh)))
            
            # Upload to Strapi with JWT token
            upload_url = f"{self.strapi_url}/api/upload"
            headers = {
                "Authorization": f"Bearer {token}"
            }
            data = {
                'uuid': export_uuid,
                'layer_name': layer_name
            }
            
            QgsMessageLog.logMessage(f"Uploading to {upload_url}...", "TLGeo", Qgis.Info)
            
            try:
                response = requests.post(upload_url, files=files, data=data, headers=headers, timeout=60)
                
                if response.status_code == 200:
                    QgsMessageLog.logMessage(f"✓ Uploaded to Strapi successfully", "TLGeo", Qgis.Success)
                    self.iface.messageBar().pushSuccess(
                        "TLGeo",
                        f"✓ Đã tải layer '{layer_name}' lên server thành công!"
                    )
                elif response.status_code == 401:
                    QgsMessageLog.logMessage(f"✗ Upload failed: Unauthorized (token expired)", "TLGeo", Qgis.Warning)
                    QMessageBox.warning(
                        None,
                        "TLGeo",
                        "Phiên đăng nhập đã hết hạn.\n"
                        "Vui lòng khởi động lại plugin để đăng nhập lại."
                    )
                else:
                    error_msg = response.text
                    QgsMessageLog.logMessage(f"✗ Upload failed ({response.status_code}): {error_msg}", "TLGeo", Qgis.Warning)
                    self.iface.messageBar().pushWarning(
                        "TLGeo",
                        f"Tải lên thất bại: {response.status_code}"
                    )
            finally:
                # Close all file handles
                for fh in file_handles:
                    fh.close()
            
        except requests.exceptions.Timeout:
            QgsMessageLog.logMessage("Upload timeout", "TLGeo", Qgis.Warning)
            self.iface.messageBar().pushWarning("TLGeo", "Tải lên bị quá thời gian chờ")
        except Exception as e:
            QgsMessageLog.logMessage(f"Upload error: {str(e)}", "TLGeo", Qgis.Warning)
            self.iface.messageBar().pushWarning("TLGeo", f"Lỗi khi tải lên: {str(e)}")
    
    def unload(self):
        """Clean up menu connections"""
        layer_tree_view = self.iface.layerTreeView()
        if layer_tree_view:
            try:
                layer_tree_view.contextMenuAboutToShow.disconnect(self.add_context_menu)
            except Exception:
                _ = None

def init_provider(iface, plugin_instance=None):
    """Initialize the layer menu provider"""
    global _provider
    _provider = TLGeoProvider(iface, plugin_instance)
    _provider.init_menu()

def unload():
    """Unload the layer menu provider"""
    global _provider
    if _provider:
        _provider.unload()
        _provider = None
