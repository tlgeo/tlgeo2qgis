# FRMS Agent

## Overview

FRMS Agent là AI agent tích hợp trong **TLGeo2QGIS Plugin**, sử dụng **LangChain** để trả lời câu hỏi của người dùng về dữ liệu FRMS (Forest Resource Management System).

```
┌─────────────────────────────────────────────────────────────┐
│                    TLGeo2QGIS Plugin                         │
│  ┌─────────────────┐    ┌──────────────────────────────┐     │
│  │  FRMS Ribbon     │───▶│  AgentChatDialog (UI)       │     │
│  │  "Hỏi Agent"    │    │  - Chat interface           │     │
│  └─────────────────┘    │  - Query input              │     │
│                         │  - Response display         │     │
│                         └──────────────┬──────────────┘     │
│                                        │                    │
│                         ┌──────────────▼──────────────┐     │
│                         │  src/app/frms_agent/       │     │
│                         │  - agent.py                │     │
│                         │  - agents/tools/           │     │
│                         │  - agents/skills/          │     │
│                         └──────────────┬──────────────┘     │
│                                        │                    │
│                         ┌──────────────▼──────────────┐     │
│                         │  FRMS PostgreSQL Database  │     │
│                         │  (data_forest @ :8088)     │     │
│                         └────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
src/app/frms_agent/
├── __init__.py
├── agent.py                    # LangChain agent core
├── ui/
│   ├── __init__.py
│   └── agent_chat_dialog.py    # PyQt5 chat UI dialog
└── agents/
    ├── __init__.py
    ├── tools/
    │   ├── __init__.py
    │   └── database.py        # PostgreSQL FRMS tools
    ├── skills/
    │   └── (FRMS domain knowledge .md files)
    ├── data/
    │   └── (local cache files)
    └── logs/
        └── agent.log          # Rotating logs
```

## Implementation

### 1. agent.py - LangChain Agent Core

**Location**: `src/app/frms_agent/agent.py`

LangChain agent với:
- **LLM**: MiniMax Text API (`ChatOpenAI`)
- **Tools**: Database queries, calculator, time
- **Memory**: Thread-based `MemorySaver` checkpointing
- **Skills**: Dynamically loaded from `.md` files at runtime

```python
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver

llm = ChatOpenAI(
    model=os.getenv("MINIMAX_MODEL", "MiniMax-M2.7"),
    api_key=os.getenv("MINIMAX_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    temperature=0
)

agent = create_agent(
    llm,
    tools,
    system_prompt=system_prompt,
    checkpointer=MemorySaver()
)
```

### 2. database.py - PostgreSQL Tools

**Location**: `src/app/frms_agent/agents/tools/database.py`

Tools kết nối PostgreSQL FRMS database:

```python
@tool query_database(sql: str)        # Execute SELECT query
@tool list_tables()                   # List all tables
@tool describe_table(table_name: str)  # Get table schema
```

Config từ `.env`:
```env
FRMS_DB_HOST=localhost
FRMS_DB_PORT=8088
FRMS_DB_NAME=data_forest
FRMS_DB_USER=postgres
FRMS_DB_PASSWORD=xxx
```

### 3. agent_chat_dialog.py - Chat UI

**Location**: `src/app/frms_agent/ui/agent_chat_dialog.py`

PyQt5 dialog với:
- `AgentWorker(QThread)` - Chạy agent trong background thread
- `AgentChatDialog(QDialog)` - Giao diện chat

Features:
- Non-blocking UI (worker thread)
- Real-time status updates
- Error handling với message display
- Responsive design

## Environment Variables

### .env

```env
# FRMS Database
FRMS_DB_HOST=localhost
FRMS_DB_PORT=8088
FRMS_DB_NAME=data_forest
FRMS_DB_USER=postgres
FRMS_DB_PASSWORD=xxx
FRMS_DB_TIMEOUT=10
FRMS_DB_SSL_MODE=prefer

# LLM Agent
MINIMAX_API_KEY=xxx
MINIMAX_MODEL=MiniMax-M2.7
OPENAI_BASE_URL=https://api.minimax.io/v1
SYSTEM_PROMPT=Bạn là trợ lý FRMS...
```

## Integration Points

### Ribbon Button
**Location**: `src/ui/dock_widget.py`

FRMS ribbon tab → Group "Agent" → Button "Hỏi Agent" → `open_frms_agent()` → `AgentChatDialog(self).exec_()`

```python
def open_frms_agent(self):
    """Open FRMS Agent chat dialog"""
    dlg = AgentChatDialog(self)
    dlg.exec_()
```

### Dependencies

**requirements.txt** (development):
```txt
langchain>=0.3.0
langchain-openai>=0.3.0
langgraph>=0.2.0
psycopg2-binary
python-dotenv
```

**requirements.runtime.txt** (runtime):
```txt
# Same agent dependencies
```

## Skills

Skills được load từ `agents/skills/*.md` tại runtime, merge vào `system_prompt`:

| File | Description |
|------|-------------|
| `frms.md` | FRMS domain knowledge (do user cung cấp) |
| `database.md` | Query patterns & schema hints |

## Future Extensions

### Planned Tools
- `search_plots()` - Tìm kiếm lô rừng theo tên, mã, diện tích
- `search_owners()` - Tìm kiếm chủ rừng
- `get_change_history()` - Lịch sử diễn biến
- `get_statistics()` - Thống kê dữ liệu
- `generate_report()` - Tạo báo cáo

### Planned QGIS Integration
- Zoom to feature từ search results
- Highlight features on map
- Context menu actions
- Layer interaction commands

## Reference

- [TLGeoAgent Reference](../_library_docs/TLGeoAgent/) - Original LangChain agent pattern
- [FRMS Menu Design](../features/FRMS_MENU_DESIGN.md)
- [FRMS Tasks Index](../_TASKS/FRMS_TASKS_INDEX.md)