from importlib.metadata import PackageNotFoundError, version as _metadata_version

from .core import (
    DECISIONS,
    SCHEMA_VERSION,
    STAGES,
    TARGET_KINDS,
    PromotionDecision,
    PromotionGate,
    PromotionPolicy,
    PromotionRequest,
    PromotionValidationError,
    canonical_json,
    sha256_ref,
)

__all__ = [
    "DECISIONS",
    "SCHEMA_VERSION",
    "STAGES",
    "TARGET_KINDS",
    "PromotionDecision",
    "PromotionGate",
    "PromotionPolicy",
    "PromotionRequest",
    "PromotionValidationError",
    "canonical_json",
    "sha256_ref",
]

try:
    __version__ = _metadata_version("neuruh-promotion-gate")
except PackageNotFoundError:  # running from a source tree that was never installed
    __version__ = "unknown"
