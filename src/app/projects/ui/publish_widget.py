from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt
from qgis.core import QgsVectorLayer, QgsApplication
from ..util.project_service import ProjectService
from ..tasks.layer_publish_task import LayerPublishTask

class PublishWidget(QWidget):
    def __init__(self, parent=None):
        super(PublishWidget, self).__init__(parent)
        self.project_service = ProjectService()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Trạng thái lớp đang chọn:"))
        
        # Status Label
        self.status_label = QLabel("Chưa chọn lớp nào")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("border: 1px dashed gray; padding: 20px;")
        layout.addWidget(self.status_label)
        
        # Refresh Selection Button
        refresh_btn = QPushButton("Làm mới lớp")
        refresh_btn.clicked.connect(self.check_active_layer)
        layout.addWidget(refresh_btn)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Action buttons
        btn_layout = QHBoxLayout()
        self.publish_btn = QPushButton("Xuất bản lớp")
        self.publish_btn.setEnabled(False)
        self.publish_btn.clicked.connect(self.start_publish_task)
        btn_layout.addWidget(self.publish_btn)
        
        layout.addLayout(btn_layout)
        layout.addStretch()
        
        self.setLayout(layout)

    def check_active_layer(self):
        from qgis.utils import iface
        if not iface:
            self.status_label.setText("Giao diện không khả dụng")
            return

        layer = iface.activeLayer()
        if not layer:
            self.status_label.setText("Chưa chọn lớp nào")
            self.publish_btn.setEnabled(False)
            return
            
        if layer.type() != QgsVectorLayer.VectorLayer:
             self.status_label.setText(f"Lớp '{layer.name()}' không phải là lớp vector")
             self.publish_btn.setEnabled(False)
             return
             
        self.status_label.setText(f"Sẵn sàng xuất bản: {layer.name()}\nCRS: {layer.crs().authid()}\nSố lượng đối tượng: {layer.featureCount()}")
        self.status_label.setStyleSheet("border: 1px solid green; padding: 20px; color: green;")
        self.publish_btn.setEnabled(True)

    def start_publish_task(self):
        from qgis.utils import iface
        if not iface:
            return
            
        layer = iface.activeLayer()
        if not layer:
            return
            
        if not self.project_service.auth_service.is_authenticated():
            QMessageBox.warning(self, "Lỗi xác thực", "Vui lòng đăng nhập trước.")
            return

        self.publish_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        token = self.project_service.auth_service.get_token()
        strapi_url = self.project_service.strapi_url
        
        self.task = LayerPublishTask(layer, token, strapi_url)
        
        self.task.progressChanged.connect(self.progress_bar.setValue)
        self.task.status_changed.connect(lambda s: self.status_label.setText(s))
        self.task.upload_complete.connect(self.on_publish_complete)
        self.task.error_occurred.connect(self.on_publish_error)
        self.task.taskCompleted.connect(self.on_task_finished)
        
        QgsApplication.taskManager().addTask(self.task)
        
    def on_publish_complete(self, project_id):
        self.status_label.setText(f"Xuất bản thành công!\nID Dự án: {project_id}")
        self.status_label.setStyleSheet("border: 1px solid green; padding: 20px; color: green; font-weight: bold;")
        self.progress_bar.setValue(100)
        QMessageBox.information(self, "Thành công", "Lớp đã được xuất bản thành công!")
        
    def on_publish_error(self, error):
        self.status_label.setText(f"Lỗi: {error}")
        self.status_label.setStyleSheet("border: 1px solid red; padding: 20px; color: red;")
        self.progress_bar.setVisible(False)
        
    def on_task_finished(self):
        self.publish_btn.setEnabled(True)
