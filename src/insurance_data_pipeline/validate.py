"""Row level validation that reports every problem instead of stopping at the first."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

import pandas as pd

from .schema import COMMON_CURRENCIES, RISK_BORDEREAU, Schema

ISSUE_COLUMNS = ["row", "column", "rule", "value", "message"]
_COUNTRY = re.compile(r"^[A-Z]{2}$")
_NUMBER_JUNK = re.compile(r"[,\s£$€]")


@dataclass(frozen=True)
class ValidationResult:
    clean: pd.DataFrame  # typed data (invalid cells become missing)
    issues: pd.DataFrame  # one row per problem: row, column, rule, value, message

    @property
    def is_valid(self) -> bool:
        return self.issues.empty

    def summary(self) -> pd.Series:
        """Count of issues by rule."""
        return self.issues["rule"].value_counts()


def validate(
    df: pd.DataFrame,
    schema: Schema = RISK_BORDEREAU,
    *,
    currencies: Iterable[str] = COMMON_CURRENCIES,
    dayfirst: bool = True,
) -> ValidationResult:
    """Type-check and validate a standardised bordereau.

    ``row`` in the issues table is the original row label of ``df``, so problems
    can be traced back to the source file (add 2 for a spreadsheet line number
    when the index is a default range and there is one header row).
    """
    issues: list[dict] = []
    clean = pd.DataFrame(index=df.index)
    valid_ccy = {c.upper() for c in currencies}

    def add(row, column, rule, value, message):
        issues.append(
            {"row": row, "column": column, "rule": rule, "value": value, "message": message}
        )

    for field in schema.fields:
        if field.name not in df.columns:
            if field.required:
                add(
                    None,
                    field.name,
                    "missing_column",
                    None,
                    f"required column {field.name!r} not found",
                )
            continue

        raw = df[field.name]
        present = raw.notna()

        if field.kind == "date":
            values = pd.to_datetime(raw, errors="coerce", dayfirst=dayfirst, format="mixed")
            _flag(add, raw, present & values.isna(), field.name, "invalid_date", "not a valid date")
        elif field.kind == "number":
            values = pd.to_numeric(
                raw.astype("string").str.replace(_NUMBER_JUNK, "", regex=True), errors="coerce"
            )
            _flag(add, raw, present & values.isna(), field.name, "invalid_number", "not a number")
            if field.min_value is not None:
                _flag(
                    add,
                    raw,
                    values < field.min_value,
                    field.name,
                    "below_minimum",
                    f"less than {field.min_value}",
                )
            if field.max_value is not None:
                _flag(
                    add,
                    raw,
                    values > field.max_value,
                    field.name,
                    "above_maximum",
                    f"greater than {field.max_value}",
                )
        elif field.kind == "currency":
            values = raw.astype("string").str.upper()
            bad = present & ~values.isin(valid_ccy)
            _flag(add, raw, bad, field.name, "unknown_currency", "not a recognised ISO 4217 code")
            values = values.mask(bad)
        elif field.kind == "country":
            values = raw.astype("string").str.upper()
            bad = present & ~values.fillna("").str.match(_COUNTRY)
            _flag(
                add, raw, bad, field.name, "invalid_country", "expected a 2 letter ISO country code"
            )
            values = values.mask(bad)
        else:
            values = raw.astype("string")

        if field.required:
            _flag(add, raw, ~present, field.name, "missing_value", "required value is blank")
        clean[field.name] = values

    if schema.date_order and set(schema.date_order) <= set(clean.columns):
        start, end = schema.date_order
        bad = clean[end] <= clean[start]
        _flag(add, df[end], bad.fillna(False), end, "date_order", f"{end} is on or before {start}")

    key = [k for k in schema.key if k in clean.columns]
    if key:
        dupes = clean.duplicated(subset=key, keep=False) & clean[key[0]].notna()
        _flag(add, df[key[0]], dupes, key[0], "duplicate_key", f"duplicate {'/'.join(key)}")

    issue_df = pd.DataFrame(issues, columns=ISSUE_COLUMNS)
    return ValidationResult(clean=clean, issues=issue_df)


def _flag(add, raw: pd.Series, mask: pd.Series, column: str, rule: str, message: str) -> None:
    for idx in raw.index[mask.fillna(False).astype(bool)]:
        value = raw.loc[idx]
        add(idx, column, rule, None if pd.isna(value) else value, message)
