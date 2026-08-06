from datetime import date

from projektguard.benchmark.evaluator import _temporal_integrity
from projektguard.benchmark.models import BenchmarkCase, BenchmarkExpectation, BenchmarkMode
from projektguard.domain.enums import Verdict
from projektguard.domain.models import AuditContext, EligibilityPeriod, ProjectFinancials


def _context() -> AuditContext:
    return AuditContext(
        project_id="P",
        as_of=date(2020, 6, 30),
        eligibility=EligibilityPeriod(start=date(2018, 1, 1), end=date(2020, 12, 31)),
        financials=ProjectFinancials(currency="HRK"),
    )


def test_pre_cutoff_requires_later_ground_truth_metadata():
    case = BenchmarkCase(
        test_id="T-pre-ground-required",
        case_id="T",
        rule_id="R51",
        fixture="unused.json",
        expected=BenchmarkExpectation(verdict=Verdict.UNKNOWN),
        source_url="https://example.test/input",
        source_observed_at=date(2020, 1, 1),
        ground_truth="later outcome",
        mode=BenchmarkMode.PRE_CUTOFF,
    )
    assert _temporal_integrity(case, _context()) is False


def test_pre_cutoff_requires_ground_truth_url_and_verdict():
    missing_url = BenchmarkCase(
        test_id="T-pre-ground-url",
        case_id="T",
        rule_id="R51",
        fixture="unused.json",
        expected=BenchmarkExpectation(verdict=Verdict.UNKNOWN),
        source_url="https://example.test/input",
        source_observed_at=date(2020, 1, 1),
        ground_truth="later outcome",
        ground_truth_observed_at=date(2020, 7, 1),
        ground_truth_verdict=Verdict.WARNING,
        mode=BenchmarkMode.PRE_CUTOFF,
    )
    missing_verdict = BenchmarkCase(
        test_id="T-pre-ground-verdict",
        case_id="T",
        rule_id="R51",
        fixture="unused.json",
        expected=BenchmarkExpectation(verdict=Verdict.UNKNOWN),
        source_url="https://example.test/input",
        source_observed_at=date(2020, 1, 1),
        ground_truth="later outcome",
        ground_truth_url="https://example.test/outcome",
        ground_truth_observed_at=date(2020, 7, 1),
        mode=BenchmarkMode.PRE_CUTOFF,
    )
    assert _temporal_integrity(missing_url, _context()) is False
    assert _temporal_integrity(missing_verdict, _context()) is False
