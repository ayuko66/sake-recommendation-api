import math
from typing import List, Dict, Any, Optional
from .. import database as db
from ..models import RecommendationRequest, RecommendationResponse, RecommendationItem, RecommendationQuery
from ..config import settings
from .taste_v1 import estimate_taste_vector
from .embedding import EmbeddingClient

def _generate_reason(cand: Dict[str, Any], q_hits: Dict[str, List[str]], s_vector: List[float]) -> str:
    """
    推薦理由を生成する
    """
    # 1. ユーザー入力でヒットした特徴
    hit_cats = []
    # 優先度順にチェック
    if q_hits.get("fruity"): hit_cats.append("フルーティ")
    if q_hits.get("light"): hit_cats.append("すっきり")
    if q_hits.get("rich"): hit_cats.append("芳醇/旨味")
    if q_hits.get("sweet"): hit_cats.append("甘口")
    if q_hits.get("dry"): hit_cats.append("辛口/キレ")
    if q_hits.get("modern"): hit_cats.append("モダン")
    if q_hits.get("classic"): hit_cats.append("クラシック")
    
    parts = []
    if hit_cats:
        # 重複を除去しつつ先頭2つを採用
        u_keywords = "」や「".join(hit_cats[:2])
        parts.append(f"「{u_keywords}」というご希望に対し")
    else:
        parts.append("ご希望のイメージに対し")

    # 2. お酒の特徴 (ベクトル値から)
    # vector: [sweet_dry, body, fruity, style]
    # sweet_dry: -1(sweet) ~ 1(dry)
    # body: -1(light) ~ 1(rich)
    # fruity: 0 ~ 1
    # style: -1(classic) ~ 1(modern)
    
    s_features = []
    
    # フルーティ
    if s_vector[2] >= 0.8:
        s_features.append("華やかな香り")
    elif s_vector[2] >= 0.4:
        s_features.append("程よい香り")

    # ボディ
    if s_vector[1] >= 0.4:
        s_features.append("しっかりとした旨味")
    elif s_vector[1] <= -0.4:
        s_features.append("軽快な飲み口")
        
    # 甘辛 (Positive=Sweet, Negative=Dry)
    if s_vector[0] >= 0.5:
        s_features.append("優しい甘み")
    elif s_vector[0] <= -0.5:
        s_features.append("キレのある後味")

    if s_features:
        # 特徴を結合
        desc = "、".join(s_features[:2]) # 長くなりすぎないように2つまで
        parts.append(f"このお酒は{desc}が特徴で、相性が良いと判断しました。")
    else:
        parts.append("全体のバランスが良く、おすすめの一本です。")

    return "、".join(parts)

def recommend(request: RecommendationRequest) -> RecommendationResponse:
    # 1. 入力テキストのベクトル化
    q_vector, _, q_hits = estimate_taste_vector(request.text)
    
    q_embedding = None
    mode = "dict"
    if settings.USE_EMBEDDING == 1:
        try:
            client = EmbeddingClient()
            q_embedding = client.get_query_embedding(request.text)
            mode = "embedding"
        except Exception as e:
            print(f"Failed to get embedding: {e}")
            # フォールバック: 従来モード
            pass
    
    # 2. 候補データの取得
    candidates = db.get_all_sakes_with_vectors()
    
    # 3. フィルタリング
    filtered_candidates = []
    for cand in candidates:
        # 都道府県フィルタ
        if request.filters and request.filters.prefecture:
            if cand["prefecture"] not in request.filters.prefecture:
                continue
        
        # 蔵元除外フィルタ
        if request.filters and request.filters.exclude_brewery:
            # 部分一致で除外判定 (簡易的)
            is_excluded = False
            for excl in request.filters.exclude_brewery:
                if cand["brewery"] and excl in cand["brewery"]:
                    is_excluded = True
                    break
            if is_excluded:
                continue
                
        filtered_candidates.append(cand)

    # 4. スコア計算
    scored_items = []
    for cand in filtered_candidates:
        s_vector = cand["vector"]
        
        if settings.USE_EMBEDDING == 1 and cand.get("embedding"):
            # Embeddingによる類似度計算 (Cosine Similarity)
            # q_embedding はループの外で計算すべきだが、構造上ここで参照できるようにする
            # recommend関数の冒頭で計算しておく
            if q_embedding is None:
                 # フォールバック (あるいはエラー)
                 score = 0
                 dist = 1.0 # 適当な大文字
            else:
                s_embedding = cand["embedding"]
                # Cosine Similarity: dot(A, B) / (norm(A) * norm(B))
                # Gemini Embeddingは通常正規化されていると仮定できるが、念のため計算
                
                dot_product = sum(a * b for a, b in zip(q_embedding, s_embedding))
                norm_q = math.sqrt(sum(a * a for a in q_embedding))
                norm_s = math.sqrt(sum(b * b for b in s_embedding))
                
                if norm_q * norm_s == 0:
                    similarity = 0.0
                else:
                    similarity = dot_product / (norm_q * norm_s)
                
                # スコアは類似度そのものを使う (0~1)
                score = similarity
                # distanceは便宜上 1 - similarity とする
                dist = 1.0 - similarity

        else:
            # 従来ロジック: L2距離 (Euclidean distance)
            # q_vector, s_vector は共に float のリスト
            dist = math.sqrt(sum((q - s) ** 2 for q, s in zip(q_vector, s_vector)))
            
            # スコア化 (距離が0に近いほどスコアは1に近づく)
            score = 1.0 / (1.0 + dist)
        
        # 理由生成
        reason_text = _generate_reason(cand, q_hits, s_vector)
        
        item = RecommendationItem(
            sake_id=cand["sake_id"],
            name=cand["name"],
            brewery=cand["brewery"],
            prefecture=cand["prefecture"],
            score=score,
            distance=dist,
            taste_vector=s_vector,
            reason=reason_text,
            debug_info={"hits": q_hits} if request.debug else None
        )
        scored_items.append(item)
    
    # 5. ランキング (スコア降順)
    scored_items.sort(key=lambda x: x.score, reverse=True)
    
    # top_k 件返す
    top_k = request.top_k if request.top_k else 5
    result_items = scored_items[:top_k]
    
    return RecommendationResponse(
        input_text=request.text,
        top_k=top_k,
        mode=mode,
        query=RecommendationQuery(taste_vector=q_vector),
        recommendations=result_items
    )
