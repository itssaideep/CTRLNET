import json
from pathlib import Path

from ctrlnet.config import config
from ctrlnet.database.database import db_manager

async def fetch_results(run_id: str) -> list:
    """Fetch all prediction results for a specific run."""
    query = """
        SELECT e.evidence_level, e.service, p.confidence, p.abstained, 
               ev.product_accurate, ev.version_accurate, ev.cpe_accurate, 
               ev.cve_precision, ev.cve_recall, ev.cve_f1, ev.failure_category, ev.verdict
        FROM evidence e
        JOIN predictions p ON e.id = p.evidence_id
        JOIN evaluations ev ON p.id = ev.prediction_id
        WHERE e.run_id = ?
    """
    rows = await db_manager.fetch_all(query, (run_id,))
    return [dict(r) for r in rows]

class MetricsAggregator:
    """Aggregates metrics across a set of results."""
    
    @staticmethod
    def aggregate(results: list) -> dict:
        total = len(results)
        if total == 0:
            return {}
            
        abstained = sum(1 for r in results if r['abstained'])
        predicted = total - abstained
        
        metrics = {
            "total_cases": total,
            "abstained": abstained,
            "abstention_rate": abstained / total if total > 0 else 0,
            "predictions_made": predicted
        }
        
        if predicted > 0:
            pred_results = [r for r in results if not r['abstained']]
            
            metrics["product_accuracy"] = sum(1 for r in pred_results if r['product_accurate']) / predicted
            metrics["version_accuracy"] = sum(1 for r in pred_results if r['version_accurate']) / predicted
            metrics["cpe_accuracy"] = sum(1 for r in pred_results if r['cpe_accurate']) / predicted
            
            metrics["avg_cve_precision"] = sum(r['cve_precision'] for r in pred_results) / predicted
            metrics["avg_cve_recall"] = sum(r['cve_recall'] for r in pred_results) / predicted
            metrics["avg_cve_f1"] = sum(r['cve_f1'] for r in pred_results) / predicted
            
            metrics["avg_confidence"] = sum(r['confidence'] for r in pred_results) / predicted
            
        return metrics
