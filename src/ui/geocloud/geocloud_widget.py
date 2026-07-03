from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout, QLabel
from qgis.PyQt.QtCore import Qt
from ...util.i18n import tr

class GeocloudWidget(QWidget):
    """
    Placeholder Widget for Geocloud integration.
    """
    def __init__(self, parent=None):
        super(GeocloudWidget, self).__init__(parent)
        self.setObjectName("GeocloudWidget")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        self.setLayout(layout)
        
        lbl_geocloud = QLabel(tr("Tính năng sử dụng kho dữ liệu Geocloud đang được phát triển."))
        lbl_geocloud.setWordWrap(True)
        lbl_geocloud.setAlignment(Qt.AlignCenter)
        lbl_geocloud.setStyleSheet("color: #666666; font-size: 13px; font-style: italic;")
        layout.addWidget(lbl_geocloud)
        layout.addStretch()
