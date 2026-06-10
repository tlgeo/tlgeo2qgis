"""
Vendor package for cross-version compatibility.
"""

from .qt_compat import (
    PYQT5,
    PYQT6,
    Qt,
    QtCore,
    QtGui,
    QtWidgets,
    pyqtSignal,
    pyqtSlot,
    QUrl,
    QDesktopServices,
    QMessageBox,
    QStyle,
    get_qwebview,
)

from .qgis_compat import (
    is_qgis_4,
    qgis_version_int,
    qgis_min_version,
    MessageBarCompat,
    write_vector_format_v3,
    check_writer_error,
)