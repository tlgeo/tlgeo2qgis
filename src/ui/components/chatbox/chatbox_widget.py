import os
import re
from qgis.PyQt.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                QPushButton, QScrollArea, QFrame, QLineEdit, 
                                QStyle, QApplication)
from qgis.PyQt.QtCore import Qt, pyqtSignal, QTimer
from ....util.i18n import tr
from ....app.auth.util.auth_service import AuthService
from .chat_worker import ChatWSWorker

def format_to_html(text):
    """Simple markdown/plain-text to HTML formatter."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace("&lt;think&gt;", "<think>").replace("&lt;/think&gt;", "</think>")
    
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
    text = text.replace("\n", "<br>")
    return text

def parse_thinking(text):
    """Extract <think>...</think> content and clean the main response text."""
    thinking = ""
    cleaned = ""
    remaining = text
    
    while True:
        start = remaining.find("<think>")
        if start == -1:
            cleaned += remaining
            break
        cleaned += remaining[:start]
        end = remaining.find("</think>", start)
        if end == -1:
            thinking += remaining[start+7:]
            break
        thinking += remaining[start+7:end]
        remaining = remaining[end+8:]
        
    return thinking.strip(), cleaned.strip()

class MessageBubble(QWidget):
    """
    Styled message bubble representing a chat message.
    """
    def __init__(self, role, text="", parent=None):
        super().__init__(parent)
        self.role = role
        self.text = text
        
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(main_layout)
        
        self.bubble_frame = QFrame()
        bubble_layout = QVBoxLayout()
        bubble_layout.setContentsMargins(10, 8, 10, 8)
        bubble_layout.setSpacing(6)
        self.bubble_frame.setLayout(bubble_layout)
        
        self.thinking_frame = QFrame()
        self.thinking_frame.setVisible(False)
        self.thinking_frame.setStyleSheet("""
            QFrame {
                background-color: #fafafa;
                border: 1px dashed #dcdfe6;
                border-radius: 6px;
                padding: 6px;
            }
        """)
        thinking_layout = QVBoxLayout()
        thinking_layout.setContentsMargins(4, 4, 4, 4)
        self.thinking_frame.setLayout(thinking_layout)
        
        self.thinking_title = QLabel("<b>" + tr("Thinking:") + "</b>")
        self.thinking_title.setStyleSheet("color: #909399; font-size: 11px;")
        self.thinking_label = QLabel()
        self.thinking_label.setWordWrap(True)
        self.thinking_label.setStyleSheet("color: #7f8c8d; font-size: 11px; font-style: italic;")
        thinking_layout.addWidget(self.thinking_title)
        thinking_layout.addWidget(self.thinking_label)
        
        self.main_label = QLabel()
        self.main_label.setWordWrap(True)
        self.main_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
        self.main_label.setOpenExternalLinks(True)
        
        if role == "user":
            main_layout.addStretch()
            main_layout.addWidget(self.bubble_frame)
            self.bubble_frame.setStyleSheet("""
                QFrame {
                    background-color: #e8f0fe;
                    border: 1px solid #d2e3fc;
                    border-radius: 12px;
                }
            """)
            self.main_label.setStyleSheet("color: #1a73e8; font-size: 13px;")
            bubble_layout.addWidget(self.main_label)
        else:
            main_layout.addWidget(self.bubble_frame)
            main_layout.addStretch()
            self.bubble_frame.setStyleSheet("""
                QFrame {
                    background-color: #f1f3f4;
                    border: 1px solid #e8eaed;
                    border-radius: 12px;
                }
            """)
            self.main_label.setStyleSheet("color: #3c4043; font-size: 13px; line-height: 1.4;")
            
            bubble_layout.addWidget(self.thinking_frame)
            bubble_layout.addWidget(self.main_label)
            
        self.update_content(text)
        
    def update_content(self, text):
        self.text = text
        if self.role == "user":
            self.main_label.setText(format_to_html(text))
        else:
            thinking, cleaned = parse_thinking(text)
            
            if thinking:
                self.thinking_label.setText(format_to_html(thinking))
                self.thinking_frame.setVisible(True)
            else:
                self.thinking_frame.setVisible(False)
                
            self.main_label.setText(format_to_html(cleaned) if cleaned else "...")

class ChatBox(QWidget):
    """
    Reusable ChatBox widget component.
    """
    reload_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super(ChatBox, self).__init__(parent)
        self.auth_service = AuthService()
        self.thread_id = "qgis_ui_" + os.urandom(4).hex()
        
        self.worker = None
        self.is_generating = False
        self.current_bot_text = ""
        self.last_bot_bubble = None
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)
        self.setLayout(main_layout)
        
        # 1. Top toolbar
        toolbar_layout = QHBoxLayout()
        
        self.status_title = QLabel("<b>" + tr("Status:") + "</b>")
        self.status_title.setStyleSheet("font-size: 12px; color: #333333;")
        toolbar_layout.addWidget(self.status_title)
        
        self.status_val_label = QLabel(tr("Disconnected"))
        self.status_val_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #c62828;")
        toolbar_layout.addWidget(self.status_val_label)
        
        # Reload Button
        self.btn_reload = QPushButton()
        self.btn_reload.setToolTip(tr("Refresh connection and profile"))
        self.btn_reload.setIcon(QApplication.style().standardIcon(QStyle.SP_BrowserReload))
        self.btn_reload.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 2px;
                min-width: 20px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #e5e5e5;
            }
        """)
        self.btn_reload.clicked.connect(self.reload_clicked.emit)
        toolbar_layout.addWidget(self.btn_reload)
        
        toolbar_layout.addStretch()
        
        # New Chat Button
        self.btn_new_chat = QPushButton()
        self.btn_new_chat.setToolTip(tr("New Chat"))
        self.btn_new_chat.setIcon(QApplication.style().standardIcon(QStyle.SP_FileIcon))
        self.btn_new_chat.setStyleSheet("QPushButton { background: transparent; border: none; padding: 4px; } QPushButton:hover { background: #e5e5e5; border-radius: 4px; }")
        self.btn_new_chat.clicked.connect(self.new_chat)
        toolbar_layout.addWidget(self.btn_new_chat)
        
        # Clear History Button
        self.btn_clear = QPushButton()
        self.btn_clear.setToolTip(tr("Clear History"))
        self.btn_clear.setIcon(QApplication.style().standardIcon(QStyle.SP_TrashIcon))
        self.btn_clear.setStyleSheet("QPushButton { background: transparent; border: none; padding: 4px; } QPushButton:hover { background: #e5e5e5; border-radius: 4px; }")
        self.btn_clear.clicked.connect(self.clear_chat)
        toolbar_layout.addWidget(self.btn_clear)
        
        main_layout.addLayout(toolbar_layout)
        
        # 2. Message Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.StyledPanel)
        self.scroll_area.setStyleSheet("QScrollArea { background-color: #ffffff; border: 1px solid #dadce0; border-radius: 8px; }")
        
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background-color: #ffffff;")
        self.messages_layout = QVBoxLayout()
        self.messages_layout.setContentsMargins(10, 10, 10, 10)
        self.messages_layout.setSpacing(10)
        self.scroll_content.setLayout(self.messages_layout)
        self.scroll_area.setWidget(self.scroll_content)
        
        self.messages_layout.addStretch()
        main_layout.addWidget(self.scroll_area)
        
        # 3. Status Logs / Activity text
        self.activity_label = QLabel()
        self.activity_label.setWordWrap(True)
        self.activity_label.setStyleSheet("color: #0b57d0; font-size: 11px; font-style: italic; padding-left: 5px;")
        self.activity_label.setVisible(False)
        main_layout.addWidget(self.activity_label)
        
        # 4. Input layout
        input_layout = QHBoxLayout()
        input_layout.setSpacing(6)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(tr("Hỏi TLGeo Agent..."))
        self.input_field.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dadce0;
                border-radius: 16px;
                padding: 6px 12px;
                font-size: 13px;
                background-color: #ffffff;
            }
            QLineEdit:focus {
                border: 1px solid #1a73e8;
            }
        """)
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        
        # Send Button
        self.btn_send = QPushButton()
        self.btn_send.setToolTip(tr("Send message"))
        self.btn_send.setIcon(QApplication.style().standardIcon(QStyle.SP_DialogOkButton))
        self.btn_send.setStyleSheet("""
            QPushButton {
                background-color: #1a73e8;
                border: none;
                border-radius: 16px;
                padding: 6px;
                min-width: 32px;
                min-height: 32px;
            }
            QPushButton:hover {
                background-color: #1557b0;
            }
        """)
        self.btn_send.clicked.connect(self.send_message)
        input_layout.addWidget(self.btn_send)
        
        # Stop Button (Hidden by default)
        self.btn_stop = QPushButton()
        self.btn_stop.setToolTip(tr("Stop Thinking"))
        self.btn_stop.setIcon(QApplication.style().standardIcon(QStyle.SP_MediaStop))
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #c62828;
                border: none;
                border-radius: 16px;
                padding: 6px;
                min-width: 32px;
                min-height: 32px;
            }
            QPushButton:hover {
                background-color: #b71c1c;
            }
        """)
        self.btn_stop.setVisible(False)
        self.btn_stop.clicked.connect(self.stop_thinking)
        input_layout.addWidget(self.btn_stop)
        
        main_layout.addLayout(input_layout)
        
        # Add Welcome Guide
        self.add_welcome_message()
        
        # Connect websocket
        QTimer.singleShot(100, self.connect_websocket)

    def connect_websocket(self):
        """Initialize the background websocket worker."""
        if self.worker:
            self.worker.stop()
            self.worker.wait()
            self.worker = None
            
        token = self.auth_service.get_token()
        agent_url = os.getenv("TLGEO_AGENT_URL", "wss://agent.tlgeo.net/ws/qgis")
        ws_url = agent_url.replace("/ws/qgis", "/ws/ui")
        
        self.worker = ChatWSWorker(ws_url, token, self.thread_id)
        self.worker.connection_changed.connect(self.set_connection_status)
        self.worker.message_received.connect(self.on_message_received)
        self.worker.auth_failed.connect(self.on_auth_failed)
        self.worker.start()

    def set_connection_status(self, connected):
        """Update connection status label."""
        if connected:
            self.status_val_label.setText(tr("Connected"))
            self.status_val_label.setStyleSheet("color: #2e7d32; font-weight: bold;")
        else:
            self.status_val_label.setText(tr("Disconnected"))
            self.status_val_label.setStyleSheet("color: #c62828; font-weight: bold;")

    def on_auth_failed(self, error_msg):
        self.activity_label.setText(error_msg)
        self.activity_label.setVisible(True)

    def on_message_received(self, data):
        """Process incoming websocket messages."""
        msg_type = data.get("type")
        
        if msg_type == "status":
            content = data.get("content", "")
            if content:
                # Clean up system symbols
                clean_text = content.replace("🛠️", "").replace("🔧", "").strip()
                self.activity_label.setText(clean_text + "...")
                self.activity_label.setVisible(True)
                
        elif msg_type == "chat_chunk":
            self.activity_label.setVisible(False)
            chunk = data.get("content", "")
            self.current_bot_text += chunk
            if self.last_bot_bubble:
                self.last_bot_bubble.update_content(self.current_bot_text)
            self.scroll_to_bottom()
            
        elif msg_type == "chat_response":
            self.activity_label.setVisible(False)
            self.current_bot_text = data.get("content", "")
            if self.last_bot_bubble:
                self.last_bot_bubble.update_content(self.current_bot_text)
            self.is_generating = False
            self.update_ui_states()
            self.scroll_to_bottom()

    def send_message(self):
        text = self.input_field.text().strip()
        if not text:
            return
        if self.is_generating:
            return
            
        # Add User bubble
        user_bubble = MessageBubble("user", text)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, user_bubble)
        self.input_field.clear()
        
        # Prepare state for Bot streaming
        self.is_generating = True
        self.current_bot_text = ""
        self.last_bot_bubble = MessageBubble("bot", "")
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, self.last_bot_bubble)
        
        self.update_ui_states()
        self.scroll_to_bottom()
        
        if self.worker:
            self.worker.send_message(text)

    def stop_thinking(self):
        if self.worker:
            self.worker.stop_generation()
        self.is_generating = False
        self.update_ui_states()

    def new_chat(self):
        self.thread_id = "qgis_ui_" + os.urandom(4).hex()
        self.clear_chat()
        self.connect_websocket()

    def clear_chat(self):
        while self.messages_layout.count() > 1:
            child = self.messages_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.add_welcome_message()
        self.scroll_to_bottom()

    def add_welcome_message(self):
        welcome_text = (
            "<b>" + tr("Xin chào!") + "</b> " + tr("Tôi là") + " <b>TLGeo Agent</b>, " 
            + tr("trợ lý không gian địa lý thông minh được phát triển bởi đội ngũ") + " <b>TLGeo</b>.<br><br>"
            + tr("Tôi có thể giúp bạn làm việc trực tiếp trên QGIS Desktop qua cửa sổ chat này. Bạn có thể yêu cầu tôi:") + "<br>"
            "&bull; <b>" + tr("Zoom, di chuyển") + "</b> " + tr("tới bất cứ lớp bản đồ nào.") + "<br>"
            "&bull; <b>" + tr("Chọn (Select) hoặc Highlight") + "</b> " + tr("các thửa đất/lô rừng theo thuộc tính mong muốn.") + "<br>"
            "&bull; <b>" + tr("Ẩn/Hiện") + "</b> " + tr("các layer nhanh chóng.") + "<br>"
            "&bull; <b>" + tr("Đọc bảng thuộc tính") + "</b> " + tr("và phân tích, thống kê diện tích rừng.") + "<br><br>"
            "<i>" + tr("Hãy nhập câu hỏi bên dưới để bắt đầu!") + "</i>"
        )
        welcome_bubble = MessageBubble("bot", welcome_text)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, welcome_bubble)

    def update_ui_states(self):
        """Toggle send and stop buttons depending on generation status."""
        self.btn_send.setVisible(not self.is_generating)
        self.btn_stop.setVisible(self.is_generating)
        self.input_field.setEnabled(not self.is_generating)
        if not self.is_generating:
            self.input_field.setFocus()

    def scroll_to_bottom(self):
        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))

    def closeEvent(self, event):
        if self.worker:
            self.worker.stop()
            self.worker.wait()
        super().closeEvent(event)
