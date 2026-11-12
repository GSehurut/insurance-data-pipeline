import pandas as pd
import pytest

from insurance_data_pipeline import (
    COVERHOLDER_MAPPING,
    convert,
    generate_bordereau,
    load_mapping,
    standardise,
    validate,
)
from insurance_data_pipeline.cli import main


def test_clean_synthetic_bordereau_passes():
    raw = generate_bordereau(200, seed=1)
    result = validate(standardise(raw, COVERHOLDER_MAPPING))
    assert result.is_valid, result.issues.head()
    assert result.clean["gross_premium"].dtype.kind == "f"
    assert str(result.clean["inception_date"].dtype).startswith("datetime64")


def test_injected_errors_are_all_detected():
    raw = generate_bordereau(500, seed=3, error_rate=0.2)
    result = validate(standardise(raw, COVERHOLDER_MAPPING))
    rules = set(result.issues["rule"])
    assert {
        "missing_value",
        "unknown_currency",
        "date_order",
        "invalid_number",
        "duplicate_key",
    } <= rules


def test_issue_rows_point_back_to_source():
    raw = pd.DataFrame(
        {
            "policy_ref": ["A1", "A2"],
            "insured_name": ["X Ltd", "Y Ltd"],
            "country": ["GB", "GBR"],
            "class_of_business": ["Cargo", "Cargo"],
            "inception_date": ["01/01/2026", "01/01/2026"],
            "expiry_date": ["31/12/2026", "31/12/2026"],
            "currency": ["GBP", "GBP"],
            "sum_insured": ["1,000,000", "-5"],
            "gross_premium": ["£2,500.00", "100"],
        }
    )
    issues = validate(standardise(raw, {})).issues
    assert set(zip(issues["row"], issues["rule"], strict=True)) == {
        (1, "invalid_country"),
        (1, "below_minimum"),
    }


def test_missing_required_column_reported():
    raw = pd.DataFrame({"policy_ref": ["A1"]})
    issues = validate(raw).issues
    assert "missing_column" in set(issues["rule"])


def test_standardise_ignores_case_and_whitespace():
    raw = pd.DataFrame({"  policy NO. ": ["A1 "], "ccy": ["usd"]})
    out = standardise(raw, {"Policy No.": "policy_ref", "Ccy": "currency"})
    assert list(out.columns) == ["policy_ref", "currency"]
    assert out.loc[0, "policy_ref"] == "A1"


def test_mapping_to_unknown_column_rejected():
    with pytest.raises(ValueError):
        standardise(pd.DataFrame({"a": [1]}), {"a": "not_a_field"})


def test_load_mapping(tmp_path):
    path = tmp_path / "m.yml"
    path.write_text('columns:\n  "Policy No.": policy_ref\n')
    assert load_mapping(path) == {"Policy No.": "policy_ref"}


def test_convert_and_missing_rate():
    df = pd.DataFrame({"currency": ["GBP", "USD"], "gross_premium": [100.0, 100.0]})
    out = convert(df, {"USD": 0.8}, ["gross_premium"], to="GBP")
    assert out["gross_premium_gbp"].tolist() == [100.0, 80.0]
    with pytest.raises(ValueError, match="EUR"):
        convert(pd.DataFrame({"currency": ["EUR"], "x": [1.0]}), {"USD": 0.8}, ["x"])


def test_cli_round_trip(tmp_path, capsys):
    data, mapping = tmp_path / "b.csv", tmp_path / "m.yml"
    mapping.write_text(
        "columns:\n" + "".join(f'  "{k}": {v}\n' for k, v in COVERHOLDER_MAPPING.items())
    )
    assert main(["generate", str(data), "--rows", "50", "--seed", "2"]) == 0
    assert main(["validate", str(data), "--mapping", str(mapping)]) == 0
    main(["generate", str(data), "--rows", "200", "--seed", "2", "--errors", "0.3"])
    issues = tmp_path / "issues.csv"
    code = main(["validate", str(data), "--mapping", str(mapping), "--issues", str(issues)])
    assert code == 1 and issues.exists()
