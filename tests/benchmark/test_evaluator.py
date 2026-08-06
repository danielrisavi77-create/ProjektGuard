from decimal import Decimal
from pathlib import Path

from projektguard.audit.tolerance import TolerancePolicy
from projektguard.benchmark.evaluator import BenchmarkResult, evaluate_manifest, summarize
from projektguard.domain.enums import Severity, Verdict


def test_summary_tracks_unknown_discipline_and_critical_false_positives():
    rows = [
        BenchmarkResult(
            test_id="T1", rule_id="R30", expected_verdict=Verdict.UNKNOWN,
            actual_verdict=Verdict.UNKNOWN, severity=Severity.HIGH, passed=True,
            source_requirement_satisfied=True,
        ),
        BenchmarkResult(
            test_id="T2", rule_id="R44", expected_verdict=Verdict.VERIFIED,
            actual_verdict=Verdict.VERIFIED, severity=Severity.CRITICAL, passed=True,
            source_requirement_satisfied=True,
        ),
    ]
    summary = summarize(rows)
    assert summary.pass_rate == 1.0
    assert summary.critical_false_positives == 0
    assert summary.unknown_discipline == 1.0


def test_committed_manifest_meets_acceptance_thresholds():
    _, summary = evaluate_manifest(
        Path("benchmark/financial_integrity_core/manifest.json"),
        TolerancePolicy(absolute=Decimal("10"), relative_percent=Decimal("0.1")),
    )
    assert summary.pass_rate >= 0.98
    assert summary.critical_false_positives == 0
    assert summary.critical_false_negatives == 0
    assert summary.unknown_discipline >= 0.95
    assert summary.high_critical_source_completeness == 1.0
    assert summary.pre_cutoff_temporal_integrity == 1.0


def test_committed_manifest_contains_strict_pre_cutoff_case_with_later_ground_truth():
    from projektguard.benchmark.loader import load_manifest
    from projektguard.benchmark.models import BenchmarkMode

    manifest = load_manifest(Path("benchmark/financial_integrity_core/manifest.json"))
    case = next((row for row in manifest if row.test_id == "B07-R51-pre-cutoff"), None)
    assert case is not None
    assert case.mode == BenchmarkMode.PRE_CUTOFF
    assert case.source_observed_at is not None
    assert case.ground_truth_observed_at is not None
    assert case.ground_truth_observed_at > case.source_observed_at
    assert case.ground_truth_verdict == Verdict.WARNING

    rows, summary = evaluate_manifest(
        Path("benchmark/financial_integrity_core/manifest.json"),
        TolerancePolicy(absolute=Decimal("10"), relative_percent=Decimal("0.1")),
    )
    result = next(row for row in rows if row.test_id == "B07-R51-pre-cutoff")
    assert result.actual_verdict == Verdict.UNKNOWN
    assert result.temporal_integrity_satisfied is True
    assert result.passed is True
    assert summary.pre_cutoff_cases >= 1
