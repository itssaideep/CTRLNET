import logging
from typing import Dict, Any

from ctrlnet.llm.schemas import LLMPrediction

logger = logging.getLogger(__name__)

class Scorer:
    """Compares predictions against ground truth and calculates basic accuracy metrics."""

    @staticmethod
    def calculate_cve_metrics(predicted_cves: list[str], ground_truth_cves: list[str]) -> Dict[str, float]:
        """Calculate precision, recall, and F1 for a list of CVEs."""
        pred_set = set([c.upper() for c in predicted_cves])
        gt_set = set([c.upper() for c in ground_truth_cves])
        
        if not pred_set and not gt_set:
             return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
        if not pred_set:
             return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
        if not gt_set:
             return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
             
        true_positives = len(pred_set.intersection(gt_set))
        
        precision = true_positives / len(pred_set)
        recall = true_positives / len(gt_set)
        
        f1 = 0.0
        if (precision + recall) > 0:
             f1 = 2 * (precision * recall) / (precision + recall)
             
        return {
             "precision": precision,
             "recall": recall,
             "f1": f1
        }

    @staticmethod
    def score_prediction(prediction: LLMPrediction, ground_truth: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score a single prediction against ground truth.
        """
        scores = {
            "product_accurate": False,
            "version_accurate": False,
            "cpe_accurate": False,
            "cve_precision": 0.0,
            "cve_recall": 0.0,
            "cve_f1": 0.0
        }
        
        # Product
        gt_product = ground_truth.get("product", "").lower()
        pred_product = (prediction.product or "").lower()
        if gt_product and pred_product and gt_product in pred_product or pred_product in gt_product:
             scores["product_accurate"] = True
             
        # Version
        gt_version = ground_truth.get("version", "").lower()
        pred_version = (prediction.version or "").lower()
        if gt_version and pred_version and gt_version == pred_version:
             scores["version_accurate"] = True
             
        # CPE
        gt_cpe = ground_truth.get("cpe", "").lower().rstrip(':*')
        pred_cpe = (prediction.cpe or "").lower().rstrip(':*')
        if gt_cpe and pred_cpe and gt_cpe == pred_cpe:
             scores["cpe_accurate"] = True
             
        # CVEs
        pred_cves = [cve.id for cve in prediction.cves]
        gt_cves = ground_truth.get("known_cves", [])
        
        cve_metrics = Scorer.calculate_cve_metrics(pred_cves, gt_cves)
        scores.update({
            "cve_precision": cve_metrics["precision"],
            "cve_recall": cve_metrics["recall"],
            "cve_f1": cve_metrics["f1"]
        })
        
        return scores
