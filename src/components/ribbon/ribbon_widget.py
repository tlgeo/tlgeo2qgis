import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QToolButton, 
    QStackedWidget, QTabBar, QFrame, QLabel, QScrollArea,
    QSizePolicy, QMenu, QAction
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal

class RibbonButton(QToolButton):
    """
    Action Button for the Ribbon.
    Modes:
    - Large: Icon (32px) on top, text below.
    - Small: Icon (16px) on left, text beside.
    """
    def __init__(self, text, icon=None, mode="large", parent=None):
        super(RibbonButton, self).__init__(parent)
        self.setText(text)
        self._mode = mode
        
        if icon:
            self.setIcon(icon)

        # Set specific object name for QSS styling
        self.setObjectName("RibbonButton")
        self.setProperty("ribbonMode", mode)

        if mode == "large":
            self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            self.setIconSize(QSize(32, 32))
            self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            self.setFixedHeight(70) # Standard height for large buttons
            self.setMinimumWidth(50)
        else: # Small
            self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            self.setIconSize(QSize(16, 16))
            self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            # self.setFixedSize(None, None) # Let layout handle it

    def set_menu(self, menu):
        self.setMenu(menu)
        self.setPopupMode(QToolButton.InstantPopup)


class RibbonColumn(QWidget):
    """
    Helper widget to stack small buttons vertically.
    """
    def __init__(self, parent=None):
        super(RibbonColumn, self).__init__(parent)
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.layout)

    def add_button(self, button):
        self.layout.addWidget(button)

    def add_small_button(self, text, icon=None, callback=None):
        btn = RibbonButton(text, icon, mode="small")
        if callback:
            btn.clicked.connect(callback)
        self.layout.addWidget(btn)
        return btn


class RibbonGallery(QScrollArea):
    """
    Visual Choice List (e.g., for Styles).
    """
    def __init__(self, parent=None):
        super(RibbonGallery, self).__init__(parent)
        self.setObjectName("RibbonGallery")
        self.setWidgetResizable(True)
        self.setFixedHeight(70) # Match large button height
        self.setFixedWidth(200) # Default width (increased from 100)
        
        self.content_widget = QWidget()
        self.grid_layout = QHBoxLayout() # Or QGridLayout if expanding
        self.grid_layout.setContentsMargins(2, 2, 2, 2)
        self.grid_layout.setSpacing(2)
        self.content_widget.setLayout(self.grid_layout)
        
        self.setWidget(self.content_widget)

    def add_item(self, button):
        self.grid_layout.addWidget(button)


class RibbonGroup(QFrame):
    """
    Functional Grouping (e.g., 'Clipboard').
    Contains a horizontal layout of buttons/columns and a label at the bottom.
    """
    def __init__(self, title, parent=None):
        super(RibbonGroup, self).__init__(parent)
        self.setObjectName("RibbonGroup")
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        
        # Main Layout: Vertical (Content Area + Label Area)
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(2, 2, 2, 2)
        self.main_layout.setSpacing(0)
        self.setLayout(self.main_layout)

        # Content Layout (Horizontal)
        self.content_widget = QWidget()
        self.content_layout = QHBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(2)
        self.content_layout.setAlignment(Qt.AlignLeft)
        self.content_widget.setLayout(self.content_layout)
        
        self.main_layout.addWidget(self.content_widget)

        # Bottom Label Area
        self.label_container = QWidget()
        self.label_layout = QHBoxLayout()
        self.label_layout.setContentsMargins(0, 0, 0, 0)
        self.label_layout.setSpacing(0)
        self.label_container.setLayout(self.label_layout)
        
        # Label
        self.title_label = QLabel(title)
        self.title_label.setObjectName("RibbonGroupLabel")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.label_layout.addWidget(self.title_label, 1) # Stretch

        # Option Button (Dialog Launcher)
        self.option_button = QToolButton()
        self.option_button.setObjectName("RibbonGroupOptionButton")
        self.option_button.setFixedSize(12, 12)
        self.option_button.setToolTip("Show more options")
        self.option_button.setVisible(False) # Hidden by default
        self.label_layout.addWidget(self.option_button, 0, Qt.AlignBottom | Qt.AlignRight)

        self.main_layout.addWidget(self.label_container)

    def add_large_button(self, text, icon=None, callback=None):
        btn = RibbonButton(text, icon, mode="large")
        if callback:
            btn.clicked.connect(callback)
        self.content_layout.addWidget(btn)
        return btn

    def add_column(self):
        col = RibbonColumn()
        self.content_layout.addWidget(col)
        return col
    
    def add_gallery(self):
        gallery = RibbonGallery()
        self.content_layout.addWidget(gallery)
        return gallery

    def add_widget(self, widget):
        self.content_layout.addWidget(widget)

    def enable_option_button(self, callback):
        self.option_button.setVisible(True)
        self.option_button.clicked.connect(callback)


