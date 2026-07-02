from qgis.PyQt.QtWidgets import QTabWidget, QWidget, QMessageBox
from qgis.PyQt.QtCore import Qt

class TabManager(QWidget):
    """
    Manages the main content area with tabs.
    Supports closing tabs and managing active tabs.
    """
    def __init__(self, parent=None):
        super(TabManager, self).__init__(parent)
        
        # We can use a layout for this widget if needed, 
        # but for now let's just inherit QTabWidget or wrap it.
        # Inheriting QTabWidget directly is often easier for integration unless we need extra chrome.
        # But to keep separation, let's wrap it.
        
        from qgis.PyQt.QtWidgets import QVBoxLayout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        
        self.layout.addWidget(self.tabs)
        
        # Keep track of tabs to avoid duplicates if needed, or by ID
        # self.open_tabs = {} 

    def add_tab(self, widget, title, icon=None, focus=True):
        """
        Adds a new tab or focuses on existing one if identified (logic can be extended).
        For now, simple add.
        """
        # Optional: Check if widget already exists or has a unique ID property
        # For now, just add.
        index = self.tabs.addTab(widget, title)
        if icon:
            self.tabs.setTabIcon(index, icon)
            
        if focus:
            self.tabs.setCurrentIndex(index)
            
        return index

    def close_tab(self, index):
        """
        Closes the tab at the given index.
        """
        widget = self.tabs.widget(index)
        if widget:
            # Optional: Check if widget has a 'can_close' method
            if hasattr(widget, 'can_close') and not widget.can_close():
                return

            self.tabs.removeTab(index)
            widget.deleteLater()

    def clear_all(self):
        while self.tabs.count() > 0:
            self.close_tab(0)
    
    def current_widget(self):
        return self.tabs.currentWidget()
