from typing import Tuple
import math

class Statistics:
    @staticmethod
    def wilson_score_interval(p: float, n: int, z: float = 1.96) -> Tuple[float, float]:
        """
        Calculate the Wilson score interval for a proportion.
        p: observed proportion
        n: sample size
        z: z-score for desired confidence level (1.96 for 95%)
        """
        if n == 0:
            return 0.0, 0.0
            
        denominator = 1 + z**2 / n
        center = (p + z**2 / (2 * n)) / denominator
        spread = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denominator
        
        lower_bound = max(0.0, center - spread)
        upper_bound = min(1.0, center + spread)
        
        return lower_bound, upper_bound
