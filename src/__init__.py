import sys
import os

# Self-healing hotfix for QGIS packaging bugs (e.g. QGIS 4.2.1 on macOS)
# where system pydantic and pydantic_core versions are mismatched out-of-the-box.
try:
    import pydantic
except SystemError as e:
    try:
        msg = str(e)
        if "requires" in msg:
            target_version = msg.split("requires")[-1].strip().split()[0].strip(" .\'\"")
            # Clear partially imported pydantic modules from cache
            for k in list(sys.modules.keys()):
                if k == "pydantic" or k.startswith("pydantic."):
                    sys.modules.pop(k, None)
            import pydantic_core
            pydantic_core.__version__ = target_version
            # Clear cache again to allow clean re-import
            for k in list(sys.modules.keys()):
                if k == "pydantic" or k.startswith("pydantic."):
                    sys.modules.pop(k, None)
    except Exception:
        _ = None
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

# Define persistent ext_libs directory in the user's home folder to keep the plugin lightweight
ext_libs_dir = os.path.join(os.path.expanduser("~"), ".tlgeo", "ext_libs")

def cleanup_conflicts(ext_libs_dir):
    """Remove packages from ext_libs that are already pre-installed in QGIS.
    This prevents version mismatches (e.g. pydantic vs pydantic-core) and macOS signature errors.
    """
    # Always evict typing_extensions from sys.modules to force loading the newer version from ext_libs
    for k in list(sys.modules.keys()):
        if k == "typing_extensions" or k.startswith("typing_extensions."):
            sys.modules.pop(k, None)

    # Determine which packages are already pre-installed in QGIS's system python path
    # by temporarily removing ext_libs_dir from sys.path and trying to import them.
    # Note: On macOS (darwin), we always treat them as pre-installed to avoid Team ID signature issues.
    pre_installed_to_remove = []
    
    if sys.platform == "darwin":
        pre_installed_to_remove = ['pydantic', 'pydantic_core', 'psycopg2']
    else:
        # Check system availability
        sys_path_backup = list(sys.path)
        clean_sys_path = [p for p in sys.path if os.path.abspath(p) != os.path.abspath(ext_libs_dir)]
        
        # Temporarily use clean path
        sys.path = clean_sys_path
        
        has_system_pydantic = False
        try:
            import pydantic
            import pydantic_core
            has_system_pydantic = True
        except ImportError:
            _ = None
            
        has_system_psycopg2 = False
        try:
            import psycopg2
            has_system_psycopg2 = True
        except ImportError:
            _ = None
            
        # Restore sys.path
        sys.path = sys_path_backup
        
        if has_system_pydantic:
            pre_installed_to_remove.extend(['pydantic', 'pydantic_core'])
        if has_system_psycopg2:
            pre_installed_to_remove.append('psycopg2')

    # Remove the pre-installed packages from ext_libs_dir so we fallback to QGIS's system versions.
    # Also, if we are NOT using the system version of a package, we evict it from sys.modules
    # to force loading our local ext_libs version.
    if sys.platform != "darwin":
        if 'pydantic' not in pre_installed_to_remove:
            for k in list(sys.modules.keys()):
                if k in ("pydantic", "pydantic_core") or k.startswith(("pydantic.", "pydantic_core.")):
                    sys.modules.pop(k, None)

    import shutil
    if os.path.exists(ext_libs_dir):
        # We delete folders or files that match or are related to the pre-installed packages
        try:
            for item in os.listdir(ext_libs_dir):
                should_remove = False
                for pkg in pre_installed_to_remove:
                    # Matches pkg exactly, or matches as a prefix (like _pydantic_core, pydantic-xxx, etc.)
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

# Run startup cleanup to fix any existing dirty state from older plugin versions
cleanup_conflicts(ext_libs_dir)

# Diagnostics for pydantic version conflicts
if os.environ.get("QGIS_INTEGRATION_TEST") != "1":
    try:
        import pydantic
        print(f"TLGeo2QGIS Diagnostics - pydantic version: {pydantic.VERSION} ({pydantic.__file__})")
    except Exception as e:
        print(f"TLGeo2QGIS Diagnostics - pydantic check error: {e}")
    try:
        import pydantic_core
        print(f"TLGeo2QGIS Diagnostics - pydantic_core version: {pydantic_core.__version__} ({pydantic_core.__file__})")
    except Exception as e:
        print(f"TLGeo2QGIS Diagnostics - pydantic_core check error: {e}")
    if os.path.exists(ext_libs_dir):
        try:
            print(f"TLGeo2QGIS Diagnostics - ext_libs content: {os.listdir(ext_libs_dir)}")
        except Exception:
            _ = None

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

# Check for required dependencies and only install the missing ones
required_dependencies = {
    'fastapi': 'fastapi',
    'uvicorn': 'uvicorn',
    'qrcode': 'qrcode',
    'python_multipart': 'python-multipart',
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