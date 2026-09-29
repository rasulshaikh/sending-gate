import json
from pathlib import Path

from sending_gate import evaluate_batch, evaluate_row

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = json.loads((ROOT / "examples" / "sample_rows.json").read_text(encoding="utf-8"))


def test_good_row_passes():
    row = SAMPLE["rows"][0]
    result = evaluate_row(row)
    assert result["verdict"] == "PASS"
    assert result["score"] >= 80
    assert result["hard_failures"] == []


def test_role_account_and_placeholders_fail():
    row = SAMPLE["rows"][1]
    result = evaluate_row(row)
    assert result["verdict"] == "FAIL"
    assert "role_account_email" in result["hard_failures"]


def test_domain_mismatch_flags():
    row = SAMPLE["rows"][2]
    result = evaluate_row(row)
    assert result["verdict"] in {"FLAG", "PASS"}
    assert "email_domain_mismatch" in result["flags"]


def test_invalid_email_fails():
    row = SAMPLE["rows"][3]
    result = evaluate_row(row)
    assert result["verdict"] == "FAIL"
    assert "invalid_or_missing_email" in result["hard_failures"]


def test_batch_counts_and_duplicates():
    rows = [
        SAMPLE["rows"][0],
        dict(SAMPLE["rows"][0]),  # duplicate email
        SAMPLE["rows"][2],
    ]
    report = evaluate_batch(rows)
    assert report["counts"]["FAIL"] >= 1
    assert any("duplicate_email" in r["hard_failures"] for r in report["results"])


def test_sample_file_batch():
    report = evaluate_batch(SAMPLE["rows"])
    assert report["counts"]["PASS"] >= 1
    assert report["counts"]["FAIL"] >= 1
