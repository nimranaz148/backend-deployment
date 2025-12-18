# src\services\db_service.py
import psycopg2
import json
from typing import List, Dict, Optional
from src.core.config import settings

class DBService:
    def __init__(self):
        self.conn = None

    def get_connection(self):
        if not self.conn or self.conn.closed:
            self.conn = psycopg2.connect(settings.NEON_DB_URL)
        return self.conn

    def create_tables_if_not_exists(self):
        """Create all required tables."""
        conn = self.get_connection()
        with conn.cursor() as cur:
            # Chat history table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id BIGSERIAL PRIMARY KEY,
                    user_message TEXT NOT NULL,
                    ai_response TEXT NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    source_documents JSONB
                );
            """)
            # Users table for Better-Auth
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id VARCHAR(255) PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    background JSONB,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """)
            conn.commit()

    def create_chat_history_table_if_not_exists(self):
        """Legacy method for backwards compatibility."""
        self.create_tables_if_not_exists()

    def log_chat_interaction(
        self,
        user_message: str,
        ai_response: str,
        source_documents: Optional[List[Dict]] = None
    ):
        conn = self.get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO chat_history (user_message, ai_response, source_documents)
                VALUES (%s, %s, %s);
                """,
                (user_message, ai_response, json.dumps(source_documents) if source_documents else None)
            )
            conn.commit()

    # User management methods for Better-Auth
    def create_user(self, user_data: Dict) -> None:
        """Create a new user in the database."""
        conn = self.get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (id, email, name, password_hash, background, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                ON CONFLICT (email) DO NOTHING;
                """,
                (
                    user_data["id"],
                    user_data["email"],
                    user_data["name"],
                    user_data["password_hash"],
                    json.dumps(user_data.get("background"))
                )
            )
            conn.commit()

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email address."""
        conn = self.get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, email, name, password_hash, background FROM users WHERE email = %s",
                (email,)
            )
            row = cur.fetchone()
            if row:
                return {
                    "id": row[0],
                    "email": row[1],
                    "name": row[2],
                    "password_hash": row[3],
                    "background": row[4]
                }
            return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID."""
        conn = self.get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, email, name, password_hash, background FROM users WHERE id = %s",
                (user_id,)
            )
            row = cur.fetchone()
            if row:
                return {
                    "id": row[0],
                    "email": row[1],
                    "name": row[2],
                    "password_hash": row[3],
                    "background": row[4]
                }
            return None

# Ensure tables are created on service initialization
db_service = DBService()
db_service.create_tables_if_not_exists()

if __name__ == "__main__":
    # Example usage:
    # Requires NEON_DB_URL to be set in .env and a running Neon Postgres database
    print("Attempting to connect to DB and create table...")
    try:
        db_service.create_chat_history_table_if_not_exists()
        print("Table 'chat_history' ensured to exist.")
        
        # Test logging
        db_service.log_chat_interaction(
            user_message="Hello, chatbot!",
            ai_response="Hello, user! How can I help you?",
            source_documents=[{"file": "intro.md", "chunk": "Introduction to AI"}]
        )
        print("Test chat interaction logged successfully.")

    except Exception as e:
        print(f"Error: {e}")
