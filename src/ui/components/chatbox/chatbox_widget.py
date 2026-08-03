import os
import re
import markdown
from qgis.PyQt.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                QPushButton, QScrollArea, QFrame, QLineEdit, 
                                QStyle, QApplication, QPlainTextEdit, QSizePolicy)
from qgis.PyQt.QtCore import Qt, pyqtSignal, QTimer, QSize
from qgis.PyQt.QtGui import QIcon, QPixmap, QPainter, QColor, QPen, QPainterPath
from ....util.i18n import tr
from ....app.auth.util.auth_service import AuthService
from .chat_worker import ChatWSWorker

def get_paper_plane_icon(color="#ffffff"):
    """Draw a vector-like paper plane icon dynamically on a QPixmap."""
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Path for paper plane pointing top-right
    path = QPainterPath()
    path.moveTo(26, 6)    # Nose
    path.lineTo(6, 15)    # Bottom-left wing tip
    path.lineTo(13, 19)   # Inner fold
    path.lineTo(17, 26)   # Bottom-right wing tip
    path.closeSubpath()
    
    painter.setBrush(QColor(color))
    painter.setPen(Qt.NoPen)
    painter.drawPath(path)
    
    # Inner fold line
    painter.setPen(QPen(QColor(color), 1.5))
    painter.drawLine(26, 6, 13, 19)
    
    painter.end()
    return QIcon(pixmap)

