"""
Qt Compatibility Layer for PyQt5/PyQt6.

QGIS 3.x uses PyQt5, QGIS 4.x uses PyQt6.
This module provides unified imports that work with both.

Usage:
    from _vendor.qt_compat import QWidget, QVBoxLayout, Qt, pyqtSignal
"""

import sys
import logging

logger = logging.getLogger(__name__)

PYQT6 = False
PYQT5 = False

try:
    from PyQt6 import QtCore, QtGui, QtWidgets
    from PyQt6.QtCore import pyqtSignal, pyqtSlot
    PYQT6 = True
    logger.debug("Using PyQt6")
except ImportError:
    try:
        from PyQt5 import QtCore, QtGui, QtWidgets
        from PyQt5.QtCore import pyqtSignal, pyqtSlot
        PYQT5 = True
        logger.debug("Using PyQt5")
    except ImportError:
        logger.error("Neither PyQt5 nor PyQt6 is available")
        raise

Qt = QtCore.Qt
QUrl = QtCore.QUrl
QDesktopServices = QtGui.QDesktopServices
QMessageBox = QtWidgets.QMessageBox

if PYQT6:
    from PyQt6 import QtPrintSupport
    QStyle = None
else:
    from PyQt5 import QtPrintSupport
    QStyle = QtWidgets.QStyle


def get_qwebview():
    """Get the appropriate QWebView/QWebEngineView class."""
    if PYQT6:
        from PyQt6.QtWebEngineWidgets import QWebEngineView
        return QWebEngineView
    else:
        from PyQt5.QtWebKitWidgets import QWebView
        return QWebView