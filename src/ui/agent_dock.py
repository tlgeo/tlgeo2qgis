from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from qgis.PyQt.QtCore import Qt, QUrl
from qgis.gui import QgsDockWidget

class TLGeoAgentDock(QgsDockWidget):
    """
    Right Dock Widget: Contains a web view pointing to https://agent.tlgeo.net.
    Provides fallback to opening in external browser if QtWebEngine is not available.
    """
    def __init__(self, parent=None):
        super(TLGeoAgentDock, self).__init__("TLGeo Agent", parent)
        self.setObjectName("TLGeoAgentDock")
        
        self.main_widget = QWidget()
        self.setWidget(self.main_widget)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.main_widget.setLayout(layout)
        
        # Try to import QWebEngineView dynamically (excluding obsolete QtWebKit QWebView)
        WebView = None
        web_module = ""
        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            WebView = QWebEngineView
            web_module = "PyQt6.QtWebEngineWidgets"
        except ImportError:
            try:
                from PyQt5.QtWebEngineWidgets import QWebEngineView
                WebView = QWebEngineView
                web_module = "PyQt5.QtWebEngineWidgets"
            except ImportError:
                pass
                
        from qgis.core import QgsMessageLog, Qgis
        if WebView is not None:
            QgsMessageLog.logMessage(f"TLGeoAgentDock initialized successfully using {web_module}.", 'TLGeo2QGIS', level=Qgis.Info)
            self.web_view = WebView()
            self.web_view.setUrl(QUrl("https://agent.tlgeo.net"))
            layout.addWidget(self.web_view)
        else:
            QgsMessageLog.logMessage("TLGeoAgentDock: QtWebEngineWidgets not available, falling back to placeholder.", 'TLGeo2QGIS', level=Qgis.Warning)
            from qgis.PyQt.QtGui import QDesktopServices
            
            placeholder = QWidget()
            vbox = QVBoxLayout()
            vbox.setContentsMargins(20, 20, 20, 20)
            vbox.setSpacing(15)
            placeholder.setLayout(vbox)
            
            lbl = QLabel(
                "Môi trường QGIS của bạn không hỗ trợ bộ duyệt web nhúng (WebEngine).<br><br>"
                "Bấm nút dưới đây để mở công cụ trong trình duyệt ngoài:"
            )
            lbl.setWordWrap(True)
            lbl.setAlignment(Qt.AlignCenter)
            vbox.addWidget(lbl)
            
            btn = QPushButton("Mở https://agent.tlgeo.net")
            btn.setStyleSheet("padding: 10px; font-weight: bold; background-color: #0078d4; color: white; border-radius: 4px;")
            btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://agent.tlgeo.net")))
            vbox.addWidget(btn)
            
            vbox.addStretch()
            layout.addWidget(placeholder)
