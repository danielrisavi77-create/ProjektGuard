from projektguard.benchmark.evaluator import BenchmarkResult, summarize
from projektguard.domain.enums import Severity, Verdict


def row(*, expected, actual, severity=Severity.CRITICAL, passed=False, source_required=False, source_ok=True):
    return BenchmarkResult(
        test_id="T", rule_id="R", expected_verdict=expected, actual_verdict=actual,
        severity=severity, passed=passed, source_required=source_required,
        source_requirement_satisfied=source_ok,
    )


def test_critical_warning_against_expected_unknown_counts_as_false_positive():
    summary = summarize([row(expected=Verdict.UNKNOWN, actual=Verdict.WARNING)])
    assert summary.critical_false_positives == 1


def test_expected_critical_warning_missed_by_engine_counts_as_false_negative():
    summary = summarize([row(expected=Verdict.WARNING, actual=Verdict.VERIFIED)])
    assert summary.critical_false_negatives == 1


def test_source_completeness_denominator_only_includes_cases_that_require_sources():
    summary = summarize([
        row(expected=Verdict.WARNING, actual=Verdict.WARNING, source_required=True, source_ok=False),
        row(expected=Verdict.VERIFIED, actual=Verdict.VERIFIED, source_required=False, source_ok=True),
    ])
    assert summary.high_critical_source_completeness == 0.0


def test_pre_cutoff_temporal_integrity_rejects_future_source():
    from datetime import date
    from decimal import Decimal
    from projektguard.benchmark.evaluator import _temporal_integrity
    from projektguard.benchmark.models import BenchmarkCase, BenchmarkExpectation, BenchmarkMode
    from projektguard.domain.models import AuditContext, Cost, EligibilityPeriod, ProjectFinancials, SourceRef

    case = BenchmarkCase(
        test_id="T-pre", case_id="T", rule_id="R04", fixture="unused.json",
        expected=BenchmarkExpectation(verdict=Verdict.VERIFIED), source_url="synthetic",
        ground_truth="temporal fixture", mode=BenchmarkMode.PRE_CUTOFF,
    )
    context = AuditContext(
        project_id="P", as_of=date(2026, 5, 1),
        eligibility=EligibilityPeriod(start=date(2026, 1, 1), end=date(2026, 12, 31)),
        financials=ProjectFinancials(total_project_cost=Decimal("100"), eligible_cost=Decimal("90"), grant_amount=Decimal("50"), currency="EUR"),
        costs=[Cost(
            cost_id="C1", invoice_number="I1", invoice_date=date(2026, 4, 1), amount=Decimal("10"),
            currency="EUR", budget_line_id="B1", sources=[SourceRef(document_id="future.pdf", available_from=date(2026, 6, 1))],
        )],
    )
    assert _temporal_integrity(case, context) is False


def test_pre_cutoff_temporal_integrity_rejects_future_contract_execution_observation():
    from datetime import date
    from decimal import Decimal
    from projektguard.benchmark.evaluator import _temporal_integrity
    from projektguard.benchmark.models import BenchmarkCase, BenchmarkExpectation, BenchmarkMode
    from projektguard.domain.models import AuditContext, Contract, EligibilityPeriod, ProjectFinancials

    case = BenchmarkCase(
        test_id="T-pre", case_id="T", rule_id="R51", fixture="unused.json",
        expected=BenchmarkExpectation(verdict=Verdict.UNKNOWN), source_url="synthetic",
        ground_truth="temporal fixture", mode=BenchmarkMode.PRE_CUTOFF,
    )
    context = AuditContext(
        project_id="P", as_of=date(2026, 5, 1),
        eligibility=EligibilityPeriod(start=date(2026, 1, 1), end=date(2026, 12, 31)),
        financials=ProjektFinancials(total_project_cost=Decimal("100"), eligible_cost=Decimal("90"), grant_amount=Decimal("50"), currency="EUR"),
        contracts=[Contract(
            contract_id="C1", amount=Decimal("100"), currency="EUR", actual_paid=Decimal("120"),
            actual_paid_observed_at=date(2026, 6, 1),
        )],
    )
    assert _temporal_integrity(case, context) is False
