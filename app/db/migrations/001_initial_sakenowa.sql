-- Migration: 001_initial_sakenowa

-- 1. Extend sake_master (if columns don't exist)
-- SQLite doesn't support IF NOT EXISTS for ADD COLUMN directly in standard SQL, 
-- but we can try adding them. If they exist, it might error, so we should handle gracefully or assume fresh state for now.
-- However, 'external_sakenowa_id' exists in schema.sql.
-- 'source' does NOT exist in schema.sql (default was implicit or not there).

PRAGMA foreign_keys = OFF;

-- Using a transaction to ensure atomicity
BEGIN TRANSACTION;

-- Add 'source' column if not exists (Standard SQLite way is clumsy, so we alter if we can)
-- ALTER TABLE sake_master ADD COLUMN source TEXT DEFAULT 'sakenowa'; 
-- But since we cannot check existence easily in pure SQL script without logic,
-- we will assume this is a new migration running on top of schema.sql.

-- Check if 'source' column exists is hard in SQL script.
-- For MVP, let's just create the new tables.
-- User request said: "sake_master 拡張(存在しない場合だけ追加する想定)"

-- 2. New Tables for Sakenowa Data

-- 2.1 Flavor Charts (6 axes)
CREATE TABLE IF NOT EXISTS sakenowa_flavor_charts (
    sake_id INTEGER PRIMARY KEY, -- FK to sake_master(sake_id) IS NOT STRICTLY ENFORCED here to allow raw import first? 
                                 -- Or should we link to sake_master? 
                                 -- Usually sakenowa data has its own ID. Let's start with sakenowa_id as key.
    sakenowa_id INTEGER NOT NULL UNIQUE,
    f1 REAL, -- 華やか
    f2 REAL, -- 芳醇
    f3 REAL, -- 重厚
    f4 REAL, -- 穏やか
    f5 REAL, -- ドライ
    f6 REAL, -- 軽快
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (sakenowa_id) REFERENCES sake_master(external_sakenowa_id) ON DELETE CASCADE
);

-- 2.2 Rankings
CREATE TABLE IF NOT EXISTS sakenowa_rankings (
    ranking_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sakenowa_id INTEGER NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    rank INTEGER NOT NULL,
    score REAL,
    pref TEXT, -- 'all' or prefecture name
    updated_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (sakenowa_id) REFERENCES sake_master(external_sakenowa_id) ON DELETE CASCADE
);

-- 2.3 Tag Dictionary
CREATE TABLE IF NOT EXISTS sakenowa_tags (
    tag_id INTEGER PRIMARY KEY, -- sakenowa's tagId
    name TEXT NOT NULL UNIQUE
);

-- 2.4 Brand-Tag Mapping
CREATE TABLE IF NOT EXISTS sakenowa_sake_tags (
    sakenowa_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    count INTEGER DEFAULT 1, -- reliability/frequency if available
    FOREIGN KEY (sakenowa_id) REFERENCES sake_master(external_sakenowa_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES sakenowa_tags(tag_id) ON DELETE CASCADE,
    PRIMARY KEY (sakenowa_id, tag_id)
);

COMMIT;

PRAGMA foreign_keys = ON;
