import argparse
import json
from decimal import Decimal
from pathlib import Path

from projektguard.audit.tolerance import TolerancePolicy
from projektguard.benchmark.evaluator import evaluate_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Run ProjektGuard Financial Integrity benchmark")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()

    _, summary = evaluate_manifest(
        args.manifest,
        TolerancePolicy(absolute=Decimal("10"), relative_percent=Decimal("0.1")),
    )
    print("ProjektGuard Financial Integrity Benchmark")
    print(f"Tests: {summary.total}")
    print(f"Passed: {summary.passed}")
    print(f"Pass rate: {summary.pass_rate:.2%}")
    print(f"Critical false positives: {summary.critical_false_positives}")
    print(f"Critical false negatives: {summary.critical_false_negatives}")
    print(f"UNKNOWN discipline: {summary.unknown_discipline:.2%}")
    print(f"Source-required cases: {summary.source_required_cases}")
    print(f"HIGH/CRITICAL source completeness: {summary.high_critical_source_completeness:.2%}")
    print(f"Pre-cutoff historical cases: {summary.pre_cutoff_cases}")
    print(f"Retrospective historical cases: {summary.retrospective_cases}")
    print(f"Pre-cutoff temporal integrity: {summary.pre_cutoff_temporal_integrity:.2%}")

    if args.json_output:
        args.json_output.write_text(
            json.dumps(summary.model_dump(), indent=2, ensure_ascii=False), encoding="utf-8"
        )

    accepted = (
        summary.pass_rate >= 0.98
        and summary.critical_false_positives == 0
        and summary.critical_false_negatives == 0
        and summary.unknown_discipline >= 0.95
        and summary.high_critical_source_completeness == 1.0
        and summary.pre_cutoff_temporal_integrity == 1.0
    )
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
