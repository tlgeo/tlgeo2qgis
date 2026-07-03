from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from qgis.PyQt.QtCore import Qt, QUrl
from qgis.gui import QgsDockWidget
from ..util.i18n import tr

class TLGeoAgentDock(QgsDockWidget):
    """
    Right Dock Widget: Contains a web view pointing to https://agent.tlgeo.net.
    Provides fallback to opening in external browser if QtWebEngine is not available.
    """
    def __init__(self, parent=None):
        super(TLGeoAgentDock, self).__init__(tr("TLGeo Agent"), parent)
        self.setObjectName("TLGeoAgentDock")
        
        self.main_widget = QWidget()
        self.setWidget(self.main_widget)
        
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.main_widget.setLayout(self.layout)
        
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
                
        from qgis.core import QgsMessageLog, Qgis
        if WebView is not None:
            QgsMessageLog.logMessage(f"TLGeoAgentDock initialized successfully using {web_module}.", 'TLGeo2QGIS', level=Qgis.Info)
            self.web_view = WebView()
            self.setup_ssl_handler()
            self.web_view.setUrl(QUrl("https://agent.tlgeo.xyz"))
            self.layout.addWidget(self.web_view)
        else:
            errors_str = " | ".join(import_errors)
            QgsMessageLog.logMessage(f"TLGeoAgentDock: Web View not available ({errors_str}). Falling back to placeholder.", 'TLGeo2QGIS', level=Qgis.Warning)
            from qgis.PyQt.QtGui import QDesktopServices
            
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
            self.layout.addWidget(placeholder)

    def setup_ssl_handler(self):
        """Bypass SSL Handshake and Certificate Errors in WebView/QWebEngineView"""
        try:
            # 1. QtWebKit (QWebView) sslErrors hook
            if hasattr(self.web_view, "page"):
                page = self.web_view.page()
                if hasattr(page, "networkAccessManager"):
                    nam = page.networkAccessManager()
                    nam.sslErrors.connect(self.handle_ssl_errors)
            
            # 2. QtWebEngine (QWebEngineView) certificateError hook
            if hasattr(self.web_view, "page"):
                page = self.web_view.page()
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
