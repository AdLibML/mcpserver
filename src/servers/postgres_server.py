import os
import psycopg2
from mcp import MCPServer, mcp_tool

DB_HOST = os.environ.get("POSTGRES_HOST", "localhost")
DB_PORT = os.environ.get("POSTGRES_PORT", "5432")
DB_NAME = os.environ.get("POSTGRES_DB", "postgres")
DB_USER = os.environ.get("POSTGRES_USER", "postgres")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "password")

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

@mcp_tool
def query_postgres(query: str) -> str:
    """Exécute une requête SQL sur la base PostgreSQL et retourne le résultat."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query)
        if cur.description:
            result = cur.fetchall()
        else:
            result = f"{cur.rowcount} rows affected."
        cur.close()
        conn.close()
        return str(result)
    except Exception as e:
        return f"Erreur lors de la requête : {e}"

if __name__ == "__main__":
    server = MCPServer(tools=[query_postgres])
    server.serve()
