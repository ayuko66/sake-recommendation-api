-- sake_master 拡張 (SQLite: check if column exists is hard in pure SQL without PRAGMA)
-- The Python script handles column addition logic.

-- さけのわデータ保存用テーブル
-- Clean up old incorrect tables if any
DROP TABLE IF EXISTS sakenowa_flavor_charts;
DROP TABLE IF EXISTS sakenowa_sake_tags;
DROP TABLE IF EXISTS sakenowa_tags;
DROP TABLE IF EXISTS sakenowa_rankings;
DROP TABLE IF EXISTS sakenowa_brands;
DROP TABLE IF EXISTS sakenowa_breweries;
DROP TABLE IF EXISTS sakenowa_areas;

-- Recreate with correct schema for Raw Ingest

CREATE TABLE sakenowa_areas (
    areaId INTEGER PRIMARY KEY,
    name TEXT
);

CREATE TABLE sakenowa_breweries (
    breweryId INTEGER PRIMARY KEY,
    name TEXT,
    areaId INTEGER,
    FOREIGN KEY (areaId) REFERENCES sakenowa_areas(areaId)
);

CREATE TABLE sakenowa_brands (
    brandId INTEGER PRIMARY KEY,
    name TEXT,
    breweryId INTEGER,
    FOREIGN KEY (breweryId) REFERENCES sakenowa_breweries(breweryId)
);

-- フレーバーチャート (6軸)
CREATE TABLE sakenowa_flavor_charts (
    brandId INTEGER PRIMARY KEY,
    f1 REAL, -- 華やか
    f2 REAL, -- 芳醇
    f3 REAL, -- 重厚
    f4 REAL, -- 穏やか
    f5 REAL, -- ドライ
    f6 REAL, -- 軽快
    FOREIGN KEY (brandId) REFERENCES sakenowa_brands(brandId)
);

-- タグ辞書
CREATE TABLE sakenowa_tags (
    tagId INTEGER PRIMARY KEY,
    tagName TEXT
);

-- ブランド-タグ紐付け
CREATE TABLE sakenowa_sake_tags (
    brandId INTEGER,
    tagId INTEGER,
    PRIMARY KEY (brandId, tagId),
    FOREIGN KEY (brandId) REFERENCES sakenowa_brands(brandId),
    FOREIGN KEY (tagId) REFERENCES sakenowa_tags(tagId)
);

-- ランキング
CREATE TABLE sakenowa_rankings (
    yearMonth INTEGER, -- YYYYMM
    rank INTEGER, 
    brandId INTEGER,
    score REAL, -- 任意
    PRIMARY KEY (yearMonth, rank),
    FOREIGN KEY (brandId) REFERENCES sakenowa_brands(brandId)
);
