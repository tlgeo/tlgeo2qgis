from qgis.PyQt.QtWidgets import QDialog, QLabel, QVBoxLayout, QHBoxLayout
from qgis.PyQt.QtGui import QPixmap, QImage
from qgis.PyQt.QtCore import Qt
import qrcode
from io import BytesIO

class QRCodeDialog(QDialog):
    def __init__(self, url, hint):
        super().__init__()
        self.setWindowTitle("QR Code")
        self.setGeometry(100, 100, 300, 300)

        # Generate QR Code
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="darkgreen", back_color="white")

        # Convert to QPixmap
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qimg = QImage.fromData(buffer.getvalue())
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