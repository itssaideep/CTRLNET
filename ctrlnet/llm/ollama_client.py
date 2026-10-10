import json
import logging
from typing import Dict, Any, Optional

import ollama
from pydantic import BaseModel

from ctrlnet.config import config

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for interacting with local Ollama instance."""

    def __init__(self):
        # The ollama library respects OLLAMA_HOST env var, 
        # but we can explicitly instantiate a client if needed.
        # For simplicity, we use the module-level functions which use the env var.
        self.host = config.ollama_base_url
        logger.info(f"Initialized OllamaClient pointing to {self.host}")

    async def health_check(self) -> bool:
        """Check if Ollama is accessible."""
        try:
             # ollama.list() is synchronous in the standard client, 
             # but we wrap it conceptually or use the async client if available.
             # In python-ollama 0.4.0+, there is AsyncClient.
             client = ollama.AsyncClient(host=self.host)
             await client.list()
             return True
        except Exception as e:
             logger.error(f"Ollama health check failed: {e}")
             return False

    async def check_model_available(self, model_name: str) -> bool:
        """Check if a specific model is pulled and available."""
        try:
            client = ollama.AsyncClient(host=self.host)
            models = await client.list()
            for m in models.get('models', []):
                if m.get('name') == model_name or m.get('name').startswith(f"{model_name}:"):
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to check model availability: {e}")
            return False

    async def generate_structured(self, model: str, prompt: str, schema: type[BaseModel], temperature: float = None) -> Dict[str, Any]:
        """
        Generate a structured response enforcing a Pydantic schema.
        Returns (parsed_dict, raw_response, metrics)
        """
        temp = temperature if temperature is not None else config.ollama_temperature
        client = ollama.AsyncClient(host=self.host)
        
        logger.debug(f"Sending prompt to {model} (temp={temp})")
        
        try:
            response = await client.chat(
                model=model,
                messages=[{'role': 'user', 'content': prompt}],
                format=schema.model_json_schema(),
                options={'temperature': temp}
            )
            
            raw_content = response['message']['content']
            
            # Ollama returns the generated JSON string in content
            parsed_dict = json.loads(raw_content)
            
            metrics = {
                "eval_count": response.get("eval_count", 0),
                "eval_duration": response.get("eval_duration", 0),
                "load_duration": response.get("load_duration", 0),
                "prompt_eval_count": response.get("prompt_eval_count", 0)
            }
            
            return parsed_dict, raw_content, metrics
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM output as JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"LLM inference failed: {e}")
            raise
