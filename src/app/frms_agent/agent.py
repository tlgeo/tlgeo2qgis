import os
import logging
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler

# Load environment variables directly (no dotenv dependency)
base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
_env_path = os.path.join(base_path, ".env")
if os.path.exists(_env_path):
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver

from .agents.tools.database import query_database, list_tables, describe_table

log_dir = os.path.join(os.path.dirname(__file__), "agents/logs")
os.makedirs(log_dir, exist_ok=True)

agent_logger = logging.getLogger("frms_agent")
agent_logger.setLevel(logging.INFO)
handler = TimedRotatingFileHandler(
    os.path.join(log_dir, "agent.log"),
    when="midnight",
    interval=1,
    backupCount=30
)
handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
))
agent_logger.addHandler(handler)

skill_dir = os.path.join(os.path.dirname(__file__), "agents/skills")
system_prompt = os.getenv("SYSTEM_PROMPT", "Bạn là trợ lý FRMS, giúp quản lý dữ liệu tài nguyên rừng.")
for skill_file in os.listdir(skill_dir):
    if skill_file.endswith(".md"):
        with open(os.path.join(skill_dir, skill_file), "r") as f:
            system_prompt += "\n\n" + f.read()


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


tools = [get_current_time, calculator, query_database, list_tables, describe_table]

llm = ChatOpenAI(
    model=os.getenv("MINIMAX_MODEL", "MiniMax-M2.7"),
    api_key=os.getenv("MINIMAX_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL"),
    temperature=0
)

checkpointer = MemorySaver()

agent = create_agent(
    llm,
    tools,
    system_prompt=system_prompt,
    checkpointer=checkpointer
)


def run(query: str, thread_id: str = "default") -> str:
    agent_logger.info(f"REQUEST [thread={thread_id}]: {query}")
    config = {"configurable": {"thread_id": thread_id}}
    inputs = {"messages": [{"role": "user", "content": query}]}
    result = agent.invoke(inputs, config)
    response = result["messages"][-1].content
    agent_logger.info(f"RESPONSE [thread={thread_id}]: {response}")
    return response