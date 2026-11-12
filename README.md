# insurance-data-pipeline

[![CI](https://github.com/GSehurut/insurance-data-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/GSehurut/insurance-data-pipeline/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Tools for the least glamorous and most important part of insurance analytics: getting bordereaux and other incoming data into a consistent, validated shape.

Every coverholder and system sends data in its own layout, with its own column names, date formats and quirks. This project maps those layouts onto a canonical schema, validates every row, and produces an issue list you can send back to the source, instead of failing on the first bad cell or silently coercing it.

## Features

- **Canonical risk bordereau schema** with an explicit grain (`policy_ref` + `section`)
- **YAML column mappings** per source, matched case and whitespace insensitively
- **Row level validation:** required values, dates, numbers (handles `1,000.00` and `£`), ISO currencies and countries, expiry after inception, duplicate keys
- **Currency conversion** with explicit rates that fails loudly on missing currencies
- **Synthetic bordereaux,** optionally with realistic injected errors, for testing and teaching (no real data anywhere)
- **Command line tool:** `idp validate` and `idp generate`

## Quick start

```sh
pip install git+https://github.com/GSehurut/insurance-data-pipeline.git

# Generate a messy synthetic bordereau, then validate it
idp generate bordereau.csv --rows 300 --errors 0.1 --seed 7
idp validate bordereau.csv --mapping examples/coverholder_mapping.yml --issues issues.csv
```

```text
bordereau.csv: 307 rows, 34 issues
duplicate_key       14
invalid_number       7
missing_value        6
unknown_currency     4
date_order           3
```

### In Python

```python
import pandas as pd
from insurance_data_pipeline import load_mapping, standardise, validate, convert

raw = pd.read_csv("bordereau.csv", dtype=object)
result = validate(standardise(raw, load_mapping("examples/coverholder_mapping.yml")))

if not result.is_valid:
    result.issues.to_csv("issues.csv", index=False)  # row, column, rule, value, message

gbp = convert(result.clean, {"USD": 0.79, "EUR": 0.85}, ["gross_premium"], to="GBP")
```

## Contributing

Contributions from data engineers, actuaries and anyone who has wrestled with a bordereau are very welcome. See [CONTRIBUTING.md](CONTRIBUTING.md), the [roadmap](ROADMAP.md) and issues labelled [`good first issue`](https://github.com/GSehurut/insurance-data-pipeline/labels/good%20first%20issue).

## Background

- Lloyd's, *Coverholder Reporting Standards*, which define expected bordereau fields for delegated authority business.
- Reis and Housley (2022), *Fundamentals of Data Engineering*, O'Reilly.
- Blog posts: [Data engineering for insurance analytics](https://gsehurut.github.io/blog/2024/03/22/data-engineering-insurance/) and [Working with data in the London market](https://gsehurut.github.io/blog/2026/09/14/working-with-london-market-data/).

## Licence

MIT. See [LICENSE](LICENSE).
