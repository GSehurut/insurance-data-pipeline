"""Canonical layouts that incoming bordereaux are mapped into."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Kind = Literal["string", "date", "number", "currency", "country"]


@dataclass(frozen=True)
class Field:
    name: str
    kind: Kind
    required: bool = True
    min_value: float | None = None
    max_value: float | None = None
    description: str = ""


@dataclass(frozen=True)
class Schema:
    name: str
    fields: tuple[Field, ...]
    key: tuple[str, ...]  # columns that must be unique together (the grain)
    date_order: tuple[str, str] | None = None  # (start, end) that must satisfy end > start

    @property
    def columns(self) -> list[str]:
        return [f.name for f in self.fields]

    def field(self, name: str) -> Field:
        for f in self.fields:
            if f.name == name:
                return f
        raise KeyError(name)


# A deliberately small, readable risk bordereau layout. Field choices are informed
# by common delegated authority reporting; full mapping to the Lloyd's Coverholder
# Reporting Standards is on the roadmap.
RISK_BORDEREAU = Schema(
    name="risk_bordereau",
    fields=(
        Field("policy_ref", "string", description="Unique policy or certificate reference"),
        Field("section", "string", required=False, description="Section of the policy"),
        Field("insured_name", "string"),
        Field("country", "country", description="ISO 3166-1 alpha-2 risk country"),
        Field("class_of_business", "string"),
        Field("inception_date", "date"),
        Field("expiry_date", "date"),
        Field("currency", "currency", description="ISO 4217 original currency"),
        Field("sum_insured", "number", min_value=0),
        Field("gross_premium", "number", description="Negative for return premium"),
        Field("brokerage_pct", "number", required=False, min_value=0, max_value=100),
    ),
    key=("policy_ref", "section"),
    date_order=("inception_date", "expiry_date"),
)

# Common ISO 4217 codes in London market business. Extend via validate(currencies=...).
COMMON_CURRENCIES = frozenset(
    {
        "GBP",
        "USD",
        "EUR",
        "CAD",
        "AUD",
        "NZD",
        "JPY",
        "CHF",
        "SGD",
        "HKD",
        "ZAR",
        "SEK",
        "NOK",
        "DKK",
    }
)
