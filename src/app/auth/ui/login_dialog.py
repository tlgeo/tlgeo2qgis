"""
Login Dialog for TLGeo2QGIS Plugin
Provides authentication UI for GEOADMIN Strapi
"""

import os
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QMessageBox, QCheckBox
)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QPixmap, QIcon
from ..util.auth_service import AuthService


class LoginDialog(QDialog):
    """
    Login dialog for GEOADMIN authentication
    """
    
    def __init__(self, parent=None):
        """
        Initialize login dialog
        
        Args:
            parent: Parent widget (usually QGIS main window)
        """
        from tlgeo2qgis.util.i18n import tr
        super().__init__(parent)
        self.auth_service = AuthService()
        self.setWindowTitle(tr("Login TLGeo2QGIS"))
        self.setMinimumWidth(400)
        self.setModal(True)
        
        # Initialize UI
        self.init_ui()
        
        # Check HTTPS security
        security_warning = self.auth_service.check_https_security()
        if security_warning:
            QMessageBox.warning(self, tr("Security Warning"), security_warning)
    
    def init_ui(self):
        """Setup UI components"""
        from tlgeo2qgis.util.i18n import tr
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        
        # Logo section (if exists)
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logo.png')
        if os.path.exists(logo_path):
            logo_label = QLabel()
            pixmap = QPixmap(logo_path)
            # Scale logo to reasonable size
            scaled_pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(logo_label)
        
        # Title
        title_label = QLabel(tr("Login GEOADMIN"))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px 0;")
        main_layout.addWidget(title_label)
        
        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Email/Username input
        self.identifier_input = QLineEdit()
        self.identifier_input.setPlaceholderText(tr("Email or username"))
        self.identifier_input.returnPressed.connect(self.on_login_clicked)
        form_layout.addRow(tr("Account:"), self.identifier_input)
        
        # Password input
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText(tr("Password"))
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.returnPressed.connect(self.on_login_clicked)
        form_layout.addRow(tr("Password:"), self.password_input)
        
        main_layout.addLayout(form_layout)
        
        # Remember me checkbox (optional feature)
        # self.remember_checkbox = QCheckBox("Ghi nhớ đăng nhập")
        # self.remember_checkbox.setChecked(True)
        # main_layout.addWidget(self.remember_checkbox)
        
        # Error message label
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red; font-size: 12px;")
        self.error_label.setWordWrap(True)
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.hide()
        main_layout.addWidget(self.error_label)
        
        # Buttons layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Login button
        self.login_button = QPushButton(tr("Login"))
        self.login_button.setDefault(True)
        self.login_button.clicked.connect(self.on_login_clicked)
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #1890ff;
                color: white;
                border: none;
                padding: 8px 20px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
            QPushButton:pressed {
                background-color: #096dd9;
            }
            QPushButton:disabled {
                background-color: #d9d9d9;
                color: #8c8c8c;
            }
        """)
        button_layout.addWidget(self.login_button)
        
        # Cancel button
        self.cancel_button = QPushButton(tr("Cancel"))
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #595959;
                border: 1px solid #d9d9d9;
                padding: 8px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                color: #40a9ff;
                border-color: #40a9ff;
            }
        """)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
        
        # Server info
        server_label = QLabel(f"Server: {self.auth_service.strapi_url}")
        server_label.setStyleSheet("color: #8c8c8c; font-size: 10px;")
        server_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(server_label)
        
        self.setLayout(main_layout)
    
    def on_login_clicked(self):
        """Handle login button click"""
        from tlgeo2qgis.util.i18n import tr
        # Validate inputs
        identifier = self.identifier_input.text().strip()
        password = self.password_input.text()
        
        if not identifier:
            self.show_error(tr("Please enter email or username"))
            self.identifier_input.setFocus()
            return
        
        if not password:
            self.show_error(tr("Please enter password"))
            self.password_input.setFocus()
            return
        
        # Show loading state
        self.set_loading(True)
        self.error_label.hide()
        
        # Attempt login
        result = self.auth_service.login(identifier, password)
        
        # Clear password field for security
        self.password_input.clear()
        
        # Handle result
        if result['success']:
            self.set_loading(False)
            self.accept()  # Close dialog with success
        else:
            self.set_loading(False)
            error_message = result.get('error', tr("Login failed"))
            self.show_error(error_message)
    
    def show_error(self, message: str):
        """
        Display error message
        
        Args:
            message: Error message to display
        """
        self.error_label.setText(message)
        self.error_label.show()
    
    def set_loading(self, loading: bool):
        """
        Set loading state for UI
        
        Args:
            loading: True to show loading state, False to normal state
        """
        from tlgeo2qgis.util.i18n import tr
        self.login_button.setEnabled(not loading)
        self.cancel_button.setEnabled(not loading)
        self.identifier_input.setEnabled(not loading)
        self.password_input.setEnabled(not loading)
        
        if loading:
            self.login_button.setText(tr("Logging in..."))
        else:
            self.login_button.setText(tr("Login"))