def get_copy_icon(color="#5f6368"):
    """Draw a vector-like Copy document icon dynamically on a QPixmap."""
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    painter.setPen(QPen(QColor(color), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.setBrush(Qt.NoBrush)
    
    # Draw back document: top-left (6, 6), width 12, height 12
    painter.drawRoundedRect(6, 6, 12, 12, 2, 2)
    
    # Draw front document: top-left (12, 12), width 12, height 12
    # Fill background first to mask overlapping lines
    painter.setBrush(QColor("#f1f3f4"))
    painter.drawRoundedRect(12, 12, 12, 12, 2, 2)
    
    painter.end()
    return QIcon(pixmap)

def format_to_html(text, escape_html=False):
    """Convert markdown/plain-text to HTML using python-markdown library and custom styles."""
    if escape_html:
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    else:
        text = text.replace("&lt;think&gt;", "<think>").replace("&lt;/think&gt;", "</think>")
        
    html = markdown.markdown(text, extensions=['nl2br', 'tables', 'fenced_code'])
    
    # CSS styling to override default rich text rendering sizes and margins
    style_block = (
        "<style>"
        "h1 { font-size: 15px; font-weight: bold; color: #202124; margin-top: 8px; margin-bottom: 4px; }"
        "h2 { font-size: 14px; font-weight: bold; color: #202124; margin-top: 6px; margin-bottom: 3px; }"
        "h3 { font-size: 13px; font-weight: bold; color: #1a73e8; margin-top: 4px; margin-bottom: 2px; }"
        "code { background-color: #e8eaed; color: #c62828; font-family: monospace; padding: 2px 4px; }"
        "ul { margin-top: 4px; margin-bottom: 4px; padding-left: 16px; }"
        "li { margin-bottom: 2px; }"
        "table { width: 100%; border-collapse: collapse; margin-top: 6px; margin-bottom: 6px; }"
        "th, td { border: 1px solid #dadce0; padding: 4px 6px; font-size: 12px; }"
        "th { background-color: #f1f3f4; font-weight: bold; }"
        "</style>"
    )
    return style_block + html

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
            main_layout.addStretch(1)
            main_layout.addWidget(self.bubble_frame, 9)
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
            main_layout.addWidget(self.bubble_frame, 9)
            main_layout.addStretch(1)
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
            
            # Actions layout (Like, Dislike, Copy)
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(0, 4, 0, 0)
            actions_layout.setSpacing(4)
            
            self.btn_like = QPushButton("👍")
            self.btn_like.setToolTip(tr("Like"))
            self.btn_like.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    border-radius: 4px;
                    padding: 2px 4px;
                    font-size: 11px;
                    min-width: 20px;
                    min-height: 20px;
                }
                QPushButton:hover {
                    background-color: #e5e5e5;
                }
            """)
            
            self.btn_dislike = QPushButton("👎")
            self.btn_dislike.setToolTip(tr("Dislike"))
            self.btn_dislike.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    border-radius: 4px;
                    padding: 2px 4px;
                    font-size: 11px;
                    min-width: 20px;
                    min-height: 20px;
                }
                QPushButton:hover {
                    background-color: #e5e5e5;
                }
            """)
            
            self.btn_copy = QPushButton()
            self.btn_copy.setToolTip(tr("Copy"))
            self.btn_copy.setIcon(get_copy_icon("#5f6368"))
            self.btn_copy.setIconSize(QSize(13, 13))
            self.btn_copy.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    border-radius: 4px;
                    padding: 2px 4px;
                    min-width: 20px;
                    min-height: 20px;
                }
                QPushButton:hover {
                    background-color: #e5e5e5;
                }
            """)
            self.btn_copy.clicked.connect(self.copy_to_clipboard)
            
            actions_layout.addWidget(self.btn_like)
            actions_layout.addWidget(self.btn_dislike)
            actions_layout.addWidget(self.btn_copy)
            actions_layout.addStretch()
            
            bubble_layout.addLayout(actions_layout)
            
        self.update_content(text)

    def copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        if clipboard:
            thinking, cleaned = parse_thinking(self.text)
            clipboard.setText(cleaned)
        
    def update_content(self, text):
        self.text = text
        if self.role == "user":
            self.main_label.setText(format_to_html(text, escape_html=True))
        else:
            thinking, cleaned = parse_thinking(text)
            
            if thinking:
                self.thinking_label.setText(format_to_html(thinking, escape_html=False))
                self.thinking_frame.setVisible(True)
            else:
                self.thinking_frame.setVisible(False)
                
            self.main_label.setText(format_to_html(cleaned, escape_html=False) if cleaned else "...")

class ChatInputEdit(QPlainTextEdit):
    returnPressed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_container = None
        self.setPlaceholderText("")
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.document().setDocumentMargin(12)
        self.textChanged.connect(self.adjust_height)
        self.setFixedHeight(72)
        
    def keyPressEvent(self, event):
        # Send message on Enter, but insert new line on Shift+Enter
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() & Qt.ShiftModifier:
                super().keyPressEvent(event)
            else:
                self.returnPressed.emit()
        else:
            super().keyPressEvent(event)

    def adjust_height(self):
        doc = self.document()
        doc_height = doc.size().height()
        clamped_height = max(72, min(int(doc_height), 120))
        self.setFixedHeight(clamped_height)
        if self.parent_container:
            self.parent_container.setFixedHeight(clamped_height + 8)

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
        
        # Loading spinner animation variables
        self.spinner_timer = QTimer(self)
        self.spinner_timer.timeout.connect(self.update_spinner)
        self.spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_index = 0
        self.current_activity_base = ""
        
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
        main_layout.addWidget(self.scroll_area, 1)
        
        # 3. Status Logs / Activity text
        self.activity_label = QLabel()
        self.activity_label.setWordWrap(True)
        self.activity_label.setStyleSheet("color: #0b57d0; font-size: 11px; font-style: italic; padding-left: 5px;")
        self.activity_label.setFixedHeight(18)
        self.activity_label.setText("")
        main_layout.addWidget(self.activity_label)
        
        # 4. Input Container (looks like the input box)
        self.input_container = QFrame()
        self.input_container.setStyleSheet("""
            QFrame {
                border: 1px solid #dadce0;
                border-radius: 18px;
                background-color: #ffffff;
            }
            QFrame:focus-within {
                border: 1px solid #1a73e8;
            }
        """)
        self.input_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.input_container.setFixedHeight(80)
        container_layout = QHBoxLayout(self.input_container)
        container_layout.setContentsMargins(10, 4, 6, 4)
        container_layout.setSpacing(6)

        self.input_field = ChatInputEdit()
        self.input_field.parent_container = self.input_container
        self.input_field.adjust_height()
        self.input_field.setPlaceholderText(tr("Ask TLGeo Agent..."))
        self.input_field.setStyleSheet("""
            QPlainTextEdit {
                border: none;
                background-color: transparent;
                color: #202124;
                font-size: 13px;
                padding: 0px;
            }
        """)
        self.input_field.returnPressed.connect(self.send_message)
        container_layout.addWidget(self.input_field, 1)

        # Send Button (clean modern icon button)
        self.btn_send = QPushButton()
        self.btn_send.setToolTip(tr("Send message"))
        self.btn_send.setIcon(get_paper_plane_icon("#1a73e8"))
        self.btn_send.setIconSize(QSize(18, 18))
        self.btn_send.setCursor(Qt.PointingHandCursor)
        self.btn_send.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 14px;
                min-width: 28px;
                min-height: 28px;
                max-width: 28px;
                max-height: 28px;
            }
            QPushButton:hover {
                background-color: #f1f3f4;
            }
            QPushButton:pressed {
                background-color: #e8eaed;
            }
        """)
        self.btn_send.clicked.connect(self.send_message)
        container_layout.addWidget(self.btn_send, 0, Qt.AlignBottom)

        # Stop Button (Hidden by default)
        self.btn_stop = QPushButton()
        self.btn_stop.setToolTip(tr("Stop Thinking"))
        self.btn_stop.setIcon(QApplication.style().standardIcon(QStyle.SP_MediaStop))
        self.btn_stop.setCursor(Qt.PointingHandCursor)
        self.btn_stop.setStyleSheet("""
            QPushButton {
                background-color: #c62828;
                border: none;
                border-radius: 14px;
                min-width: 28px;
                min-height: 28px;
                max-width: 28px;
                max-height: 28px;
            }
            QPushButton:hover {
                background-color: #b71c1c;
            }
        """)
        self.btn_stop.setVisible(False)
        self.btn_stop.clicked.connect(self.stop_thinking)

        # Wrap in a horizontal layout to sit in the main UI layout
        input_wrapper = QHBoxLayout()
        input_wrapper.setContentsMargins(0, 0, 0, 0)
        input_wrapper.setSpacing(6)
        input_wrapper.addWidget(self.input_container)
        input_wrapper.addWidget(self.btn_stop, 0, Qt.AlignBottom)
        main_layout.addLayout(input_wrapper)
        
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
        # agent_url = os.getenv("TLGEO_AGENT_URL", "ws://localhost:13001/ws/qgis")
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
                self.current_activity_base = clean_text
                
        elif msg_type == "chat_chunk":
            self.activity_label.setText("")
            self.current_activity_base = ""
            chunk = data.get("content", "")
            self.current_bot_text += chunk
            if self.last_bot_bubble:
                self.last_bot_bubble.update_content(self.current_bot_text)
            self.scroll_to_bottom()
            
        elif msg_type == "chat_response":
            self.activity_label.setText("")
            self.current_activity_base = ""
            self.current_bot_text = data.get("content", "")
            if self.last_bot_bubble:
                self.last_bot_bubble.update_content(self.current_bot_text)
            self.is_generating = False
            self.update_ui_states()
            self.scroll_to_bottom()

    def send_message(self):
        text = self.input_field.toPlainText().strip()
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
        if self.is_generating:
            self.spinner_index = 0
            self.spinner_timer.start(80)
        else:
            self.spinner_timer.stop()
            self.activity_label.setText("")
            self.input_field.setFocus()

    def update_spinner(self):
        """Cycle the braille loading spinner animation next to active status text."""
        if not self.is_generating:
            return
        frame = self.spinner_frames[self.spinner_index]
        self.spinner_index = (self.spinner_index + 1) % len(self.spinner_frames)
        
        base_text = self.current_activity_base or tr("Trợ lý đang suy nghĩ")
        self.activity_label.setText(f"<span style='color: #1a73e8; font-weight: bold;'>{frame}</span> {base_text}...")
        self.activity_label.setVisible(True)

    def scroll_to_bottom(self):
        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))

    def closeEvent(self, event):
        self.spinner_timer.stop()
        if self.worker:
            self.worker.stop()
            self.worker.wait()
        super().closeEvent(event)
