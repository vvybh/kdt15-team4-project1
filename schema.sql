CREATE TABLE IF NOT EXISTS crawl_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    keyword TEXT,
    category TEXT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    item_count INTEGER DEFAULT 0,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS raw_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crawl_run_id INTEGER,
    source TEXT NOT NULL,
    collected_keyword TEXT,
    source_item_id TEXT,
    source_url TEXT,
    raw_title TEXT,
    raw_price TEXT,
    raw_status TEXT,
    raw_location TEXT,
    raw_date TEXT,
    raw_category TEXT,
    raw_condition TEXT,
    raw_components TEXT,
    raw_shipping_fee TEXT,
    raw_trade_method TEXT,
    raw_image_url TEXT,
    raw_description TEXT,
    raw_payload TEXT,
    crawled_at TEXT NOT NULL,
    FOREIGN KEY (crawl_run_id) REFERENCES crawl_runs(id)
);

CREATE TABLE IF NOT EXISTS market_items (
    id INTEGER PRIMARY KEY,
    raw_item_id INTEGER,
    source TEXT NOT NULL,
    collected_keyword TEXT,
    source_item_id TEXT,
    source_url TEXT,
    title TEXT NOT NULL,
    normalized_title TEXT,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    source_category TEXT,
    brand TEXT,
    model_name TEXT,
    product_key TEXT NOT NULL,
    item_condition TEXT,
    components TEXT,
    price INTEGER NOT NULL,
    currency TEXT NOT NULL DEFAULT 'KRW',
    trade_status TEXT,
    source_status TEXT,
    listed_at TEXT,
    sold_at TEXT,
    location TEXT,
    shipping_fee INTEGER,
    trade_method TEXT,
    image_url TEXT,
    description TEXT,
    crawled_at TEXT NOT NULL,
    FOREIGN KEY (raw_item_id) REFERENCES raw_items(id)
);

CREATE TABLE IF NOT EXISTS price_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    market_item_id INTEGER NOT NULL,
    product_key TEXT NOT NULL,
    price INTEGER NOT NULL,
    observed_at TEXT NOT NULL,
    source TEXT NOT NULL,
    trade_status TEXT,
    item_condition TEXT,
    FOREIGN KEY (market_item_id) REFERENCES market_items(id)
);

CREATE TABLE IF NOT EXISTS auctions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    brand TEXT,
    model_name TEXT,
    product_key TEXT NOT NULL,
    description TEXT,
    image_url TEXT,
    seller_name TEXT NOT NULL,
    start_price INTEGER NOT NULL,
    current_price INTEGER NOT NULL,
    bid_unit INTEGER NOT NULL DEFAULT 1000,
    end_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    item_condition TEXT,
    components TEXT,
    created_at TEXT NOT NULL,
    winner_name TEXT,
    winning_bid INTEGER
);

CREATE TABLE IF NOT EXISTS bids (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    auction_id INTEGER NOT NULL,
    bidder_name TEXT NOT NULL,
    bid_amount INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (auction_id) REFERENCES auctions(id)
);

CREATE TABLE IF NOT EXISTS inspection_statuses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    auction_id INTEGER NOT NULL UNIQUE,
    status TEXT NOT NULL,
    note TEXT,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (auction_id) REFERENCES auctions(id)
);

CREATE INDEX IF NOT EXISTS idx_market_items_product_key ON market_items(product_key);
CREATE INDEX IF NOT EXISTS idx_price_snapshots_product_key ON price_snapshots(product_key);
CREATE INDEX IF NOT EXISTS idx_auctions_status ON auctions(status);
CREATE INDEX IF NOT EXISTS idx_bids_auction_id ON bids(auction_id);
