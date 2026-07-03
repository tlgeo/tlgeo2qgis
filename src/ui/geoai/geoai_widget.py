from qgis.PyQt.QtWidgets import QWidget, QVBoxLayout
from ..components.chatbox import ChatBox

class GeoAIWidget(QWidget):
    """
    GeoAI Tab Widget: Wraps the reusable ChatBox component.
    """
    def __init__(self, parent=None):
        super(GeoAIWidget, self).__init__(parent)
        self.setObjectName("GeoAIWidget")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(layout)
        
        self.chatbox = ChatBox()
        layout.addWidget(self.chatbox)

    def set_connection_status(self, connected):
        """Forward connection status updates to the ChatBox component."""
        self.chatbox.set_connection_status(connected)
