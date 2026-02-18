
import sys
import os
import unittest
from unittest.mock import MagicMock, patch
import json

# プロジェクトルートをパスに追加
sys.path.append(os.getcwd())

from app.config import settings
from app.models import RecommendationRequest

# google.generativeai を使用するモジュールをインポートする前にモック化
sys.modules["google.generativeai"] = MagicMock()

def test_embedding_flow():
    print("Testing Embedding Flow with Mocks...")

    # モックデータ
    mock_embedding = [0.1] * 768
    
    # 1. Embedding計算スクリプトのテスト
    print("\n[1] Testing scripts/compute_embeddings.py")
    
    # スクリプトモジュールをインポート
    # スクリプトとして実行されるが、関数 compute_embeddings() も持っているためインポート可能
    from scripts.compute_embeddings import compute_embeddings
    
    # 使用されている箇所でパッチを当てる
    with patch("scripts.compute_embeddings.EmbeddingClient") as MockClient:
        # 設定のモック
        settings.GEMINI_API_KEY = "DUMMY_KEY"
        
        instance = MockClient.return_value
        instance.get_embedding.return_value = mock_embedding
        
        # 計算実行（注意: 実際のDBを更新しないようにする）
        # テスト用DBを使うべきだが、ここでは compute_embeddings 内の get_conn をモック化して
        # 実際のDBへの書き込みを回避する。
        
        with patch("scripts.compute_embeddings.get_conn") as mock_get_conn:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            mock_conn.execute.return_value = mock_cursor
            
            # 銘柄取得のモック
            mock_cursor.fetchall.return_value = [
                {"sake_id": 1, "name": "Sake A", "brewery": "B1", "prefecture": "P1", "all_text": "text"}
            ]
            # 既存ベクトルの取得モック
            mock_cursor.fetchone.return_value = None # 既存なし
            
            compute_embeddings()
            
            # 呼び出し確認
            assert instance.get_embedding.call_count == 1
            print("  -> compute_embeddings called get_embedding: OK")
            
            # DBへの書き込み確認
            # INSERT または UPDATE が実行されたか
            args, _ = mock_conn.execute.call_args_list[-1]
            sql_executed = args[0]
            print(f"  -> Last SQL executed: {sql_executed[:50]}...")
            assert "INSERT INTO sake_vectors" in sql_executed or "UPDATE sake_vectors" in sql_executed
            print("  -> DB Update attempted: OK")

    # 2. レコメンドエンジンのテスト
    print("\n[2] Testing app/reco/engine.py")
    from app.reco import engine
    
    # Embeddingモードを強制的に有効化
    settings.USE_EMBEDDING = 1
    
    # 使用されている箇所でパッチを当てる
    with patch("app.reco.engine.EmbeddingClient") as MockClient:
        instance = MockClient.return_value
        instance.get_query_embedding.return_value = [0.1] * 768 # 次元数を合わせる
        
        # DBの get_all_sakes_with_vectors をモック化して、ダミーデータと有効な taste_vector を返す
        with patch("app.database.get_all_sakes_with_vectors") as mock_get_all:
             mock_get_all.return_value = [
                 {
                     "sake_id": 1, 
                     "name": "Sake A", 
                     "brewery": "B1", 
                     "prefecture": "P1", 
                     "vector": [0.1, 0.2, 0.3, 0.4], # taste_vector
                     "embedding": [0.1] * 768  # 完全一致
                 },
                 {
                     "sake_id": 2, 
                     "name": "Sake B", 
                     "brewery": "B2", 
                     "prefecture": "P2", 
                     "vector": [0.9, 0.9, 0.9, 0.9], 
                     "embedding": [0.0] * 768 # 直交 -> 類似度0
                 }
             ]
             
             req = RecommendationRequest(text="dummy")
             resp = engine.recommend(req)
             
             print(f"  -> Response mode: {resp.mode}")
             assert resp.mode == "embedding"
             print("  -> Mode check: OK")
             
             top_item = resp.recommendations[0]
             print(f"  -> Top item score: {top_item.score}")
             # 同一ベクトルのコサイン類似度は 1.0 になるはず
             assert top_item.score > 0.99
             print("  -> Score calculation: OK")
             
             # 理由生成の確認 (taste_vector に基づくロジックが走るか確認)
             # q_hits は既存ロジック由来。dummyテキストなのでヒットなしの汎用メッセージになるはず。
             print(f"  -> Reason: {top_item.reason}")

    print("\n✅ Verification Passed!")

if __name__ == "__main__":
    test_embedding_flow()
