"""insurance-data-pipeline: map, validate and standardise insurance bordereaux."""

from .fx import convert
from .mapping import load_mapping, standardise
from .schema import RISK_BORDEREAU, Field, Schema
from .synthetic import COVERHOLDER_MAPPING, generate_bordereau
from .validate import ValidationResult, validate

__all__ = [
    "COVERHOLDER_MAPPING",
    "RISK_BORDEREAU",
    "Field",
    "Schema",
    "ValidationResult",
    "convert",
    "generate_bordereau",
    "load_mapping",
    "standardise",
    "validate",
]

__version__ = "0.1.0"
