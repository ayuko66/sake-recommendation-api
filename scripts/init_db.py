# Usage: uv run python scripts/init_db.py
from __future__ import annotations

import os
import sqlite3

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DB_PATH = Path(os.environ.get("SAKE_DB_PATH", str(ROOT / "var" / "sake.db")))
SCHEMA_PATH = ROOT / "app" / "db" / "schema.sql"


def init_db() -> None:
    """データベースを初期化する"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    schema = SCHEMA_PATH.read_text(encoding="utf-8")

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")  # 外部キー制約を有効化
        conn.executescript(schema)
        conn.commit()
    finally:
        conn.close()

    print(f"✅ DB initialized: {DB_PATH}")
    print(f"✅ Schema applied : {SCHEMA_PATH}")


if __name__ == "__main__":
    init_db()
