import os
import shutil
import subprocess
import requests
from qgis.core import (
    QgsTask, QgsMessageLog, Qgis, QgsVectorLayer,
    QgsVectorFileWriter, QgsCoordinateTransformContext
)
from PyQt5.QtCore import pyqtSignal

class LayerPublishTask(QgsTask):
    """
    Background task for converting and publishing a map layer.
    """
    
    status_changed = pyqtSignal(str)
    upload_complete = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, layer, token, strapi_url, project_name=None):
        """
        Initialize the task.
        
        Args:
            layer (QgsVectorLayer): The layer to publish (from main thread).
            token (str): JWT Auth token.
            strapi_url (str): Base URL of the Strapi backend.
            project_name (str, optional): Name of the project to create.
        """
        super().__init__(f"Publish Layer: {layer.name()}", QgsTask.CanCancel)
        
        # Store necessary info from layer, but DO NOT store the layer object itself
        # to avoid thread safety issues. We will create a new instance in run()
        self.layer_source = layer.source()
        self.layer_name = layer.name()
        self.layer_provider = layer.providerType()
        self.crs = layer.crs()
        
        self.token = token
        self.strapi_url = strapi_url
        self.project_name = project_name or self.layer_name
        self.exception = None
        
        # Temp paths
        self.temp_dir = os.path.join(os.path.expanduser("~"), ".tlgeo_temp")
        os.makedirs(self.temp_dir, exist_ok=True)
        # Use sanitized name for files
        safe_name = "".join([c for c in self.layer_name if c.isalnum() or c in (' ', '-', '_')]).strip().replace(' ', '_')
        self.geojson_path = os.path.join(self.temp_dir, f"{safe_name}.geojson")
        self.pmtiles_path = os.path.join(self.temp_dir, f"{safe_name}.pmtiles")

    def run(self):
        """
        Execute the task in a background thread.
        Returns True if successful, False otherwise.
        """
        try:
            self.status_changed.emit("Preparing export...")
            
            # Step 1: Export to GeoJSON
            # Create a fresh instance of the layer in this thread
            layer_clone = QgsVectorLayer(self.layer_source, self.layer_name, self.layer_provider)
            if not layer_clone.isValid():
                raise Exception(f"Could not load layer '{self.layer_name}' in background thread.")
            
            # Configure options
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = "GeoJSON"
            options.fileEncoding = "UTF-8"
            
            # Transform to EPSG:4326 for web mapping if not already
            if self.crs.authid() != "EPSG:4326":
                transform_context = QgsCoordinateTransformContext()
                # options.ct = ... (Transformation logic if needed, but usually QGIS handles it if we specify target CRS)
                # Actually writeAsVectorFormatV3 handles it via transform context or options
                # Let's simple use options.outputCrs
                # options.outputCrs = QgsCoordinateReferenceSystem("EPSG:4326")
                pass 
                
            self.status_changed.emit("Exporting to GeoJSON...")
            
            # Write to file
            error = QgsVectorFileWriter.writeAsVectorFormatV3(
                layer_clone,
                self.geojson_path,
                QgsCoordinateTransformContext(),
                options
            )
            
            if error[0] != QgsVectorFileWriter.NoError:
                raise Exception(f"Export failed with error code: {error[0]}")
            
            if self.isCanceled():
                return False
                
            self.setProgress(30)
            self.status_changed.emit("Converting to PMTiles...")
            
            # Step 2: Tippecanoe Conversion
            if not shutil.which("tippecanoe"):
                raise Exception("tippecanoe executable not found in PATH.")
                
            # Basic tippecanoe command
            cmd = [
                "tippecanoe",
                "-o", self.pmtiles_path,
                self.geojson_path,
                "--force",
                "-zg", # Auto zoom
                "--drop-densest-as-needed"
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Monitor process
            while True:
                if self.isCanceled():
                    process.terminate()
                    return False
                    
                output = process.stderr.readline()
                if output == '' and process.poll() is not None:
                    break
                # Could parse output for percentage here
            
            if process.returncode != 0:
                stderr = process.stderr.read()
                raise Exception(f"Tippecanoe conversion failed: {stderr}")
                
            if self.isCanceled():
                return False

            self.setProgress(60)
            self.status_changed.emit("Uploading to Cloud...")
            
            # Step 3: Upload to Strapi
            if not os.path.exists(self.pmtiles_path):
                raise Exception("PMTiles file was not created.")
                
            with open(self.pmtiles_path, 'rb') as f:
                files = {'files': (os.path.basename(self.pmtiles_path), f, 'application/octet-stream')}
                headers = {'Authorization': f'Bearer {self.token}'}
                
                # Upload file
                upload_res = requests.post(
                    f"{self.strapi_url}/api/upload",
                    files=files,
                    headers=headers,
                    timeout=300 # 5 minutes timeout for upload
                )
            
            if upload_res.status_code != 200:
                raise Exception(f"Upload failed ({upload_res.status_code}): {upload_res.text}")
                
            uploaded_files = upload_res.json()
            if not uploaded_files:
                raise Exception("Upload response contained no file data.")
                
            file_id = uploaded_files[0]['id']
            # file_url = uploaded_files[0]['url']
            
            if self.isCanceled():
                return False
                
            self.setProgress(90)
            self.status_changed.emit("Creating map project...")
            
            # Step 4: Create Map Project Entry
            # Note: Adjust fields based on actual Strapi Content Type 'map-project'
            project_data = {
                "data": {
                    "Title": self.project_name,
                    "MapFile": file_id, # Assuming relation field
                    "Description": f"Uploaded from QGIS: {self.layer_name}",
                    "Status": "published"
                }
            }
            
            project_res = requests.post(
                f"{self.strapi_url}/api/map-projects",
                json=project_data,
                headers=headers,
                timeout=30
            )
            
            # If map-projects endpoint doesn't exist or differs, this might fail.
            # Assuming standard Strapi create endpoint.
            
            if project_res.status_code not in (200, 201):
                 raise Exception(f"Project creation failed ({project_res.status_code}): {project_res.text}")
            
            final_data = project_res.json()
            project_id = final_data.get('data', {}).get('id')
            
            self.setProgress(100)
            self.upload_complete.emit(f"Project ID: {project_id}")
            return True
            
        except Exception as e:
            self.exception = e
            return False
            
    def finished(self, result):
        """Called when the task is finished (success or failure)"""
        if result:
            QgsMessageLog.logMessage(f"Layer '{self.layer_name}' published successfully!", "TLGeo", Qgis.Success)
        else:
            if self.exception:
                self.error_occurred.emit(str(self.exception))
                QgsMessageLog.logMessage(f"Publish failed: {self.exception}", "TLGeo", Qgis.Critical)
            else:
                 QgsMessageLog.logMessage("Publish task canceled or failed unknown.", "TLGeo", Qgis.Warning)
            
        # Cleanup temp files
        try:
            if os.path.exists(self.geojson_path):
                os.remove(self.geojson_path)
            if os.path.exists(self.pmtiles_path):
                os.remove(self.pmtiles_path)
        except Exception as e:
            QgsMessageLog.logMessage(f"Cleanup failed: {e}", "TLGeo", Qgis.Warning)
