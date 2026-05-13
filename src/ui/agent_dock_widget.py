from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import traceback
import os
import logging
from logging.handlers import TimedRotatingFileHandler


def get_db_offline_message():
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    skill_path = os.path.join(base_path, "app", "frms_agent", "agents", "skills", "frms.md")
    try:
        with open(skill_path, "r", encoding="utf-8") as f:
            content = f.read()
            start = content.find("## Khi không có kết nối Database")
            end = content.find("## Best Practices", start) if start != -1 else -1
            if start != -1 and end != -1:
                return content[start:end]
    except:
        pass
    return """Xin lỗi, hiện tại tôi không thể kết nối đến cơ sở dữ liệu FRMS.

Nguyên nhân có thể là:
• Database server chưa được khởi động
• Sai cấu hình kết nối trong .env
• Tường lửa chặn kết nối

Bạn có thể:
1. Kiểm tra database PostgreSQL đang chạy trên port 8088
2. Xem lại FRMS_DB_HOST, FRMS_DB_PORT trong file .env
3. Liên hệ quản trị viên để được hỗ trợ

Khi hệ thống hoạt động, bạn có thể hỏi tôi về:
• Lô rừng và thông tin chi tiết
• Chủ rừng và thông tin liên hệ
• Diễn biến rừng theo thời gian
• Báo cáo và thống kê"""


def load_env():
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    env_path = os.path.join(base_path, ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value


def setup_logging():
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    log_dir = os.path.join(base_path, "app", "frms_agent", "agents", "logs")
    os.makedirs(log_dir, exist_ok=True)

    agent_logger = logging.getLogger("frms_agent")
    agent_logger.setLevel(logging.INFO)
    handler = TimedRotatingFileHandler(
        os.path.join(log_dir, "agent.log"),
        when="midnight",
        interval=1,
        backupCount=30
    )
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    agent_logger.addHandler(handler)
    return agent_logger


class AgentWorker(QThread):
    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, query, thread_id="frms_ui", parent=None):
        super().__init__(parent)
        self.query = query
        self.thread_id = thread_id
        self.logger = setup_logging()

    def run(self):
        try:
            import os
            import sys

            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            sys.path.insert(0, base_path)

            load_env()

            self.logger.info(f"REQUEST [thread={self.thread_id}]: {self.query}")

            from langchain_openai import ChatOpenAI
            from langchain_core.tools import tool

            @tool
            def get_current_time():
                """Returns the current time."""
                from datetime import datetime
                return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            @tool
            def calculator(expression: str) -> str:
                """Evaluates a math expression and returns the result."""
                try:
                    result = eval(expression, {"__builtins__": {}}, {})
                    return str(result)
                except Exception as e:
                    return f"Error: {e}"

            @tool
            def query_database(sql: str) -> str:
                """Execute a SQL query on the FRMS database. Returns results as tab-separated text."""
                if not sql.strip().upper().startswith("SELECT"):
                    return "Error: Only SELECT queries are allowed."
                try:
                    import psycopg2
                    FRMS_DB_CONFIG = {
                        "host": os.getenv("FRMS_DB_HOST", "localhost"),
                        "port": int(os.getenv("FRMS_DB_PORT", "8088")),
                        "dbname": os.getenv("FRMS_DB_NAME", "data_forest"),
                        "user": os.getenv("FRMS_DB_USER", "postgres"),
                        "password": os.getenv("FRMS_DB_PASSWORD", ""),
                    }
                    conn = psycopg2.connect(**FRMS_DB_CONFIG)
                    cursor = conn.cursor()
                    cursor.execute(sql)
                    rows = cursor.fetchall()
                    conn.close()
                    if not rows:
                        return "No results found."
                    headers = [desc[0] for desc in cursor.description]
                    result = "\t".join(headers) + "\n"
                    for row in rows:
                        result += "\t".join(str(val) for val in row) + "\n"
                    return result
                except Exception as e:
                    return f"Error: {str(e)}"

            @tool
            def list_tables() -> str:
                """List all table names in FRMS database."""
                try:
                    import psycopg2
                    FRMS_DB_CONFIG = {
                        "host": os.getenv("FRMS_DB_HOST", "localhost"),
                        "port": int(os.getenv("FRMS_DB_PORT", "8088")),
                        "dbname": os.getenv("FRMS_DB_NAME", "data_forest"),
                        "user": os.getenv("FRMS_DB_USER", "postgres"),
                        "password": os.getenv("FRMS_DB_PASSWORD", ""),
                    }
                    conn = psycopg2.connect(**FRMS_DB_CONFIG)
                    cursor = conn.cursor()
                    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
                    tables = [row[0] for row in cursor.fetchall()]
                    conn.close()
                    return ", ".join(tables) if tables else "No tables found"
                except Exception as e:
                    return f"Error: {str(e)}"

            tools = [get_current_time, calculator, query_database, list_tables]

            MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY") or "sk-cp-g8W7vBGUtY-XO0fTLvlp0uwYKSKq_4vPDl7is0XXyeYHlCTmEBUgUfYmkr1ZcHoC0YFfa939VJyW9lpR_GRGtIk4VMko5L3BA3PVGlS1fpB-BLmdTTe8HzA"
            MINIMAX_MODEL = os.getenv("MINIMAX_MODEL") or "MiniMax-M2.7"
            OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL") or "https://api.minimax.io/v1"

            llm = ChatOpenAI(
                model=MINIMAX_MODEL,
                api_key=MINIMAX_API_KEY,
                base_url=OPENAI_BASE_URL,
                temperature=0
            )

            skill_path = os.path.join(base_path, "app", "frms_agent", "agents", "skills", "frms.md")
            system_prompt = "Bạn là trợ lý FRMS, giúp quản lý dữ liệu tài nguyên rừng."
            if os.path.exists(skill_path):
                with open(skill_path, "r", encoding="utf-8") as f:
                    system_prompt += "\n\n" + f.read()

            tool_desc = "\n".join([f"- {t.name}: {t.description}" for t in tools])
            full_prompt = system_prompt + f"\n\nCác tools bạn có thể sử dụng:\n{tool_desc}\n\nKhi cần truy vấn database, hãy sử dụng query_database hoặc list_tables tool."

            messages = [{"role": "system", "content": full_prompt}]
            messages.append({"role": "user", "content": self.query})

            response = llm.invoke(messages)
            response_text = response.content if hasattr(response, 'content') else str(response)

            self.logger.info(f"RESPONSE [thread={self.thread_id}]: {response_text}")
            self.response_ready.emit(response_text)

        except Exception as e:
            error_msg = f"Lỗi: {str(e)}"
            self.logger.error(f"ERROR: {error_msg}")
            self.error_occurred.emit(error_msg)


class AgentChatWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.thread_counter = 0
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)

        header = QLabel("🤖 FRMS Agent - Trợ lý thông minh")
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
        self.input_field.setPlaceholderText("Nhập câu hỏi của bạn...")
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
        self.status_label.setStyleSheet("color: #666; font-size: 9px; font-style: italic;")
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
                             "• Báo cáo và thống kê<br/>"
                             "</div>")

    def send_message(self):
        query = self.input_field.text().strip()
        if not query:
            return

        if self.worker is not None and self.worker.isRunning():
            self.status_label.setText("⚠️ Đang xử lý...")
            return

        self.chat_area.append(f"<div style='color: #333;'><b>👤 Bạn:</b><br/>{query}</div>")
        self.input_field.clear()
        self.send_button.setEnabled(False)
        self.status_label.setText("⏳ Đang xử lý...")

        self.thread_counter += 1
        thread_id = f"frms_ui_{self.thread_counter}"

        self.worker = AgentWorker(query, thread_id, self)
        self.worker.response_ready.connect(self.on_response_ready)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.start()

    def on_response_ready(self, response):
        self.chat_area.append(f"<div style='color: #006600;'><b>🤖 Agent:</b><br/>{response}</div>")
        self.send_button.setEnabled(True)
        self.status_label.setText("")
        self.worker = None

    def on_error(self, error_msg):
        self.chat_area.append(f"<div style='color: #cc0000;'><b>❌ Lỗi:</b><br/>{error_msg}</div>")
        self.send_button.setEnabled(True)
        self.status_label.setText("❌ Có lỗi xảy ra")
        self.worker = None