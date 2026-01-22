import sys
import os

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
except ImportError:
    import subprocess

    qgis_executable = sys.executable  # This gives '/Applications/QGIS.app/Contents/MacOS/QGIS'
    qgis_base = os.path.dirname(qgis_executable)  # Move up one level
    qgis_python = ''
    if os.name == 'nt':
        qgis_python = os.path.join(qgis_base, "python3")
    else:
        qgis_python = os.path.join(qgis_base, "bin", "python3")  # Append 'bin/python3'

    try:
        # subprocess.run([qgis_python, '-m', 'pip', 'install', 'Flask'])
        # subprocess.run([qgis_python, '-m', 'pip', 'install', 'flask-cors'])

        subprocess.run([qgis_python, '-m', 'pip', 'install', 'fastapi'], check=True)
        subprocess.run([qgis_python, '-m', 'pip', 'install', 'uvicorn'], check=True)
        subprocess.run([qgis_python, '-m', 'pip', 'install', 'qrcode'], check=True)
        subprocess.run([qgis_python, '-m', 'pip', 'install', 'python-multipart'], check=True)
        subprocess.run([qgis_python, '-m', 'pip', 'install', 'python-dotenv'], check=True)
        subprocess.run([qgis_python, '-m', 'pip', 'install', 'requests'], check=True)
    except (subprocess.CalledProcessError, PermissionError, OSError) as e:
        error_msg = "TLGeo2QGIS Plugin - Cài đặt thư viện thất bại\n\n"
        
        if os.name == 'nt':  # Windows
            error_msg += "⚠️ WINDOWS: Bạn cần mở QGIS với quyền Administrator lần đầu tiên để cài đặt các thư viện.\n\n"
            error_msg += "Cách làm:\n"
            error_msg += "1. Đóng QGIS\n"
            error_msg += "2. Click phải vào biểu tượng QGIS\n"
            error_msg += "3. Chọn 'Run as Administrator'\n"
            error_msg += "4. Mở lại plugin này\n\n"
        else:  # macOS/Linux
            error_msg += "⚠️ Lỗi cài đặt thư viện. Vui lòng thử:\n"
            error_msg += f"1. Mở Terminal\n"
            error_msg += f"2. Chạy: {qgis_python} -m pip install fastapi uvicorn qrcode python-multipart python-dotenv requests\n\n"
        
        error_msg += f"Chi tiết lỗi: {str(e)}"
        
        if HAS_QGIS:
            QMessageBox.critical(None, "TLGeo2QGIS - Lỗi cài đặt", error_msg)
        else:
            print(error_msg)  # Fallback for non-QGIS environment
        
        raise ImportError(f"Failed to install dependencies: {e}")

# Always define classFactory, even if imports fail above
from .main import TLGeoQGISPlugin

def classFactory(iface):
    return TLGeoQGISPlugin(iface)