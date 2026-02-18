# 日本酒レコメンドシステム MVP 設計書

## 0. 設計方針(重要)

### 0.1 さけのわAPIは「データソースの1つ」

- **オンラインのリアルタイムAPI呼び出し結果をそのまま返さない**
- さけのわは **Ingest(取り込み)** して自前DBに正規化保存し、推論/推薦は **自前データ** で行う
- 外部API停止・仕様変更・レート制限に耐える

### 0.2 自前価値を必ず挟む3点セット

1. **正規化/名寄せ**: 銘柄名・蔵名・表記ゆれを統一
2. **味ベクトル付与**: レビュー/説明文から taste_vector を生成(自前価値の核)
3. **推薦理由生成**: reason(説明可能性)を返す(EC導入しやすい)

---

## 1. 全体アーキテクチャ

```text
          (External Sources)
   ┌──────────────┐   ┌──────────────┐
   │  さけのわAPI  │   │  酒屋/公式説明 │
   └───────┬──────┘   └───────┬──────┘
           │                  │
           ▼                  ▼
      [ Ingest / Normalize / Enrich ]   ← バッチ/定期実行
           │
           ▼
        [ 自前DB ]
           │
           ▼
      [ Embedding / Taste Vector ]      ← オフライン事前計算
           │
           ▼
  ┌───────────────────────────────┐
  │            FastAPI            │
  │  POST /recommend              │
  │  - Query Embed                │
  │  - Similarity + Ranking       │
  │  - Reason Generation          │
  └───────────────────────────────┘
```

---

## 2. データ設計(自前ドメインモデル)

### 2.1 テーブル構成(最小)
外部APIのJSON構造に寄せず、**自前のモデル** を中心にする。

#### sake_master

| カラム名 | 型 | 説明 |
| --- | --- | --- |
| sake_id | int | 内部ID(自前採番) |
| external_sakenowa_id | int/null | さけのわ側ID(紐付け用) |
| name | string | 銘柄名(正規化後) |
| brewery | string | 蔵元(正規化後) |
| prefecture | string | 都道府県 |
| rice | string/null | 酒米(任意) |
| grade | string/null | 特定名称(純米吟醸など任意) |
| abv | float/null | アルコール度数(任意) |
| updated_at | datetime | 更新日時 |

#### sake_aliases
| カラム名 | 型 | 説明 |
|---|---|---|
| alias_id | int | PK |
| sake_id | int | FK |
| alias | string | 別表記(旧字体/スペース違いなど) |
| source | string | 由来(sakenowa/import/manual) |

#### sake_texts
| カラム名 | 型 | 説明 |
|---|---|---|
| text_id | int | PK |
| sake_id | int | FK |
| source | string | "sakenowa_review" / "shop_desc" / "official" |
| text | text | 生テキスト |
| lang | string | "ja" |
| created_at | datetime | 追加日時 |

#### sake_vectors
| カラム名 | 型 | 説明 |
|---|---|---|
| sake_id | int | PK/FK |
| embedding | blob/array | テキスト埋め込み(任意) |
| taste_vector | array[float] | 味ベクトル(後述) |
| computed_at | datetime | 計算日時 |
| version | string | 生成ロジックのバージョン |

#### ingest_runs
| カラム名 | 型 | 説明 |
|---|---|---|
| run_id | int | PK |
| source | string | "sakenowa" 等 |
| status | string | success/failed |
| started_at | datetime | 開始 |
| ended_at | datetime | 終了 |
| detail | text | エラーや件数ログ |

> DBはMVPでは SQLite / DuckDB でOK。将来はPostgreSQLに移行可能。

---

## 3. 味ベクトル設計(自前価値の核)

### 3.1 ベクトル定義
```
[sweet_dry, body, fruity, modern]
```

- sweet_dry: -1.0(辛口) ～ 1.0(甘口)
- body: -1.0(淡麗) ～ 1.0(芳醇)
- fruity: 0.0 / 0.5 / 1.0 (low/mid/high)
- modern: -1.0(クラシック) ～ 1.0(モダン)

### 3.2 生成方式

#### 方式A: 辞書スコアリング (v1 - MVP)

