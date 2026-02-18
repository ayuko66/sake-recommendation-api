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
    Returns:
        (vector, scores, hits)
        - vector: [sweet_dry, body, fruity, style]
        - scores: 各項目の素点辞書
        - hits: 各項目のヒット単語リスト辞書
    """
    if not text:
        return [0.0, 0.0, 0.0, 0.0], {}, {}

    scores = {}
    hits = {}

    def _calc(category: str, lexicon: Dict[str, float]):
        matched = {k: v for k, v in lexicon.items() if k in text}
        if matched:
            scores[category] = max(matched.values())
            # マッチした単語を全て記録 (理由生成で使う)
            hits[category] = list(matched.keys())
        else:
            scores[category] = 0.0
            hits[category] = []

    _calc("sweet", SWEET_WORDS)
    _calc("dry", DRY_WORDS)
    _calc("light", LIGHT_WORDS)
    _calc("rich", RICH_WORDS)
    _calc("fruity", FRUITY_WORDS)
    _calc("modern", MODERN_WORDS)
    _calc("classic", CLASSIC_WORDS)

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
    
    return vector, scores, hits
