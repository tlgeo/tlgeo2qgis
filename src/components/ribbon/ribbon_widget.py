from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, 
    QToolButton, QGroupBox, QSizePolicy, QTabBar
)
from PyQt5.QtCore import Qt, QSize

class RibbonWidget(QWidget):
    """
    A custom Ribbon-like widget.
    It uses a QTabWidget but styled to look more like a Ribbon.
    Inside each tab, there is a RibbonTab widget.
    """
    def __init__(self, parent=None):
        super(RibbonWidget, self).__init__(parent)
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.setLayout(self.layout)

        # The main container for tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border-top: 1px solid #C0C0C0;
                background-color: #F0F0F0;
            }
            QTabBar::tab {
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #F0F0F0;
                border-bottom: 2px solid #0078D7;
            }
        """)
        
        # Fixed height for the ribbon content area
        # Adjust as needed, usually ribbon is around 100-120px
        # self.tab_widget.setFixedHeight(140) 

        self.layout.addWidget(self.tab_widget)

    def add_tab(self, tab_widget, title):
        """Adds a RibbonTab to the ribbon."""
        self.tab_widget.addTab(tab_widget, title)

class RibbonTab(QWidget):
    """
    Represents the content of a single ribbon tab.
    It contains RibbonGroups horizontally.
    """
    def __init__(self, parent=None):
        super(RibbonTab, self).__init__(parent)
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)
        self.layout.setAlignment(Qt.AlignLeft)
        self.setLayout(self.layout)
        
        # Set a fixed height or max height to keep ribbon look
        self.setFixedHeight(110)

    def add_group(self, group):
        self.layout.addWidget(group)
    
    def add_stretch(self):
        self.layout.addStretch()

class RibbonGroup(QGroupBox):
    """
    A group of buttons within a RibbonTab.
    """
    def __init__(self, title, parent=None):
        super(RibbonGroup, self).__init__(title, parent)
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)
        self.setLayout(self.layout)
        
        self.setStyleSheet("""
            QGroupBox {
                border: 1px solid #D0D0D0;
                border-radius: 3px;
                margin-top: 5px;
                padding-top: 10px;
                font-weight: bold;
                color: #555555;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 3px;
                font-size: 10px;
            }
        """)

    def add_button(self, button):
        self.layout.addWidget(button)

class RibbonButton(QToolButton):
    """
    A large button with text under icon.
    """
    def __init__(self, text, icon=None, parent=None):
        super(RibbonButton, self).__init__(parent)
        self.setText(text)
        if icon:
            self.setIcon(icon)
        
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setIconSize(QSize(32, 32))
        self.setFixedSize(60, 70) # Adjust size as needed
        
        self.setStyleSheet("""
            QToolButton {
                border: none;
                border-radius: 3px;
                padding: 5px;
            }
            QToolButton:hover {
                background-color: #E0E0E0;
            }
            QToolButton:pressed {
                background-color: #C0C0C0;
            }
        """)
