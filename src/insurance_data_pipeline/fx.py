"""Currency conversion to a reporting currency."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

import pandas as pd


def convert(
    df: pd.DataFrame,
    rates: Mapping[str, float],
    amount_columns: Iterable[str],
    to: str = "GBP",
    currency_column: str = "currency",
) -> pd.DataFrame:
    """Add ``<column>_<to>`` columns converted at the given rates.

    ``rates`` maps each original currency to units of the reporting currency
    per one unit of the original (so ``{"USD": 0.79}`` means 1 USD = 0.79 GBP).
    The reporting currency itself does not need a rate. Raises if any currency
    in the data has no rate, rather than silently producing missing values.
    """
    to = to.upper()
    table = {k.upper(): float(v) for k, v in rates.items()}
    table.setdefault(to, 1.0)

    ccy = df[currency_column].astype("string").str.upper()
    missing = sorted(set(ccy.dropna()) - set(table))
    if missing:
        raise ValueError(f"no rate of exchange for: {missing}")

    factor = ccy.map(table).astype(float)
    out = df.copy()
    for col in amount_columns:
        out[f"{col}_{to.lower()}"] = out[col].astype(float) * factor
    return out
