import json
import sqlite3
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.db.core import get_conn
from app.reco import estimate_taste_vector

def compute_vectors():
    print("🚀 Starting taste vector computation (Dictionary-based)...")
    
    with get_conn() as conn:
        # 1. 銘柄とそのテキスト情報を取得
        # 各銘柄の全てのテキストを結合して分析対象とする
        sql = """
            SELECT m.sake_id, m.name, GROUP_CONCAT(t.text, ' ') as all_text
            FROM sake_master m
            LEFT JOIN sake_texts t ON m.sake_id = t.sake_id
            GROUP BY m.sake_id
        """
        sakes = conn.execute(sql).fetchall()
        
        count = 0
        for sake in sakes:
            sake_id = sake["sake_id"]
            name = sake["name"]
            desc = sake["all_text"] or ""
            
            # 銘柄名も分析対象に含める
            analysis_text = f"{name} {desc}"
            
            # 2. 味ベクトルを推定 (現在は辞書ベース)
            # estimate_taste_vector returns (vector, scores, hits)
            vector, _, _ = estimate_taste_vector(analysis_text)
            
            # 3. DBを更新 (upsert)
            conn.execute("""
                INSERT INTO sake_vectors (sake_id, taste_vector, version)
                VALUES (?, ?, ?)
                ON CONFLICT(sake_id) DO UPDATE SET
                    taste_vector = excluded.taste_vector,
                    version = excluded.version,
                    computed_at = datetime('now')
            """, (sake_id, json.dumps(vector), "v1-dict"))
            
            count += 1
            if count % 10 == 0:
                print(f"  Processed {count} sakes...")

    print(f"✅ Successfully computed vectors for {count} sakes.")

if __name__ == "__main__":
    compute_vectors()
