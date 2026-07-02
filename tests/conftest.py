import sys
import os
from unittest.mock import MagicMock

# 1. Mock QGIS and PyQt5 Dependencies BEFORE importing source code
# This allows us to test logic without a real QGIS installation
IS_INTEGRATION_TEST = os.environ.get("QGIS_INTEGRATION_TEST") == "1"

if not IS_INTEGRATION_TEST:
    # Mock PyQt5
    mock_pyqt5 = MagicMock()
    mock_pyqt5.QtCore = MagicMock()
    mock_pyqt5.QtWidgets = MagicMock()
    mock_pyqt5.QtGui = MagicMock()
    mock_pyqt5.QtWebKitWidgets = MagicMock()
    sys.modules["PyQt5"] = mock_pyqt5
    sys.modules["PyQt5.QtCore"] = mock_pyqt5.QtCore
    sys.modules["PyQt5.QtWidgets"] = mock_pyqt5.QtWidgets
    sys.modules["PyQt5.QtGui"] = mock_pyqt5.QtGui
    sys.modules["PyQt5.QtWebKitWidgets"] = mock_pyqt5.QtWebKitWidgets

    # Mock QSettings behavior specifically
    class MockQSettings:
        def __init__(self, org, app):
            self.store = {}
        
        def setValue(self, key, value):
            self.store[key] = value
            
        def value(self, key, default=None):
            return self.store.get(key, default)
        
        def remove(self, key):
            if key in self.store:
                del self.store[key]

    mock_pyqt5.QtCore.QSettings = MockQSettings

    # Mock QGIS
    mock_qgis = MagicMock()
    mock_qgis.core = MagicMock()
    mock_qgis.gui = MagicMock()
    mock_qgis.PyQt = MagicMock()
    mock_qgis.PyQt.QtCore = MagicMock()
    mock_qgis.PyQt.QtCore.QSettings = MockQSettings
    mock_qgis.PyQt.QtGui = MagicMock()
    sys.modules["qgis"] = mock_qgis
    sys.modules["qgis.core"] = mock_qgis.core
    sys.modules["qgis.gui"] = mock_qgis.gui
    sys.modules["qgis.PyQt"] = mock_qgis.PyQt
    sys.modules["qgis.PyQt.QtCore"] = mock_qgis.PyQt.QtCore
    sys.modules["qgis.PyQt.QtGui"] = mock_qgis.PyQt.QtGui
    mock_qgis.PyQt.QtWidgets = MagicMock()
    sys.modules["qgis.PyQt.QtWidgets"] = mock_qgis.PyQt.QtWidgets
    mock_qgis.utils = MagicMock()
    sys.modules["qgis.utils"] = mock_qgis.utils

    # Mock OSGeo
    sys.modules["osgeo"] = MagicMock()

    # Mock processing
    sys.modules["processing"] = MagicMock()

# 2. Setup import paths
# Add src directory to path so we can import 'util', 'ui', etc.
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))
