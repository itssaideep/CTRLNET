-- CTRLNET Database Schema

-- ──────────────────────────────────────────────────────────────────────
-- Configuration & Metadata
-- ──────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS experiment_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT UNIQUE NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    dataset_version TEXT NOT NULL,
    model TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    temperature REAL NOT NULL,
    condition TEXT NOT NULL
);

-- ──────────────────────────────────────────────────────────────────────
-- Entities
-- ──────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS targets (
    id TEXT PRIMARY KEY,
    ip_address TEXT,
    hostname TEXT,
    os_hint TEXT
);

CREATE TABLE IF NOT EXISTS ground_truth (
    target_id TEXT NOT NULL,
    service TEXT NOT NULL,
    port INTEGER NOT NULL,
    product TEXT,
    vendor TEXT,
    version TEXT,
    cpe TEXT,
    cves TEXT, -- JSON array of CVE IDs
    FOREIGN KEY(target_id) REFERENCES targets(id),
    PRIMARY KEY(target_id, service, port)
);

CREATE TABLE IF NOT EXISTS evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    service TEXT NOT NULL,
    port INTEGER NOT NULL,
    evidence_level TEXT NOT NULL,
    raw_banner TEXT,
    extracted_product TEXT,
    extracted_version TEXT,
    FOREIGN KEY(run_id) REFERENCES experiment_configs(run_id),
    FOREIGN KEY(target_id) REFERENCES targets(id)
);

-- ──────────────────────────────────────────────────────────────────────
-- Predictions
-- ──────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evidence_id INTEGER NOT NULL,
    source TEXT NOT NULL, -- 'DETERMINISTIC' or 'LLM'
    service TEXT,
    product TEXT,
    version TEXT,
    cpe TEXT,
    cves TEXT, -- JSON array
    confidence REAL,
    abstained BOOLEAN,
    latency_ms REAL,
    raw_output TEXT,
    FOREIGN KEY(evidence_id) REFERENCES evidence(id)
);

-- ──────────────────────────────────────────────────────────────────────
-- Evaluations
-- ──────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_id INTEGER NOT NULL UNIQUE,
    verdict TEXT NOT NULL,
    failure_category TEXT,
    product_accurate BOOLEAN,
    version_accurate BOOLEAN,
    cpe_accurate BOOLEAN,
    cve_precision REAL,
    cve_recall REAL,
    cve_f1 REAL,
    FOREIGN KEY(prediction_id) REFERENCES predictions(id)
);

-- ──────────────────────────────────────────────────────────────────────
-- Cache
-- ──────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS nvd_cache (
    cpe TEXT PRIMARY KEY,
    cves TEXT NOT NULL, -- JSON array of CVE objects
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);
