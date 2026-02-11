# Usage: uv run python scripts/seed_dummy.py
import json
import os
import sqlite3
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.environ.get("SAKE_DB_PATH", str(ROOT / "var" / "sake.db")))

DUMMY_DATA = [
    {
        "master": {
            "name": "獺祭 純米大吟醸 45",
            "brewery": "旭酒造",
            "prefecture": "山口県",
            "rice": "山田錦",
            "grade": "純米大吟醸",
            "abv": 16.0,
            "external_sakenowa_id": 1
        },
        "aliases": ["獺祭45", "だっさい"],
        "texts": [
            {"source": "official", "text": "最高の酒米といわれる山田錦を45%まで磨いて作り上げました。きれいで華やかな香りと、口に含んだ時の蜂蜜のような甘み、飲み込んだ後の長い余韻が特徴です。"},
            {"source": "sakenowa_review", "text": "とてもフルーティで飲みやすい。日本酒が苦手な人にもおすすめ。"}
        ],
        "vector": [0.4, -0.2, 1.0, 0.8]  # [sweet_dry, body, fruity, modern]
    },
    {
        "master": {
            "name": "久保田 千寿",
            "brewery": "朝日酒造",
            "prefecture": "新潟県",
            "rice": "五百万石",
            "grade": "吟醸",
            "abv": 15.0,
            "external_sakenowa_id": 2
        },
        "aliases": ["久保田", "くぼた"],
        "texts": [
            {"source": "official", "text": "「食事と楽しむ吟醸酒」を目指し、香りは穏やかに、飲み飽きしない味わいに仕上げました。口当たりが柔らかく、ドライな後味が特徴です。"},
            {"source": "sakenowa_review", "text": "スッキリしていてどんな料理にも合う。冷やでも熱燗でもいける。"}
        ],
        "vector": [-0.3, -0.6, 0.2, -0.5]
    },
    {
        "master": {
            "name": "田酒 特別純米",
            "brewery": "西田酒造店",
            "prefecture": "青森県",
            "rice": "華吹雪",
            "grade": "特別純米",
            "abv": 16.0,
            "external_sakenowa_id": 3
        },
        "aliases": ["田酒", "でんしゅ"],
        "texts": [
            {"source": "official", "text": "米の旨みがしっかりと感じられる、純米酒らしい味わい。酸味と旨みのバランスが良く、飲み飽きしません。"},
            {"source": "sakenowa_review", "text": "お米の味がしっかりする。刺身と合わせると最高。"}
        ],
        "vector": [0.1, 0.3, 0.3, -0.2]
    },
    {
        "master": {
            "name": "而今 特別純米",
            "brewery": "木屋正酒造",
            "prefecture": "三重県",
            "rice": "五百万石",
            "grade": "特別純米",
            "abv": 16.0,
            "external_sakenowa_id": 4
        },
        "aliases": ["而今", "じこん"],
        "texts": [
            {"source": "official", "text": "フレッシュ感溢れるジューシーな味わい。甘みと酸味のバランスが絶妙で、モダンな日本酒の代表格です。"},
            {"source": "sakenowa_review", "text": "メロンのような香りがして、とてもフルーティ。今のトレンドという感じ。"}
        ],
        "vector": [0.5, 0.1, 0.9, 0.9]
    },
    {
        "master": {
            "name": "剣菱",
            "brewery": "剣菱酒造",
            "prefecture": "兵庫県",
            "rice": "山田錦",
            "grade": "本醸造",
            "abv": 17.0,
            "external_sakenowa_id": 5
        },
        "aliases": ["剣菱", "けんびし"],
        "texts": [
            {"source": "official", "text": "古来より続く伝統的な製法を守り、濃厚でコクのある味わいを追求しています。熟成による黄金色と、力強い旨みが特徴です。"},
            {"source": "sakenowa_review", "text": "かなりガツンとくる重層的な味。お湯割りにすると最高に旨い。"}
        ],
        "vector": [-0.2, 0.9, 0.0, -1.0]
    }
]

def seed_data():
    if not DB_PATH.exists():
        print(f"❌ Database not found at {DB_PATH}. Please run `scripts/init_db.py` first.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    try:
        # 既存データのクリア (必要に応じて)
        # cursor.execute("DELETE FROM sake_master")
        
        for data in DUMMY_DATA:
            m = data["master"]
            cursor.execute("""
                INSERT INTO sake_master (name, brewery, prefecture, rice, grade, abv, external_sakenowa_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (m["name"], m["brewery"], m["prefecture"], m.get("rice"), m.get("grade"), m.get("abv"), m.get("external_sakenowa_id")))
            
            sake_id = cursor.lastrowid
            
            # Aliases
            for alias in data["aliases"]:
                cursor.execute("""
                    INSERT INTO sake_aliases (sake_id, alias, source)
                    VALUES (?, ?, ?)
                """, (sake_id, alias, "manual"))
            
            # Texts
            for text_data in data["texts"]:
                cursor.execute("""
                    INSERT INTO sake_texts (sake_id, source, text, lang)
                    VALUES (?, ?, ?, ?)
                """, (sake_id, text_data["source"], text_data["text"], "ja"))
            
            # Vector
            cursor.execute("""
                INSERT INTO sake_vectors (sake_id, taste_vector, version)
                VALUES (?, ?, ?)
            """, (sake_id, json.dumps(data["vector"]), "v1"))

        conn.commit()
        print(f"✅ Seeded {len(DUMMY_DATA)} dummy sake entries to {DB_PATH}")

    except Exception as e:
        conn.rollback()
        print(f"❌ Failed to seed data: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    seed_data()
