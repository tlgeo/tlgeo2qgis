"""Layer Export Background Task - Non-blocking UI export for TLGeo2QGIS plugin."""

import os
import uuid
import json
import shutil
import subprocess
import requests
from qgis.core import (
    Qgis,QgsVectorLayer,QgsTask
)
from qgis.PyQt.QtCore import pyqtSignal

# Import converters
from .app.projects.util.converters import (
    SQLiteConverter,
    SLDConverter,
    QMLConverter,
    GeostylerConverter,
    TippecanoeConverter
)


class LayerExportTask(QgsTask):
    """Background task for layer export - non-blocking UI.
    
    Usage:
        task = LayerExportTask(layer, strapi_url, auth_service)
        task.progress_changed.connect(callback)
        task.export_complete.connect(callback)
        task.export_failed.connect(callback)
        # QgsApplication.taskManager().addTask(task)
    """
    
    progress_changed = pyqtSignal(str)
    export_complete = pyqtSignal(str, str)  # export_dir, export_uuid
    export_failed = pyqtSignal(str)
    
    def __init__(self, layer, strapi_url, auth_service):
        """Initialize export task."""
        super().__init__("TLGeo Export: " + layer.name(),QgsTask.CanCancel)
        self.layer_source = layer.source()
        self.layer_name = layer.name()
        self.layer_provider = layer.providerType()
        self.layer_crs = layer.crs().authid()
        self.strapi_url = strapi_url
        self.auth_service = auth_service
        self.exception = None
        
        # Create export directory
        self.export_uuid = str(uuid.uuid4())
        home = os.path.expanduser("~")
        self.export_dir = os.path.join(home, "TLGeo_Exports", self.export_uuid)
        os.makedirs(self.export_dir, exist_ok=True)
        
        # Safe name for files
        safe = "".join(c for c in self.layer_name if c.isalnum() or c in (' ', '_', '-')).strip()
        self.safe_name = safe.replace(' ', '_')
        
        # Initialize converters
        self.sqlite_converter = SQLiteConverter()
        self.sld_converter = SLDConverter()
        self.qml_converter = QMLConverter()
        self.geostyler_converter = GeostylerConverter()
        self.tippecanoe_converter = TippecanoeConverter()
    
    def run(self):
        """Execute export in background thread. Returns True on success."""
        try:
            # Stage 1: Initialize
            self.setProgress(5)
            self.progress_changed.emit("🔄 Preparing export...")
            
            # Clone layer for this thread (thread-safe)
            layer =QgsVectorLayer(self.layer_source, self.layer_name, self.layer_provider)
            if not layer.isValid():
                raise Exception("Could not load layer in background thread")
            
            # Stage 2: Export metadata
            self.setProgress(15)
            self.progress_changed.emit("📋 Exporting metadata...")
            metadata = {
                "name": self.layer_name,
                "type": "vector",
                "crs": self.layer_crs,
                "export_uuid": self.export_uuid
            }
            metadata_path = os.path.join(self.export_dir, f"{self.safe_name}.metadata.json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # Stage 3: Export SQLite (EPSG:4326)
            self.setProgress(20)
            self.progress_changed.emit("💾 Exporting SQLite (WGS84)...")
            sqlite_4326 = os.path.join(self.export_dir, f"{self.safe_name}_sqlite_4326.sqlite")
            if self.sqlite_converter.convert(layer, sqlite_4326, dest_crs="EPSG:4326"):
                self.progress_changed.emit("✅ SQLite (WGS84) exported")
            else:
                self.progress_changed.emit("⚠️ SQLite (WGS84) failed")
            
            # Stage 4: Export SQLite (Original CRS)
            self.setProgress(35)
            self.progress_changed.emit("💾 Exporting SQLite (Original CRS)...")
            sqlite_orig = os.path.join(self.export_dir, f"{self.safe_name}_sqlite.sqlite")
            if self.sqlite_converter.convert(layer, sqlite_orig):
                self.progress_changed.emit("✅ SQLite (Original) exported")
            else:
                self.progress_changed.emit("⚠️ SQLite (Original) failed")
            
            # Stage 5: Export MBTiles
            self.setProgress(45)
            self.progress_changed.emit("🗺️ Exporting MBTiles...")
            mbtiles_path = os.path.join(self.export_dir, f"{self.safe_name}.mbtiles")
            if self.tippecanoe_converter.can_convert():
                if self.tippecanoe_converter.convert(layer, mbtiles_path):
                    self.progress_changed.emit("✅ MBTiles (tippecanoe) exported")
                else:
                    self.progress_changed.emit("⚠️ MBTiles failed")
            else:
                self.progress_changed.emit("ℹ️ MBTiles: tippecanoe not installed")
            
            # Stage 6: Export SLD
            self.setProgress(55)
            self.progress_changed.emit("🎨 Exporting SLD style...")
            sld_path = os.path.join(self.export_dir, f"{self.safe_name}.sld")
            if self.sld_converter.convert(layer, sld_path):
                self.progress_changed.emit("✅ SLD exported")
            else:
                self.progress_changed.emit("⚠️ SLD failed")
            
            # Stage 7: Export QML
            self.setProgress(57)
            self.progress_changed.emit("🎨 Exporting QML style...")
            qml_path = os.path.join(self.export_dir, f"{self.safe_name}.qml")
            if self.qml_converter.convert(layer, qml_path):
                self.progress_changed.emit("✅ QML exported")
            else:
                self.progress_changed.emit("⚠️ QML failed")
            
            # Stage 8: Export Mapbox Style
            self.setProgress(62)
            self.progress_changed.emit("🗺️ Exporting Mapbox Style...")
            mapbox_path = os.path.join(self.export_dir, f"{self.safe_name}.mapbox.json")
            if os.path.exists(sld_path) and self.geostyler_converter.can_convert():
                if self.geostyler_converter.convert(sld_path, mapbox_path):
                    self.progress_changed.emit("✅ Mapbox Style exported")
                else:
                    self.progress_changed.emit("⚠️ Mapbox Style failed")
            else:
                self.progress_changed.emit("ℹ️ Mapbox Style skipped")
            
            # Stage 9: Upload to Strapi
            self.setProgress(70)
            self.progress_changed.emit("☁️ Uploading to server...")
            
            token = self.auth_service.get_token()
            if token:
                upload_success = self._upload_to_strapi(token)
                if upload_success:
                    self.progress_changed.emit("✅ Uploaded to server!")
                else:
                    self.progress_changed.emit("⚠️ Upload failed (saved locally)")
            else:
                self.progress_changed.emit("⚠️ No auth token (saved locally)")
            
            # Stage 10: Complete
            self.setProgress(100)
            self.progress_changed.emit(f"✅ Complete! UUID: {self.export_uuid[:8]}...")
            return True
            
        except Exception as e:
            self.exception = str(e)
            return False
    
    def _upload_to_strapi(self, token):
        """Upload exported files to Strapi."""
        try:
            files = []
            file_handles = []
            
            for fn in os.listdir(self.export_dir):
                fp = os.path.join(self.export_dir, fn)
                if os.path.isfile(fp):
                    fh = open(fp, 'rb')
                    files.append(('files', (fn, fh)))
                    file_handles.append(fh)
            
            upload_url = f"{self.strapi_url}/api/upload"
            headers = {"Authorization": f"Bearer {token}"}
            data = {'uuid': self.export_uuid, 'layer_name': self.layer_name}
            
            resp = requests.post(upload_url, files=files, data=data, headers=headers, timeout=120)
            return resp.status_code == 200
            
        except Exception as e:
            self.progress_changed.emit(f"Upload error: {str(e)}")
            return False
        finally:
            for fh in file_handles:
                try:
                    fh.close()
                except:
                    pass
    
    def finished(self, result):
        """Called when task completes."""
        if result:
            self.progress_changed.emit(f"🎉 Done! {self.export_dir}")
            self.export_complete.emit(self.export_dir, self.export_uuid)
        else:
            err = self.exception or "Unknown error"
            self.progress_changed.emit(f"❌ Failed: {err}")
            self.export_failed.emit(err)