- テキスト中の語彙をカウントして軸スコア化
- 例: modern_words と classic_words の差を正規化して modern を算出


#### 方式B: Embedding + 軸射影 (v2)
- **Gemini API (`models/gemini-embedding-001`)** を使用してテキストをベクトル化
- 入力テキストと全銘柄の Embedding 同士で Cosine Similarity を計算
- 意味的な類似度（味、香り、シーンのマッチ度）でランキング

---

## 4. 推論/推薦フロー

### 4.1 オフライン(定期バッチ)

1. 外部データをIngestして自前DBへ保存
2. 正規化(名寄せ/表記ゆれ)
3. sake_texts を集約して embedding / taste_vector を計算
4. sake_vectors に保存(推論を高速化)

### 4.2 オンライン(API)

1. 設定(`USE_EMBEDDING`)により分岐
   - **Embeddingモード**: 入力テキストをGemini APIでベクトル化し、DB内の `embedding` とCos類似度計算
   - **Dictモード**: 入力テキストから `taste_vector` を推定し、DB内の `taste_vector` とL2距離計算
2. ランキング(スコア合成)
3. reason を生成して返却 (Embeddingモードでも、説明生成にはDictベースのキーワード抽出を併用)

---

## 5. ランキング設計(単なる類似検索で終わらせない)

### 5.1 スコア合成例

- text_similarity: 入力embeddingと酒embeddingのcosine
- taste_similarity: 入力tasteと酒tasteの近さ(例えばL2距離→スコア化)
- popularity: さけのわ等の人気指標を正規化(任意)

例:
```
final_score = 0.7*text_similarity + 0.2*taste_similarity + 0.1*popularity
```

### 5.2 偏り抑制(予定)

- 同一蔵が上位を独占しないようペナルティ
- 同一カテゴリ(例: すべて純米吟醸)に偏りすぎたら再ランキング

---

## 6. API設計(外部APIのJSONを返さない)

### 6.1 エンドポイント

```
POST /recommend
```

### 6.2 Request

```json
{
  "text": "白ワインみたいな日本酒が好き",
  "top_k": 5,
  "filters": {
    "prefecture": ["新潟県", "山形県"],
    "exclude_brewery": ["○○酒造"]
  },
  "debug": false
}
```

### 6.3 Response

```json
{
  "input_text": "白ワインみたいな日本酒が好き",
  "top_k": 5,
  "mode": "dict",
  "query": {
    "taste_vector": [0.2, -0.4, 1.0, 0.6]
  },
  "recommendations": [
    {
      "sake_id": 1,
      "name": "〇〇 純米吟醸",
      "brewery": "蔵元名",
      "prefecture": "都道府県",
      "score": 0.82,
      "distance": 0.22,
      "taste_vector": [0.2, -0.4, 1.0, 0.6],
      "reason": "フルーティでモダン寄りの香味表現が入力に近い"
    }
  ]
}
```

---

## 7. 外部データ依存を吸収する実装(Adapterパターン)

### 7.1 インターフェース
- `SakeSourceClient` を定義し、`SakenowaClient` はその実装の1つにする
- 将来、酒屋DB/CSV/別APIへ差し替え可能

### 7.2 取得戦略
- **リアルタイム参照を避ける**
- Ingestバッチで差分更新
- 失敗時は前回成功データでサービス継続

---

## 8. 技術スタック

| 領域 | 技術 |
| --- | --- |
| API | FastAPI |
| DB | SQLite / DuckDB |
| NLP | **Gemini API (Embedding)** / SBERT |
| MxL | cosine similarity + スコア合成 |
| バッチ | Python scripts / cron |
| Deploy | ローカル / Render |

---

## 9. 非機能要件(MVP)

- オンライン推論はDB参照中心で **レスポンス1秒以内**
- 推論再現性: `taste_vector` の生成ロジックに **version** を付ける
- READMEで「なぜラッパーでないか」を説明できる構成

---

## 10. 拡張余地

- 協調フィルタリング(レビュー蓄積後)
- ユーザー嗜好履歴/セッション推薦
- 料理画像→推薦
- EC向けSDK/プラグイン化
