from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame
from qgis.PyQt.QtGui import QPixmap, QImage, QColor, QPainter
from qgis.PyQt.QtCore import Qt
import qrcode
from ...util import net_util
from ...util.i18n import tr

PORT = 13000

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
        
        # 1. Greeting Label
        self.user_label = QLabel()
        self.user_label.setStyleSheet("font-size: 13px; color: #333333;")
        self.user_label.setWordWrap(True)
        layout.addWidget(self.user_label)
        
        # Divider Line
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        divider.setStyleSheet("color: #cccccc;")
        layout.addWidget(divider)
        
        # 2. Warning label
        warning_label = QLabel(tr("QGIS and Geocollect mobile must be on the same LAN"))
        warning_label.setWordWrap(True)
        warning_label.setAlignment(Qt.AlignCenter)
        warning_label.setStyleSheet("color: #d32f2f; font-size: 12px; font-style: italic; font-weight: bold;")
        layout.addWidget(warning_label)
        
        # 3. QR Code Display
        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.qr_label)
        
        # 4. Address text
        self.address_label = QLabel()
        self.address_label.setAlignment(Qt.AlignCenter)
        self.address_label.setStyleSheet("color: #666666; font-size: 12px;")
        layout.addWidget(self.address_label)
        
        layout.addStretch()
        
        self.refresh_qr()

    def set_user_greeting(self, text):
        """Update the user greeting message."""
        self.user_label.setText(text)

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
        address = f"{ip_address}:{PORT}"
        self.address_label.setText(f"<b>{tr('LAN IP Address:')}</b> {address}")
        
        pixmap = self.generate_qr_pixmap(address)
        self.qr_label.setPixmap(pixmap)
