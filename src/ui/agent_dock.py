import os
import qrcode
from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QFrame, QStyle, QApplication, QTabWidget
from qgis.PyQt.QtGui import QPixmap, QImage, QColor, QPainter, QDesktopServices, QFont, QIcon
from qgis.PyQt.QtCore import Qt, QUrl, QTimer
from qgis.gui import QgsDockWidget
from ..util import net_util
from ..util.i18n import tr
from ..app.auth.util.auth_service import AuthService

PORT = 13000

class TLGeoAgentDock(QgsDockWidget):
    """
    Right Dock Widget: Displays user profile, GeoAI status, and connection QR Code for Geocollect Mobile,
    and embedded web views for GeoAI and Geocloud.
    """
    def __init__(self, parent=None):
        super(TLGeoAgentDock, self).__init__(tr("TLGeo Connection"), parent)
        self.setObjectName("TLGeoAgentDock")
        self.auth_service = AuthService()
        
        # 1. Create QTabWidget as main widget of the dock
        self.tab_widget = QTabWidget()
        self.setWidget(self.tab_widget)
        
        # Try to import Web View dynamically (including QWebEngineView and legacy PyQt5 QWebView)
        WebView = None
        web_module = ""
        import_errors = []
        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            WebView = QWebEngineView
            web_module = "PyQt6.QtWebEngineWidgets.QWebEngineView"
        except ImportError as e:
            import_errors.append(f"PyQt6 WebEngine error: {str(e)}")
            try:
                from PyQt5.QtWebEngineWidgets import QWebEngineView
                WebView = QWebEngineView
                web_module = "PyQt5.QtWebEngineWidgets.QWebEngineView"
            except ImportError as e2:
                import_errors.append(f"PyQt5 WebEngine error: {str(e2)}")
                try:
                    from PyQt5.QtWebKitWidgets import QWebView
                    WebView = QWebView
                    web_module = "PyQt5.QtWebKitWidgets.QWebView"
                except ImportError as e3:
                    import_errors.append(f"PyQt5 WebKit error: {str(e3)}")
                    
        # ========== Tab 1: GeoAI TLGeo Agent ==========
        self.tab_geoai = QWidget()
        layout_geoai = QVBoxLayout()
        layout_geoai.setContentsMargins(0, 0, 0, 0)
        layout_geoai.setSpacing(0)
        self.tab_geoai.setLayout(layout_geoai)
        
        if WebView is not None:
            self.agent_web_view = WebView()
            self.setup_ssl_handler(self.agent_web_view)
            self.agent_web_view.setUrl(QUrl("https://agent.tlgeo.xyz"))
            layout_geoai.addWidget(self.agent_web_view)
        else:
            placeholder = QWidget()
            vbox = QVBoxLayout()
            vbox.setContentsMargins(20, 20, 20, 20)
            vbox.setSpacing(15)
            placeholder.setLayout(vbox)
            
            lbl = QLabel(
                f"{tr('Your QGIS environment does not support embedded web browser (WebEngine).')}<br><br>"
                f"{tr('Click the button below to open the tool in an external browser:')}"
            )
            lbl.setWordWrap(True)
            lbl.setAlignment(Qt.AlignCenter)
            vbox.addWidget(lbl)
            
            btn = QPushButton(tr("Open https://agent.tlgeo.xyz"))
            btn.setStyleSheet("padding: 10px; font-weight: bold; background-color: #0078d4; color: white; border-radius: 4px;")
            btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://agent.tlgeo.xyz")))
            vbox.addWidget(btn)
            vbox.addStretch()
            layout_geoai.addWidget(placeholder)
            
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
        
        # 1. Greeting Label
        self.user_label = QLabel()
        self.user_label.setStyleSheet("font-size: 13px; color: #333333;")
        self.user_label.setWordWrap(True)
        layout_mobile.addWidget(self.user_label)
        
        # 2. Status and Reload button Layout
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
        layout_mobile.addLayout(status_layout)
        
        # Divider Line
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        divider.setStyleSheet("color: #cccccc;")
        layout_mobile.addWidget(divider)
        
        # 3. Warning label
        warning_label = QLabel(tr("QGIS and Geocollect mobile must be on the same LAN"))
        warning_label.setWordWrap(True)
        warning_label.setAlignment(Qt.AlignCenter)
        warning_label.setStyleSheet("color: #d32f2f; font-size: 12px; font-style: italic; font-weight: bold;")
        layout_mobile.addWidget(warning_label)
        
        # 4. QR Code Display
        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignCenter)
        layout_mobile.addWidget(self.qr_label)
        
        # 5. Address text (so users can also input manually)
        self.address_label = QLabel()
        self.address_label.setAlignment(Qt.AlignCenter)
        self.address_label.setStyleSheet("color: #666666; font-size: 12px;")
        layout_mobile.addWidget(self.address_label)
        
        layout_mobile.addStretch()
        
        self.tab_widget.addTab(self.scroll_area, tr("Mobile Geocollect"))
        
        # ========== Tab 3: Geocloud ==========
        self.tab_geocloud = QWidget()
        layout_geocloud = QVBoxLayout()
        layout_geocloud.setContentsMargins(0, 0, 0, 0)
        layout_geocloud.setSpacing(0)
        self.tab_geocloud.setLayout(layout_geocloud)
        
        if WebView is not None:
            self.geocloud_web_view = WebView()
            self.setup_ssl_handler(self.geocloud_web_view)
            self.geocloud_web_view.setUrl(QUrl("https://geocloud.tlgeo.xyz"))
            layout_geocloud.addWidget(self.geocloud_web_view)
        else:
            placeholder = QWidget()
            vbox = QVBoxLayout()
            vbox.setContentsMargins(20, 20, 20, 20)
            vbox.setSpacing(15)
            placeholder.setLayout(vbox)
            
            lbl = QLabel(
                f"{tr('Your QGIS environment does not support embedded web browser (WebEngine).')}<br><br>"
                f"{tr('Click the button below to open the tool in an external browser:')}"
            )
            lbl.setWordWrap(True)
            lbl.setAlignment(Qt.AlignCenter)
            vbox.addWidget(lbl)
            
            btn = QPushButton(tr("Open https://geocloud.tlgeo.xyz"))
            btn.setStyleSheet("padding: 10px; font-weight: bold; background-color: #0078d4; color: white; border-radius: 4px;")
            btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://geocloud.tlgeo.xyz")))
            vbox.addWidget(btn)
            vbox.addStretch()
            layout_geocloud.addWidget(placeholder)
            
        self.tab_widget.addTab(self.tab_geocloud, tr("Geocloud"))
        
        # Initial generation of status, user greeting, and QR code
        self.refresh_all()
        
        # Status Auto-update Timer
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_status_only)
        self.status_timer.start(3000) # Every 3 seconds

    def setup_ssl_handler(self, web_view):
        """Bypass SSL Handshake and Certificate Errors in WebView/QWebEngineView"""
        try:
            # 1. QtWebKit (QWebView) sslErrors hook
            if hasattr(web_view, "page"):
                page = web_view.page()
                if hasattr(page, "networkAccessManager"):
                    nam = page.networkAccessManager()
                    nam.sslErrors.connect(self.handle_ssl_errors)
            
            # 2. QtWebEngine (QWebEngineView) certificateError hook
            if hasattr(web_view, "page"):
                page = web_view.page()
                if hasattr(page, "certificateError"):
                    page.certificateError.connect(self.handle_webengine_cert_error)
        except Exception as e:
            from qgis.core import QgsMessageLog, Qgis
            QgsMessageLog.logMessage(f"TLGeoAgentDock: Failed to setup SSL error handler: {e}", 'TLGeo2QGIS', level=Qgis.Warning)

    def handle_ssl_errors(self, reply, errors):
        """Ignore SSL handshake issues for QWebView (QtWebKit)"""
        reply.ignoreSslErrors()
        from qgis.core import QgsMessageLog, Qgis
        QgsMessageLog.logMessage("TLGeoAgentDock: Ignored SSL handshake errors in QtWebKit QWebView.", 'TLGeo2QGIS', level=Qgis.Info)

    def handle_webengine_cert_error(self, cert_error):
        """Ignore SSL certificate issues for QWebEngineView (QtWebEngine)"""
        try:
            if hasattr(cert_error, "acceptCertificate"):
                cert_error.acceptCertificate()
            elif hasattr(cert_error, "ignoreCertificateError"):
                cert_error.ignoreCertificateError()
            from qgis.core import QgsMessageLog, Qgis
            QgsMessageLog.logMessage("TLGeoAgentDock: Ignored SSL certificate error in QWebEnginePage.", 'TLGeo2QGIS', level=Qgis.Info)
        except Exception as e:
            pass

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
