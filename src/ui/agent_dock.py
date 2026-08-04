from qgis.PyQt.QtWidgets import QTabWidget
from qgis.PyQt.QtCore import QTimer
from qgis.gui import QgsDockWidget
from ..util.i18n import tr
from ..app.auth.util.auth_service import AuthService

# Import separated tab widgets
from .geoai import GeoAIWidget
from .mobile import MobileWidget
from .geocloud import GeocloudWidget

class TLGeoAgentDock(QgsDockWidget):
    """
    Right Dock Widget: Displays different tabs for GeoAI Agent connection status, 
    Mobile Geocollect QR Code, and disabled Geocloud placeholder.
    """
    def __init__(self, parent=None, instance_id=None):
        super(TLGeoAgentDock, self).__init__(tr("TLGeo Connection"), parent)
        self.setObjectName("TLGeoAgentDock")
        self.auth_service = AuthService()
        
        # 1. Create QTabWidget as main widget of the dock
        self.tab_widget = QTabWidget()
        self.setWidget(self.tab_widget)
        
        # ========== Tab 1: GeoAI TLGeo Agent ==========
        self.geoai_tab = GeoAIWidget(instance_id=instance_id)
        self.geoai_tab.reload_clicked.connect(self.refresh_all)
        self.tab_widget.addTab(self.geoai_tab, tr("GeoAI TLGeo Agent"))
        
        # ========== Tab 2: Mobile Geocollect ==========
        self.mobile_tab = MobileWidget()
        self.tab_widget.addTab(self.mobile_tab, tr("Mobile Geocollect"))
        
        # ========== Tab 3: Geocloud ==========
        self.geocloud_tab = GeocloudWidget()
        self.tab_widget.addTab(self.geocloud_tab, tr("Geocloud"))
        # Disable the Geocloud tab temporarily
        self.tab_widget.setTabEnabled(2, False)
        
        # Initial generation of status, user greeting, and QR code
        self.refresh_all()
        
        # Status Auto-update Timer
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_status_only)
        self.status_timer.start(3000) # Every 3 seconds

    def update_status_only(self):
        """Check bridge connection status and update label style dynamically."""
        connected = False
        from ..main import qgis_plugin
        if qgis_plugin and qgis_plugin.agent_bridge:
            connected = qgis_plugin.agent_bridge.is_connected
            
        self.geoai_tab.set_connection_status(connected)

    def refresh_all(self):
        """Refresh connection status, user profile greeting, and QR code."""
        # 1. Update user info
        user = self.auth_service.get_current_user()
        if user:
            fullname = user.get('fullname', 'User')
            username = user.get('username', 'username')
            greeting = tr("Xin chào, <b>{}</b> ({})").format(fullname, username)
        else:
            greeting = tr("Xin chào, <b>Khách</b> (chưa đăng nhập)")
            
        self.mobile_tab.set_user_greeting(greeting)
            
        # 2. Update WebSocket connection status and reconnect if needed
        connected = False
        from ..main import qgis_plugin
        if qgis_plugin and qgis_plugin.agent_bridge:
            connected = qgis_plugin.agent_bridge.is_connected
            if not connected and qgis_plugin.is_authenticated:
                qgis_plugin.agent_bridge.stop()
                qgis_plugin.agent_bridge.start()
                
        self.geoai_tab.set_connection_status(connected)
            
        # 3. Refresh QR connection details
        self.mobile_tab.refresh_qr()