class RibbonTabContent(QWidget):
    """
    The Panel Area for a specific tab.
    Holds RibbonGroups.
    """
    def __init__(self, parent=None):
        super(RibbonTabContent, self).__init__(parent)
        self.setObjectName("RibbonTabContent")
        self.setFixedHeight(100) # Fixed height as per spec
        
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(0) # No spacing between groups (groups have their own separators)
        self.layout.setAlignment(Qt.AlignLeft)
        self.setLayout(self.layout)

    def add_group(self, title):
        group = RibbonGroup(title)
        self.layout.addWidget(group)
        return group
    
    def add_stretch(self):
        self.layout.addStretch()


class RibbonTabBar(QTabBar):
    """
    Custom Tab Bar. 
    Can hold an application button logic if needed, but primarily for styling.
    """
    def __init__(self, parent=None):
        super(RibbonTabBar, self).__init__(parent)
        self.setObjectName("RibbonTabBar")
        self.setDrawBase(False) # Remove standard bottom border
        self.setShape(QTabBar.RoundedNorth)


class RibbonFileMenu(QMenu):
    """
    Application Menu (File Menu).
    """
    def __init__(self, parent=None):
        super(RibbonFileMenu, self).__init__(parent)
        self.setObjectName("RibbonFileMenu")


class RibbonWidget(QWidget):
    """
    Root Ribbon Container.
    Structure:
    - Top Area (HBox): [FileButton] [RibbonTabBar]
    - Bottom Area: QStackedWidget (Tab Content)
    """
    def __init__(self, parent=None):
        super(RibbonWidget, self).__init__(parent)
        self.setObjectName("RibbonWidget")
        
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setLayout(self.main_layout)

        # 1. Top Area (File Button + Tabs)
        self.top_container = QWidget()
        self.top_layout = QHBoxLayout()
        self.top_layout.setContentsMargins(0, 0, 0, 0)
        self.top_layout.setSpacing(0)
        self.top_container.setLayout(self.top_layout)

        # File Button
        self.file_button = QToolButton()
        self.file_button.setText("File")
        self.file_button.setObjectName("RibbonFileButton")
        self.file_button.setPopupMode(QToolButton.InstantPopup)
        self.file_menu = RibbonFileMenu(self)
        self.file_button.setMenu(self.file_menu)
        
        self.top_layout.addWidget(self.file_button)

        # Tab Bar
        self.tab_bar = RibbonTabBar()
        self.tab_bar.currentChanged.connect(self.switch_tab)
        self.top_layout.addWidget(self.tab_bar)
        
        self.top_layout.addStretch() # Push tabs to left

        self.main_layout.addWidget(self.top_container)

        # 2. Content Area
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)
        
        # Load Styles
        self.load_styles()

    def load_styles(self):
        # Attempt to load QSS from the standard location
        style_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            "ui", "styles", "ribbon.qss"
        )
        if os.path.exists(style_path):
            with open(style_path, "r") as f:
                self.setStyleSheet(f.read())

    def add_tab(self, title):
        """
        Creates a new RibbonTabContent, adds it to the stack, 
        and adds a tab to the bar.
        Returns the RibbonTabContent.
        """
        tab_content = RibbonTabContent()
        index = self.stacked_widget.addWidget(tab_content)
        self.tab_bar.addTab(title)
        return tab_content

    def add_context_tab(self, title, color):
        """
        Adds a context tab (e.g. for specific tools).
        """
        tab_content = self.add_tab(title)
        index = self.tab_bar.count() - 1
        # In a full implementation, this would adjust the painting of the tab header.
        # For now, we set text color as a hint.
        from PyQt5.QtGui import QColor
        self.tab_bar.setTabTextColor(index, QColor(color))
        return tab_content

    def switch_tab(self, index):
        self.stacked_widget.setCurrentIndex(index)

    def add_file_menu_action(self, text, callback=None, icon=None):
        action = QAction(text, self)
        if icon:
            action.setIcon(icon)
        if callback:
            action.triggered.connect(callback)
        self.file_menu.addAction(action)
        return action
