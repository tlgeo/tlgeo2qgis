import sys
import os

# Apply PyQt6 compatibility patches immediately if in QGIS environment
try:
    from . import pyqt6_compat
except ImportError:
    pass

# Define local ext_libs directory inside the plugin folder
plugin_dir = os.path.dirname(os.path.abspath(__file__))
ext_libs_dir = os.path.join(plugin_dir, "ext_libs")
if os.environ.get("QGIS_INTEGRATION_TEST") != "1":
    if ext_libs_dir not in sys.path:
        sys.path.insert(0, ext_libs_dir)

# Try to import QGIS components (will only work inside QGIS environment)
HAS_QGIS = False
try:
    from qgis.PyQt.QtWidgets import QMessageBox
    HAS_QGIS = True
except ImportError:
    # Running outside QGIS (e.g., during testing)
    pass

# Check for required dependencies
try:
    import fastapi
    import qrcode
    import python_multipart
    import dotenv
    import requests
    import psycopg2
    import websockets
except ImportError:
    # Skip installation if running in pytest
    if "PYTEST_CURRENT_TEST" in os.environ:
        pass
    else:
        import subprocess

        qgis_executable = sys.executable  # This gives '/Applications/QGIS.app/Contents/MacOS/QGIS'
        qgis_base = os.path.dirname(qgis_executable)  # Move up one level
        qgis_python = ''
        if os.name == 'nt':
            windows_python_paths = [
                os.path.join(qgis_base, "python3.exe"),
                os.path.join(qgis_base, "python.exe"),
                os.path.join(qgis_base, "python3"),
                os.path.join(qgis_base, "python"),
            ]
            for p in windows_python_paths:
                if os.path.exists(p):
                    qgis_python = p
                    break
            if not qgis_python:
                qgis_python = os.path.join(qgis_base, "python3")
        else:
            unix_python_paths = [
                os.path.join(qgis_base, "python"),
                os.path.join(qgis_base, "python3"),
                os.path.join(qgis_base, "bin", "python3"),
            ]
            for p in unix_python_paths:
                if os.path.exists(p):
                    qgis_python = p
                    break
            if not qgis_python:
                qgis_python = os.path.join(qgis_base, "bin", "python3")

        # Create ext_libs directory if it doesn't exist
        os.makedirs(ext_libs_dir, exist_ok=True)

        try:
            # Install all requirements directly into the local ext_libs folder
            subprocess.run([
                qgis_python, '-m', 'pip', 'install', 
                '--target', ext_libs_dir,
                'fastapi', 'uvicorn', 'qrcode', 'python-multipart', 
                'python-dotenv', 'requests', 'psycopg2-binary', 'websockets'
            ], check=True)
            
            # Invalidate Python import caches to discover the newly installed packages immediately
            import importlib
            importlib.invalidate_caches()
        except (subprocess.CalledProcessError, PermissionError, OSError) as e:
            error_msg = "TLGeo2QGIS Plugin - Cài đặt thư viện thất bại\n\n"
            
            if os.name == 'nt':  # Windows
                error_msg += "⚠️ WINDOWS: Có lỗi xảy ra khi cài đặt các thư viện vào thư mục plugin.\n"
                error_msg += f"Vui lòng kiểm tra quyền ghi của bạn tại thư mục:\n{ext_libs_dir}\n\n"
            else:  # macOS/Linux
                error_msg += "⚠️ Lỗi cài đặt thư viện. Vui lòng thử:\n"
                error_msg += f"1. Mở Terminal\n"
                error_msg += f"2. Chạy: {qgis_python} -m pip install --target \"{ext_libs_dir}\" fastapi uvicorn qrcode python-multipart python-dotenv requests psycopg2-binary websockets\n\n"
            
            error_msg += f"Chi tiết lỗi: {str(e)}"
            
            if HAS_QGIS:
                QMessageBox.critical(None, "TLGeo2QGIS - Lỗi cài đặt", error_msg)
            else:
                print(error_msg)  # Fallback for non-QGIS environment
            
            raise ImportError(f"Failed to install dependencies: {e}")

# Reload submodules to support development with Plugin Reloader
if "tlgeo2qgis.main" in sys.modules:
    import importlib
    submodules = [
        "tlgeo2qgis.util.qgis_tools",
        "tlgeo2qgis.util.qgis_bridge",
        "tlgeo2qgis.util.fastapi_server",
        "tlgeo2qgis.util.agent_client",
        "tlgeo2qgis.main"
    ]
    for m in submodules:
        if m in sys.modules:
            try:
                importlib.reload(sys.modules[m])
            except Exception as e:
                pass

# Always define classFactory, even if imports fail above
from .main import TLGeoQGISPlugin

def classFactory(iface):
    return TLGeoQGISPlugin(iface)