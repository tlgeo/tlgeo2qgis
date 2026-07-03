import sys
import os

# Clear old local ext_libs leftover from previous versions
plugin_dir = os.path.dirname(os.path.abspath(__file__))
old_ext_libs = os.path.join(plugin_dir, "ext_libs")
if os.path.exists(old_ext_libs):
    import shutil
    try:
        shutil.rmtree(old_ext_libs)
    except Exception:
        pass

# Clean up stale paths in sys.path
for p in list(sys.path):
    if p and os.path.abspath(p) == os.path.abspath(old_ext_libs):
        try:
            sys.path.remove(p)
        except ValueError:
            pass

# Apply PyQt6 compatibility patches immediately if in QGIS environment
try:
    from . import pyqt6_compat
except ImportError:
    pass

# Define persistent ext_libs directory in the user's home folder to keep the plugin lightweight
ext_libs_dir = os.path.join(os.path.expanduser("~"), ".tlgeo", "ext_libs")

def cleanup_conflicts(ext_libs_dir):
    """Remove packages from ext_libs that are already pre-installed in QGIS.
    This prevents version mismatches (e.g. pydantic vs pydantic-core) and macOS signature errors.
    """
    if sys.platform != "darwin":
        # On Windows/Linux, we do not have Team ID signature issues.
        # To prevent version mismatches if QGIS core or another plugin loaded the system pydantic_core
        # into sys.modules earlier, we evict pydantic and pydantic_core from sys.modules to force
        # them to load the matching, newer versions from our ext_libs.
        for k in list(sys.modules.keys()):
            if k in ("pydantic", "pydantic_core") or k.startswith(("pydantic.", "pydantic_core.")):
                sys.modules.pop(k, None)
        return

    import shutil
    pre_installed_to_remove = [
        'pydantic', 'pydantic_core', 'psycopg2', 'requests', 'typing_extensions'
    ]
    if os.path.exists(ext_libs_dir):
        for pkg in pre_installed_to_remove:
            pkg_path = os.path.join(ext_libs_dir, pkg)
            if os.path.exists(pkg_path):
                try:
                    if os.path.isdir(pkg_path):
                        shutil.rmtree(pkg_path)
                    else:
                        os.remove(pkg_path)
                except Exception:
                    pass
            
            # Clean up dist-info directories
            try:
                for item in os.listdir(ext_libs_dir):
                    if (item.startswith(f"{pkg}-") or (pkg == 'psycopg2' and item.startswith("psycopg2_binary-"))) and item.endswith(".dist-info"):
                        shutil.rmtree(os.path.join(ext_libs_dir, item))
            except Exception:
                pass

# Run startup cleanup to fix any existing dirty state from older plugin versions
cleanup_conflicts(ext_libs_dir)

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
    
    # Ensure markdown and its extension submodules are loaded correctly from our ext_libs folder
    try:
        import markdown
        import markdown.extensions.tables
    except ImportError:
        # If standard import failed or incorrect cached version was loaded, clear cache and retry
        for k in list(sys.modules.keys()):
            if k == "markdown" or k.startswith("markdown."):
                sys.modules.pop(k, None)
        import markdown
        import markdown.extensions.tables
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
                'python-dotenv', 'requests', 'psycopg2-binary', 'websockets', 'markdown'
            ], check=True)
            
            # Remove packages from ext_libs that are already pre-installed in QGIS.
            # This is critical on macOS to avoid Team ID code signature verification errors
            # (e.g. for pydantic_core and psycopg2 compiled binary extensions).
            cleanup_conflicts(ext_libs_dir)
            
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
                error_msg += f"2. Chạy: {qgis_python} -m pip install --target \"{ext_libs_dir}\" fastapi uvicorn qrcode python-multipart python-dotenv requests psycopg2-binary websockets markdown\n\n"
            
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