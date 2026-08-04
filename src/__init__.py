import sys
import os

# Define persistent ext_libs directory in the user's home folder to keep the plugin lightweight
ext_libs_dir = os.path.join(os.path.expanduser("~"), ".tlgeo", "ext_libs")

if os.environ.get("QGIS_INTEGRATION_TEST") != "1":
    if ext_libs_dir not in sys.path:
        sys.path.insert(0, ext_libs_dir)

def cleanup_conflicts(ext_libs_dir):
    """Remove packages from ext_libs that are already pre-installed in QGIS.
    This prevents macOS Team ID code signature errors for compiled binary extensions.
    """
    pre_installed_to_remove = []

    if sys.platform == "darwin":
        # On macOS, always remove compiled binaries to avoid Team ID signature issues
        pre_installed_to_remove = ['psycopg2', 'typing_extensions']
    else:
        # Check if QGIS system python already has these packages
        sys_path_backup = list(sys.path)
        clean_sys_path = [p for p in sys.path if os.path.abspath(p) != os.path.abspath(ext_libs_dir)]
        sys.path = clean_sys_path

        try:
            import psycopg2
            pre_installed_to_remove.append('psycopg2')
        except ImportError:
            _ = None

        try:
            import typing_extensions
            pre_installed_to_remove.append('typing_extensions')
        except ImportError:
            _ = None

        sys.path = sys_path_backup

    # Remove pre-installed packages from ext_libs_dir so we fallback to QGIS's system versions
    import shutil
    if os.path.exists(ext_libs_dir):
        try:
            for item in os.listdir(ext_libs_dir):
                should_remove = False
                for pkg in pre_installed_to_remove:
                    if (item == pkg or
                        item.startswith(f"{pkg}-") or
                        item.startswith(f"_{pkg}") or
                        (pkg == 'psycopg2' and (item.startswith("psycopg2_binary-") or item == 'psycopg2_binary' or item.startswith('_psycopg2')))):
                        should_remove = True
                        break

                if should_remove:
                    pkg_path = os.path.join(ext_libs_dir, item)
                    try:
                        if os.path.isdir(pkg_path):
                            shutil.rmtree(pkg_path)
                        else:
                            os.remove(pkg_path)
                    except Exception:
                        _ = None
        except Exception:
            _ = None

# Run startup cleanup
cleanup_conflicts(ext_libs_dir)

# Also clean up leftover FastAPI/pydantic packages from previous plugin versions (<1.2.0)
# that used FastAPI. These are no longer needed and can cause conflicts.
import shutil as _shutil
if os.path.exists(ext_libs_dir):
    _legacy_packages = ['fastapi', 'starlette', 'uvicorn', 'h11', 'anyio',
                        'pydantic', 'pydantic_core', 'python_multipart', 'multipart',
                        'annotated_doc', 'annotated_types', 'typing_inspection']
    try:
        for item in os.listdir(ext_libs_dir):
            for pkg in _legacy_packages:
                if item == pkg or item.startswith(f"{pkg}-") or item.startswith(f"_{pkg}"):
                    pkg_path = os.path.join(ext_libs_dir, item)
                    try:
                        if os.path.isdir(pkg_path):
                            _shutil.rmtree(pkg_path)
                        else:
                            os.remove(pkg_path)
                    except Exception:
                        _ = None
                    break
    except Exception:
        _ = None
# Clear old local ext_libs leftover from previous versions
plugin_dir = os.path.dirname(os.path.abspath(__file__))
old_ext_libs = os.path.join(plugin_dir, "ext_libs")
if os.path.exists(old_ext_libs):
    import shutil
    try:
        shutil.rmtree(old_ext_libs)
    except Exception:
        _ = None

# Clean up stale paths in sys.path
for p in list(sys.path):
    if p and os.path.abspath(p) == os.path.abspath(old_ext_libs):
        try:
            sys.path.remove(p)
        except ValueError:
            _ = None

# Reorder sys.path to prioritize QGIS's system site-packages over the user's personal site-packages.
# This prevents incompatible user-installed packages (like pydantic-core) from overriding QGIS's built-in versions.
if "PYTEST_CURRENT_TEST" not in os.environ:
    user_site_paths = []
    system_paths = []
    home_dir = os.path.expanduser("~")
    for p in sys.path:
        if p:
            p_abs = os.path.abspath(p)
            if p_abs.startswith(home_dir) and ("site-packages" in p_abs or "dist-packages" in p_abs):
                user_site_paths.append(p)
            else:
                system_paths.append(p)
    sys.path = system_paths + user_site_paths

# Apply PyQt6 compatibility patches immediately if in QGIS environment
try:
    from . import pyqt6_compat
except ImportError:
    _ = None


# Try to import QGIS components (will only work inside QGIS environment)
HAS_QGIS = False
try:
    from qgis.PyQt.QtWidgets import QMessageBox
    HAS_QGIS = True
except ImportError:
    # Running outside QGIS (e.g., during testing)
    _ = None

# Check for required dependencies and only install the missing ones
required_dependencies = {
    'qrcode': 'qrcode',
    'dotenv': 'python-dotenv',
    'requests': 'requests',
    'psycopg2': 'psycopg2-binary',
    'websockets': 'websockets',
}

missing_packages = []
for module_name, pip_name in required_dependencies.items():
    try:
        __import__(module_name)
    except Exception:
        # Catch all exceptions (including SystemError, AttributeError) during imports
        missing_packages.append(pip_name)

# Special check for markdown and its table extension
try:
    import markdown
    import markdown.extensions.tables
except ImportError:
    # If standard import failed or incorrect cached version was loaded, clear cache and retry
    for k in list(sys.modules.keys()):
        if k == "markdown" or k.startswith("markdown."):
            sys.modules.pop(k, None)
    try:
        import markdown
        import markdown.extensions.tables
    except ImportError:
        missing_packages.append('markdown')

if missing_packages:
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
            # Install only the missing requirements directly into the local ext_libs folder
            subprocess.run([  # nosec
                qgis_python, '-m', 'pip', 'install', 
                '--target', ext_libs_dir
            ] + missing_packages, check=True)
            
            # Remove packages from ext_libs that are already pre-installed in QGIS.
            # This is critical on macOS to avoid Team ID code signature verification errors
            # (e.g. for pydantic_core and psycopg2 compiled binary extensions).
            cleanup_conflicts(ext_libs_dir)
            
            # Invalidate Python import caches to discover the newly installed packages immediately
            import importlib
            importlib.invalidate_caches()
        except (subprocess.CalledProcessError, PermissionError, OSError) as e:
            error_msg = "TLGeo2QGIS Plugin - Cài đặt thư viện thất bại\n\n"
            missing_str = " ".join(missing_packages)
            
            if os.name == 'nt':  # Windows
                error_msg += "⚠️ WINDOWS: Có lỗi xảy ra khi cài đặt các thư viện vào thư mục plugin.\n"
                error_msg += f"Vui lòng kiểm tra quyền ghi của bạn tại thư mục:\n{ext_libs_dir}\n\n"
            else:  # macOS/Linux
                error_msg += "⚠️ Lỗi cài đặt thư viện. Vui lòng thử:\n"
                error_msg += f"1. Mở Terminal\n"
                error_msg += f"2. Chạy: {qgis_python} -m pip install --target \"{ext_libs_dir}\" {missing_str}\n\n"
            
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
                _ = e

# Always define classFactory, even if imports fail above
from .main import TLGeoQGISPlugin

def classFactory(iface):
    return TLGeoQGISPlugin(iface)