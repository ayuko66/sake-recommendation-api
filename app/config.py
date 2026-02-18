import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]

class Config:
    # データベース
    DB_PATH = os.environ.get("SAKE_DB_PATH", str(ROOT / "var" / "sake.db"))
    
    # レコメンド/検索設定
    USE_EMBEDDING = int(os.environ.get("USE_EMBEDDING", "0"))
    EMBED_PROVIDER = os.environ.get("EMBED_PROVIDER", "openai") # openai | sbert
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

settings = Config()
