from pathlib import Path

from pydantic import BaseModel

from projektguard.audit.runner import run_rule
from projektguard.audit.tolerance import TolerancePolicy
from projektguard.benchmark.loader import load_context, load_manifest
from projektguard.benchmark.models import BenchmarkCase
from projektguard.domain.enums import Severity, Verdict
from projektguard.rules import load_financial_integrity_rules


class BenchmarkResult(BaseModel):
    test_id: str
    rule_id: str
    expected_verdict: Verdict
    actual_verdict: Verdict
    severity: Severity
    passed: bool
    source_requirement_satisfied: bool


class BenchmarkSummary(BaseModel):
    total: int
    passed: int
    pass_rate: float
    critical_false_positives: int
    unknown_expected: int
    unknown_correct: int
    unknown_discipline: float
    high_critical_source_completeness: float


def evaluate_case(case: BenchmarkCase, manifest_path: Path, tolerance: TolerancePolicy) -> BenchmarkResult:
    fixture_path = manifest_path.parent / case.fixture
    context = load_context(fixture_path)
    findings = run_rule(case.rule_id, context, tolerance)
    if len(findings) != 1:
        raise AssertionError(f"{case.test_id} expected exactly one finding, got {len(findings)}")
    finding = findings[0]
    verdict_ok = finding.verdict == case.expected.verdict
    severity_ok = case.expected.severity is None or finding.severity == case.expected.severity
    reason_ok = case.expected.reason_code is None or finding.reason_code == case.expected.reason_code
    fixture_has_sources = any(
        [
            *(bool(cost.sources) for cost in context.costs),
            *(bool(contract.sources) for contract in context.contracts),
            *(bool(procurement.sources) for procurement in context.procurements),
            *(bool(payment.evidence_sources) for payment in context.payments),
            *(bool(budget.approval_source) for budget in context.budget_versions),
            bool(context.baseline_approval_source),
        ]
    )
    source_required = (
        finding.severity in {Severity.HIGH, Severity.CRITICAL}
        and fixture_has_sources
        and finding.verdict != Verdict.UNKNOWN
    )
    source_ok = (not source_required) or bool(finding.sources)
    return BenchmarkResult(
        test_id=case.test_id,
        rule_id=case.rule_id,
        expected_verdict=case.expected.verdict,
        actual_verdict=finding.verdict,
        severity=finding.severity,
        passed=verdict_ok and severity_ok and reason_ok and source_ok,
        source_requirement_satisfied=source_ok,
    )


def summarize(rows: list[BenchmarkResult]) -> BenchmarkSummary:
    total = len(rows)
    passed = sum(row.passed for row in rows)
    unknown_rows = [row for row in rows if row.expected_verdict == Verdict.UNKNOWN]
    critical_false_positives = sum(
        1
        for row in rows
        if row.severity == Severity.CRITICAL
        and row.expected_verdict == Verdict.VERIFIED
        and row.actual_verdict == Verdict.WARNING
    )
    source_rows = [row for row in rows if row.severity in {Severity.HIGH, Severity.CRITICAL}]
    return BenchmarkSummary(
        total=total,
        passed=passed,
        pass_rate=1.0 if total == 0 else passed / total,
        critical_false_positives=critical_false_positives,
        unknown_expected=len(unknown_rows),
        unknown_correct=sum(row.actual_verdict == Verdict.UNKNOWN for row in unknown_rows),
        unknown_discipline=(
            1.0
            if not unknown_rows
            else sum(row.actual_verdict == Verdict.UNKNOWN for row in unknown_rows) / len(unknown_rows)
        ),
        high_critical_source_completeness=(
            1.0
            if not source_rows
            else sum(row.source_requirement_satisfied for row in source_rows) / len(source_rows)
        ),
    )


def evaluate_manifest(
    manifest_path: Path,
    tolerance: TolerancePolicy,
) -> tuple[list[BenchmarkResult], BenchmarkSummary]:
    load_financial_integrity_rules()
    rows = [evaluate_case(case, manifest_path, tolerance) for case in load_manifest(manifest_path)]
    return rows, summarize(rows)
