-- Avalytics Database Schema

CREATE TABLE IF NOT EXISTS transactions (
    tx_hash TEXT PRIMARY KEY,
    block_number INTEGER NOT NULL,
    from_address TEXT NOT NULL,
    to_address TEXT,
    value TEXT,
    gas_price TEXT,
    gas_used INTEGER,
    status INTEGER,
    timestamp DATETIME,
    input_data TEXT
);

CREATE INDEX IF NOT EXISTS idx_tx_block ON transactions(block_number);
CREATE INDEX IF NOT EXISTS idx_tx_from ON transactions(from_address);
CREATE INDEX IF NOT EXISTS idx_tx_to ON transactions(to_address);
CREATE INDEX IF NOT EXISTS idx_tx_timestamp ON transactions(timestamp);

CREATE TABLE IF NOT EXISTS event_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tx_hash TEXT NOT NULL,
    block_number INTEGER NOT NULL,
    log_index INTEGER NOT NULL,
    address TEXT NOT NULL,
    topic0 TEXT,
    topic1 TEXT,
    topic2 TEXT,
    topic3 TEXT,
    data TEXT,
    timestamp DATETIME
);

CREATE INDEX IF NOT EXISTS idx_log_tx ON event_logs(tx_hash);
CREATE INDEX IF NOT EXISTS idx_log_block ON event_logs(block_number);
CREATE INDEX IF NOT EXISTS idx_log_address ON event_logs(address);
CREATE INDEX IF NOT EXISTS idx_log_topic0 ON event_logs(topic0);

CREATE TABLE IF NOT EXISTS wallet_profiles (
    wallet_address TEXT PRIMARY KEY,
    first_seen DATETIME,
    last_active DATETIME,
    total_txs INTEGER DEFAULT 0,
    total_volume_wei TEXT DEFAULT '0',
    unique_contracts INTEGER DEFAULT 0,
    is_whale INTEGER DEFAULT 0,
    is_bot INTEGER DEFAULT 0,
    is_dex_user INTEGER DEFAULT 0,
    is_nft_collector INTEGER DEFAULT 0,
    avg_tx_value_wei TEXT,
    behavior_score REAL,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_wallet_last_active ON wallet_profiles(last_active);
CREATE INDEX IF NOT EXISTS idx_wallet_whale ON wallet_profiles(is_whale);
CREATE INDEX IF NOT EXISTS idx_wallet_score ON wallet_profiles(behavior_score);

CREATE TABLE IF NOT EXISTS wallet_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wallet_address TEXT NOT NULL,
    tag TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(wallet_address, tag)
);

CREATE INDEX IF NOT EXISTS idx_tag_wallet ON wallet_tags(wallet_address);
CREATE INDEX IF NOT EXISTS idx_tag_tag ON wallet_tags(tag);

CREATE TABLE IF NOT EXISTS contracts (
    address TEXT PRIMARY KEY,
    name TEXT,
    contract_type TEXT,
    first_seen DATETIME,
    total_interactions INTEGER DEFAULT 0,
    is_verified INTEGER DEFAULT 0
);
