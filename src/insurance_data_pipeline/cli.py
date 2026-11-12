"""Command line interface: ``idp validate`` and ``idp generate``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from .mapping import load_mapping, standardise
from .synthetic import generate_bordereau
from .validate import validate


def _read(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in (".xlsx", ".xls"):
        return pd.read_excel(path, dtype=object)
    return pd.read_csv(path, dtype=object)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="idp", description="Insurance bordereau tools")
    sub = parser.add_subparsers(dest="command", required=True)

    v = sub.add_parser("validate", help="Validate a bordereau against the risk schema")
    v.add_argument("file", type=Path)
    v.add_argument("--mapping", type=Path, help="YAML column mapping for this source")
    v.add_argument("--issues", type=Path, help="Write the issue list to this CSV")
    v.add_argument("--monthfirst", action="store_true", help="Parse dates as month first (US)")

    g = sub.add_parser("generate", help="Write a synthetic bordereau")
    g.add_argument("out", type=Path)
    g.add_argument("--rows", type=int, default=100)
    g.add_argument("--errors", type=float, default=0.0, help="Share of rows with injected errors")
    g.add_argument("--seed", type=int)

    args = parser.parse_args(argv)

    if args.command == "generate":
        generate_bordereau(args.rows, seed=args.seed, error_rate=args.errors).to_csv(
            args.out, index=False
        )
        print(f"Wrote {args.out}")
        return 0

    raw = _read(args.file)
    mapping = load_mapping(args.mapping) if args.mapping else {}
    result = validate(standardise(raw, mapping), dayfirst=not args.monthfirst)

    if result.is_valid:
        print(f"{args.file}: {len(raw)} rows, no issues found")
        return 0

    print(f"{args.file}: {len(raw)} rows, {len(result.issues)} issues")
    print(result.summary().to_string())
    if args.issues:
        result.issues.to_csv(args.issues, index=False)
        print(f"Issue list written to {args.issues}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
