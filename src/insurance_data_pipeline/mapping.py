"""Map source columns (each coverholder's own layout) onto a canonical schema."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pandas as pd
import yaml

from .schema import RISK_BORDEREAU, Schema


def load_mapping(path: str | Path) -> dict[str, str]:
    """Load a YAML mapping of the form ``columns: {"Source name": canonical_name}``."""
    data = yaml.safe_load(Path(path).read_text())
    if not isinstance(data, dict) or not isinstance(data.get("columns"), dict):
        raise ValueError(f"{path}: expected a top level 'columns' mapping")
    return {str(k): str(v) for k, v in data["columns"].items()}


def standardise(
    df: pd.DataFrame, mapping: Mapping[str, str], schema: Schema = RISK_BORDEREAU
) -> pd.DataFrame:
    """Rename source columns to canonical names and keep only schema columns.

    Matching of source names ignores case and surrounding whitespace, because
    "Policy No", "policy no " and "POLICY NO" are the same column in practice.
    Values are left as they are; type checks happen in :func:`validate`.
    """
    unknown = set(mapping.values()) - set(schema.columns)
    if unknown:
        raise ValueError(f"mapping targets not in schema {schema.name!r}: {sorted(unknown)}")

    lookup = {_norm(src): dst for src, dst in mapping.items()}
    renamed = {}
    for col in df.columns:
        target = lookup.get(_norm(col))
        if target is None and _norm(col) in {_norm(c) for c in schema.columns}:
            target = next(c for c in schema.columns if _norm(c) == _norm(col))
        if target is not None:
            if target in renamed.values():
                raise ValueError(f"more than one source column maps to {target!r}")
            renamed[col] = target

    out = df.rename(columns=renamed)[list(renamed.values())].copy()
    for col in out.columns:
        if out[col].dtype == object or pd.api.types.is_string_dtype(out[col]):
            out[col] = out[col].map(lambda v: v.strip() if isinstance(v, str) else v)
            out[col] = out[col].replace("", pd.NA)
    return out[[c for c in schema.columns if c in out.columns]]


def _norm(name: object) -> str:
    return " ".join(str(name).strip().lower().split())
