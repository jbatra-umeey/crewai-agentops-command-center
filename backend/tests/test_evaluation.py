import json
from pathlib import Path
from app.evaluation import evaluate_cases


def test_golden_fixture_cases():
    cases = json.loads((Path(__file__).resolve().parents[2] / "evaluation" / "cases.json").read_text())
    report = evaluate_cases(cases)
    assert report["total"] == 6
    assert report["passed"] == report["total"]


def test_evaluation_detects_wrong_expectation():
    report = evaluate_cases([{"id": "wrong", "logs": ["timeout"], "cause": "memory failure", "risk": "high"}])
    assert report["passed"] == 0
    assert report["results"][0]["checks"]["expected_cause"] is False
