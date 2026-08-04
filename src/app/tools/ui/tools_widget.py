from qgis.PyQt.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLabel, 
    QPushButton, QFrame, QMessageBox
)
from qgis.PyQt.QtCore import Qt
from ..util.dependency_checker import DependencyChecker
from ....util import net_util
from ....util import fastapi_server
from .qr_code_dialog import QRCodeDialog

class ToolsWidget(QWidget):
    def __init__(self, parent=None):
        super(ToolsWidget, self).__init__(parent)
        self.dep_checker = DependencyChecker()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Dependency Check Group
        check_group = QGroupBox("Thư viện hệ thống")
        check_layout = QVBoxLayout()
        
        # Tippecanoe Status
        self.tippecanoe_status = QLabel("Tippecanoe: Đang kiểm tra...")
        self.tippecanoe_btn = QPushButton("Cài đặt/Sửa")
        self.tippecanoe_btn.setVisible(False)
        self.tippecanoe_btn.clicked.connect(self.install_tippecanoe)
        
        check_layout.addWidget(self.tippecanoe_status)
        check_layout.addWidget(self.tippecanoe_btn)
        
        # GDAL Status
        self.gdal_status = QLabel("GDAL: Đang kiểm tra...")
        self.gdal_help_btn = QPushButton("Trợ giúp")
        self.gdal_help_btn.setVisible(False)
        self.gdal_help_btn.clicked.connect(self.help_gdal)

        check_layout.addWidget(self.gdal_status)
        check_layout.addWidget(self.gdal_help_btn)

        check_group.setLayout(check_layout)
        layout.addWidget(check_group)
        
        # Re-check button
        check_btn = QPushButton("Kiểm tra lại")
        check_btn.clicked.connect(self.run_dependency_check)
        layout.addWidget(check_btn)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # Server Status
        layout.addWidget(QLabel("Truy cập từ xa:"))
        
        ip = net_util.get_lan_ip()
        port = fastapi_server.PORT
        url = f"{ip}:{port}"
        
        self.server_label = QLabel(f"IP: {url}")
        self.server_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.server_label)
        
        qr_btn = QPushButton("Hiện mã QR")
        qr_btn.clicked.connect(self.show_qr_code)
        layout.addWidget(qr_btn)
        
        layout.addStretch()
        self.setLayout(layout)
        
        # Run check initially
        self.run_dependency_check()

    def run_dependency_check(self):
        # Check Tippecanoe
        found_tip, msg_tip = self.dep_checker.check_tippecanoe()
        if found_tip:
            self.tippecanoe_status.setText(f"✅ Tippecanoe: {msg_tip}")
            self.tippecanoe_status.setStyleSheet("color: green")
            self.tippecanoe_btn.setVisible(False)
        else:
            self.tippecanoe_status.setText(f"❌ Tippecanoe: Không tìm thấy")
            self.tippecanoe_status.setStyleSheet("color: red")
            self.tippecanoe_btn.setVisible(True)
            self.tippecanoe_btn.setText(self.get_install_btn_text())

        # Check GDAL
        found_gdal, info_gdal = self.dep_checker.check_gdal()
        if found_gdal:
            ver = info_gdal.get('version', 'Unknown')
            mvt = "✅" if info_gdal.get('mvt_driver') else "❌"
            pmt = "✅" if info_gdal.get('pmtiles_driver') else "⚠️" 
            
            status_text = f"✅ GDAL {ver} (MVT: {mvt}, PMTiles: {pmt})"
            self.gdal_status.setText(status_text)
            self.gdal_status.setStyleSheet("color: green")
            self.gdal_help_btn.setVisible(False)
        else:
            self.gdal_status.setText(f"❌ GDAL: {info_gdal}")
            self.gdal_status.setStyleSheet("color: red")
            self.gdal_help_btn.setVisible(True)

    def get_install_btn_text(self):
        os_type = self.dep_checker.get_os_type()
        if os_type == "Windows":
            return "Cài đặt bản Portable"
        else:
            return "Xem hướng dẫn"

    def install_tippecanoe(self):
        os_type = self.dep_checker.get_os_type()
        if os_type == "Windows":
            QMessageBox.information(
                self, 
                "Cài đặt Tippecanoe",
                "Tính năng tự động cài đặt cho Windows đang được phát triển.\n"
                "Vui lòng tải tippecanoe-windows và đặt vào thư mục 'bin' của plugin."
            )
        elif os_type == "Darwin":
             QMessageBox.information(self, "Hướng dẫn cài đặt", "Vui lòng chạy lệnh sau trong terminal:\nbrew install tippecanoe")
        else:
             QMessageBox.information(self, "Hướng dẫn cài đặt", "Vui lòng cài đặt tippecanoe thông qua trình quản lý gói (apt, yum, ...)")

    def help_gdal(self):
        QMessageBox.information(
            self, 
            "Trợ giúp GDAL", 
            "GDAL thường được cài đặt cùng QGIS.\n"
            "Nếu thiếu driver, vui lòng nâng cấp QGIS hoặc cài đặt gdal-bin."
        )

    def show_qr_code(self):
        ip = net_util.get_lan_ip()
        port = fastapi_server.PORT
        address = f"{ip}:{port}"
        hint = f"TLGeo QGIS running at {address}"
        dialog = QRCodeDialog(address, hint)
        dialog.exec_()
