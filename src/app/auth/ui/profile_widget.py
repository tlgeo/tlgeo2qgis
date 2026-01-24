from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QPushButton, QMessageBox
)
from PyQt5.QtCore import pyqtSignal
from ..util.auth_service import AuthService

class ProfileWidget(QWidget):
    user_logged_out = pyqtSignal()
    
    def __init__(self, parent=None):
        super(ProfileWidget, self).__init__(parent)
        self.auth_service = AuthService()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        self.profile_content = QTextEdit()
        self.profile_content.setReadOnly(True)
        layout.addWidget(self.profile_content)
        
        refresh_btn = QPushButton("Làm mới")
        refresh_btn.clicked.connect(self.load_profile)
        layout.addWidget(refresh_btn)
        
        logout_btn = QPushButton("Đăng xuất")
        logout_btn.clicked.connect(self.logout_requested)
        layout.addWidget(logout_btn)
        
        self.setLayout(layout)
        
        # Initial load if authenticated
        if self.auth_service.is_authenticated():
            self.load_profile()
        else:
             self.profile_content.setHtml("<i>Chưa đăng nhập</i>")

    def load_profile(self):
        user = self.auth_service.get_current_user()
        if not user:
            self.profile_content.setHtml("<i>Chưa đăng nhập</i>")
            return
            
        info_html = f"""
        <h3>Thông tin người dùng</h3>
        <table style="width: 100%; border-collapse: collapse;">
            <tr><td style="font-weight: bold;">ID:</td><td>{user.get('id', 'N/A')}</td></tr>
            <tr style="background-color: #f5f5f5;"><td style="font-weight: bold;">Tên đăng nhập:</td><td>{user.get('username', 'N/A')}</td></tr>
            <tr><td style="font-weight: bold;">Email:</td><td>{user.get('email', 'N/A')}</td></tr>
            <tr style="background-color: #f5f5f5;"><td style="font-weight: bold;">Họ tên:</td><td>{user.get('fullname', 'N/A')}</td></tr>
        """
        
        if user.get('phoneNumber'):
            info_html += f"<tr><td style='font-weight: bold;'>Điện thoại:</td><td>{user.get('phoneNumber')}</td></tr>"
        if user.get('department'):
            info_html += f"<tr style='background-color: #f5f5f5;'><td style='font-weight: bold;'>Phòng ban:</td><td>{user.get('department')}</td></tr>"
        if user.get('job_title'):
             info_html += f"<tr><td style='font-weight: bold;'>Chức danh:</td><td>{user.get('job_title')}</td></tr>"
             
        info_html += "</table>"
        self.profile_content.setHtml(info_html)

    def logout_requested(self):
        reply = QMessageBox.question(
            self, "Đăng xuất", "Bạn có chắc chắn muốn đăng xuất không?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.auth_service.logout()
            self.profile_content.setHtml("<i>Đã đăng xuất</i>")
            QMessageBox.information(self, "Đăng xuất", "Đăng xuất thành công.")
            self.user_logged_out.emit()
