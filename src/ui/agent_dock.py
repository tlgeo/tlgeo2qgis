import os
import qrcode
from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QFrame, QStyle, QApplication
from qgis.PyQt.QtGui import QPixmap, QImage, QColor, QPainter, QDesktopServices, QFont, QIcon
from qgis.PyQt.QtCore import Qt, QUrl, QTimer
from qgis.gui import QgsDockWidget
from ..util import net_util
from ..util.i18n import tr
from ..app.auth.util.auth_service import AuthService

PORT = 13000

class TLGeoAgentDock(QgsDockWidget):
    """
    Right Dock Widget: Displays user profile, GeoAI status, and connection QR Code for Geocollect Mobile.
    """
    def __init__(self, parent=None):
        super(TLGeoAgentDock, self).__init__(tr("TLGeo Connection"), parent)
        self.setObjectName("TLGeoAgentDock")
        self.auth_service = AuthService()
        
        # Create scroll area to prevent clipping when dock is resized small
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)
        self.setWidget(self.scroll_area)
        
        self.main_widget = QWidget()
        self.scroll_area.setWidget(self.main_widget)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        self.main_widget.setLayout(layout)
        
        # 1. Greeting Label
        self.user_label = QLabel()
        self.user_label.setStyleSheet("font-size: 13px; color: #333333;")
        self.user_label.setWordWrap(True)
        layout.addWidget(self.user_label)
        
        # 2. Divider: GeoAI
        layout.addWidget(self.create_divider("GeoAI"))
        
        # 3. Description text with Link
        desc_label = QLabel()
        desc_label.setWordWrap(True)
        desc_label.setOpenExternalLinks(True)
        desc_label.setStyleSheet("color: #555555; font-size: 12px; line-height: 1.4;")
        desc_label.setText(
            tr("Cầu nối giúp <a href=\"https://agent.tlgeo.net\" style=\"color: #0078d4; text-decoration: none; font-weight: bold;\">TLGeo Agent</a> hỗ trợ sử dụng QGIS thông qua trợ lý ảo AI.")
        )
        layout.addWidget(desc_label)
        
        # 4. Status and Reload button Layout
        status_layout = QHBoxLayout()
        status_layout.setSpacing(6)
        
        status_title = QLabel(tr("Tình trạng:"))
        status_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #333333;")
        status_layout.addWidget(status_title)
        
        self.status_val_label = QLabel(tr("Chưa kết nối"))
        self.status_val_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #c62828;")
        status_layout.addWidget(self.status_val_label)
        
        status_layout.addStretch()
        
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
        self.btn_reload.clicked.connect(self.refresh_all)
        status_layout.addWidget(self.btn_reload)
        
        layout.addLayout(status_layout)
        
        # 5. Divider: Mobile Geocollect
        layout.addWidget(self.create_divider("Mobile Geocollect"))
        
        # 6. Warning label
        warning_label = QLabel(tr("QGIS and Geocollect mobile must be on the same LAN"))
        warning_label.setWordWrap(True)
        warning_label.setAlignment(Qt.AlignCenter)
        warning_label.setStyleSheet("color: #d32f2f; font-size: 12px; font-style: italic; font-weight: bold;")
        layout.addWidget(warning_label)
        
        # 7. QR Code Display
        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.qr_label)
        
        # 8. Address text (so users can also input manually)
        self.address_label = QLabel()
        self.address_label.setAlignment(Qt.AlignCenter)
        self.address_label.setStyleSheet("color: #666666; font-size: 12px;")
        layout.addWidget(self.address_label)
        
        layout.addStretch()
        
        # Initial generation of status, user greeting, and QR code
        self.refresh_all()
        
        # Status Auto-update Timer
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_status_only)
        self.status_timer.start(3000) # Every 3 seconds

    def create_divider(self, title_text):
        """Create a stylized horizontal line divider with a title in the middle."""
        widget = QWidget()
        hbox = QHBoxLayout()
        hbox.setContentsMargins(0, 5, 0, 5)
        hbox.setSpacing(10)
        widget.setLayout(hbox)
        
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setFrameShadow(QFrame.Sunken)
        line1.setStyleSheet("color: #cccccc;")
        
        lbl = QLabel(title_text)
        lbl.setStyleSheet("font-weight: bold; color: #1b5e20; font-size: 10px; text-transform: uppercase; letter-spacing: 1px;")
        
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        line2.setStyleSheet("color: #cccccc;")
        
        hbox.addWidget(line1)
        hbox.addWidget(lbl)
        hbox.addWidget(line2)
        return widget
        
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
        
        self.address_label.setText(f"<b>LAN IP Address:</b> {address}")
        
        pixmap = self.generate_qr_pixmap(address)
        self.qr_label.setPixmap(pixmap)
        
    def update_status_only(self):
        """Check bridge connection status and update label style dynamically."""
        connected = False
        from ..main import qgis_plugin
        if qgis_plugin and qgis_plugin.agent_bridge:
            connected = qgis_plugin.agent_bridge.is_connected
            
        if connected:
            self.status_val_label.setText(tr("Đã kết nối"))
            self.status_val_label.setStyleSheet("color: #2e7d32; font-weight: bold;")
        else:
            self.status_val_label.setText(tr("Chưa kết nối"))
            self.status_val_label.setStyleSheet("color: #c62828; font-weight: bold;")

    def refresh_all(self):
        """Refresh connection status, user profile greeting, and QR code."""
        # 1. Update user info
        user = self.auth_service.get_current_user()
        if user:
            fullname = user.get('fullname', 'User')
            username = user.get('username', 'username')
            self.user_label.setText(tr("Xin chào, <b>{}</b> ({})").format(fullname, username))
        else:
            self.user_label.setText(tr("Xin chào, <b>Khách</b> (chưa đăng nhập)"))
            
        # 2. Update WebSocket connection status and reconnect if needed
        connected = False
        from ..main import qgis_plugin
        if qgis_plugin and qgis_plugin.agent_bridge:
            connected = qgis_plugin.agent_bridge.is_connected
            if not connected and qgis_plugin.is_authenticated:
                qgis_plugin.agent_bridge.stop()
                qgis_plugin.agent_bridge.start()
                
        if connected:
            self.status_val_label.setText(tr("Đã kết nối"))
            self.status_val_label.setStyleSheet("color: #2e7d32; font-weight: bold;")
        else:
            self.status_val_label.setText(tr("Chưa kết nối"))
            self.status_val_label.setStyleSheet("color: #c62828; font-weight: bold;")
            
        # 3. Refresh QR connection details
        self.refresh_qr()
