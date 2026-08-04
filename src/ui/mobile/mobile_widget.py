from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame
from qgis.PyQt.QtGui import QPixmap, QImage, QColor, QPainter
from qgis.PyQt.QtCore import Qt
import qrcode
from ...util import net_util
from ...util.i18n import tr
from ...util import fastapi_server

class MobileWidget(QScrollArea):
    """
    Scrollable Widget containing QR code and connection details for Geocollect Mobile.
    """
    def __init__(self, parent=None):
        super(MobileWidget, self).__init__(parent)
        self.setObjectName("MobileWidget")
        self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.NoFrame)
        
        self.content_widget = QWidget()
        self.setWidget(self.content_widget)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        self.content_widget.setLayout(layout)
        
        # 1. Warning label
        warning_label = QLabel(tr("QGIS and Geocollect mobile must be on the same LAN"))
        warning_label.setWordWrap(True)
        warning_label.setAlignment(Qt.AlignCenter)
        warning_label.setStyleSheet("color: #d32f2f; font-size: 12px; font-style: italic; font-weight: bold;")
        layout.addWidget(warning_label)
        
        # 2. QR Code Display
        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.qr_label)
        
        # 3. Address text
        self.address_label = QLabel()
        self.address_label.setAlignment(Qt.AlignCenter)
        self.address_label.setStyleSheet("color: #666666; font-size: 12px;")
        layout.addWidget(self.address_label)
        
        # 4. Connection & Purpose Instructions
        layout.addSpacing(10)
        self.instructions_frame = QFrame()
        self.instructions_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
        """)
        inst_layout = QVBoxLayout(self.instructions_frame)
        inst_layout.setContentsMargins(12, 12, 12, 12)
        inst_layout.setSpacing(6)
        
        inst_title = QLabel(tr("Instructions"))
        inst_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #1b5e20;")
        inst_layout.addWidget(inst_title)
        
        inst_text = QLabel(
            tr("1. Download the **Geocollect** app on your mobile device.<br/>"
               "2. Ensure your phone and QGIS are on the same Wi-Fi network.<br/>"
               "3. Open Geocollect, scan the QR code above to connect.<br/>"
               "4. Collect and transfer spatial data directly from your phone to this QGIS plugin.")
        )
        inst_text.setWordWrap(True)
        inst_text.setStyleSheet("font-size: 11px; color: #5f6368; line-height: 1.4;")
        inst_layout.addWidget(inst_text)
        
        layout.addWidget(self.instructions_frame)
        
        layout.addStretch()
        
        self.refresh_qr()

    def set_user_greeting(self, text):
        """Update the user greeting message (disabled in layout)."""
        _ = text

    def generate_qr_pixmap(self, data):
        """Generate a QPixmap of the QR code using QPainter."""
        qr = qrcode.QRCode(border=4)
        qr.add_data(data)
        qr.make(fit=True)
        
        matrix = qr.modules
        size = len(matrix)
        
        box_size = 5
        img_size = size * box_size
        
        qimg = QImage(img_size, img_size, QImage.Format_RGB32)
        qimg.fill(QColor("white"))
        
        painter = QPainter(qimg)
        painter.setBrush(QColor("#1b5e20")) # Dark green color matching TLGeo branding
        painter.setPen(Qt.NoPen)
        
        for row in range(size):
            for col in range(size):
                if matrix[row][col]:
                    painter.drawRect(col * box_size, row * box_size, box_size, box_size)
                    
        painter.end()
        return QPixmap.fromImage(qimg)
        
    def refresh_qr(self):
        """Re-detect LAN IP and redraw QR code."""
        ip_address = net_util.get_lan_ip()
        address = f"{ip_address}:{fastapi_server.PORT}"
        self.address_label.setText(f"<b>{tr('LAN IP Address:')}</b> {address}")
        
        pixmap = self.generate_qr_pixmap(address)
        self.qr_label.setPixmap(pixmap)
