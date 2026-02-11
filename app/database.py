import json
from typing import List, Optional, Dict, Any
from .db.core import get_conn
from .models import SakeListItem, SakeDetail, TasteProfile

def _map_fruity(val: float) -> str:
    if val >= 0.7:
        return "high"
    elif val >= 0.3:
        return "mid"
    else:
        return "low"

def get_total_sakes() -> int:
    with get_conn() as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM sake_master")
        return cursor.fetchone()[0]

def get_sakes(page: int, limit: int) -> List[SakeListItem]:
    offset = (page - 1) * limit
    with get_conn() as conn:
        cursor = conn.execute(
            "SELECT sake_id, name, brewery, prefecture FROM sake_master LIMIT ? OFFSET ?",
            (limit, offset)
        )
        rows = cursor.fetchall()
        return [SakeListItem(**dict(row)) for row in rows]

def get_sake_by_id(sake_id: int) -> Optional[SakeDetail]:
    with get_conn() as conn:
        # 銘柄マスタ取得
        cursor = conn.execute(
            "SELECT * FROM sake_master WHERE sake_id = ?",
            (sake_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        
        sake_dict = dict(row)
        
        # テイストプロファイル取得
        cursor = conn.execute(
            "SELECT taste_vector FROM sake_vectors WHERE sake_id = ?",
            (sake_id,)
        )
        v_row = cursor.fetchone()
        if v_row:
            vector = json.loads(v_row["taste_vector"])
            # vector: [sweet_dry, body, fruity_val, style]
            sake_dict["taste_profile"] = TasteProfile(
                sweet_dry=vector[0],
                body=vector[1],
                fruity=_map_fruity(vector[2]),
                style=vector[3]
            )
        
        return SakeDetail(**sake_dict)

def search_sakes(query: str, limit: int) -> List[SakeListItem]:
    with get_conn() as conn:
        # 銘柄名または蔵元名で検索
        sql = """
            SELECT sake_id, name, brewery, prefecture 
            FROM sake_master 
            WHERE name LIKE ? OR brewery LIKE ? OR prefecture LIKE ?
            ORDER BY prefecture ASC, brewery ASC, sake_id ASC
            LIMIT ?
        """
        q = f"%{query}%"
        cursor = conn.execute(sql, (q, q, q, limit))
        rows = cursor.fetchall()
        return [SakeListItem(**dict(row)) for row in rows]
