from qgis.PyQt.QtWidgets import QDialog, QLabel, QVBoxLayout
from qgis.PyQt.QtGui import QPixmap, QImage, QColor, QPainter
from qgis.PyQt.QtCore import Qt
import qrcode

class QRCodeDialog(QDialog):
    def __init__(self, url, hint):
        super().__init__()
        self.setWindowTitle("QR Code")
        self.setGeometry(100, 100, 300, 300)

        # Generate QR Code matrix (border=4 is standard)
        qr = qrcode.QRCode(border=4)
        qr.add_data(url)
        qr.make(fit=True)
        
        matrix = qr.modules
        size = len(matrix)
        
        # Draw QR code using pure Qt (QPainter) to avoid any PIL/Pillow dependency
        box_size = 8
        img_size = size * box_size
        
        qimg = QImage(img_size, img_size, QImage.Format_RGB32)
        qimg.fill(QColor("white"))
        
        painter = QPainter(qimg)
        painter.setBrush(QColor("darkgreen"))
        painter.setPen(Qt.NoPen)
        
        for row in range(size):
            for col in range(size):
                if matrix[row][col]:
                    painter.drawRect(col * box_size, row * box_size, box_size, box_size)
                    
        painter.end()
        pixmap = QPixmap.fromImage(qimg)

        # Add text label
        text_label = QLabel(hint, self)
        text_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        text_label.setAlignment(Qt.AlignCenter)  # Center align text

        # Add text label
        warning_label = QLabel("QGIS và Geocollect mobile phải cùng mạng LAN", self)
        warning_label.setStyleSheet("color: #AAff0000; font-size: 14px; font-style: italic;")
        warning_label.setAlignment(Qt.AlignCenter)  # Center align text

        # add hint label
        hint_label = QLabel("Quét mã QR này này để kết nối Geocollect mobile tới QGIS", self)
        hint_label.setStyleSheet("color: gray; font-size: 14px; font-style: italic;")
        hint_label.setAlignment(Qt.AlignCenter)  # Center align text
        
        # Create UI
        qr_label = QLabel(self)
        qr_label.setPixmap(pixmap)
        qr_label.setAlignment(Qt.AlignHCenter) 

         # Create UI
        layout = QVBoxLayout()
        layout.addWidget(text_label)
        layout.addWidget(hint_label)
        layout.addWidget(warning_label)
        layout.addWidget(qr_label, alignment=Qt.AlignHCenter)
        self.setLayout(layout)