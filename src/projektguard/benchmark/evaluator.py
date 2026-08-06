from pathlib import Path

from pydantic import BaseModel

from projektguard.audit.finding import Finding
from projektguard.audit.runner import run_rule
from projektguard.audit.tolerance import TolerancePolicy
from projektguard.benchmark.loader import load_context, load_manifest
from projektguard.benchmark.models import BenchmarkCase, BenchmarkMode
from projektguard.domain.enums import Severity, Verdict
from projektguard.domain.models import AuditContext
from projektguard.rules import load_financial_integrity_rules


_VERDICT_PRIORITY = {
    Verdict.NOT_APPLICABLE: 0,
    Verdict.VERIFIED: 1,
    Verdict.UNKNOWN: 2,
    Verdict.EXPERT_REVIEW: 3,
    Verdict.WARNING: 4,
}
_SEVERITY_PRIORITY = {
    Severity.INFO: 0,
    Severity.LOW: 1,
    Severity.MEDIUM: 2,
    Severity.HIGH: 3,
    Severity.CRITICAL: 4,
}


class BenchmarkResult(BaseModel):
    test_id: str
    rule_id: str
    expected_verdict: Verdict
    actual_verdict: Verdict
    severity: Severity
    passed: bool
    source_required: bool = False
    source_requirement_satisfied: bool
    temporal_integrity_satisfied: bool = True
    mode: BenchmarkMode = BenchmarkMode.SYNTHETIC


class BenchmarkSummary(BaseModel):
    total: int
    passed: int
    pass_rate: float
    critical_false_positives: int
    critical_false_negatives: int
    unknown_expected: int
    unknown_correct: int
    unknown_discipline: float
    source_required_cases: int
    high_critical_source_completeness: float
    pre_cutoff_cases: int
    retrospective_cases: int
    pre_cutoff_temporal_integrity: float


def _decisive_finding(findings: list[Finding]) -> Finding:
    if not findings:
        raise AssertionError("rule returned no findings")
    return max(
        findings,
        key=lambda finding: (
            _VERDICT_PRIORITY[finding.verdict],
            _SEVERITY_PRIORITY[finding.severity],
        ),
    )


def _temporal_integrity(case: BenchmarkCase, context: AuditContext) -> bool:
    if case.mode != BenchmarkMode.PRE_CUTOFF:
        return True
    sources = [
        *[source for cost in context.costs for source in cost.sources],
        *[source for contract in context.contracts for source in contract.sources],
        *[source for procurement in context.procurements for source in procurement.sources],
        *[source for payment in context.payments for source in payment.evidence_sources],
        *[budget.approval_source for budget in context.budget_versions if budget.approval_source],
        *([context.baseline_approval_source] if context.baseline_approval_source else []),
    ]
    if any(source.available_from is not None and source.available_from > context.as_of for source in sources):
        return False
    if any(
        contract.actual_invoiced_observed_at is not None and contract.actual_invoiced_observed_at > context.as_of
        for contract in context.contracts
    ):
        return False
    if any(
        contract.actual_paid_observed_at is not None and contract.actual_paid_observed_at > context.as_of
        for contract in context.contracts
    ):
        return False
    return True


def evaluate_case(case: BenchmarkCase, manifest_path: Path, tolerance: TolerancePolicy) -> BenchmarkResult:
    fixture_path = manifest_path.parent / case.fixture
    context = load_context(fixture_path)
    findings = run_rule(case.rule_id, context, tolerance)
    finding = _decisive_finding(findings)
    verdict_ok = finding.verdict == case.expected.verdict
    severity_ok = case.expected.severity is None or finding.severity == case.expected.severity
    reason_ok = case.expected.reason_code is None or finding.reason_code == case.expected.reason_code
    source_required = case.expected.requires_source
    source_ok = (not source_required) or bool(finding.sources)
    temporal_ok = _temporal_integrity(case, context)
    return BenchmarkResult(
        test_id=case.test_id,
        rule_id=case.rule_id,
        expected_verdict=case.expected.verdict,
        actual_verdict=finding.verdict,
        severity=finding.severity,
        passed=verdict_ok and severity_ok and reason_ok and source_ok and temporal_ok,
        source_required=source_required,
        source_requirement_satisfied=source_ok,
        temporal_integrity_satisfied=temporal_ok,
        mode=case.mode,
    )


def summarize(rows: list[BenchmarkResult]) -> BenchmarkSummary:
    total = len(rows)
    passed = sum(row.passed for row in rows)
    unknown_rows = [row for row in rows if row.expected_verdict == Verdict.UNKNOWN]
    source_rows = [row for row in rows if row.source_required]
    pre_cutoff_rows = [row for row in rows if row.mode == BenchmarkMode.PRE_CUTOFF]
    retrospective_rows = [row for row in rows if row.mode == BenchmarkMode.RETROSPECTIVE]
    critical_false_positives = sum(
        1
        for row in rows
        if row.severity == Severity.CRITICAL
        and row.actual_verdict == Verdict.WARNING
        and row.expected_verdict != Verdict.WARNING
    )
    critical_false_negatives = sum(
        1
        for row in rows
        if row.severity == Severity.CRITICAL
        and row.expected_verdict == Verdict.WARNING
        and row.actual_verdict != Verdict.WARNING
    )
    return BenchmarkSummary(
        total=total,
        passed=passed,
        pass_rate=1.0 if total == 0 else passed / total,
        critical_false_positives=critical_false_positives,
        critical_false_negatives=critical_false_negatives,
        unknown_expected=len(unknown_rows),
        unknown_correct=sum(row.actual_verdict == Verdict.UNKNOWN for row in unknown_rows),
        unknown_discipline=(
            1.0
            if not unknown_rows
            else sum(row.actual_verdict == Verdict.UNKNOWN for row in unknown_rows) / len(unknown_rows)
        ),
        source_required_cases=len(source_rows),
        high_critical_source_completeness=(
            1.0
            if not source_rows
            else sum(row.source_requirement_satisfied for row in source_rows) / len(source_rows)
        ),
        pre_cutoff_cases=len(pre_cutoff_rows),
        retrospective_cases=len(retrospective_rows),
        pre_cutoff_temporal_integrity=(
            1.0
            if not pre_cutoff_rows
            else sum(row.temporal_integrity_satisfied for row in pre_cutoff_rows) / len(pre_cutoff_rows)
        ),
    )


def evaluate_manifest(
    manifest_path: Path,
    tolerance: TolerancePolicy,
) -> tuple[list[BenchmarkResult], BenchmarkSummary]:
    load_financial_integrity_rules()
    rows = [evaluate_case(case, manifest_path, tolerance) for case in load_manifest(manifest_path)]
    return rows, summarize(rows)
