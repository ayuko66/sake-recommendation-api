import sqlite3
import sys
import os

# 追加: プロジェクトルートをパスに追加して app モジュールをインポート可能にする
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.db.core import get_conn
from scripts.sakenowa_client import SakenowaClient

def run_migrations():
    print("Running migrations...")
    with get_conn() as conn:
        # DB拡張
        # column check
        try:
            conn.execute("SELECT source FROM sake_master LIMIT 1")
        except sqlite3.OperationalError:
            print("Adding 'source' column to sake_master")
            conn.execute("ALTER TABLE sake_master ADD COLUMN source TEXT DEFAULT 'manual'")
        
        try:
            conn.execute("SELECT external_sakenowa_id FROM sake_master LIMIT 1")
        except sqlite3.OperationalError:
            print("Adding 'external_sakenowa_id' column to sake_master")
            conn.execute("ALTER TABLE sake_master ADD COLUMN external_sakenowa_id INTEGER")
            
        # SQLファイル実行
        with open("app/db/migrations/001_sakenowa.sql", "r") as f:
            sql = f.read()
            conn.executescript(sql)
    print("Migrations done.")

def load_sakenowa_data():
    client = SakenowaClient()
    
    with get_conn() as conn:
        # ingest log start
        conn.execute("INSERT INTO ingest_runs (source, status, started_at) VALUES (?, ?, datetime('now'))", ("sakenowa", "running"))
        
        try:
            # 1. Areas
            data = client.get_areas()
            print(f"Upserting {len(data)} areas...")
            for row in data:
                conn.execute("INSERT OR REPLACE INTO sakenowa_areas (areaId, name) VALUES (?, ?)", (row["id"], row["name"]))

            # 2. Breweries
            data = client.get_breweries()
            print(f"Upserting {len(data)} breweries...")
            for row in data:
                conn.execute("INSERT OR REPLACE INTO sakenowa_breweries (breweryId, name, areaId) VALUES (?, ?, ?)", (row["id"], row["name"], row["areaId"]))

            # 3. Brands
            data = client.get_brands()
            print(f"Upserting {len(data)} brands...")
            for row in data:
                conn.execute("INSERT OR REPLACE INTO sakenowa_brands (brandId, name, breweryId) VALUES (?, ?, ?)", (row["id"], row["name"], row["breweryId"]))
            
            # 4. Flavor Charts
            data = client.get_flavor_charts()
            print(f"Upserting {len(data)} flavor charts...")
            for row in data:
                conn.execute("""
                    INSERT OR REPLACE INTO sakenowa_flavor_charts (brandId, f1, f2, f3, f4, f5, f6) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (row["brandId"], row["f1"], row["f2"], row["f3"], row["f4"], row["f5"], row["f6"]))

            # 5. Tags
            data = client.get_tags()
            print(f"Upserting {len(data)} tags...")
            for row in data:
                conn.execute("INSERT OR REPLACE INTO sakenowa_tags (tagId, tagName) VALUES (?, ?)", (row["id"], row["tag"]))

            # 6. Brand Tags
            data = client.get_brand_tags()
            print(f"Upserting {len(data)} brand tags...")
            conn.execute("DELETE FROM sakenowa_sake_tags") 
            for row in data:
                brand_id = row["brandId"]
                tag_ids = row["tagIds"] # List[int]
                for tid in tag_ids:
                    conn.execute("INSERT OR IGNORE INTO sakenowa_sake_tags (brandId, tagId) VALUES (?, ?)", (brand_id, tid))

            # 7. Rankings
            data = client.get_rankings()
            
            print(f"Upserting rankings...")
            conn.execute("DELETE FROM sakenowa_rankings")
            
            count = 0
            for year_data in data:
                if not isinstance(year_data, dict): continue
                ym = year_data.get("yearMonth")
                ranks = year_data.get("overall", [])
                if not ranks:
                    ranks = year_data.get("ranking", [])
                
                for r in ranks:
                    conn.execute("INSERT INTO sakenowa_rankings (yearMonth, rank, brandId, score) VALUES (?, ?, ?, ?)", 
                                 (ym, r["rank"], r["brandId"], r.get("score")))
                    count += 1
            print(f"Upserted {count} ranking records.")


            # --- Transfer to Internal Model (sake_master, sake_texts) ---
            print("Transferring to internal model...")
            
            # sake_master へ取り込み
            # sakenowa_brands + breweries + areas => sake_master
            sql_master = """
                SELECT b.brandId, b.name as brandName, br.name as breweryName, a.name as prefName
                FROM sakenowa_brands b
                LEFT JOIN sakenowa_breweries br ON b.breweryId = br.breweryId
                LEFT JOIN sakenowa_areas a ON br.areaId = a.areaId
            """
            rows = conn.execute(sql_master).fetchall()
            
            updated_count = 0
            inserted_count = 0
            
            for r in rows:
                # Check exist by external_id
                cursor = conn.execute("SELECT sake_id FROM sake_master WHERE external_sakenowa_id = ?", (r["brandId"],))
                existing = cursor.fetchone()
                
                if existing:
                    conn.execute("""
                        UPDATE sake_master SET 
                            name = ?, brewery = ?, prefecture = ?, updated_at = datetime('now')
                        WHERE sake_id = ?
                    """, (r["brandName"], r["breweryName"], r["prefName"], existing[0]))
                    sake_id = existing[0]
                    updated_count += 1
                else:
                    conn.execute("""
                        INSERT INTO sake_master (name, brewery, prefecture, source, external_sakenowa_id)
                        VALUES (?, ?, ?, 'sakenowa', ?)
                    """, (r["brandName"], r["breweryName"], r["prefName"], r["brandId"]))
                    sake_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                    inserted_count += 1

                # sake_texts へ取り込み (タグ情報)
                tags_query = """
                    SELECT t.tagName 
                    FROM sakenowa_sake_tags st
                    JOIN sakenowa_tags t ON st.tagId = t.tagId
                    WHERE st.brandId = ?
                """
                tags = [tr[0] for tr in conn.execute(tags_query, (r["brandId"],)).fetchall()]
                
                if tags:
                    tag_text = "さけのわタグ: " + ", ".join(tags)
                    # テキスト重複チェック
                    conn.execute("DELETE FROM sake_texts WHERE sake_id = ? AND source = 'sakenowa_tags'", (sake_id,))
                    conn.execute("""
                        INSERT INTO sake_texts (sake_id, source, text, created_at)
                        VALUES (?, 'sakenowa_tags', ?, datetime('now'))
                    """, (sake_id, tag_text))
            
            print(f"Master Sync: Inserted={inserted_count}, Updated={updated_count}")

            # Log success
            conn.execute("UPDATE ingest_runs SET status = 'success', ended_at = datetime('now') WHERE status = 'running'")
            print("Completed successfully.")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            conn.execute("UPDATE ingest_runs SET status = 'failed', ended_at = datetime('now'), detail = ? WHERE status = 'running'", (str(e),))
            # raise

if __name__ == "__main__":
    run_migrations()
    load_sakenowa_data()
