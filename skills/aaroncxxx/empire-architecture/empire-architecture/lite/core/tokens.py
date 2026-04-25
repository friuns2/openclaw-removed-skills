"""帝国架构 - Token 追踪"""
import sqlite3
import time
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "tokens.db")


class TokenTracker:
    """Token 消耗追踪"""

    def __init__(self, db_path: str = DB_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self._init_db()

    def _init_db(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS token_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                task_id TEXT,
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                model TEXT,
                timestamp REAL DEFAULT (strftime('%s','now'))
            );
            CREATE TABLE IF NOT EXISTS token_budget (
                agent_id TEXT PRIMARY KEY,
                daily_limit INTEGER DEFAULT 100000,
                used_today INTEGER DEFAULT 0,
                last_reset TEXT DEFAULT (date('now'))
            );
        """)
        self.conn.commit()

    def log_usage(self, agent_id: str, input_tokens: int, output_tokens: int,
                  model: str = "", task_id: str = ""):
        self.conn.execute(
            "INSERT INTO token_usage (agent_id, task_id, input_tokens, output_tokens, model) VALUES (?,?,?,?,?)",
            (agent_id, task_id, input_tokens, output_tokens, model),
        )
        self.conn.execute(
            "UPDATE token_budget SET used_today = used_today + ? WHERE agent_id = ?",
            (input_tokens + output_tokens, agent_id),
        )
        self.conn.commit()

    def get_usage(self, agent_id: str = None) -> dict:
        if agent_id:
            row = self.conn.execute(
                "SELECT used_today, daily_limit FROM token_budget WHERE agent_id = ?",
                (agent_id,),
            ).fetchone()
            return {"used": row[0] if row else 0, "limit": row[1] if row else 100000}
        rows = self.conn.execute(
            "SELECT agent_id, SUM(input_tokens), SUM(output_tokens) FROM token_usage GROUP BY agent_id"
        ).fetchall()
        return {r[0]: {"input": r[1], "output": r[2]} for r in rows}

    def get_total_today(self) -> int:
        row = self.conn.execute("SELECT SUM(used_today) FROM token_budget").fetchone()
        return row[0] or 0

    def reset_daily(self):
        self.conn.execute("UPDATE token_budget SET used_today = 0")
        self.conn.commit()

    def set_budget(self, agent_id: str, daily_limit: int):
        self.conn.execute(
            "INSERT OR REPLACE INTO token_budget (agent_id, daily_limit, used_today) VALUES (?, ?, 0)",
            (agent_id, daily_limit),
        )
        self.conn.commit()

    def check_budget(self, agent_id: str) -> bool:
        """检查是否还有 token 额度"""
        row = self.conn.execute(
            "SELECT used_today, daily_limit FROM token_budget WHERE agent_id = ?",
            (agent_id,),
        ).fetchone()
        if not row:
            return True
        return row[0] < row[1]
