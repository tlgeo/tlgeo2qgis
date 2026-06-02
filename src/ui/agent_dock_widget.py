from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import traceback
import os
import json
import logging
import asyncio
import websockets

def setup_logging():
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    log_dir = os.path.join(base_path, "src", "app", "frms_agent", "agents", "logs")
    os.makedirs(log_dir, exist_ok=True)

    agent_logger = logging.getLogger("qgis.chat_ui")
    agent_logger.setLevel(logging.INFO)
    if not agent_logger.handlers:
        handler = logging.FileHandler(os.path.join(log_dir, "chat_ui.log"))
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        agent_logger.addHandler(handler)
    return agent_logger


class AgentWorker(QThread):
    """
    Lightweight worker thread that connects to the external backend Agent server
    via WebSocket, sends the query, and forwards intermediate status updates and 
    the final response back to the main thread.
    """
    response_ready = pyqtSignal(str)
    status_updated = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, query, thread_id="qgis_dock_ui", parent=None):
        super().__init__(parent)
        self.query = query
        self.thread_id = thread_id
        self.logger = setup_logging()

    def run(self):
        try:
            self.logger.info(f"QGIS DOCK REQUEST: {self.query}")
            
            # Start event loop inside QThread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run websocket communication
            loop.run_until_complete(self.communicate())
            loop.close()
            
        except Exception as e:
            error_msg = f"Không thể kết nối tới Server: {str(e)}"
            self.logger.error(f"ERROR: {error_msg}\n{traceback.format_exc()}")
            self.error_occurred.emit(error_msg)

    async def communicate(self):
        # Default backend Agent URL
        ws_url = "ws://localhost:13001/ws/ui"
        
        async with websockets.connect(ws_url, ping_interval=20, ping_timeout=10) as ws:
            # Send the user query formatted as a standard JSON request
            payload = {
                "type": "query",
                "query": self.query,
                "thread_id": self.thread_id
            }
            await ws.send(json.dumps(payload))
            
            # Read incoming websocket events from server
            async for message in ws:
                data = json.loads(message)
                msg_type = data.get("type")
                
                if msg_type == "status":
                    status_content = data.get("content", "")
                    if status_content == "thinking":
                        self.status_updated.emit("⏳ Trợ lý đang suy nghĩ...")
                    else:
                        # Forward GIS tool execution statuses (e.g., "🛠️ Đang chạy công cụ GIS: ...")
                        self.status_updated.emit(status_content)
                        
                elif msg_type == "chat_response":
                    content = data.get("content", "")
                    self.response_ready.emit(content)
                    break


class AgentChatWidget(QWidget):
    """
    Thin Chat Client UI running inside QGIS DockWidget.
    Tunnels user prompts directly to the external Deep Agent backend.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.thread_counter = 0
        self.chat_history = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        header = QLabel("🤖 TLGeo Agent - Trợ lý thông minh")
        header.setFont(QFont("Arial", 11, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setFont(QFont("Arial", 10))
        self.chat_area.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.chat_area)

        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Nhập yêu cầu tương tác QGIS...")
        self.input_field.setFont(QFont("Arial", 10))
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)

        self.send_button = QPushButton("Gửi")
        self.send_button.setFixedWidth(70)
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)

        layout.addLayout(input_layout)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #0284c7; font-size: 10px; font-weight: bold; font-style: italic;")
        layout.addWidget(self.status_label)

        self.setLayout(layout)
        self.welcome_message()

    def welcome_message(self):
        self.chat_area.append("<div style='color: #0ea5e9; font-family: sans-serif;'>"
                             "<b>🤖 Xin chào!</b><br/>"
                             "Tôi là <b>TLGeo Deep Agent</b>. Tôi có thể tương tác trực tiếp với bản đồ của bạn!<br/>"
                             "Hãy thử hỏi tôi:<br/>"
                             "• <i>\"Zoom tới lớp Lô Rừng\"</i><br/>"
                             "• <i>\"Chọn các thửa đất diện tích lớn hơn 10 ha\"</i><br/>"
                             "• <i>\"Highlight các lô của ông Nguyễn Văn A\"</i><br/>"
                             "• <i>\"Ẩn lớp ranh giới xã đi\"</i><br/>"
                             "</div>")

    def send_message(self):
        query = self.input_field.text().strip()
        if not query:
            return

        if self.worker is not None and self.worker.isRunning():
            self.status_label.setText("⚠️ Đang bận xử lý...")
            return

        self.chat_area.append(f"<div style='color: #333;'><b>👤 Bạn:</b><br/>{query}</div>")
        self.input_field.clear()
        self.send_button.setEnabled(False)
        self.status_label.setText("⏳ Đang kết nối tới server...")

        self.thread_counter += 1
        thread_id = f"qgis_dock_{self.thread_counter}"

        self.worker = AgentWorker(query, thread_id, self)
        self.worker.response_ready.connect(self.on_response_ready, Qt.QueuedConnection)
        self.worker.status_updated.connect(self.on_status_updated, Qt.QueuedConnection)
        self.worker.error_occurred.connect(self.on_error, Qt.QueuedConnection)
        self.worker.start()

    def on_status_updated(self, status):
        self.status_label.setText(status)

    def on_response_ready(self, response):
        # Format code blocks and bold items a bit nicer in PyQt QTextEdit
        formatted_response = response.replace("\n", "<br/>")
        self.chat_area.append(f"<div style='color: #0369a1;'><b>🤖 Agent:</b><br/>{formatted_response}</div>")
        self.send_button.setEnabled(True)
        self.status_label.setText("")
        self.worker = None

    def on_error(self, error_msg):
        self.chat_area.append(f"<div style='color: #ef4444;'><b>❌ Lỗi:</b><br/>{error_msg}</div>")
        self.send_button.setEnabled(True)
        self.status_label.setText("❌ Có lỗi xảy ra")
        self.worker = None