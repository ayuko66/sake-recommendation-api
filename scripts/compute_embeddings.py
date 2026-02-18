
import sys
import os
import json
import time
import sqlite3
from typing import List, Dict, Any

# プロジェクトルートをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.database import get_conn
from app.reco.embedding import EmbeddingClient
from app.config import settings

def compute_embeddings():
    print("Starting embedding computation...")
    
    if not settings.GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY is not set.")
        return

    client = EmbeddingClient()
    
    with get_conn() as conn:
        # 1. 全銘柄を取得
        sql = """
            SELECT 
                m.sake_id, m.name, m.brewery, m.prefecture,
                GROUP_CONCAT(t.text, ' ') as all_text
            FROM sake_master m
            LEFT JOIN sake_texts t ON m.sake_id = t.sake_id
            GROUP BY m.sake_id
        """
        cursor = conn.execute(sql)
        rows = cursor.fetchall()
        
        print(f"Found {len(rows)} sakes.")
        
        # 2. Embeddingを計算して保存
        updated_count = 0
        for row in rows:
            sake_id = row['sake_id']
            name = row['name']
            brewery = row['brewery'] or ""
            prefecture = row['prefecture'] or ""
            texts = row['all_text'] or ""
            
            # 埋め込み対象のテキストを作成
            # 銘柄名、蔵元、都道府県、説明文を含める
            content = f"{name} {brewery} {prefecture} {texts}"
            
            # テキストが短すぎる場合はスキップ（あるいは名前だけでもやるか）
            if len(content.strip()) == 0:
                print(f"Skipping sake_id={sake_id} (empty content)")
                continue
                
            print(f"Processing sake_id={sake_id} ({name})...")
            
            try:
                embedding = client.get_embedding(content)
                
                # DBに保存
                # sake_vectorsテーブルが存在し、embeddingカラムがある前提
                # taste_vectorは既存のものを維持するか、なければ初期値を入れる
                # ここではUPSERT的に処理したいが、SQLiteのバージョンによる
                # まずは既存行があるか確認
                
                check_sql = "SELECT sake_id, taste_vector FROM sake_vectors WHERE sake_id = ?"
                curr_row = conn.execute(check_sql, (sake_id,)).fetchone()
                
                embedding_json = json.dumps(embedding)
                
                if curr_row:
                    # 更新
                    update_sql = "UPDATE sake_vectors SET embedding = ?, computed_at = datetime('now') WHERE sake_id = ?"
                    conn.execute(update_sql, (embedding_json, sake_id))
                else:
                    # 新規 (taste_vectorはデフォルト値でとりあえず埋める)
                    insert_sql = """
                        INSERT INTO sake_vectors (sake_id, embedding, taste_vector, computed_at)
                        VALUES (?, ?, ?, datetime('now'))
                    """
                    # taste_vectorは空配列のJSONにしておく（アプリ側でハンドリング必要）
                    default_taste = "[0,0,0,0]"
                    conn.execute(insert_sql, (sake_id, embedding_json, default_taste))
                
                updated_count += 1
                conn.commit()
                
                # Rate Limit回避のためのウェイト
                time.sleep(1.0) 
                
            except Exception as e:
                print(f"Error processing sake_id={sake_id}: {e}")
                # 継続する
    
    print(f"Finished. Updated {updated_count} sakes.")

if __name__ == "__main__":
    compute_embeddings()
