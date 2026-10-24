"""Offline regression checks; not a measure of live LLM quality."""
import json
from pathlib import Path
from .agents import fixture_investigation
from .models import Incident


def evaluate_cases(cases: list[dict]) -> dict:
    results = []
    for case in cases:
        finding = fixture_investigation(Incident(title=case["id"], service="evaluation", logs=case["logs"]))
        checks = {
            "expected_cause": finding.root_cause == case["cause"],
            "expected_risk": finding.risk == case["risk"],
            "evidence_from_input": bool(finding.evidence) and all(x in case["logs"] for x in finding.evidence),
            "bounded_confidence": 0 <= finding.confidence <= 1,
        }
        results.append({"id": case["id"], "passed": all(checks.values()), "checks": checks})
    return {"mode": "fixture", "total": len(results), "passed": sum(x["passed"] for x in results), "results": results}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=Path(__file__).resolve().parents[2] / "evaluation" / "cases.json")
    args = parser.parse_args()
    report = evaluate_cases(json.loads(args.cases.read_text()))
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["total"] > 0 and report["passed"] == report["total"] else 1)
