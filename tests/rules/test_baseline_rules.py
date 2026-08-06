from datetime import date
from decimal import Decimal

from projektguard.audit.runner import run_rule
from projektguard.audit.tolerance import TolerancePolicy
from projektguard.domain.enums import Verdict
from projektguard.domain.models import AuditContext, Contract, EligibilityPeriod, ProjectFinancials, SourceRef
import projektguard.rules.baseline


def _context(current_approved="100", actual_paid="120", changed=False, approval=None):
    return AuditContext(
        project_id="P1",
        as_of=date(2026, 5, 1),
        eligibility=EligibilityPeriod(start=date(2026, 1, 1), end=date(2026, 12, 31)),
        financials=ProjectFinancials(
            total_project_cost=Decimal("150"), eligible_cost=Decimal("120"), grant_amount=Decimal("80"),
            current_approved_project_cost=Decimal(current_approved), currency="EUR"
        ),
        contracts=[Contract(
            contract_id="CON1", amount=Decimal("100"), currency="EUR", actual_paid=Decimal(actual_paid)
        )],
        baseline_changed=changed,
        baseline_approval_source=approval,
    )


def test_r53_warns_when_known_execution_exceeds_current_approved_baseline():
    finding = run_rule("R53", _context(), TolerancePolicy())[0]
    assert finding.verdict == Verdict.WARNING
    assert finding.reason_code == "EXECUTION_EXCEEDS_PROJECT_BASELINE"


def test_r54_unknown_when_baseline_changed_but_approval_evidence_is_not_linked():
    finding = run_rule("R54", _context(changed=True, approval=None), TolerancePolicy())[0]
    assert finding.verdict == Verdict.UNKNOWN
    assert finding.reason_code == "BASELINE_APPROVAL_EVIDENCE_NOT_LINKED"


def test_r54_verified_when_change_has_linked_approval_source():
    source = SourceRef(document_id="addendum.pdf", page=1)
    finding = run_rule("R54", _context(changed=True, approval=source), TolerancePolicy())[0]
    assert finding.verdict == Verdict.VERIFIED
    assert finding.sources == [source]


def test_r62_verifies_total_eligible_and_grant_are_ordered():
    finding = run_rule("R62", _context(), TolerancePolicy())[0]
    assert finding.verdict == Verdict.VERIFIED


def test_r62_warns_when_eligible_cost_exceeds_total_project_cost():
    ctx = _context()
    ctx.financials.total_project_cost = Decimal("100")
    ctx.financials.eligible_cost = Decimal("120")
    finding = run_rule("R62", ctx, TolerancePolicy())[0]
    assert finding.verdict == Verdict.WARNING
    assert finding.reason_code == "FINANCIAL_AMOUNT_ORDER_INVALID"


def test_r62_unknown_when_financial_layers_are_incomplete():
    ctx = _context()
    ctx.financials.eligible_cost = None
    finding = run_rule("R62", ctx, TolerancePolicy())[0]
    assert finding.verdict == Verdict.UNKNOWN
    assert finding.reason_code == "FINANCIAL_AMOUNT_LAYER_INCOMPLETE"
