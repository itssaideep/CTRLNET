import asyncio
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiosqlite

from ctrlnet.config import config


class DatabaseManager:
    """Manages async SQLite connections and queries for CTRLNET."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or config.database_path
        self.schema_path = Path(__file__).parent / "schema.sql"

    async def initialize_schema(self):
        """Initialize the database schema if it doesn't exist."""
        config.ensure_dirs()
        async with aiosqlite.connect(self.db_path) as db:
            with open(self.schema_path, "r") as f:
                schema = f.read()
            await db.executescript(schema)
            await db.commit()

    async def execute(self, query: str, parameters: tuple = ()) -> None:
        """Execute a write operation."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(query, parameters)
            await db.commit()

    async def fetch_one(self, query: str, parameters: tuple = ()) -> Optional[sqlite3.Row]:
        """Fetch a single row."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            async with db.execute(query, parameters) as cursor:
                return await cursor.fetchone()

    async def fetch_all(self, query: str, parameters: tuple = ()) -> List[sqlite3.Row]:
        """Fetch multiple rows."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = sqlite3.Row
            async with db.execute(query, parameters) as cursor:
                return await cursor.fetchall()
                
    # ── Experiment Configs ──
    async def create_experiment_config(self, run_id: str, dataset_version: str, model: str, prompt_version: str, temperature: float, condition: str):
        query = """
            INSERT INTO experiment_configs 
            (run_id, dataset_version, model, prompt_version, temperature, condition)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        await self.execute(query, (run_id, dataset_version, model, prompt_version, temperature, condition))

    # ── Evidence ──
    async def save_evidence(self, run_id: str, target_id: str, service: str, port: int, evidence_level: str, raw_banner: str = None, extracted_product: str = None, extracted_version: str = None) -> int:
        query = """
            INSERT INTO evidence 
            (run_id, target_id, service, port, evidence_level, raw_banner, extracted_product, extracted_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query, (run_id, target_id, service, port, evidence_level, raw_banner, extracted_product, extracted_version))
            await db.commit()
            return cursor.lastrowid

    # ── Predictions ──
    async def save_prediction(self, evidence_id: int, source: str, service: str, product: str, version: str, cpe: str, cves: list, confidence: float, abstained: bool, latency_ms: float, raw_output: str) -> int:
        query = """
            INSERT INTO predictions 
            (evidence_id, source, service, product, version, cpe, cves, confidence, abstained, latency_ms, raw_output)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cves_json = json.dumps(cves) if cves is not None else None
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query, (evidence_id, source, service, product, version, cpe, cves_json, confidence, abstained, latency_ms, raw_output))
            await db.commit()
            return cursor.lastrowid
            
    # ── Evaluations ──
    async def save_evaluation(self, prediction_id: int, verdict: str, failure_category: str, product_accurate: bool, version_accurate: bool, cpe_accurate: bool, cve_precision: float, cve_recall: float, cve_f1: float) -> int:
        query = """
            INSERT INTO evaluations 
            (prediction_id, verdict, failure_category, product_accurate, version_accurate, cpe_accurate, cve_precision, cve_recall, cve_f1)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query, (prediction_id, verdict, failure_category, product_accurate, version_accurate, cpe_accurate, cve_precision, cve_recall, cve_f1))
            await db.commit()
            return cursor.lastrowid
            
    # ── NVD Cache ──
    async def get_cached_cves(self, cpe: str) -> Optional[List[Dict]]:
        query = "SELECT cves FROM nvd_cache WHERE cpe = ?"
        row = await self.fetch_one(query, (cpe,))
        if row:
            return json.loads(row['cves'])
        return None
        
    async def cache_cves(self, cpe: str, cves: List[Dict]):
        query = """
            INSERT INTO nvd_cache (cpe, cves)
            VALUES (?, ?)
            ON CONFLICT(cpe) DO UPDATE SET
                cves=excluded.cves,
                last_updated=CURRENT_TIMESTAMP
        """
        await self.execute(query, (cpe, json.dumps(cves)))

    # ── API Queries ──
    async def get_runs(self) -> List[Dict[str, Any]]:
        query = "SELECT * FROM experiment_configs ORDER BY timestamp DESC"
        rows = await self.fetch_all(query)
        return [dict(row) for row in rows]
        
    async def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM experiment_configs WHERE run_id = ?"
        row = await self.fetch_one(query, (run_id,))
        return dict(row) if row else None
        
    async def get_run_results(self, run_id: str) -> List[Dict[str, Any]]:
        query = """
            SELECT e.target_id, e.service, e.port, e.evidence_level, p.*
            FROM evidence e
            LEFT JOIN predictions p ON e.id = p.evidence_id
            WHERE e.run_id = ?
        """
        rows = await self.fetch_all(query, (run_id,))
        
        # Parse JSON fields
        results = []
        for row in rows:
            r_dict = dict(row)
            if r_dict.get('cves'):
                try:
                    r_dict['cves'] = json.loads(r_dict['cves'])
                except:
                    pass
            results.append(r_dict)
        return results

db_manager = DatabaseManager()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--init":
        asyncio.run(db_manager.initialize_schema())
        print("Database schema initialized.")

