from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStyle, QApplication
from qgis.PyQt.QtCore import Qt, pyqtSignal
from ...util.i18n import tr

class GeoAIWidget(QWidget):
    """
    Widget containing the GeoAI Agent instruction text and connection status.
    """
    reload_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super(GeoAIWidget, self).__init__(parent)
        self.setObjectName("GeoAIWidget")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        self.setLayout(layout)
        
        # 1. Description label with hyperlink
        self.desc_label = QLabel()
        self.desc_label.setWordWrap(True)
        self.desc_label.setOpenExternalLinks(True)
        self.desc_label.setStyleSheet("color: #333333; font-size: 13px; line-height: 1.5;")
        self.desc_label.setText(
            f"<a href=\"https://agent.tlgeo.xyz\" style=\"color: #0078d4; text-decoration: none; font-weight: bold;\">TLGeo Agent</a> "
            f"{tr('là trợ lý hỗ trợ sử dụng QGIS bằng cách ra lệnh với ngôn ngữ tự nhiên')}"
        )
        layout.addWidget(self.desc_label)
        
        # 2. Connection Status Layout
        status_layout = QHBoxLayout()
        status_layout.setSpacing(8)
        
        status_title = QLabel(tr("Tình trạng:"))
        status_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #333333;")
        status_layout.addWidget(status_title)
        
        self.status_val_label = QLabel(tr("Chưa kết nối"))
        self.status_val_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #c62828;")
        status_layout.addWidget(self.status_val_label)
        
        # Reload Button
        self.btn_reload = QPushButton()
        self.btn_reload.setToolTip(tr("Refresh connection and profile"))
        self.btn_reload.setIcon(QApplication.style().standardIcon(QStyle.SP_BrowserReload))
        self.btn_reload.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 4px;
                min-width: 24px;
                min-height: 24px;
            }
            QPushButton:hover {
                background-color: #e5e5e5;
            }
        """)
        self.btn_reload.clicked.connect(self.reload_clicked.emit)
        status_layout.addWidget(self.btn_reload)
        status_layout.addStretch()
        
        layout.addLayout(status_layout)
        layout.addStretch()

    def set_connection_status(self, connected):
        """Update connection status text and color."""
        if connected:
            self.status_val_label.setText(tr("Đã kết nối"))
            self.status_val_label.setStyleSheet("color: #2e7d32; font-weight: bold;")
        else:
            self.status_val_label.setText(tr("Chưa kết nối"))
            self.status_val_label.setStyleSheet("color: #c62828; font-weight: bold;")
