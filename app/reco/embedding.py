
import google.generativeai as genai
from typing import List
import time
from ..config import settings

class EmbeddingClient:
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            # APIキーがない場合は警告を出すか、エラーにする
            # ここでは初期化時にエラーにはせず、呼び出し時にチェックする方針
            pass
        else:
            genai.configure(api_key=settings.GEMINI_API_KEY)

    def get_embedding(self, text: str) -> List[float]:
        """
        テキストのEmbeddingを取得する
        """
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set")
            
        try:
            # モデル名は 'models/gemini-embedding-001' を使用
            result = genai.embed_content(
                model="models/gemini-embedding-001",
                content=text,
                task_type="retrieval_document",
                title=None
            )
            return result['embedding']
        except Exception as e:
            print(f"Error getting embedding: {e}")
            # リトライロジックなどは必要に応じて追加
            raise e

    def get_query_embedding(self, text: str) -> List[float]:
        """
        クエリ用のEmbeddingを取得する
        task_typeを retrieval_query に設定
        """
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set")

        try:
            result = genai.embed_content(
                model="models/gemini-embedding-001",
                content=text,
                task_type="retrieval_query"
            )
            return result['embedding']
        except Exception as e:
            print(f"Error getting query embedding: {e}")
            raise e
