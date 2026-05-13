from langchain_core.tools import tool
import psycopg2
import os

# Load environment variables from project root
base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
_env_path = os.path.join(base_path, ".env")
if os.path.exists(_env_path):
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

FRMS_DB_CONFIG = {
    "host": os.getenv("FRMS_DB_HOST", "localhost"),
    "port": int(os.getenv("FRMS_DB_PORT", "5432")),
    "dbname": os.getenv("FRMS_DB_NAME", "data_forest"),
    "user": os.getenv("FRMS_DB_USER", "postgres"),
    "password": os.getenv("FRMS_DB_PASSWORD", ""),
    "connect_timeout": int(os.getenv("FRMS_DB_TIMEOUT", "10")),
    "sslmode": os.getenv("FRMS_DB_SSL_MODE", "prefer"),
}


def get_connection():
    """Get PostgreSQL connection to FRMS database."""
    return psycopg2.connect(**FRMS_DB_CONFIG)


@tool
def query_database(sql: str) -> str:
    """
    Execute a SQL query on the FRMS PostgreSQL database and return results.

    Args:
        sql: SQL SELECT query to execute

    Returns:
        Tab-separated results with headers
    """
    if not sql.strip().upper().startswith("SELECT"):
        return "Error: Only SELECT queries are allowed for security reasons."

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()

        if not rows:
            return "No results found."

        headers = [desc[0] for desc in cursor.description]
        result = "\t".join(headers) + "\n"
        for row in rows:
            result += "\t".join(str(val) for val in row) + "\n"

        conn.close()
        return result
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def list_tables() -> str:
    """
    List all table names in the FRMS database.

    Returns:
        List of table names
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return ", ".join(tables) if tables else "No tables found"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def describe_table(table_name: str) -> str:
    """
    Get the schema of a specific table in FRMS database.

    Args:
        table_name: Name of the table to describe

    Returns:
        Column information (name, type, nullable, default)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        columns = cursor.fetchall()
        conn.close()

        if not columns:
            return f"Table '{table_name}' not found"

        result = f"Table: {table_name}\n"
        result += "Column | Type | Nullable | Default\n"
        result += "-" * 60 + "\n"
        for col in columns:
            result += f"{col[0]} | {col[1]} | {col[2]} | {col[3] or ''}\n"
        return result
    except Exception as e:
        return f"Error: {str(e)}"