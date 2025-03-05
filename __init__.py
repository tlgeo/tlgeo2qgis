try :
    import flask
    import flask_cors
except ImportError:
    import sys
    import os
    import subprocess

    qgis_executable = sys.executable  # This gives '/Applications/QGIS.app/Contents/MacOS/QGIS'
    qgis_base = os.path.dirname(qgis_executable)  # Move up one level
    qgis_python = os.path.join(qgis_base, "bin", "python3")  # Append 'bin/python3'

    subprocess.run([qgis_python, '-m', 'pip', 'install', 'Flask'])
    subprocess.run([qgis_python, '-m', 'pip', 'install', 'flask-cors'])

from .main import TLGeoQGISPlugin
def classFactory(iface):
    return TLGeoQGISPlugin(iface)