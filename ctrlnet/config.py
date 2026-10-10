"""
CTRLNET Configuration

Central configuration via environment variables with sensible defaults.
All settings can be overridden via .env file or environment variables.
"""

import os
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

# ──────────────────────────────────────────────────────────────────────
# Project Paths
# ──────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
CTRLNET_ROOT = Path(__file__).parent
DATABASE_DIR = CTRLNET_ROOT / "database"
CORPUS_DIR = CTRLNET_ROOT / "corpus"
DASHBOARD_DIR = CTRLNET_ROOT / "dashboard"
RESEARCH_OUTPUT_DIR = PROJECT_ROOT / "research_output"


# ──────────────────────────────────────────────────────────────────────
# Evidence Levels
# ──────────────────────────────────────────────────────────────────────
class EvidenceLevel(str, Enum):
    """Evidence quality classification for controlled experiments."""
    E4_EXACT = "E4"           # Complete product + version
    E3_MOSTLY_COMPLETE = "E3" # Product identifiable, some info missing
    E2_PARTIAL = "E2"         # Only partial identifying info
    E1_AMBIGUOUS = "E1"       # Multiple products/versions could explain
    E0_INSUFFICIENT = "E0"    # Not enough to identify reliably


# ──────────────────────────────────────────────────────────────────────
# Experiment Conditions
# ──────────────────────────────────────────────────────────────────────
class ExperimentCondition(str, Enum):
    """Primary experimental approaches."""
    DETERMINISTIC = "deterministic"
    LLM = "llm"
    HYBRID = "hybrid"


# ──────────────────────────────────────────────────────────────────────
# Prediction Verdicts
# ──────────────────────────────────────────────────────────────────────
class PredictionVerdict(str, Enum):
    """Primary evaluation result for each predicted CVE."""
    CONFIRMED = "CONFIRMED"
    UNVERIFIED_REAL = "UNVERIFIED_REAL"
    HALLUCINATED = "HALLUCINATED"
    MALFORMED = "MALFORMED"


# ──────────────────────────────────────────────────────────────────────
# Failure Categories
# ──────────────────────────────────────────────────────────────────────
class FailureCategory(str, Enum):
    """Failure taxonomy for incorrect predictions."""
    WRONG_PRODUCT = "WRONG_PRODUCT"
    WRONG_VERSION = "WRONG_VERSION"
    WRONG_CPE = "WRONG_CPE"
    WRONG_CVE = "WRONG_CVE"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    FALSE_NEGATIVE = "FALSE_NEGATIVE"
    HALLUCINATED_CVE = "HALLUCINATED_CVE"
    HALLUCINATED_VERSION = "HALLUCINATED_VERSION"
    UNSUPPORTED_INFERENCE = "UNSUPPORTED_INFERENCE"
    OVERCONFIDENT = "OVERCONFIDENT"
    UNDERCONFIDENT = "UNDERCONFIDENT"
    FAILURE_TO_ABSTAIN = "FAILURE_TO_ABSTAIN"
    INSUFFICIENT_EVIDENCE_NOT_RECOGNIZED = "INSUFFICIENT_EVIDENCE_NOT_RECOGNIZED"


# ──────────────────────────────────────────────────────────────────────
# Pipeline Stage Labels
# ──────────────────────────────────────────────────────────────────────
class PipelineStage(str, Enum):
    """Stages in the CTRLNET analysis pipeline."""
    OBSERVED = "OBSERVED"         # Raw network evidence
    INFERRED = "INFERRED"         # LLM hypothesis
    VERIFIED = "VERIFIED"         # Deterministic verification passed
    REJECTED = "REJECTED"         # Deterministic verification failed
    INSUFFICIENT = "INSUFFICIENT" # Not enough evidence to conclude


# ──────────────────────────────────────────────────────────────────────
# Configuration Dataclass
# ──────────────────────────────────────────────────────────────────────
@dataclass
class CtrlnetConfig:
    """Central configuration for CTRLNET."""

    # ── Ollama / LLM ──
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    ollama_temperature: float = float(os.getenv("OLLAMA_TEMPERATURE", "0.1"))
    ollama_timeout: int = int(os.getenv("OLLAMA_TIMEOUT", "120"))
    ollama_max_retries: int = int(os.getenv("OLLAMA_MAX_RETRIES", "3"))

    # ── NVD API ──
    nvd_api_key: str = os.getenv("NVD_API_KEY", "")
    nvd_rate_limit: float = float(os.getenv("NVD_RATE_LIMIT", "0.6"))  # seconds between requests (with key)
    nvd_rate_limit_nokey: float = float(os.getenv("NVD_RATE_LIMIT_NOKEY", "6.0"))  # without key
    nvd_cache_ttl: int = int(os.getenv("NVD_CACHE_TTL", "86400"))  # 24 hours

    # ── Nmap ──
    nmap_path: str = os.getenv("NMAP_PATH", "nmap")
    nmap_arguments: str = os.getenv("NMAP_ARGUMENTS", "-sV -O --version-intensity 5")
    nmap_timeout: int = int(os.getenv("NMAP_TIMEOUT", "300"))
    nmap_default_ports: str = os.getenv("NMAP_DEFAULT_PORTS", "1-1024")

    # ── Database ──
    database_path: str = os.getenv(
        "CTRLNET_DB",
        str(DATABASE_DIR / "ctrlnet.db")
    )

    # ── Server ──
    server_host: str = os.getenv("CTRLNET_HOST", "0.0.0.0")
    server_port: int = int(os.getenv("CTRLNET_PORT", "8000"))

    # ── Research ──
    research_output_dir: str = os.getenv(
        "RESEARCH_OUTPUT_DIR",
        str(RESEARCH_OUTPUT_DIR)
    )

    # ── Supported Models ──
    supported_models: list = field(default_factory=lambda: [
        "llama3.1:8b",
        "qwen2.5:7b",
        "mistral:7b",
    ])

    @property
    def effective_rate_limit(self) -> float:
        """Return the appropriate NVD rate limit based on API key availability."""
        if self.nvd_api_key:
            return self.nvd_rate_limit
        return self.nvd_rate_limit_nokey

    def ensure_dirs(self):
        """Create required directories if they don't exist."""
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.research_output_dir).mkdir(parents=True, exist_ok=True)


# Global config singleton
config = CtrlnetConfig()
