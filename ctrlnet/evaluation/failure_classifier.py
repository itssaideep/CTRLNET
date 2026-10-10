from typing import Dict, Any

from ctrlnet.config import FailureCategory
from ctrlnet.llm.schemas import LLMPrediction

class FailureClassifier:
    """Classifies incorrect predictions into a specific failure taxonomy."""

    @staticmethod
    def classify(prediction: LLMPrediction, scores: Dict[str, Any], ground_truth: Dict[str, Any]) -> FailureCategory:
        """
        Determine the primary failure mode of a prediction.
        Returns None if the prediction was generally accurate.
        """
        # Did it fail to abstain when evidence was missing?
        # (This usually happens if E0 or E1 and it didn't abstain, but we'll infer it 
        #  from low accuracy combined with high confidence).
        
        if prediction.abstain:
             # If it abstained, but there WAS exact evidence (E4), that's a failure
             # (Not handled precisely here without evidence level, but in pipeline).
             return None # Safe abstention is not a failure

        if not scores["product_accurate"]:
             if prediction.confidence > 0.7:
                 return FailureCategory.OVERCONFIDENT
             return FailureCategory.WRONG_PRODUCT
             
        if not scores["version_accurate"]:
             # Did it hallucinate a version?
             if prediction.version and not ground_truth.get("version"):
                 return FailureCategory.HALLUCINATED_VERSION
             return FailureCategory.WRONG_VERSION
             
        if not scores["cpe_accurate"]:
             return FailureCategory.WRONG_CPE
             
        if scores["cve_precision"] < 1.0:
             # It claimed CVEs that were wrong (False Positives / Hallucinated)
             return FailureCategory.HALLUCINATED_CVE
             
        if scores["cve_recall"] < 1.0 and prediction.confidence > 0.8:
             # Missed CVEs but was highly confident
             return FailureCategory.FALSE_NEGATIVE
             
        return None # No major classified failure
