import os
import qrcode
from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QFrame, QStyle, QApplication, QTabWidget
from qgis.PyQt.QtGui import QPixmap, QImage, QColor, QPainter, QDesktopServices
from qgis.PyQt.QtCore import Qt, QUrl, QTimer
from qgis.gui import QgsDockWidget
from ..util import net_util
from ..util.i18n import tr
from ..app.auth.util.auth_service import AuthService

PORT = 13000

class TLGeoAgentDock(QgsDockWidget):
    """
    Right Dock Widget: Displays different tabs for GeoAI Agent connection status, 
    Mobile Geocollect QR Code, and disabled Geocloud placeholder.
    """
    def __init__(self, parent=None):
        super(TLGeoAgentDock, self).__init__(tr("TLGeo Connection"), parent)
        self.setObjectName("TLGeoAgentDock")
        self.auth_service = AuthService()
        
        # 1. Create QTabWidget as main widget of the dock
        self.tab_widget = QTabWidget()
        self.setWidget(self.tab_widget)
        
        # ========== Tab 1: GeoAI TLGeo Agent ==========
        self.tab_geoai = QWidget()
        layout_geoai = QVBoxLayout()
        layout_geoai.setContentsMargins(15, 15, 15, 15)
        layout_geoai.setSpacing(15)
        self.tab_geoai.setLayout(layout_geoai)
        
        # Description label with link
        desc_label = QLabel()
        desc_label.setWordWrap(True)
        desc_label.setOpenExternalLinks(True)
        desc_label.setStyleSheet("color: #333333; font-size: 13px; line-height: 1.5;")
        desc_label.setText(
            f"<a href=\"https://agent.tlgeo.xyz\" style=\"color: #0078d4; text-decoration: none; font-weight: bold;\">TLGeo Agent</a> "
            f"{tr('là trợ lý hỗ trợ sử dụng QGIS bằng cách ra lệnh với ngôn ngữ tự nhiên')}"
        )
        layout_geoai.addWidget(desc_label)
        
        # Status and Reload Layout
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
        self.btn_reload.clicked.connect(self.refresh_all)
        status_layout.addWidget(self.btn_reload)
        status_layout.addStretch()
        
        layout_geoai.addLayout(status_layout)
        layout_geoai.addStretch()
        
        self.tab_widget.addTab(self.tab_geoai, tr("GeoAI TLGeo Agent"))
        
        # ========== Tab 2: Mobile Geocollect ==========
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)
        
        self.tab_mobile = QWidget()
        layout_mobile = QVBoxLayout()
        layout_mobile.setContentsMargins(15, 15, 15, 15)
        layout_mobile.setSpacing(12)
        self.tab_mobile.setLayout(layout_mobile)
        self.scroll_area.setWidget(self.tab_mobile)
        
        # Greeting Label
        self.user_label = QLabel()
        self.user_label.setStyleSheet("font-size: 13px; color: #333333;")
        self.user_label.setWordWrap(True)
        layout_mobile.addWidget(self.user_label)
        
        # Divider Line
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        divider.setStyleSheet("color: #cccccc;")
        layout_mobile.addWidget(divider)
        
        # Warning label
        warning_label = QLabel(tr("QGIS and Geocollect mobile must be on the same LAN"))
        warning_label.setWordWrap(True)
        warning_label.setAlignment(Qt.AlignCenter)
        warning_label.setStyleSheet("color: #d32f2f; font-size: 12px; font-style: italic; font-weight: bold;")
        layout_mobile.addWidget(warning_label)
        
        # QR Code Display
        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignCenter)
        layout_mobile.addWidget(self.qr_label)
        
        # Address text (so users can also input manually)
        self.address_label = QLabel()
        self.address_label.setAlignment(Qt.AlignCenter)
        self.address_label.setStyleSheet("color: #666666; font-size: 12px;")
        layout_mobile.addWidget(self.address_label)
        
        layout_mobile.addStretch()
        
        self.tab_widget.addTab(self.scroll_area, tr("Mobile Geocollect"))
        
        # ========== Tab 3: Geocloud ==========
        self.tab_geocloud = QWidget()
        layout_geocloud = QVBoxLayout()
        layout_geocloud.setContentsMargins(15, 15, 15, 15)
        layout_geocloud.setSpacing(15)
        self.tab_geocloud.setLayout(layout_geocloud)
        
        lbl_geocloud = QLabel(tr("Tính năng sử dụng kho dữ liệu Geocloud đang được phát triển."))
        lbl_geocloud.setWordWrap(True)
        lbl_geocloud.setAlignment(Qt.AlignCenter)
        lbl_geocloud.setStyleSheet("color: #666666; font-size: 13px; font-style: italic;")
        layout_geocloud.addWidget(lbl_geocloud)
        layout_geocloud.addStretch()
        
        self.tab_widget.addTab(self.tab_geocloud, tr("Geocloud"))
        # Disable the Geocloud tab temporarily
        self.tab_widget.setTabEnabled(2, False)
        
        # Initial generation of status, user greeting, and QR code
        self.refresh_all()
        
        # Status Auto-update Timer
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_status_only)
        self.status_timer.start(3000) # Every 3 seconds

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
