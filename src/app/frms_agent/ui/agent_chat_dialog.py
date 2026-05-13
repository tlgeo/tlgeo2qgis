from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import traceback


class AgentWorker(QThread):
    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, query, parent=None):
        super().__init__(parent)
        self.query = query

    def run(self):
        try:
            import os
            import sys

            agent_module_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            if agent_module_path not in sys.path:
                sys.path.insert(0, agent_module_path)

            from src.app.frms_agent.agent import run as agent_run
            response = agent_run(self.query, thread_id="frms_ui")
            self.response_ready.emit(response)
        except Exception as e:
            error_msg = f"Lỗi: {str(e)}\n{traceback.format_exc()}"
            self.error_occurred.emit(error_msg)


class AgentChatDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FRMS Agent - Hỏi đáp")
        self.setGeometry(100, 100, 700, 500)
        self.worker = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        header = QLabel("🤖 FRMS Agent - Trợ lý thông minh", self)
        header.setFont(QFont("Arial", 12, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        self.chat_area = QTextEdit(self)
        self.chat_area.setReadOnly(True)
        self.chat_area.setFont(QFont("Arial", 10))
        self.chat_area.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                min-height: 300px;
            }
        """)
        layout.addWidget(self.chat_area)

        input_layout = QHBoxLayout()
        self.input_field = QLineEdit(self)
        self.input_field.setPlaceholderText("Nhập câu hỏi của bạn...")
        self.input_field.setFont(QFont("Arial", 10))
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)

        self.send_button = QPushButton("Gửi", self)
        self.send_button.setFixedWidth(80)
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)

        layout.addLayout(input_layout)

        self.status_label = QLabel("", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(self.status_label)

        self.setLayout(layout)
        self.welcome_message()

    def welcome_message(self):
        self.chat_area.append("<div style='color: #0066cc;'>"
                             "<b>🤖 Xin chào!</b><br/>"
                             "Tôi là FRMS Agent, trợ lý thông minh cho hệ thống quản lý tài nguyên rừng.<br/>"
                             "Bạn có thể hỏi tôi về:<br/>"
                             "• Lô rừng (plots)<br/>"
                             "• Chủ rừng (owners)<br/>"
                             "• Diễn biến rừng (changes)<br/>"
                             "• Báo cáo và thống kê<br/><br/>"
                             "<i style='color: #888;'>Đang kết nối với cơ sở dữ liệu FRMS...</i>"
                             "</div>")

    def send_message(self):
        query = self.input_field.text().strip()
        if not query:
            return

        if self.worker is not None and self.worker.isRunning():
            self.status_label.setText("⚠️ Đang xử lý câu trả lời trước...")
            return

        self.chat_area.append(f"<div style='color: #333;'><b>👤 Bạn:</b><br/>{query}</div>")
        self.input_field.clear()
        self.send_button.setEnabled(False)
        self.status_label.setText("⏳ Đang xử lý...")

        self.remove_last_processing_message()

        self.worker = AgentWorker(query, self)
        self.worker.response_ready.connect(self.on_response_ready)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.start()

    def remove_last_processing_message(self):
        cursor = self.chat_area.textCursor()
        cursor.movePosition(cursor.End)
        cursor.select(cursor.LineUnderCursor)
        cursor.removeSelectedText()
        cursor.deleteChar()
        self.chat_area.setTextCursor(cursor)

    def on_response_ready(self, response):
        self.remove_last_processing_message()
        self.chat_area.append(f"<div style='color: #006600;'><b>🤖 Agent:</b><br/>{response}</div>")
        self.send_button.setEnabled(True)
        self.status_label.setText("")
        self.worker = None

    def on_error(self, error_msg):
        self.remove_last_processing_message()
        self.chat_area.append(f"<div style='color: #cc0000;'><b>❌ Lỗi:</b><br/>{error_msg}</div>")
        self.send_button.setEnabled(True)
        self.status_label.setText("❌ Có lỗi xảy ra")
        self.worker = None