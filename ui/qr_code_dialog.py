from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout, QHBoxLayout
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
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
        img = qr.make_image(fill='black', back_color='white')

        # Convert to QPixmap
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qimg = QImage.fromData(buffer.getvalue())
        pixmap = QPixmap.fromImage(qimg)

       

        # Add text label
        text_label = QLabel(hint, self)
        text_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        text_label.setAlignment(Qt.AlignCenter)  # Center align text

        # Create UI
        qr_label = QLabel(self)
        qr_label.setPixmap(pixmap)
        qr_label.setAlignment(Qt.AlignHCenter) 

         # Create UI
        layout = QVBoxLayout()
        layout.addWidget(text_label)
        layout.addWidget(qr_label, alignment=Qt.AlignHCenter)
        self.setLayout(layout)