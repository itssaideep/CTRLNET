from typing import List, Dict, Any

class CalibrationAnalyzer:
    """Analyzes the relationship between LLM confidence and actual accuracy."""

    @staticmethod
    def calculate_ece(predictions: List[Dict[str, Any]], num_bins: int = 10) -> float:
        """
        Calculate Expected Calibration Error (ECE).
        predictions should be a list of dicts with 'confidence' and 'is_correct' keys.
        """
        if not predictions:
             return 0.0
             
        bins = [[] for _ in range(num_bins)]
        
        for p in predictions:
             conf = p['confidence']
             # Ensure conf is strictly < 1.0 for binning logic, or handle 1.0 explicitly
             bin_idx = min(int(conf * num_bins), num_bins - 1)
             bins[bin_idx].append(p)
             
        ece = 0.0
        n = len(predictions)
        
        for b in bins:
             if not b:
                 continue
                 
             bin_size = len(b)
             avg_conf = sum(p['confidence'] for p in b) / bin_size
             accuracy = sum(1 for p in b if p['is_correct']) / bin_size
             
             ece += (bin_size / n) * abs(accuracy - avg_conf)
             
        return ece

    @staticmethod
    def get_reliability_diagram_data(predictions: List[Dict[str, Any]], num_bins: int = 10) -> List[Dict[str, float]]:
        """
        Generate data points for a reliability diagram.
        """
        if not predictions:
             return []
             
        bins = [[] for _ in range(num_bins)]
        for p in predictions:
             bin_idx = min(int(p['confidence'] * num_bins), num_bins - 1)
             bins[bin_idx].append(p)
             
        data = []
        for i, b in enumerate(bins):
             if not b:
                 continue
             bin_size = len(b)
             avg_conf = sum(p['confidence'] for p in b) / bin_size
             accuracy = sum(1 for p in b if p['is_correct']) / bin_size
             
             data.append({
                 "bin_center": (i + 0.5) / num_bins,
                 "avg_confidence": avg_conf,
                 "accuracy": accuracy,
                 "count": bin_size
             })
             
        return data
