from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit
from qgis.PyQt.QtCore import Qt, QUrl
from qgis.PyQt.QtGui import QDesktopServices

class GDALUpdateDialog(QDialog):
    """Dialog to prompt user for GDAL update"""
    
    def __init__(self, current_gdal_version, parent=None):
        super().__init__(parent)
        self.current_version = current_gdal_version
        self.user_choice = None
        
        self.setWindowTitle("Cập nhật GDAL")
        self.setMinimumSize(600, 450)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Title
        title = QLabel(f"⚠️ GDAL {self.current_version} không hỗ trợ đầy đủ MBTiles/PMTiles")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #d32f2f; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Description
        desc = QLabel()
        desc.setWordWrap(True)
        desc.setText(
            "Để xuất ra định dạng MBTiles hoặc PMTiles (Cloud-Native), plugin cần phiên bản GDAL mới hơn:\n"
            "• MBTiles: Yêu cầu GDAL 3.1+ (tốt nhất 3.6+)\n"
            "• PMTiles: Yêu cầu GDAL 3.8.0+ (phát hành 11/2023)"
        )
        desc.setStyleSheet("font-size: 13px; margin-bottom: 10px;")
        layout.addWidget(desc)
        
        layout.addWidget(QLabel("Vui lòng chọn một giải pháp:"))
        
        # Option 1: Auto install (Future feature - currently disabled or placeholder)
        # For Phase 1, we might disable this or show it as "Coming Soon" if installer isn't ready
        # But per requirements, let's add the button.
        
        btn_auto = QPushButton("📥 [Khuyến nghị] Cài đặt GDAL 3.8.3 tự động")
        btn_auto.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                color: white; 
                padding: 10px; 
                font-weight: bold;
                font-size: 14px;
                text-align: left;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        btn_auto.clicked.connect(lambda: self.set_choice("auto_install"))
        layout.addWidget(btn_auto)
        
        auto_note = QLabel("  → Tải và cài đặt GDAL 3.8.3 vào thư mục người dùng\n  → Không cần quyền admin\n  → Thời gian: ~5-10 phút")
        auto_note.setStyleSheet("color: #666; margin-left: 10px; font-size: 12px;")
        layout.addWidget(auto_note)
        
        # Option 2: Download QGIS
        btn_qgis_layout = QHBoxLayout()
        
        btn_qgis_ltr = QPushButton("📥 Tải QGIS 3.28 LTR")
        btn_qgis_ltr.setStyleSheet("padding: 8px;")
        btn_qgis_ltr.clicked.connect(lambda: self.set_choice("download_qgis_ltr"))
        btn_qgis_layout.addWidget(btn_qgis_ltr)
        
        btn_qgis_latest = QPushButton("📥 Tải QGIS 3.34+")
        btn_qgis_latest.setStyleSheet("padding: 8px;")
        btn_qgis_latest.clicked.connect(lambda: self.set_choice("download_qgis_latest"))
        btn_qgis_layout.addWidget(btn_qgis_latest)
        
        layout.addLayout(btn_qgis_layout)
        
        qgis_note = QLabel("  → Nâng cấp QGIS lên bản mới nhất (ổn định nhất)\n  → QGIS 3.28: Hỗ trợ MBTiles\n  → QGIS 3.34+: Hỗ trợ cả PMTiles")
        qgis_note.setStyleSheet("color: #666; margin-left: 10px; font-size: 12px;")
        layout.addWidget(qgis_note)
        
        # Option 3: Use SQLite
        btn_sqlite = QPushButton("📄 Xem hướng dẫn dùng SQLite thay thế")
        btn_sqlite.setStyleSheet("padding: 8px; text-align: left;")
        btn_sqlite.clicked.connect(lambda: self.set_choice("use_sqlite"))
        layout.addWidget(btn_sqlite)
        
        sqlite_note = QLabel("  → Export sang SQLite (hoạt động trên mọi version)\n  → Dùng tool bên ngoài (tippecanoe) convert sang MBTiles")
        sqlite_note.setStyleSheet("color: #666; margin-left: 10px; font-size: 12px;")
        layout.addWidget(sqlite_note)
        
        layout.addStretch()
        
        # Cancel button
        btn_cancel = QPushButton("Đóng")
        btn_cancel.clicked.connect(self.reject)
        layout.addWidget(btn_cancel)
        
        self.setLayout(layout)
    
    def set_choice(self, choice):
        """Set user choice and close dialog"""
        self.user_choice = choice
        self.accept()
    
    def get_choice(self):
        """Get user's choice after dialog closes"""
        return self.user_choice
