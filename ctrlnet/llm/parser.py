import logging
from typing import Dict, Any

from pydantic import ValidationError
from ctrlnet.llm.schemas import LLMPrediction

logger = logging.getLogger(__name__)

class LLMParser:
    """Parses and validates raw JSON output from the LLM."""

    @staticmethod
    def parse_prediction(raw_dict: Dict[str, Any]) -> LLMPrediction:
        """
        Validate a dictionary against the LLMPrediction schema.
        Handles minor normalizations if necessary before validation.
        """
        try:
            # Pydantic will handle the rigorous validation
            prediction = LLMPrediction(**raw_dict)
            
            # Apply any post-validation normalization
            if prediction.cpe:
                 prediction.cpe = prediction.cpe.lower()
                 
            for cve in prediction.cves:
                 cve.id = cve.id.upper()
                 
            return prediction
            
        except ValidationError as e:
            logger.error(f"Schema validation failed for LLM output: {e}")
            raise
