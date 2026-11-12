"""Synthetic bordereaux for tests, demos and teaching. No real data is used."""

from __future__ import annotations

import numpy as np
import pandas as pd

# A typical "coverholder" layout: different names, formatted numbers, UK dates
COVERHOLDER_MAPPING = {
    "Policy No.": "policy_ref",
    "Section": "section",
    "Insured": "insured_name",
    "Risk Country": "country",
    "Class": "class_of_business",
    "Inception": "inception_date",
    "Expiry": "expiry_date",
    "Ccy": "currency",
    "TSI": "sum_insured",
    "Gross Premium": "gross_premium",
    "Brokerage %": "brokerage_pct",
}

_CLASSES = ["Marine Cargo", "Property", "Terrorism", "Political Violence", "Cyber", "Energy"]
_COUNTRIES = ["GB", "US", "DE", "FR", "NL", "AE", "ZA", "BW", "SG", "BR", "CA", "AU"]
_CCY = {"GB": "GBP", "US": "USD", "CA": "CAD", "AU": "AUD", "SG": "SGD", "ZA": "ZAR"}
_SUFFIX = ["Ltd", "plc", "Holdings", "Logistics", "Trading", "Group", "Shipping"]
_WORDS = ["Kalahari", "Thames", "Northgate", "Meridian", "Harbour", "Atlas", "Okavango", "Summit"]


def generate_bordereau(
    n: int = 100,
    *,
    seed: int | None = None,
    error_rate: float = 0.0,
    layout: str = "coverholder",
    start: str = "2026-01-01",
) -> pd.DataFrame:
    """Generate a synthetic risk bordereau.

    Parameters
    ----------
    n:
        Number of rows.
    seed:
        Seed for reproducibility.
    error_rate:
        Approximate share of rows given a realistic data quality problem
        (blank reference, bad currency, swapped dates, text in a number field,
        duplicate row). Useful for testing validation.
    layout:
        ``"coverholder"`` (messy source column names, formatted values) or
        ``"canonical"`` (schema column names, typed values).
    """
    if not 0 <= error_rate <= 1:
        raise ValueError("error_rate must be between 0 and 1")
    if layout not in ("coverholder", "canonical"):
        raise ValueError("layout must be 'coverholder' or 'canonical'")
    rng = np.random.default_rng(seed)

    countries = rng.choice(_COUNTRIES, n)
    inception = pd.Timestamp(start) + pd.to_timedelta(rng.integers(0, 365, n), unit="D")
    sum_insured = np.round(np.exp(rng.normal(14.5, 1.3, n)), -3)
    rate = rng.uniform(0.0015, 0.012, n)
    df = pd.DataFrame(
        {
            "policy_ref": [f"B1234{start[:4]}{i:05d}" for i in range(1, n + 1)],
            "section": rng.choice(["1", "2"], n, p=[0.85, 0.15]),
            "insured_name": [f"{rng.choice(_WORDS)} {rng.choice(_SUFFIX)}" for _ in range(n)],
            "country": countries,
            "class_of_business": rng.choice(_CLASSES, n),
            "inception_date": inception,
            "expiry_date": inception + pd.DateOffset(years=1) - pd.Timedelta(days=1),
            "currency": [_CCY.get(c, rng.choice(["USD", "EUR"])) for c in countries],
            "sum_insured": sum_insured,
            "gross_premium": np.round(sum_insured * rate, 2),
            "brokerage_pct": rng.choice([10.0, 12.5, 15.0, 17.5, 20.0], n),
        }
    )

    if error_rate > 0:
        df = _inject_errors(df, rng, error_rate)

    if layout == "canonical":
        return df

    out = df.copy()
    for col in ("inception_date", "expiry_date"):
        out[col] = out[col].map(
            lambda d: d.strftime("%d/%m/%Y") if isinstance(d, pd.Timestamp) else d
        )
    for col in ("sum_insured", "gross_premium"):
        out[col] = out[col].map(lambda v: f"{v:,.2f}" if isinstance(v, (int, float)) else v)
    reverse = {v: k for k, v in COVERHOLDER_MAPPING.items()}
    return out.rename(columns=reverse)


def _inject_errors(df: pd.DataFrame, rng: np.random.Generator, rate: float) -> pd.DataFrame:
    df = df.astype({"gross_premium": object, "currency": object, "policy_ref": object})
    rows = np.flatnonzero(rng.random(len(df)) < rate)
    kinds = rng.choice(
        ["blank_ref", "bad_ccy", "swapped_dates", "text_premium", "duplicate"], rows.size
    )
    duplicates = []
    for row, kind in zip(rows, kinds, strict=True):
        if kind == "blank_ref":
            df.at[row, "policy_ref"] = None
        elif kind == "bad_ccy":
            df.at[row, "currency"] = "XXX"
        elif kind == "swapped_dates":
            inc, exp = df.at[row, "inception_date"], df.at[row, "expiry_date"]
            df.at[row, "inception_date"], df.at[row, "expiry_date"] = exp, inc
        elif kind == "text_premium":
            df.at[row, "gross_premium"] = "TBC"
        else:
            duplicates.append(row)
    if duplicates:
        df = pd.concat([df, df.iloc[duplicates]], ignore_index=True)
    return df
