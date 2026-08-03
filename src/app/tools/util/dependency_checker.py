import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

class DependencyChecker:
    def __init__(self):
        self.os_type = platform.system()
        # Adjusted for new path: src/app/tools/util/dependency_checker.py -> src/
        self.plugin_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.bin_dir = os.path.join(self.plugin_dir, 'bin')

    def get_os_type(self):
        return self.os_type

    def _add_bin_to_env(self):
        env = os.environ.copy()
        if os.path.exists(self.bin_dir):
            env["PATH"] = self.bin_dir + os.pathsep + env["PATH"]
        return env

    def check_tippecanoe(self):
        """
        Checks for tippecanoe.
        Returns: (bool, str) -> (is_found, version_or_message)
        """
        # 1. Check in plugin bin directory (for Windows portable)
        tippecanoe_bin = "tippecanoe"
        if self.os_type == "Windows":
            tippecanoe_bin = "tippecanoe.exe"
        
        # Check explicit path in bin dir
        local_bin = os.path.join(self.bin_dir, tippecanoe_bin)
        if os.path.exists(local_bin):
             return True, "Found in plugin bin"

        # 2. Check in PATH
        if shutil.which("tippecanoe"):
             return True, "Found in PATH"

        return False, "Not found"

    def check_gdal(self):
        """
        Checks for gdal_translate and drivers.
        Returns: (bool, dict) -> (is_found, details)
        """
        gdal_info = {
            "version": "Unknown",
            "mvt_driver": False,
            "pmtiles_driver": False
        }

        # Try using python bindings first as it's cleaner in QGIS
        try:
            from osgeo import gdal
            gdal_info["version"] = gdal.__version__
            
            # Check drivers
            driver_count = gdal.GetDriverCount()
            for i in range(driver_count):
                driver = gdal.GetDriver(i)
                name = driver.ShortName
                if name == "MVT":
                    gdal_info["mvt_driver"] = True
                # PMTiles driver check might vary depending on GDAL version
                # Usually it's available if built with it.
                if name == "PMTiles": # Hypothetical check, sometimes handled via /vsis3/ etc.
                     gdal_info["pmtiles_driver"] = True
            
            return True, gdal_info
        except ImportError:
            _ = None

        # Fallback to command line
        if shutil.which("gdal_translate"):
            try:
                # Check version
                result = subprocess.run(["gdal_translate", "--version"], capture_output=True, text=True)  # nosec
                if result.returncode == 0:
                    # Output example: "GDAL 3.8.3, released 2024/01/04"
                    gdal_info["version"] = result.stdout.split(',')[0].strip()
                
                # Check drivers
                result_drivers = subprocess.run(["gdal_translate", "--formats"], capture_output=True, text=True)  # nosec
                if result_drivers.returncode == 0:
                    if "MVT" in result_drivers.stdout:
                         gdal_info["mvt_driver"] = True
                    # PMTiles support in GDAL is relatively new (3.9+ or via plugin?)
                    # For now we check if it's listed.
                    if "PMTiles" in result_drivers.stdout:
                         gdal_info["pmtiles_driver"] = True

                return True, gdal_info
            except Exception as e:
                return False, str(e)

        return False, "GDAL not found"
