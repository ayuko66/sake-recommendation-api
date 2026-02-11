PRAGMA foreign_keys = ON;

-- 銘柄マスタ(自前ドメインモデル)
CREATE TABLE IF NOT EXISTS sake_master (
  sake_id INTEGER PRIMARY KEY AUTOINCREMENT,
  external_sakenowa_id INTEGER,  -- さけのわのID
  name TEXT NOT NULL,  -- 銘柄名
  brewery TEXT,  -- 蔵元
  prefecture TEXT,  -- 都道府県
  rice TEXT,  -- 米
  grade TEXT,  -- 等級
  abv REAL,  -- アルコール度数
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 表記ゆれ/別名
CREATE TABLE IF NOT EXISTS sake_aliases (
  alias_id INTEGER PRIMARY KEY AUTOINCREMENT,  -- 表記ゆれのID
  sake_id INTEGER NOT NULL,  -- 銘柄ID
  alias TEXT NOT NULL,  -- 表記ゆれ
  source TEXT NOT NULL DEFAULT 'manual',  -- ソース
  FOREIGN KEY (sake_id) REFERENCES sake_master(sake_id) ON DELETE CASCADE
);

-- テキスト(レビュー/商品説明など)
CREATE TABLE IF NOT EXISTS sake_texts (
  text_id INTEGER PRIMARY KEY AUTOINCREMENT,  -- テキストID
  sake_id INTEGER NOT NULL,  -- 銘柄ID
  source TEXT NOT NULL, -- 'sakenowa_review' / 'shop_desc' / 'official'
  text TEXT NOT NULL,  -- テキスト
  lang TEXT NOT NULL DEFAULT 'ja',  -- 言語
  created_at TEXT NOT NULL DEFAULT (datetime('now')),  -- 作成日時
  FOREIGN KEY (sake_id) REFERENCES sake_master(sake_id) ON DELETE CASCADE
);

-- ベクトル(事前計算結果)
CREATE TABLE IF NOT EXISTS sake_vectors (
  sake_id INTEGER PRIMARY KEY,
  embedding BLOB,              -- optional
  taste_vector TEXT NOT NULL,  -- JSON文字列で保存(例: "[0.2,-0.4,1.0,0.6]")
  computed_at TEXT NOT NULL DEFAULT (datetime('now')),  -- 計算日時
  version TEXT NOT NULL DEFAULT 'v1',  -- バージョン
  FOREIGN KEY (sake_id) REFERENCES sake_master(sake_id) ON DELETE CASCADE
);

-- 取り込みログ
CREATE TABLE IF NOT EXISTS ingest_runs ( 
  run_id INTEGER PRIMARY KEY AUTOINCREMENT,  -- 取り込みID
  source TEXT NOT NULL,     -- 'sakenowa' etc
  status TEXT NOT NULL,     -- 'success' / 'failed'
  started_at TEXT NOT NULL,  -- 開始日時
  ended_at TEXT,  -- 終了日時
  detail TEXT  -- 詳細
);

-- インデックス(最低限)
CREATE INDEX IF NOT EXISTS idx_sake_master_name ON sake_master(name);
CREATE INDEX IF NOT EXISTS idx_sake_master_brewery ON sake_master(brewery);
CREATE INDEX IF NOT EXISTS idx_sake_texts_sake_id ON sake_texts(sake_id);