from typing import List
from .lexicon_v1 import (
    SWEET_WORDS, DRY_WORDS, LIGHT_WORDS, RICH_WORDS,
    FRUITY_WORDS, MODERN_WORDS, CLASSIC_WORDS
)

from typing import List, Dict, Tuple, Any

def estimate_taste_vector(text: str) -> Tuple[List[float], Dict[str, float]]:
    """
    テキストから日本酒の味ベクトル(4次元)とスコア明細を推定する。
    
    Returns:
        (vector, scores)
        - vector: [sweet_dry, body, fruity, style]
        - scores: 各項目の素点辞書
    """
    if not text:
        return [0.0, 0.0, 0.0, 0.0], {}

    # 各要素のスコアを計算 (最大のスコアを採用)
    scores = {
        "sweet": max([v for k, v in SWEET_WORDS.items() if k in text] + [0.0]),
        "dry": max([v for k, v in DRY_WORDS.items() if k in text] + [0.0]),
        "light": max([v for k, v in LIGHT_WORDS.items() if k in text] + [0.0]),
        "rich": max([v for k, v in RICH_WORDS.items() if k in text] + [0.0]),
        "fruity": max([v for k, v in FRUITY_WORDS.items() if k in text] + [0.0]),
        "modern": max([v for k, v in MODERN_WORDS.items() if k in text] + [0.0]),
        "classic": max([v for k, v in CLASSIC_WORDS.items() if k in text] + [0.0]),
    }

    # 4次元ベクトルの組み立て
    # 1. 甘辛 
    sweet_dry = scores["sweet"] - scores["dry"]
    
    # 2. 濃淡 (芳醇 - 淡麗)
    body = scores["rich"] - scores["light"]
    
    # 3. フルーティ度 (擬似カテゴリ 0 / 0.5 / 1.0 に丸める)
    if scores["fruity"] >= 0.75:
        fruity = 1.0
    elif scores["fruity"] >= 0.25:
        fruity = 0.5
    else:
        fruity = 0.0
        
    # 4. スタイル (モダン - クラシック)
    style = scores["modern"] - scores["classic"]

    # クランプ処理 (-1.0 ～ 1.0)
    vector = [
        max(-1.0, min(1.0, sweet_dry)),
        max(-1.0, min(1.0, body)),
        fruity,
        max(-1.0, min(1.0, style))
    ]
    
    return vector, scores
